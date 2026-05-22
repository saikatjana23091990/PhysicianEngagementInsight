# AWS Deployment Guide

This document describes the recommended AWS architecture for deploying the Commercial Analytics Platform from local prototype to enterprise production.

## 1. Target Architecture

```
                          ┌─────────────────────┐
            Users ───────►│ CloudFront + WAF    │
                          └──────────┬──────────┘
                                     │
                       ┌─────────────▼──────────────┐
                       │  S3 (Static React build)   │
                       └────────────────────────────┘
                                     │
                     /api routes via Origin Failover
                                     │
                       ┌─────────────▼──────────────┐
                       │  API Gateway (HTTP API)    │
                       └─────────────┬──────────────┘
                                     │
                       ┌─────────────▼──────────────┐
                       │  Lambda (Mangum + FastAPI) │  ← scales to demand
                       │   OR   ECS Fargate         │  ← long-running RAG
                       └──┬───────────┬─────────────┘
                          │           │
              ┌───────────▼───┐   ┌───▼──────────────┐
              │ MongoDB Atlas │   │  Amazon Bedrock  │
              │ (or DynamoDB) │   │ Claude + Titan   │
              └───────────────┘   └──────────────────┘
                          │
              ┌───────────▼──────────────┐
              │ S3 raw data lake         │ ← future Glue/Athena pipelines
              └──────────────────────────┘

Secrets:    AWS Secrets Manager / SSM Parameter Store
Logs:       CloudWatch Logs + CloudWatch Insights
Tracing:    X-Ray (optional)
CI/CD:      GitHub Actions → AWS (OIDC, no static creds)
```

## 2. Prerequisites

- AWS account with admin in a dedicated `commercial-analytics` OU
- Domain in Route 53 (optional)
- GitHub repo with OIDC federation to AWS
- MongoDB Atlas project (or RDS for relational)

## 3. Frontend Deployment (S3 + CloudFront)

```bash
cd frontend
REACT_APP_BACKEND_URL=https://api.your-domain.com yarn build

aws s3 sync build/ s3://kiwi-commercial-frontend --delete
aws cloudfront create-invalidation \
  --distribution-id E_DISTRIBUTION_ID --paths "/*"
```

**CloudFront behaviors:**
- Default → S3 bucket (private with OAC)
- `/api/*` → API Gateway origin
- Cache: HTML no-cache, static `Cache-Control: max-age=31536000, immutable`

## 4. Backend Deployment Options

### Option A — Lambda + Mangum (recommended for cost/scale)

```python
# backend/lambda_handler.py
from mangum import Mangum
from server import app
handler = Mangum(app, lifespan="on")
```

Container image (`backend/Dockerfile.lambda`):
```dockerfile
FROM public.ecr.aws/lambda/python:3.11
COPY requirements.txt ./
RUN pip install -r requirements.txt
COPY . ./
CMD ["lambda_handler.handler"]
```

Deploy with SAM/CDK/Terraform. Set Lambda memory to ≥2GB, timeout 60s.

### Option B — ECS Fargate (for longer RAG sessions)

- ECS service behind ALB
- Docker image built from `backend/Dockerfile`
- Target task: 1 vCPU / 2 GB minimum
- Auto-scaling on `ALBTargetGroup_RequestCountPerTarget`

## 5. Database

### MongoDB Atlas (preferred)

- Create M10 cluster minimum for production
- Enable Atlas Vector Search if upgrading RAG beyond TF-IDF
- Connection string stored in Secrets Manager → injected at runtime

### Alternative: DynamoDB

- HCP, account, product → DynamoDB tables (single-table-design possible)
- Conversion events → DynamoDB stream → Lambda for re-computation
- AI outputs → DynamoDB with TTL for cache/eviction

## 6. AWS Bedrock Setup

```bash
aws bedrock list-foundation-models --region us-east-1 \
  --query "modelSummaries[?contains(modelId, 'claude') && contains(modelId, 'sonnet')].modelId"
```

Enable model access in **Bedrock Console → Model access**:
- `anthropic.claude-3-5-sonnet-20241022-v2:0`
- `amazon.titan-embed-text-v2:0`

