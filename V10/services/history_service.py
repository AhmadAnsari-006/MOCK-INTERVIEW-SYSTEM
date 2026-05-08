import time
from pathlib import Path
from typing import Any, Dict, List

from utils.json_store import read_json, write_json_atomic


class HistoryService:
    def __init__(self, data_dir: Path):
        self._path = data_dir / "user_history.json"

    def add_attempt(self, *, name: str, average_score_10: float, per_question: List[float], meta: Dict[str, Any]) -> Dict[str, Any]:
        name_key = (name or "").strip() or "anonymous"
        now = int(time.time())

        record = {
            "ts": now,
            "average_score_10": round(float(average_score_10), 2),
            "per_question": [round(float(x), 2) for x in (per_question or [])],
            "meta": meta or {},
        }

        store = read_json(self._path, default={})
        if name_key not in store or not isinstance(store.get(name_key), list):
            store[name_key] = []
        store[name_key].append(record)

        write_json_atomic(self._path, store)
        return record

    def get_attempts(self, *, name: str) -> List[Dict[str, Any]]:
        name_key = (name or "").strip() or "anonymous"
        store = read_json(self._path, default={})
        attempts = store.get(name_key, [])
        return attempts if isinstance(attempts, list) else []
