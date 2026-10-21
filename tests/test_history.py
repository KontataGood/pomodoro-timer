
from pomodoro_timer.core.history import SessionHistory


def test_history_creates_database(tmp_path):
    history = SessionHistory(tmp_path / "history.db")

    assert history.database_path.exists()
    assert history.get_sessions() == []


def test_add_session_and_read_it(tmp_path):
    history = SessionHistory(tmp_path / "history.db")

    history.add_session("focus", 25 * 60)

    sessions = history.get_sessions()

    assert len(sessions) == 1
    assert sessions[0]["mode"] == "focus"
    assert sessions[0]["duration_seconds"] == 25 * 60
    assert sessions[0]["completed_at"]


def test_history_keeps_sessions_after_reopening(tmp_path):
    database_path = tmp_path / "history.db"

    history = SessionHistory(database_path)
    history.add_session("short_break", 5 * 60)

    reopened_history = SessionHistory(database_path)

    sessions = reopened_history.get_sessions()

    assert len(sessions) == 1
    assert sessions[0]["mode"] == "short_break"


def test_history_returns_newest_sessions_first(tmp_path):
    history = SessionHistory(tmp_path / "history.db")

    history.add_session("focus", 25 * 60)
    history.add_session("long_break", 15 * 60)

    sessions = history.get_sessions()

    assert [session["mode"] for session in sessions] == [
        "long_break",
        "focus",
    ]


def test_history_respects_limit(tmp_path):
    history = SessionHistory(tmp_path / "history.db")

    history.add_session("focus", 25 * 60)
    history.add_session("short_break", 5 * 60)
    history.add_session("focus", 25 * 60)

    sessions = history.get_sessions(limit=2)

    assert len(sessions) == 2
    assert [session["mode"] for session in sessions] == [
        "focus",
        "short_break",
    ]
