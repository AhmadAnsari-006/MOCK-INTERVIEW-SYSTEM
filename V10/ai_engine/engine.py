from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ai_engine.config import AiConfig
from ai_engine.embeddings import embed_texts as st_embed_texts
from ai_engine.json_utils import build_json_instruction, parse_json_strict
from ai_engine.providers.base import ChatMessage, ChatProvider
from ai_engine.providers.ollama_provider import OllamaProvider


@dataclass(frozen=True)
class AiEngine:
    config: AiConfig
    provider: ChatProvider

    @staticmethod
    def from_config(cfg: AiConfig) -> "AiEngine":
        # For hackathon reliability, default to local Ollama. Other providers can be added later without changing callers.
        if cfg.provider == "ollama":
            prov = OllamaProvider(base_url=cfg.ollama_base_url, timeout_s=cfg.request_timeout_s)
            return AiEngine(config=cfg, provider=prov)

        # fallback to ollama (safe default) if unknown provider
        prov = OllamaProvider(base_url=cfg.ollama_base_url, timeout_s=cfg.request_timeout_s)
        return AiEngine(config=cfg, provider=prov)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return st_embed_texts(model_name=self.config.embedding_model, texts=texts)

    def chat_text(
        self,
        *,
        system: str,
        user: str,
        temperature: float = 0.2,
        max_output_tokens: int = 800,
    ) -> str:
        msgs = [
            ChatMessage(role="system", content=system or ""),
            ChatMessage(role="user", content=user or ""),
        ]
        return self.provider.chat(
            model=self.config.chat_model,
            messages=msgs,
            temperature=float(temperature),
            max_tokens=int(max_output_tokens),
        )

    def chat_json(
        self,
        *,
        system: str,
        user: str,
        schema_hint: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: int = 800,
    ) -> Dict[str, Any]:
        prompt = (user or "").strip()
        prompt = f"{prompt}\n\n{build_json_instruction(schema_hint)}"
        raw = self.chat_text(
            system=system,
            user=prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )
        return parse_json_strict(raw)

