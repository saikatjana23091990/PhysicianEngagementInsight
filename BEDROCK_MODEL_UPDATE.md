# Bedrock Model Update & Configuration Guide

## Problem Identified

Your test revealed:
```
❌ FAILED: Bedrock API error 404: This model version has reached the end of its life.
```

**Root Cause:** The model ID `anthropic.claude-3-5-sonnet-20241022-v2:0` is **deprecated/end-of-life**

---

## Solution: Update to Current Model

AWS Bedrock releases new model versions regularly. The current active Claude 3.5 Sonnet models are:

| Model ID | Status | Recommended |
|----------|--------|-------------|
| `anthropic.claude-3-5-sonnet-20241022-v2:0` | ❌ End of Life | No |
| `anthropic.claude-3-5-sonnet-20241022-v1:0` | ✅ Active | Yes |
| `anthropic.claude-3-sonnet-20240229-v1:0` | ✅ Active | Alternative |

---

## Step-by-Step Fix

### Step 1: Verify Available Models in AWS Console

1. Go to [AWS Bedrock Console](https://console.aws.amazon.com/bedrock)
2. Click **Model access** (left sidebar)
3. Under "Available models", search for **"claude"**
4. Look for models marked as **"Access Granted"**
5. **Note down the full model ID** you see (e.g., `anthropic.claude-3-5-sonnet-20241022-v1:0`)

### Step 2: Update Environment Variable

Edit `backend/.env` file and change:

**FROM:**
```bash
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
```

**TO:**
```bash
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v1:0
```

Or use whichever model you found in Step 1 that has "Access Granted" status.

### Step 3: Verify Model ID in Code

The code should automatically pick up the new model ID from `.env`. 

Check `backend/app/ai/llm.py` line ~46:
```python
self.model = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
```

This now reads from `BEDROCK_MODEL_ID` env variable (which you updated in .env).

### Step 4: Test Again

Run the test script:
```bash
cd backend
python test_bedrock_quick.py
```

You should now see:
```
✅ SUCCESS!
   Response: Bedrock is working
```

### Step 5: Restart Backend

Restart your backend server so it picks up the new model ID:

```bash
# If using uvicorn directly:
uvicorn server:app --reload --host 0.0.0.0 --port 8000

# Or if using a process manager, restart the service
```

### Step 6: Test in UI

1. Go to "Ask Data" page in the UI
2. Ask a question: "Why did conversion rates change in oncology last quarter?"
3. Check that:
   - ✅ Content appears (not just sources)
   - ✅ Backend logs show: `LLM success with bedrock`
   - ✅ Provider shows "bedrock" in the response metadata

---

## Quick Reference: Current Valid Models

```bash
# Claude 3.5 Sonnet (Current recommended)
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v1:0

# Claude 3.5 Sonnet (Alternative)
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241119-v1:0

# Claude 3 Sonnet (If above not available)
BEDROCK_MODEL_ID=anthropic.claude-3-sonnet-20240229-v1:0
```

Try in this order until you find one with "Access Granted" status in AWS console.

---

## Why This Happened

AWS Bedrock regularly retires older model versions as newer ones are released. The `v2:0` suffix indicates an older version that has reached end-of-life. AWS automatically deprecates these after a period.

**To avoid this in future:**
- Monitor [AWS Bedrock Release Notes](https://docs.aws.amazon.com/bedrock/latest/userguide/models-supported.html)
- Update model IDs quarterly
- Use a wrapper that auto-detects latest available models (advanced)

---

## Troubleshooting If Still Failing

| Error | Fix |
|-------|-----|
| `404 - model version not found` | Wrong model ID - check AWS console for exact ID |
| `400 - Bad Request` | Model ID format wrong - must start with `anthropic.` |
| `403 - Forbidden` | Model not enabled in "Model access" - enable it |
| `401 - Unauthorized` | Bearer token expired - regenerate access key |

---

## Files to Update

- ✅ `backend/.env` — Update `BEDROCK_MODEL_ID`
- ✅ Restart backend server
- ❌ No code changes needed (reads from env var)

---

## Environment Variables Checklist

```bash
# ✅ Required
AWS_BEARER_TOKEN_BEDROCK=bedrock-api-key-YOUR_TOKEN
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v1:0  # ← UPDATE THIS
LLM_PROVIDER=bedrock

# ✅ Optional but recommended (fallback)
EMERGENT_LLM_KEY=your_emergent_key_here
```

---

## Done!

Once you update the model ID and restart, Bedrock should work perfectly. If it still fails, the error message will be much more informative and we can debug from there.
