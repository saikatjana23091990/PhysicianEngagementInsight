# Bedrock Setup & Troubleshooting Guide

## Current Configuration

**Model ID:** `anthropic.claude-3-5-sonnet-20241022-v2:0`  
**Region:** `us-east-1` (configurable via `AWS_REGION` env var)  
**Authentication:** Bearer Token (via `AWS_BEARER_TOKEN_BEDROCK`)

---

## Step 1: Verify Model Access in AWS Console

1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock)
2. Click **Model access** (left sidebar)
3. Search for "Claude 3.5 Sonnet"
4. Look for model: `anthropic.claude-3-5-sonnet-20241022-v2:0`
5. **Status must be: "Access Granted"**

If status is "Request access":
- Click the model row
- Click "Manage model access"
- Click "Enable" button
- Wait 1-5 minutes for activation

---

## Step 2: Generate/Get Bearer Token

### Method A: AWS Console (Short-term demo token)

1. Go to [AWS IAM Console](https://console.aws.amazon.com/iam)
2. Click **Users** → Select your user
3. Click **Security credentials** tab
4. Under "Access keys", click **Create access key**
5. Choose **"Application running outside AWS"**
6. Take note of:
   - Access Key ID
   - Secret Access Key
7. **Format the token:**
   ```
   bedrock-api-key-<base64-encoded-credentials>
   ```
   Where `<base64-encoded-credentials>` is:
   ```bash
   echo -n "AccessKeyID:SecretAccessKey" | base64
   ```

### Method B: AWS CLI (If installed)

```bash
# Get current credentials
aws sts get-caller-identity

# Create short-term credentials
aws sts get-session-token --duration-seconds 3600

# Format as bearer token:
# bedrock-api-key-<base64(AccessKeyId:SecretAccessKey)>
```

### Method C: Use IAM Role (Recommended - Easiest!)

If running on EC2/Lambda with an IAM role, **you don't need a bearer token**:
1. Ensure the IAM role has Bedrock permissions:

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
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
    }
  ]
}
```

2. Leave `AWS_BEARER_TOKEN_BEDROCK` **empty**
3. The code will auto-detect and use IAM role

---

## Step 3: Set Environment Variable

### Local Development (.env file)

Create or update `backend/.env`:

```bash
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
AWS_BEARER_TOKEN_BEDROCK=bedrock-api-key-YOUR_BASE64_TOKEN_HERE
LLM_PROVIDER=bedrock
EMERGENT_LLM_KEY=your_emergent_key_here  # Keep as backup
```

### Production (Lambda/ECS)

Set in environment variables:
```
AWS_BEARER_TOKEN_BEDROCK = bedrock-api-key-...
AWS_REGION = us-east-1
LLM_PROVIDER = bedrock
```

---

## Step 4: Test the Connection

### Method A: Python Test Script

Create `test_bedrock.py` in backend directory:

```python
import os
import asyncio
import json
from app.ai.llm import BedrockProvider

async def test():
    provider = BedrockProvider()
    print(f"Region: {provider.region}")
    print(f"Model: {provider.model}")
    print(f"Bearer token configured: {bool(provider.bearer)}")
    print(f"Is configured: {provider.configured()}")
    
    if not provider.configured():
        print("❌ Bedrock NOT configured")
        return
    
    print("\n📝 Testing with simple prompt...")
    try:
        text = await provider.chat(
            messages=[{"role": "user", "content": "Say 'Hello from Bedrock' in 5 words or less"}],
            system="You are a helpful assistant.",
            max_tokens=50
        )
        print(f"✅ Bedrock Success!\nResponse: {text}")
    except Exception as e:
        print(f"❌ Bedrock Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test())
```

Run it:
```bash
cd backend
python test_bedrock.py
```

### Method B: Via API Endpoint

Add this temporary test endpoint to `backend/app/api/health.py`:

```python
@router.get("/test_bedrock")
async def test_bedrock():
    from app.ai.llm import llm_service
    try:
        result = await llm_service.bedrock.chat(
            messages=[{"role": "user", "content": "Say 'Hello from Bedrock'"}],
            max_tokens=50
        )
        return {"status": "ok", "provider": "bedrock", "response": result[:100]}
    except Exception as e:
        return {"status": "error", "provider": "bedrock", "error": str(e)}
```

Then visit: `http://localhost:8000/api/health/test_bedrock`

---

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| `400 Not Found` | Invalid bearer token or model not enabled | Check token format; verify model access in console |
| `401 Unauthorized` | Bearer token expired | Regenerate new access key and token |
| `403 Forbidden` | IAM permissions missing | Add Bedrock policy to IAM role |
| `Model not found` | Wrong model ID | Verify model ID matches AWS console |
| `Connection timeout` | Network issue | Check AWS region; verify internet connection |

---

## Verify it's Working

After setting up, ask a question in "Ask Data" and check:

1. **Backend logs should show:**
   ```
   Attempting LLM provider: bedrock
   LLM success with bedrock (XXXms)
   ```

2. **Response should include:**
   - ✅ Sources AND content (not just sources)
   - ✅ Provider label showing "bedrock"
   - ✅ Latency in milliseconds

3. **If it falls back to Emergent:**
   ```
   LLM provider bedrock failed: ...
   Attempting LLM provider: emergent
   LLM success with emergent (XXXms)
   ```

---

## Quick Reference: Token Format

Your token should look like:
```
bedrock-api-key-QWNjZXNzS2V5SUR8U2VjcmV0QWNjZXNzS2V5
```

**NOT:**
```
bedrock-api-key-     (too short)
AWS_BEARER_TOKEN...  (wrong prefix)
your-plain-token     (not base64)
```

---

## Need Help?

- Check if model is **enabled** in Bedrock console → Model access
- Verify **token format**: `bedrock-api-key-` + base64
- Check **region matches**: us-east-1 (or your region)
- Look at backend logs for detailed error messages
- If stuck, fall back to Emergent (it's already working)
