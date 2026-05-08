from __future__ import annotations

from typing import List

from ai_engine.providers.base import ChatMessage, ChatProvider, ProviderError


class OllamaProvider(ChatProvider):
    def __init__(self, *, base_url: str, timeout_s: float = 60):
        self._base_url = (base_url or "").rstrip("/")
        self._timeout_s = float(timeout_s)

    def chat(self, *, model: str, messages: List[ChatMessage], temperature: float, max_tokens: int) -> str:
        try:
            import requests  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ProviderError(
                "Missing dependency 'requests'. Install with `pip install -r requirements.txt`.",
                provider="ollama",
            ) from e

        url = f"{self._base_url}/api/chat"
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in (messages or [])],
            "options": {"temperature": float(temperature)},
            "stream": False,
        }
        try:
            r = requests.post(url, json=payload, timeout=self._timeout_s)
        except Exception as e:
            raise ProviderError(
                "Ollama is not reachable. Start it with `ollama serve` and pull a model, e.g. `ollama pull llama3.1:8b`.",
                provider="ollama",
            ) from e

        if r.status_code >= 400:
            raise ProviderError(f"Ollama error ({r.status_code}): {r.text[:500]}", provider="ollama")

        data = r.json() or {}
        msg = (data.get("message") or {}).get("content") or ""
        return str(msg)

    def healthcheck(self):
        try:
            import requests  # type: ignore
        except Exception:  # pragma: no cover
            return {"ok": "false", "error": "missing_requests"}
        url = f"{self._base_url}/api/tags"
        try:
            r = requests.get(url, timeout=min(10.0, self._timeout_s))
            return {"ok": "true", "status_code": str(r.status_code)}
        except Exception:
            return {"ok": "false"}

