from pomodoro_timer.core.history import SessionHistory


def test_history_creates_database(tmp_path):
    """Проверяем, что база данных создаётся при инициализации."""

    # Создаём историю в тестовой временной директории.
    history = SessionHistory(tmp_path / "history.db")

    # Файл базы данных должен существовать, а история — быть пустой.
    assert history.database_path.exists()
    assert history.get_sessions() == []


def test_add_session_and_read_it(tmp_path):
    """Проверяем добавление сессии и чтение её данных."""

    history = SessionHistory(tmp_path / "history.db")

    # Добавляем завершённую фокус-сессию длительностью 25 минут.
    history.add_session("focus", 25 * 60)

    sessions = history.get_sessions()

    # Убеждаемся, что сохранилась одна запись с правильными данными.
    assert len(sessions) == 1
    assert sessions[0]["mode"] == "focus"
    assert sessions[0]["duration_seconds"] == 25 * 60

    # У записи должно быть заполнено время завершения.
    assert sessions[0]["completed_at"]


def test_history_keeps_sessions_after_reopening(tmp_path):
    """Проверяем сохранность данных после повторного открытия базы."""

    database_path = tmp_path / "history.db"

    history = SessionHistory(database_path)
    history.add_session("short_break", 5 * 60)

    # Создаём новый объект, использующий тот же файл базы данных.
    reopened_history = SessionHistory(database_path)

    sessions = reopened_history.get_sessions()

    # Ранее добавленная сессия должна остаться в базе.
    assert len(sessions) == 1
    assert sessions[0]["mode"] == "short_break"


def test_history_returns_newest_sessions_first(tmp_path):
    """Проверяем, что сначала возвращаются последние сессии."""

    history = SessionHistory(tmp_path / "history.db")

    # Добавляем две записи в определённом порядке.
    history.add_session("focus", 25 * 60)
    history.add_session("long_break", 15 * 60)

    sessions = history.get_sessions()

    # Длинный перерыв был добавлен позже, поэтому он должен быть первым.
    assert [session["mode"] for session in sessions] == [
        "long_break",
        "focus",
    ]


def test_history_respects_limit(tmp_path):
    """Проверяем ограничение количества возвращаемых записей."""

    history = SessionHistory(tmp_path / "history.db")

    # Добавляем три сессии.
    history.add_session("focus", 25 * 60)
    history.add_session("short_break", 5 * 60)
    history.add_session("focus", 25 * 60)

    # Запрашиваем только две последние записи.
    sessions = history.get_sessions(limit=2)

    assert len(sessions) == 2

    # Проверяем порядок оставшихся записей: от новой к старой.
    assert [session["mode"] for session in sessions] == [
        "focus",
        "short_break",
    ]
