import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils.json_store import read_json, write_json_atomic


class SessionService:
    def __init__(self, data_dir: Path):
        self._sessions_path = data_dir / "sessions.json"

    def create_session(
        self,
        *,
        name: str,
        role: str,
        field: str,
        difficulty: str,
        questions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        session_id = uuid.uuid4().hex
        now = int(time.time())

        session = {
            "session_id": session_id,
            "name": name or "",
            "role": role,
            "field": field,
            "difficulty": difficulty,
            "created_at": now,
            "start_time": now,
            "current_index": 0,
            "questions": questions,
            "answers": [],
            "per_question": [],
            "completed": False,
        }

        all_sessions = read_json(self._sessions_path, default={})
        all_sessions[session_id] = session
        write_json_atomic(self._sessions_path, all_sessions)
        return session

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        if not session_id:
            return None
        all_sessions = read_json(self._sessions_path, default={})
        session = all_sessions.get(session_id)
        return session if isinstance(session, dict) else None

    def save_session(self, session: Dict[str, Any]) -> None:
        session_id = session.get("session_id")
        if not session_id:
            return
        all_sessions = read_json(self._sessions_path, default={})
        all_sessions[session_id] = session
        write_json_atomic(self._sessions_path, all_sessions)

    def mark_completed(self, session: Dict[str, Any]) -> None:
        session["completed"] = True
        self.save_session(session)

    def get_time_taken(self, session: Dict[str, Any]) -> int:
        start = int(session.get("start_time") or 0)
        if start <= 0:
            return 0
        return max(0, int(time.time()) - start)
