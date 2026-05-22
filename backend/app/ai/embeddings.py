"""
Embeddings layer with two backends:

1. BedrockTitanEmbeddings — production-quality via Amazon Titan (amazon.titan-embed-text-v2:0)
2. LocalSVDEmbeddings — TF-IDF + TruncatedSVD (256d) for offline demo

Both expose `embed(texts: list[str]) -> np.ndarray (N x D)`.
"""
from __future__ import annotations

import json
import logging
import os
import threading
from typing import Optional

import httpx
import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

logger = logging.getLogger("app.embeddings")

EMBED_DIM = 256


class LocalSVDEmbeddings:
    """Lightweight: TF-IDF + TruncatedSVD → unit-norm 256d vectors."""
    name = "local-svd"
    dim = EMBED_DIM

    def __init__(self) -> None:
        self.tfidf: Optional[TfidfVectorizer] = None
        self.svd: Optional[TruncatedSVD] = None
        self._lock = threading.Lock()

    def fit(self, corpus: list[str]) -> None:
        with self._lock:
            tfidf = TfidfVectorizer(max_features=6000, ngram_range=(1, 2), stop_words="english")
            X = tfidf.fit_transform(corpus or [" "])
            k = min(EMBED_DIM, max(2, X.shape[1] - 1, X.shape[0] - 1))
            svd = TruncatedSVD(n_components=k, random_state=42)
            svd.fit(X)
            self.tfidf = tfidf
            self.svd = svd
            self.dim = k

    def embed(self, texts: list[str]) -> np.ndarray:
        if self.tfidf is None or self.svd is None:
            raise RuntimeError("LocalSVDEmbeddings not fitted yet")
        X = self.tfidf.transform([t or " " for t in texts])
        emb = self.svd.transform(X)
        emb = normalize(emb, axis=1)
        # pad to EMBED_DIM with zeros to keep schema stable across runs
        if emb.shape[1] < EMBED_DIM:
            pad = np.zeros((emb.shape[0], EMBED_DIM - emb.shape[1]))
            emb = np.hstack([emb, pad])
        return emb


class BedrockTitanEmbeddings:
    name = "titan"
    dim = 1024  # Titan v2 returns 1024-d

    def __init__(self) -> None:
        self.region = os.environ.get("AWS_REGION", "us-east-1")
        self.model = os.environ.get("BEDROCK_EMBEDDING_MODEL", "amazon.titan-embed-text-v2:0")
        self.bearer = os.environ.get("AWS_BEARER_TOKEN_BEDROCK", "").strip()
        self.endpoint = f"https://bedrock-runtime.{self.region}.amazonaws.com"

    def configured(self) -> bool:
        return bool(self.bearer) and self.bearer.startswith("bedrock-api-key-")

    def embed(self, texts: list[str]) -> np.ndarray:
        out = []
        with httpx.Client(timeout=30.0) as cli:
            for t in texts:
                r = cli.post(
                    f"{self.endpoint}/model/{self.model}/invoke",
                    headers={"Authorization": f"Bearer {self.bearer}", "Content-Type": "application/json"},
                    content=json.dumps({"inputText": (t or " ")[:8000], "dimensions": EMBED_DIM, "normalize": True}),
                )
                r.raise_for_status()
                vec = r.json().get("embedding", [])
                out.append(vec)
        arr = np.array(out, dtype=float)
        # truncate / pad to EMBED_DIM
        if arr.shape[1] > EMBED_DIM:
            arr = arr[:, :EMBED_DIM]
        elif arr.shape[1] < EMBED_DIM:
            pad = np.zeros((arr.shape[0], EMBED_DIM - arr.shape[1]))
            arr = np.hstack([arr, pad])
        return arr


def get_embeddings_provider() -> object:
    """Choose embeddings provider. Local SVD is the safe demo default."""
    provider = os.environ.get("EMBED_PROVIDER", "local").lower()
    if provider == "titan":
        emb = BedrockTitanEmbeddings()
        if emb.configured():
            return emb
        logger.warning("Titan embeddings not configured; falling back to local SVD")
    return LocalSVDEmbeddings()
