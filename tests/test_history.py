from pomodoro_timer.core.history import SessionHistory


def test_history_creates_database(tmp_path):
    """РџСЂРѕРІРµСЂСЏРµРј, С‡С‚Рѕ Р±Р°Р·Р° РґР°РЅРЅС‹С… СЃРѕР·РґР°С‘С‚СЃСЏ РїСЂРё РёРЅРёС†РёР°Р»РёР·Р°С†РёРё."""

    # РЎРѕР·РґР°С‘Рј РёСЃС‚РѕСЂРёСЋ РІ С‚РµСЃС‚РѕРІРѕР№ РІСЂРµРјРµРЅРЅРѕР№ РґРёСЂРµРєС‚РѕСЂРёРё.
    history = SessionHistory(tmp_path / "history.db")

    # Р¤Р°Р№Р» Р±Р°Р·С‹ РґР°РЅРЅС‹С… РґРѕР»Р¶РµРЅ СЃСѓС‰РµСЃС‚РІРѕРІР°С‚СЊ, Р° РёСЃС‚РѕСЂРёСЏ вЂ” Р±С‹С‚СЊ РїСѓСЃС‚РѕР№.
    assert history.database_path.exists()
    assert history.get_sessions() == []


def test_add_session_and_read_it(tmp_path):
    """РџСЂРѕРІРµСЂСЏРµРј РґРѕР±Р°РІР»РµРЅРёРµ СЃРµСЃСЃРёРё Рё С‡С‚РµРЅРёРµ РµС‘ РґР°РЅРЅС‹С…."""

    history = SessionHistory(tmp_path / "history.db")

    # Р”РѕР±Р°РІР»СЏРµРј Р·Р°РІРµСЂС€С‘РЅРЅСѓСЋ С„РѕРєСѓСЃ-СЃРµСЃСЃРёСЋ РґР»РёС‚РµР»СЊРЅРѕСЃС‚СЊСЋ 25 РјРёРЅСѓС‚.
    history.add_session("focus", 25 * 60)

    sessions = history.get_sessions()

    # РЈР±РµР¶РґР°РµРјСЃСЏ, С‡С‚Рѕ СЃРѕС…СЂР°РЅРёР»Р°СЃСЊ РѕРґРЅР° Р·Р°РїРёСЃСЊ СЃ РїСЂР°РІРёР»СЊРЅС‹РјРё РґР°РЅРЅС‹РјРё.
    assert len(sessions) == 1
    assert sessions[0]["mode"] == "focus"
    assert sessions[0]["duration_seconds"] == 25 * 60

    # РЈ Р·Р°РїРёСЃРё РґРѕР»Р¶РЅРѕ Р±С‹С‚СЊ Р·Р°РїРѕР»РЅРµРЅРѕ РІСЂРµРјСЏ Р·Р°РІРµСЂС€РµРЅРёСЏ.
    assert sessions[0]["completed_at"]


def test_history_keeps_sessions_after_reopening(tmp_path):
    """РџСЂРѕРІРµСЂСЏРµРј СЃРѕС…СЂР°РЅРЅРѕСЃС‚СЊ РґР°РЅРЅС‹С… РїРѕСЃР»Рµ РїРѕРІС‚РѕСЂРЅРѕРіРѕ РѕС‚РєСЂС‹С‚РёСЏ Р±Р°Р·С‹."""

    database_path = tmp_path / "history.db"

    history = SessionHistory(database_path)
    history.add_session("short_break", 5 * 60)

    # РЎРѕР·РґР°С‘Рј РЅРѕРІС‹Р№ РѕР±СЉРµРєС‚, РёСЃРїРѕР»СЊР·СѓСЋС‰РёР№ С‚РѕС‚ Р¶Рµ С„Р°Р№Р» Р±Р°Р·С‹ РґР°РЅРЅС‹С….
    reopened_history = SessionHistory(database_path)

    sessions = reopened_history.get_sessions()

    # Р Р°РЅРµРµ РґРѕР±Р°РІР»РµРЅРЅР°СЏ СЃРµСЃСЃРёСЏ РґРѕР»Р¶РЅР° РѕСЃС‚Р°С‚СЊСЃСЏ РІ Р±Р°Р·Рµ.
    assert len(sessions) == 1
    assert sessions[0]["mode"] == "short_break"


def test_history_returns_newest_sessions_first(tmp_path):
    """РџСЂРѕРІРµСЂСЏРµРј, С‡С‚Рѕ СЃРЅР°С‡Р°Р»Р° РІРѕР·РІСЂР°С‰Р°СЋС‚СЃСЏ РїРѕСЃР»РµРґРЅРёРµ СЃРµСЃСЃРёРё."""

    history = SessionHistory(tmp_path / "history.db")

    # Р”РѕР±Р°РІР»СЏРµРј РґРІРµ Р·Р°РїРёСЃРё РІ РѕРїСЂРµРґРµР»С‘РЅРЅРѕРј РїРѕСЂСЏРґРєРµ.
    history.add_session("focus", 25 * 60)
    history.add_session("long_break", 15 * 60)

    sessions = history.get_sessions()

    # Р”Р»РёРЅРЅС‹Р№ РїРµСЂРµСЂС‹РІ Р±С‹Р» РґРѕР±Р°РІР»РµРЅ РїРѕР·Р¶Рµ, РїРѕСЌС‚РѕРјСѓ РѕРЅ РґРѕР»Р¶РµРЅ Р±С‹С‚СЊ РїРµСЂРІС‹Рј.
    assert [session["mode"] for session in sessions] == [
        "long_break",
        "focus",
    ]