### IAM policy for the runtime role

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0",
        "arn:aws:bedrock:us-east-1::foundation-model/amazon.titan-embed-text-v2:0"
      ]
    }
  ]
}
```

Set `LLM_PROVIDER=bedrock` in the Lambda/ECS task env. With an attached IAM role, boto3 picks up credentials automatically; no `AWS_BEARER_TOKEN_BEDROCK` needed in production.

For short-term demo with a bearer token (the format `bedrock-api-key-<base64>`), set `AWS_BEARER_TOKEN_BEDROCK` in env and the platform uses HTTP bearer auth.

## 7. Secrets Management

Store in **AWS Secrets Manager**:
- `commercial-analytics/mongo-uri`
- `commercial-analytics/bedrock-bearer-token` (if applicable)
- `commercial-analytics/emergent-llm-key` (fallback)

Lambda/ECS task definition references these by ARN; the platform loads them via `python-dotenv` or directly via boto3 at startup.

## 8. Networking

- Lambda in VPC if accessing private MongoDB peering (NAT gateway needed for Bedrock)
- Public Lambda is cheaper; Bedrock + Atlas both internet-reachable
- WAF on CloudFront with AWS Managed Rules (CommonRuleSet, KnownBadInputs)

## 9. CI/CD with GitHub Actions

`.github/workflows/deploy.yml`:
```yaml
name: Deploy
on:
  push:
    branches: [main]
permissions:
  id-token: write
  contents: read
jobs:
  build-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20, cache: yarn }
      - run: cd frontend && yarn install --frozen-lockfile && yarn build
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
          aws-region: us-east-1
      - run: aws s3 sync frontend/build s3://${{ secrets.S3_BUCKET }} --delete
      - run: aws cloudfront create-invalidation --distribution-id ${{ secrets.CF_DIST_ID }} --paths "/*"

  build-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_DEPLOY_ROLE_ARN }}
          aws-region: us-east-1
      - name: Build & push image
        run: |
          docker build -t backend backend/
          ECR=$(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com
          aws ecr get-login-password | docker login --username AWS --password-stdin $ECR
          docker tag backend $ECR/commercial-backend:${{ github.sha }}
          docker push $ECR/commercial-backend:${{ github.sha }}
      - run: aws lambda update-function-code --function-name commercial-backend --image-uri $ECR/commercial-backend:${{ github.sha }}
```

## 10. Cost Optimization

| Component | Monthly estimate (light usage) |
|---|---|
| Lambda (1M invocations, 2GB) | ~$8 |
| API Gateway | ~$3 |
| CloudFront + S3 | ~$5 |
| MongoDB Atlas M10 | ~$60 |
| Bedrock Claude (1M tokens in / 100k out daily) | ~$80–150 |
| Secrets Manager | ~$2 |
| **Total** | **~$160–230 / month** |

Recommendations:
- Cache narrative + briefing outputs by `(hcp_id, version_hash)` in DynamoDB (24-hour TTL)
- Use Bedrock prompt caching for repeated context blocks
- Switch to Claude Haiku for lower-stakes endpoints (conversational drilldowns)

## 11. Security Hardening

- **WAF** rules on CloudFront
- **PHI masking** at API boundary (currently UI-only)
- **VPC endpoints** for Bedrock if running in private subnets
- **Audit logging** to CloudWatch Logs + S3 archive (30/90/365 retention tiers)
- **Role-based access** — extend the demo role switcher to Cognito groups in production
- **Rate limiting** on `/api/chat/ask` and `/api/briefing/generate` to manage Bedrock cost

## 12. Future Evolution Path

- **Glue + Athena** over `s3://kiwi-data-lake/{raw|silver|gold}` for batch enrichment
- **Step Functions** for nightly conversion-attribution recomputation
- **MSK / Kinesis** for near-real-time CRM ingestion
- **SageMaker Pipelines** for production XGBoost / LightGBM training of opportunity propensity
- **Bedrock Knowledge Bases** for managed RAG over publications/labels
- **OpenSearch** for full-text source explorer (replacing in-memory store)
