import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class DbService:
    def __init__(self, db_path: Path):
        self._db_path = db_path

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS attempts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    role TEXT NOT NULL,
                    field TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    average_score_10 REAL NOT NULL,
                    time_taken INTEGER NOT NULL,
                    created_at INTEGER NOT NULL,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS attempt_answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    attempt_id INTEGER NOT NULL,
                    question_id TEXT,
                    score_10 REAL NOT NULL,
                    answer_text TEXT NOT NULL,
                    answer_words INTEGER NOT NULL,
                    keyword_hit_count INTEGER NOT NULL,
                    keyword_total INTEGER NOT NULL,
                    matched_keywords TEXT NOT NULL,
                    missing_keywords TEXT NOT NULL,
                    feedback TEXT NOT NULL,
                    FOREIGN KEY(attempt_id) REFERENCES attempts(id) ON DELETE CASCADE
                );
                """
            )

    def create_user(self, *, name: str, email: str, password_hash: str, created_at: int) -> int:
        with self.connect() as conn:
            cur = conn.execute(
                "INSERT INTO users(name, email, password_hash, created_at) VALUES(?,?,?,?)",
                (name, email, password_hash, int(created_at)),
            )
            return int(cur.lastrowid)

    def get_user_by_email(self, *, email: str) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
            return dict(row) if row else None

    def get_user_by_id(self, *, user_id: int) -> Optional[Dict[str, Any]]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM users WHERE id=?", (int(user_id),)).fetchone()
            return dict(row) if row else None

    def update_user_password_hash(self, *, user_id: int, password_hash: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "UPDATE users SET password_hash=? WHERE id=?",
                (password_hash, int(user_id)),
            )

    def create_attempt(
        self,
        *,
        user_id: int,
        role: str,
        field: str,
        difficulty: str,
        average_score_10: float,
        time_taken: int,
        created_at: int,
    ) -> int:
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO attempts(user_id, role, field, difficulty, average_score_10, time_taken, created_at)
                VALUES(?,?,?,?,?,?,?)
                """,
                (int(user_id), role, field, difficulty, float(average_score_10), int(time_taken), int(created_at)),
            )
            return int(cur.lastrowid)

    def add_attempt_answer(
        self,
        *,
        attempt_id: int,
        question_id: str,
        score_10: float,
        answer_text: str,
        answer_words: int,
        keyword_hit_count: int,
        keyword_total: int,
        matched_keywords_json: str,
        missing_keywords_json: str,
        feedback: str,
    ) -> int:
        with self.connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO attempt_answers(
                    attempt_id, question_id, score_10, answer_text, answer_words,
                    keyword_hit_count, keyword_total, matched_keywords, missing_keywords, feedback
                ) VALUES(?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    int(attempt_id),
                    question_id,
                    float(score_10),
                    answer_text,
                    int(answer_words),
                    int(keyword_hit_count),
                    int(keyword_total),
                    matched_keywords_json,
                    missing_keywords_json,
                    feedback,
                ),
            )
            return int(cur.lastrowid)

    def get_attempt_history_scores(
        self,
        *,
        user_id: int,
        role: str,
        field: str,
        difficulty: str,
        limit: int = 20,
    ) -> List[float]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT average_score_10
                FROM attempts
                WHERE user_id=? AND role=? AND field=? AND difficulty=?
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (int(user_id), role, field, difficulty, int(limit)),
            ).fetchall()
            return [float(r[0]) for r in rows]
