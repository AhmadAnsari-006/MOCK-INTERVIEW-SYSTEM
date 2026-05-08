from __future__ import annotations

from typing import Any, Dict, List, Optional

from ai_engine.config import load_ai_config
from ai_engine.engine import AiEngine


class LlmService:
    """
    Backwards-compatible wrapper used by existing services/routes.

    Uses FREE models by default via local Ollama + sentence-transformers embeddings.
    Configure via env:
      - AI_PROVIDER=ollama
      - AI_CHAT_MODEL=llama3.1:8b (or mistral, phi, gemma etc.)
      - AI_EMBED_MODEL=sentence-transformers/all-MiniLM-L6-v2
      - OLLAMA_BASE_URL=http://127.0.0.1:11434
    """

    def __init__(self):
        cfg = load_ai_config()
        self._engine = AiEngine.from_config(cfg)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return self._engine.embed_texts(texts)

    def chat_json(
        self,
        *,
        system: str,
        user: str,
        schema_hint: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: int = 800,
    ) -> Dict[str, Any]:
        return self._engine.chat_json(
            system=system,
            user=user,
            schema_hint=schema_hint,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
