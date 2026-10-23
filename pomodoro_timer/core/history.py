from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path


class SessionHistory:
    """Хранит историю завершённых сессий Pomodoro в базе SQLite."""

    def __init__(self, database_path: str | Path) -> None:
        """Подготавливает путь к базе и создаёт таблицу при необходимости."""

        # Преобразуем переданный путь в объект Path.
        self.database_path = Path(database_path)

        # Создаём родительские каталоги, если они ещё не существуют.
        self.database_path.parent.mkdir(parents=True, exist_ok=True)

        # Убеждаемся, что таблица для хранения сессий существует.
        self._initialize_database()

    def _connect(self) -> sqlite3.Connection:
        """Открывает соединение с базой данных SQLite."""

        connection = sqlite3.connect(self.database_path)

        # Позволяет обращаться к столбцам результата по их именам.
        connection.row_factory = sqlite3.Row

        return connection

    def _initialize_database(self) -> None:
        """Создаёт таблицу sessions, если её ещё нет."""

        # Контекстный менеджер управляет транзакцией соединения.
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
        """Сохраняет завершённую сессию в истории."""

        # Записываем локальное время с указанием часового пояса.
        completed_at = datetime.now().astimezone().isoformat(
            timespec="seconds"
        )

        # Добавляем запись с помощью параметризованного SQL-запроса.
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO sessions (mode, duration_seconds, completed_at)
                VALUES (?, ?, ?)
                """,
                (mode, duration_seconds, completed_at),
            )

    def get_sessions(self, limit: int = 100) -> list[dict]:
        """Возвращает последние сессии в порядке от новых к старым."""

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

        # Преобразуем строки SQLite в обычные словари Python.
        return [dict(row) for row in rows]

    def count_completed_focus_sessions(self) -> int:
        """Возвращает количество записанных фокус-сессий."""

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*)
                FROM sessions
                WHERE mode = ?
                """,
                ("focus",),
            ).fetchone()

        # COUNT(*) возвращает число записей, соответствующих условию.
        return row[0]
