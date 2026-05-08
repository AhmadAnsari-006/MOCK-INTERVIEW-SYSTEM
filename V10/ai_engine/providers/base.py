from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


class ChatProvider:
    def chat(self, *, model: str, messages: List[ChatMessage], temperature: float, max_tokens: int) -> str:
        raise NotImplementedError()

    def healthcheck(self) -> Dict[str, str]:
        return {"ok": "true"}


class ProviderError(RuntimeError):
    def __init__(self, message: str, *, provider: Optional[str] = None):
        super().__init__(message)
        self.provider = provider

