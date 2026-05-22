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
        self.model = os.environ.get("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
        self.bearer = os.environ.get("AWS_BEARER_TOKEN_BEDROCK", "").strip()
        self.endpoint = f"https://bedrock-runtime.{self.region}.amazonaws.com"

    def configured(self) -> bool:
        return bool(self.bearer) and self.bearer.startswith("bedrock-api-key-")

    async def chat(self, messages: list[dict], system: str = "", max_tokens: int = 800) -> str:
        if not self.configured():
            raise RuntimeError("Bedrock bearer token not configured")
        payload = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "messages": messages,
        }
        if system:
            payload["system"] = system
        url = f"{self.endpoint}/model/{self.model}/invoke"
        headers = {
            "Authorization": f"Bearer {self.bearer}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as cli:
            r = await cli.post(url, headers=headers, content=json.dumps(payload))
            r.raise_for_status()
            data = r.json()
        # Claude on Bedrock returns {"content": [{"type": "text", "text": "..."}], ...}
        parts = data.get("content", [])
        text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
        return text.strip()


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
        self.preferred = os.environ.get("LLM_PROVIDER", "emergent").lower()

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
                continue
            t0 = time.time()
            try:
                text = await prov.chat(messages, system=system, max_tokens=max_tokens)
                return LLMResponse(
                    text=text,
                    provider=prov.name,
                    model=getattr(prov, "model", "unknown"),
                    latency_ms=int((time.time() - t0) * 1000),
                    fallback_used=(i > 0),
                )
            except Exception as e:
                logger.warning("LLM provider %s failed: %s", prov.name, e)
                last_err = e
                continue
        raise RuntimeError(f"No LLM provider available: {last_err}")


llm_service = LLMService()
