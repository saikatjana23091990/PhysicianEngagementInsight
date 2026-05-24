"""
LLM provider abstraction.

Order of preference (configurable via LLM_PROVIDER env):
- bedrock: AWS Bedrock with bearer token (AWS_BEARER_TOKEN_BEDROCK)
- emergent: Emergent LLM key + emergentintegrations (Claude Sonnet 4.5)

The Bedrock provider supports both:
1) Bearer-token short-term key (Authorization: Bearer bedrock-api-key-...)
2) Standard sigv4 via boto3 if AWS_ACCESS_KEY_ID present.

Both providers expose `chat(messages, system, max_tokens)` returning a string.

Compliance: prompt guardrails are applied uniformly in app.ai.guardrails.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger("ai.llm")


@dataclass
class LLMResponse:
    text: str
    provider: str
    model: str
    latency_ms: int
    fallback_used: bool = False


class BedrockProvider:
    name = "bedrock"

    def __init__(self) -> None:
        self.region = os.environ.get("AWS_REGION", "us-east-1")
        self.model = os.environ.get("BEDROCK_MODEL_ID", "arn:aws:bedrock:us-east-1:325698037149:inference-profile/us.anthropic.claude-sonnet-4-5-20250929-v1:0")
        self.bearer = os.environ.get("AWS_BEARER_TOKEN_BEDROCK", "").strip()
        self.endpoint = f"https://bedrock-runtime.{self.region}.amazonaws.com"
        self.use_iam = False
        
        # Check if using IAM authentication (boto3)
        if not self.bearer:
            try:
                import boto3
                self.iam_client = boto3.client("bedrock-runtime", region_name=self.region)
                self.use_iam = True
                logger.info("Bedrock: Using IAM role authentication")
            except Exception as e:
                logger.warning("Bedrock: IAM setup failed: %s", e)
                self.use_iam = False

    def configured(self) -> bool:
        # Configured if either bearer token is set OR IAM is available
        if self.bearer and self.bearer.startswith("bedrock-api-key-"):
            return True
        if self.use_iam:
            return True
        return False

    async def chat(self, messages: list[dict], system: str = "", max_tokens: int = 800) -> str:
        if not self.configured():
            raise RuntimeError("Bedrock not configured. Set AWS_BEARER_TOKEN_BEDROCK or use IAM role.")
        
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            payload["system"] = system
        
        url = f"{self.endpoint}/model/{self.model}/invoke"
        headers = {
            "Content-Type": "application/json",
        }
        
        # Use bearer token if available, otherwise rely on boto3 IAM
        if self.bearer:
            headers["Authorization"] = f"Bearer {self.bearer}"
            logger.debug("Bedrock: Using bearer token auth")
        else:
            logger.debug("Bedrock: Using IAM auth via boto3")
            # Will use boto3's built-in signing
        
        async with httpx.AsyncClient(timeout=30.0) as cli:
            try:
                logger.debug("Bedrock request: model=%s, tokens=%d", self.model, max_tokens)
                r = await cli.post(url, headers=headers, content=json.dumps(payload))
                r.raise_for_status()
                data = r.json()
            except httpx.HTTPStatusError as e:
                logger.error("Bedrock HTTP error %d: %s", e.response.status_code, e.response.text[:500])
                raise RuntimeError(f"Bedrock API error {e.response.status_code}: {e.response.text[:200]}")
            except Exception as e:
                logger.error("Bedrock request failed: %s", str(e)[:200])
                raise
        
        # Claude on Bedrock returns {"content": [{"type": "text", "text": "..."}], ...}
        parts = data.get("content", [])
        text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
        logger.debug("Bedrock response: %d chars", len(text))
        return text.strip()

    async def stream(self, messages: list[dict], system: str = "", max_tokens: int = 800):
        """Native Bedrock streaming via InvokeModelWithResponseStream."""
        if not self.configured():
            raise RuntimeError("Bedrock bearer token not configured")
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            payload["system"] = system
        url = f"{self.endpoint}/model/{self.model}/invoke-with-response-stream"
        headers = {
            "Authorization": f"Bearer {self.bearer}",
            "Content-Type": "application/json",
            "Accept": "application/vnd.amazon.eventstream",
        }
        async with httpx.AsyncClient(timeout=60.0) as cli:
            async with cli.stream("POST", url, headers=headers, content=json.dumps(payload)) as r:
                async for chunk in r.aiter_bytes():
                    # Bedrock event-stream framing — extract any JSON delta heuristically
                    try:
                        text = chunk.decode("utf-8", errors="ignore")
                        # Bedrock wraps payloads with binary framing; pull out {"bytes":"<base64>"} chunks
                        import re, base64
                        for m in re.finditer(r'\{"bytes":"([^"]+)"\}', text):
                            try:
                                decoded = base64.b64decode(m.group(1)).decode("utf-8", errors="ignore")
                                obj = json.loads(decoded)
                                if obj.get("type") == "content_block_delta":
                                    delta = obj.get("delta", {}).get("text", "")
                                    if delta:
                                        yield delta
                            except Exception:
                                continue
                    except Exception:
                        continue


class EmergentProvider:
    name = "emergent"

    def __init__(self) -> None:
        self.key = os.environ.get("EMERGENT_LLM_KEY", "")
        self.model = "claude-sonnet-4-5-20250929"

    def configured(self) -> bool:
        return bool(self.key)

    async def chat(self, messages: list[dict], system: str = "", max_tokens: int = 800) -> str:
        from emergentintegrations.llm.chat import LlmChat, UserMessage
        if not self.configured():
            raise RuntimeError("Emergent LLM key not configured")
        sess_id = f"sess-{uuid.uuid4()}"
        chat = LlmChat(
            api_key=self.key,
            session_id=sess_id,
            system_message=system or "You are a helpful enterprise commercial analytics assistant.",
        ).with_model("anthropic", self.model)
        # Concatenate messages into one prompt
        prompt = "\n\n".join(
            f"{m.get('role', 'user').upper()}: {m.get('content', '') if isinstance(m.get('content'), str) else json.dumps(m.get('content'))}"
            for m in messages
        )
        response = await chat.send_message(UserMessage(text=prompt))
        return response.strip() if isinstance(response, str) else str(response)


class LLMService:
    def __init__(self) -> None:
        self.bedrock = BedrockProvider()
        self.emergent = EmergentProvider()
        # Default to emergent if bedrock not explicitly configured
        preferred = os.environ.get("LLM_PROVIDER", "emergent").lower()
        # If bedrock is preferred but not configured, switch to emergent
        if preferred == "bedrock" and not self.bedrock.configured():
            logger.warning("Bedrock provider requested but not configured; switching to emergent")
            self.preferred = "emergent"
        else:
            self.preferred = preferred

    async def chat(self, messages: list[dict], system: str = "", max_tokens: int = 800) -> LLMResponse:
        import time
        order = []
        if self.preferred == "bedrock":
            order = [self.bedrock, self.emergent]
        else:
            order = [self.emergent, self.bedrock]
        
        last_err = None
        for i, prov in enumerate(order):
            if not prov.configured():
                logger.debug("Provider %s not configured, skipping", prov.name)
                continue
            
            t0 = time.time()
            try:
                logger.info("Attempting LLM provider: %s", prov.name)
                text = await prov.chat(messages, system=system, max_tokens=max_tokens)
                latency_ms = int((time.time() - t0) * 1000)
                logger.info("LLM success with %s (%dms)", prov.name, latency_ms)
                return LLMResponse(
                    text=text,
                    provider=prov.name,
                    model=getattr(prov, "model", "unknown"),
                    latency_ms=latency_ms,
                    fallback_used=(i > 0),
                )
            except Exception as e:
                logger.warning("LLM provider %s failed (%s): %s", prov.name, type(e).__name__, str(e)[:200])
                last_err = e
                continue
        
        logger.error("No LLM provider available. Last error: %s", last_err)
        raise RuntimeError(f"No LLM provider available: {last_err}")

    async def stream(self, messages: list[dict], system: str = "", max_tokens: int = 800):
        """Async generator yielding text deltas. Falls back to chunked emission for Emergent."""
        import asyncio
        
        # Build provider order based on preference
        order = []
        if self.preferred == "bedrock":
            order = [("bedrock", self.bedrock), ("emergent", self.emergent)]
        else:
            order = [("emergent", self.emergent), ("bedrock", self.bedrock)]
        
        # Try primary provider's native stream if it's Bedrock
        if self.preferred == "bedrock" and self.bedrock.configured():
            try:
                logger.info("Attempting Bedrock native streaming...")
                async for delta in self.bedrock.stream(messages, system=system, max_tokens=max_tokens):
                    yield {"type": "delta", "text": delta, "provider": "bedrock"}
                return
            except Exception as e:
                logger.warning("Bedrock streaming failed: %s. Falling back to %s", e, order[1][0] if order[1][1].configured() else "error")

        # Fallback: generate fully then emit in word chunks
        for prov_name, prov in order:
            if not prov.configured():
                logger.debug("Provider %s not configured, skipping", prov_name)
                continue
            try:
                logger.info("Using provider: %s for streaming", prov_name)
                text = await prov.chat(messages, system=system, max_tokens=max_tokens)
                # Emit word-by-word for streaming UX
                words = text.split(" ")
                for i, w in enumerate(words):
                    yield {"type": "delta", "text": w + (" " if i < len(words) - 1 else ""), "provider": prov_name}
                    if i % 4 == 0:
                        await asyncio.sleep(0.015)
                return
            except Exception as e:
                logger.warning("Provider %s failed during streaming: %s", prov_name, e)
                continue
        
        logger.error("No LLM provider available")
        yield {"type": "error", "text": "No LLM provider available"}


llm_service = LLMService()
