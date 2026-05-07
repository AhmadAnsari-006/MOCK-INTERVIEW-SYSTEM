import os
import json
from typing import Any, Dict, List, Optional

from openai import OpenAI


class LlmService:
    def __init__(self, *, model: str = "gpt-4o-mini", embedding_model: str = "text-embedding-3-small"):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self._client = OpenAI(api_key=api_key)
        self._model = model
        self._embedding_model = embedding_model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        res = self._client.embeddings.create(model=self._embedding_model, input=texts)
        return [d.embedding for d in res.data]

    def chat_json(
        self,
        *,
        system: str,
        user: str,
        schema_hint: Optional[str] = None,
        temperature: float = 0.2,
        max_output_tokens: int = 800,
    ) -> Dict[str, Any]:
        content = user
        if schema_hint:
            content = f"{user}\n\nReturn ONLY valid JSON. Schema: {schema_hint}"

        res = self._client.chat.completions.create(
            model=self._model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": content},
            ],
            max_completion_tokens=max_output_tokens,
        )

        text = (res.choices[0].message.content or "").strip()
        try:
            return json.loads(text)
        except Exception as e:
            raise RuntimeError(f"LLM did not return valid JSON: {e}. Raw: {text[:500]}")
