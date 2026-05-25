"""
LLM provider abstraction.

Order of preference (configurable via LLM_PROVIDER env):
- bedrock: AWS Bedrock with hybrid auth:
  * Primary: boto3 with AWS SigV4 (when AWS_ACCESS_KEY_ID available)
  * Fallback: Direct HTTP with bearer token (AWS_BEARER_TOKEN_BEDROCK)
- emergent: Emergent LLM key + emergentintegrations (Claude Sonnet 4.5)

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

import boto3
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
        self.model = os.environ.get("BEDROCK_MODEL_ID", "us.anthropic.claude-haiku-4-5-20251001-v1:0")
        self.bearer = os.environ.get("AWS_BEARER_TOKEN_BEDROCK", "").strip()
        self.endpoint = f"https://bedrock-runtime.{self.region}.amazonaws.com"
        
        self.client = None
        self.use_bearer = False
        self.use_boto3 = False
        
        # Try boto3 first (production with AWS credentials)
        try:
            # Check if AWS credentials are available
            creds = boto3.Session().get_credentials()
            if creds:
                self.client = boto3.client("bedrock-runtime", region_name=self.region)
                self.use_boto3 = True
                logger.info("Bedrock: Using boto3 + AWS SigV4 authentication (region=%s)", self.region)
            else:
                logger.debug("Bedrock: No AWS credentials found, will try bearer token")
        except Exception as e:
            logger.debug("Bedrock: boto3 initialization issue: %s", str(e)[:100])
        
        # Fallback to bearer token
        if not self.use_boto3:
            if self.bearer and self.bearer.startswith("bedrock-api-key-"):
                self.use_bearer = True
                logger.info("Bedrock: Using bearer token authentication")
            else:
                logger.warning("Bedrock: No valid authentication method found. Bearer token not configured or invalid.")

    def configured(self) -> bool:
        return self.use_boto3 or self.use_bearer

    async def chat(self, messages: list[dict], system: str = "", max_tokens: int = 800) -> str:
        if not self.configured():
            raise RuntimeError("Bedrock not configured. Set AWS credentials or AWS_BEARER_TOKEN_BEDROCK env var.")
        
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            payload["system"] = system
        
        if self.use_boto3:
            return await self._chat_boto3(payload)
        else:
            return await self._chat_bearer(payload)

    async def _chat_boto3(self, payload: dict) -> str:
        """Call Bedrock using boto3 with AWS SigV4."""
        try:
            logger.debug("Bedrock: invoke_model with boto3, model=%s", self.model)
            response = self.client.invoke_model(
                modelId=self.model,
                contentType="application/json",
                body=json.dumps(payload),
            )
            
            response_body = json.loads(response.get("body").read())
            logger.debug("Bedrock: Response keys: %s", list(response_body.keys()))
            
            parts = response_body.get("content", [])
            text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
            
            if not text:
                logger.warning("Bedrock: Empty response content")
            else:
                logger.debug("Bedrock: Got %d chars", len(text))
            
            return text.strip()
        except Exception as e:
            logger.error("Bedrock: boto3 invoke_model failed: %s", str(e)[:300])
            raise RuntimeError(f"Bedrock boto3 error: {str(e)[:100]}")

    async def _chat_bearer(self, payload: dict) -> str:
        """Call Bedrock using bearer token via httpx."""
        try:
            url = f"{self.endpoint}/model/{self.model}/invoke"
            headers = {
                "Authorization": f"Bearer {self.bearer}",
                "Content-Type": "application/json",
            }
            
            logger.debug("Bedrock: invoke via bearer token, model=%s", self.model)
            async with httpx.AsyncClient(timeout=30.0) as cli:
                r = await cli.post(url, headers=headers, content=json.dumps(payload))
                r.raise_for_status()
                data = r.json()
            
            logger.debug("Bedrock: Bearer response keys: %s", list(data.keys()))
            
            parts = data.get("content", [])
            text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
            
            if not text:
                logger.warning("Bedrock: Empty response content")
            else:
                logger.debug("Bedrock: Got %d chars", len(text))
            
            return text.strip()
        except httpx.HTTPStatusError as e:
            logger.error("Bedrock: Bearer token HTTP error %d: %s", e.response.status_code, e.response.text[:500])
            raise RuntimeError(f"Bedrock API error {e.response.status_code}: {e.response.text[:200]}")
        except Exception as e:
            logger.error("Bedrock: Bearer token request failed: %s", str(e)[:300])
            raise RuntimeError(f"Bedrock bearer error: {str(e)[:100]}")

    async def stream(self, messages: list[dict], system: str = "", max_tokens: int = 800):
        """Native Bedrock streaming. Supports both boto3 and bearer token auth."""
        if not self.configured():
            raise RuntimeError("Bedrock not configured")
        
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            payload["system"] = system
        
        if self.use_boto3:
            async for delta in self._stream_boto3(payload):
                yield delta
        else:
            async for delta in self._stream_bearer(payload):
                yield delta

    async def _stream_boto3(self, payload: dict):
        """Stream using boto3's invoke_model_with_response_stream."""
        try:
            logger.debug("Bedrock: Starting boto3 streaming, model=%s", self.model)
            
            response = self.client.invoke_model_with_response_stream(
                modelId=self.model,
                contentType="application/json",
                body=json.dumps(payload),
            )
            
            for event in response.get("body").iter_events():
                try:
                    chunk = event.get("ContentBlockDelta")
                    if chunk:
                        delta = chunk.get("delta", {})
                        if delta.get("type") == "text_delta":
                            text = delta.get("text", "")
                            if text:
                                logger.debug("Bedrock: boto3 stream delta: %d chars", len(text))
                                yield text
                except Exception as e:
                    logger.warning("Bedrock: Error processing boto3 event: %s", str(e)[:100])
                    continue
        except Exception as e:
            logger.error("Bedrock: boto3 streaming failed: %s", str(e)[:300])
            raise RuntimeError(f"Bedrock boto3 streaming error: {str(e)[:100]}")

    async def _stream_bearer(self, payload: dict):
        """Stream using bearer token via httpx.
        
        Note: Bedrock's event-stream format is complex binary protocol.
        For bearer token auth, we use the non-streaming endpoint and emit word chunks.
        """
        try:
            logger.debug("Bedrock: Bearer streaming - using non-streaming endpoint with word chunking")
            
            # Use regular invoke endpoint (not invoke-with-response-stream)
            # because EventStream binary protocol is complex to parse manually
            url = f"{self.endpoint}/model/{self.model}/invoke"
            headers = {
                "Authorization": f"Bearer {self.bearer}",
                "Content-Type": "application/json",
            }
            
            # Get full response first
            async with httpx.AsyncClient(timeout=60.0) as cli:
                r = await cli.post(url, headers=headers, content=json.dumps(payload))
                r.raise_for_status()
                data = r.json()
            
            logger.debug("Bedrock: Bearer response keys: %s", list(data.keys()))
            
            # Extract text from response
            parts = data.get("content", [])
            full_text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
            
            if not full_text:
                logger.warning("Bedrock: Empty response content")
                return
            
            logger.debug("Bedrock: Got %d chars, emitting word-by-word", len(full_text))
            
            # Emit word-by-word for streaming UX
            words = full_text.split(" ")
            for word in words:
                yield word + " "
        
        except httpx.HTTPStatusError as e:
            logger.error("Bedrock: Bearer token HTTP error %d: %s", e.response.status_code, e.response.text[:500])
            raise RuntimeError(f"Bedrock API error {e.response.status_code}")
        except Exception as e:
            logger.error("Bedrock: Bearer token streaming failed: %s", str(e)[:300])
            raise RuntimeError(f"Bedrock bearer streaming error: {str(e)[:100]}")


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
        """Async generator yielding text deltas. Uses native Bedrock streaming when available, falls back to chunking."""
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
                fallback = order[1][0] if len(order) > 1 and order[1][1].configured() else "none"
                logger.warning("Bedrock streaming failed: %s. Falling back to %s", str(e)[:200], fallback)

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
                logger.warning("Provider %s failed during streaming: %s", prov_name, str(e)[:200])
                continue
        
        logger.error("No LLM provider available")
        yield {"type": "error", "text": "No LLM provider available"}


llm_service = LLMService()
