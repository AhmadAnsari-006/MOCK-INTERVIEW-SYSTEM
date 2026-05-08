import random
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.json_store import read_json


class QuestionService:
    def __init__(self, data_dir: Path):
        self._questions_path = data_dir / "questions.json"
        self._cache: Optional[Dict[str, Any]] = None

    def _load(self) -> Dict[str, Any]:
        if self._cache is None:
            self._cache = read_json(self._questions_path, default={})
        return self._cache

    def get_roles(self) -> List[str]:
        data = self._load()
        return list(data.keys())

    def get_fields(self, role: str) -> List[str]:
        data = self._load()
        if not role or role not in data:
            return []
        node = data[role]
        if isinstance(node, dict):
            return list(node.keys())
        return []

    def get_questions(self, role: str, field: str, difficulty: str) -> List[Dict[str, Any]]:
        data = self._load()
        if not role or not field or not difficulty:
            return []

        try:
            questions = data[role][field][difficulty.capitalize()]
        except Exception:
            return []

        normalized: List[Dict[str, Any]] = []
        for idx, q in enumerate(questions or []):
            if not isinstance(q, dict):
                continue

            question_text = q.get("question_text") or q.get("question") or ""
            keywords = q.get("keywords") or []

            normalized.append(
                {
                    "question_id": q.get("question_id") or q.get("id") or f"{role}:{field}:{difficulty}:{idx}",
                    "question_text": question_text,
                    "keywords": keywords,
                    "role": role,
                    "field": field,
                    "difficulty": difficulty,
                }
            )

        return normalized

    def pick_questions(self, role: str, field: str, difficulty: str, num_questions: int) -> List[Dict[str, Any]]:
        pool = self.get_questions(role, field, difficulty)
        if not pool:
            return []
        k = max(1, min(int(num_questions or 1), len(pool)))
        return random.sample(pool, k)