def test_history_respects_limit(tmp_path):
    """РџСЂРѕРІРµСЂСЏРµРј РѕРіСЂР°РЅРёС‡РµРЅРёРµ РєРѕР»РёС‡РµСЃС‚РІР° РІРѕР·РІСЂР°С‰Р°РµРјС‹С… Р·Р°РїРёСЃРµР№."""

    history = SessionHistory(tmp_path / "history.db")

    # Р”РѕР±Р°РІР»СЏРµРј С‚СЂРё СЃРµСЃСЃРёРё.
    history.add_session("focus", 25 * 60)
    history.add_session("short_break", 5 * 60)
    history.add_session("focus", 25 * 60)

    # Р—Р°РїСЂР°С€РёРІР°РµРј С‚РѕР»СЊРєРѕ РґРІРµ РїРѕСЃР»РµРґРЅРёРµ Р·Р°РїРёСЃРё.
    sessions = history.get_sessions(limit=2)

    assert len(sessions) == 2

    # РџСЂРѕРІРµСЂСЏРµРј РїРѕСЂСЏРґРѕРє РѕСЃС‚Р°РІС€РёС…СЃСЏ Р·Р°РїРёСЃРµР№: РѕС‚ РЅРѕРІРѕР№ Рє СЃС‚Р°СЂРѕР№.
    assert [session["mode"] for session in sessions] == [
        "focus",
        "short_break",
    ]

def test_clear_history_removes_all_sessions(tmp_path):
    """РџСЂРѕРІРµСЂСЏРµС‚ РїРѕР»РЅСѓСЋ РѕС‡РёСЃС‚РєСѓ РёСЃС‚РѕСЂРёРё."""
    history = SessionHistory(tmp_path / "history.db")
    history.add_session("focus", 25 * 60)
    history.add_session("short_break", 5 * 60)

    history.clear_history()

    assert history.get_sessions() == []

def test_delete_sessions_older_than_removes_only_old_sessions(tmp_path):
    """РџСЂРѕРІРµСЂСЏРµС‚ СѓРґР°Р»РµРЅРёРµ СЃС‚Р°СЂС‹С… Р·Р°РїРёСЃРµР№ СЃ СЃРѕС…СЂР°РЅРµРЅРёРµРј РЅРѕРІС‹С…."""
    from datetime import datetime, timedelta

    history = SessionHistory(tmp_path / "history.db")
    history.add_session("focus", 25 * 60)
    history.add_session("short_break", 5 * 60)

    # Р”РµР»Р°РµРј РїРµСЂРІСѓСЋ Р·Р°РїРёСЃСЊ СЃС‚Р°СЂС€Рµ 10 РґРЅРµР№.
    old_date = (
        datetime.now().astimezone() - timedelta(days=11)
    ).isoformat(timespec="seconds")

    with history._connect() as connection:
        connection.execute(
            "UPDATE sessions SET completed_at = ? WHERE id = 1",
            (old_date,),
        )

    deleted_count = history.delete_sessions_older_than(10)

    assert deleted_count == 1

    sessions = history.get_sessions()
    assert len(sessions) == 1
    assert sessions[0]["mode"] == "short_break"


def test_delete_sessions_older_than_rejects_invalid_days(tmp_path):
    """РџСЂРѕРІРµСЂСЏРµС‚ РѕР±СЂР°Р±РѕС‚РєСѓ РЅРµРєРѕСЂСЂРµРєС‚РЅРѕРіРѕ СЃСЂРѕРєР° С…СЂР°РЅРµРЅРёСЏ."""
    import pytest

    history = SessionHistory(tmp_path / "history.db")

    with pytest.raises(ValueError):
        history.delete_sessions_older_than(0)

    with pytest.raises(ValueError):
        history.delete_sessions_older_than(-1)


def test_delete_sessions_older_than_keeps_recent_sessions(tmp_path):
    """РџСЂРѕРІРµСЂСЏРµС‚, С‡С‚Рѕ СЃРІРµР¶РёРµ Р·Р°РїРёСЃРё РЅРµ СѓРґР°Р»СЏСЋС‚СЃСЏ."""
    history = SessionHistory(tmp_path / "history.db")
    history.add_session("focus", 25 * 60)

    deleted_count = history.delete_sessions_older_than(30)

    assert deleted_count == 0
    assert len(history.get_sessions()) == 1
