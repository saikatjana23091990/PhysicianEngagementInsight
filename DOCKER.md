# Docker Guide

This repo has separate container images for the FastAPI backend and the React frontend.

## Build and run the full app

```bash
docker compose up --build
```

Open:

- Frontend: http://localhost:3000
- Backend API: http://localhost:8001
- Backend health: http://localhost:8001/api/health

MongoDB is started by Compose and persisted in the `mongo-data` volume. The backend also loads the demo CSV data baked into the image from `/app/data/raw/data`.

## Build images only

```bash
docker compose build
```

This creates:

- `physician-engagement-backend:local`
- `physician-engagement-frontend:local`

## Run only the backend image

```bash
docker build -f backend/Dockerfile.api -t physician-engagement-backend:local .
docker run --rm -p 8001:8001 physician-engagement-backend:local
```

For AI-backed features, pass the same environment variables used locally:

```bash
docker run --rm -p 8001:8001 ^
  -e LLM_PROVIDER=bedrock ^
  -e AWS_REGION=us-east-1 ^
  -e AWS_BEARER_TOKEN_BEDROCK=your-token ^
  physician-engagement-backend:local
```

On macOS/Linux, replace `^` with `\` for multiline commands.

## Frontend API URL

The frontend image bakes `REACT_APP_BACKEND_URL` at build time. Compose defaults it to `http://localhost:8001`, which works when you open the app from the same machine running Docker.

To build for another backend URL:

```bash
REACT_APP_BACKEND_URL=https://api.example.com docker compose build frontend
```

PowerShell:

```powershell
$env:REACT_APP_BACKEND_URL="https://api.example.com"
docker compose build frontend
```

## Notes

- `backend/Dockerfile` is still the AWS Lambda image Dockerfile.
- `backend/Dockerfile.api` is the standard FastAPI runtime image.
- `.dockerignore` excludes local virtualenvs, `node_modules`, existing frontend builds, and local `.env` files from the Docker build context.
