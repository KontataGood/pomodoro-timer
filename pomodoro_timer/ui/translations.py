
from __future__ import annotations

TRANSLATIONS = {
    "ru": {
        "window_title": "Pomodoro Timer",
        "brand": "POMODORO",
        "sessions_one": "{count} СЕССИЯ",
        "sessions_many": "{count} СЕССИЙ",
        "focus": "ФОКУС",
        "short_break": "КОРОТКИЙ ПЕРЕРЫВ",
        "long_break": "ДЛИННЫЙ ПЕРЕРЫВ",
        "start_focus": "Начать фокус",
        "start_break": "Начать перерыв",
        "start_long_break": "Начать длинный перерыв",
        "pause": "Пауза",
        "reset": "Сбросить",
        "ready": "Готов начать?",
        "stay_focused": "Сосредоточься на задаче!",
        "take_a_breather": "Немного передохни",
        "long_break_ready": "Ты заслужил длинный перерыв",
        "focus_completed": "Сессия завершена. Время отдохнуть!",
        "break_completed": "Перерыв окончен. Готов работать?",
        "focus_duration": "Длительность фокуса (мин)",
        "short_break_duration": "Короткий перерыв (мин)",
        "long_break_duration": "Длинный перерыв (мин)",
        "sessions_before_long_break": "Сессий до длинного перерыва",
        "footer": "СОСРЕДОТОЧЬСЯ НА ОДНОМ ДЕЛЕ",
        "settings": "Настройки",
        "language": "Язык",
        "russian": "Русский",
        "english": "Английский",
        "save": "Сохранить",
        "cancel": "Отмена",
    },
    "en": {
        "window_title": "Pomodoro Timer",
        "brand": "POMODORO",
        "sessions_one": "{count} SESSION",
        "sessions_many": "{count} SESSIONS",
        "focus": "FOCUS TIME",
        "short_break": "SHORT BREAK",
        "long_break": "LONG BREAK",
        "start_focus": "Start focus",
        "start_break": "Start break",
        "start_long_break": "Start long break",
        "pause": "Pause",
        "reset": "Reset",
        "ready": "Ready when you are",
        "stay_focused": "Stay focused. You've got this.",
        "take_a_breather": "Take a breather",
        "long_break_ready": "You've earned a longer break",
        "focus_completed": "Session complete. Time for a break!",
        "break_completed": "Break complete. Ready to focus?",
        "focus_duration": "Focus duration (min)",
        "short_break_duration": "Short break duration (min)",
        "long_break_duration": "Long break duration (min)",
        "sessions_before_long_break": "Sessions before long break",
        "footer": "FOCUS ON ONE THING AT A TIME",
        "settings": "Settings",
        "language": "Language",
        "russian": "Russian",
        "english": "English",
        "save": "Save",
        "cancel": "Cancel",
    },
}


def translate(language: str, key: str, **kwargs: object) -> str:
    """Return a translated string for the selected language."""
    language_translations = TRANSLATIONS.get(
        language, TRANSLATIONS["en"]
    )
    text = language_translations.get(
        key, TRANSLATIONS["en"].get(key, key)
    )
    return text.format(**kwargs)
