
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path


class SessionHistory:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_database(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mode TEXT NOT NULL,
                    duration_seconds INTEGER NOT NULL,
                    completed_at TEXT NOT NULL
                )
                """
            )

    def add_session(self, mode: str, duration_seconds: int) -> None:
        completed_at = datetime.now().astimezone().isoformat(
            timespec="seconds"
        )

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO sessions (mode, duration_seconds, completed_at)
                VALUES (?, ?, ?)
                """,
                (mode, duration_seconds, completed_at),
            )

    def get_sessions(self, limit: int = 100) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, mode, duration_seconds, completed_at
                FROM sessions
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [dict(row) for row in rows]


    def count_completed_focus_sessions(self) -> int:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*)
                FROM sessions
                WHERE mode = ?
                """,
                ("focus",),
            ).fetchone()

        return row[0]

