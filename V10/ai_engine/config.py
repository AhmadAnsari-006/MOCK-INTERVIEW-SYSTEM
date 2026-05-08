from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AiConfig:
    provider: str
    chat_model: str
    embedding_model: str
    ollama_base_url: str
    request_timeout_s: float


def load_ai_config() -> AiConfig:
    provider = (os.environ.get("AI_PROVIDER") or "ollama").strip().lower()
    chat_model = (os.environ.get("AI_CHAT_MODEL") or "llama3.1:8b").strip()
    embedding_model = (os.environ.get("AI_EMBED_MODEL") or "sentence-transformers/all-MiniLM-L6-v2").strip()
    ollama_base_url = (os.environ.get("OLLAMA_BASE_URL") or "http://127.0.0.1:11434").strip().rstrip("/")
    timeout = float(os.environ.get("AI_REQUEST_TIMEOUT_S") or "60")

    return AiConfig(
        provider=provider,
        chat_model=chat_model,
        embedding_model=embedding_model,
        ollama_base_url=ollama_base_url,
        request_timeout_s=timeout,
    )

