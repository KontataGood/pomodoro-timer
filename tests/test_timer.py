from pomodoro_timer.core.timer import PomodoroTimer, TimerMode


def test_initial_state(qapp):
    timer = PomodoroTimer()
    assert timer.mode == TimerMode.FOCUS
    assert timer.remaining_seconds == 25 * 60
    assert timer.session_count == 0
    assert not timer.is_running


def test_mode_durations(qapp):
    timer = PomodoroTimer()
    assert timer.duration_for(TimerMode.FOCUS) == 25 * 60
    assert timer.duration_for(TimerMode.SHORT_BREAK) == 5 * 60
    assert timer.duration_for(TimerMode.LONG_BREAK) == 15 * 60


def test_switching_back_restores_previous_mode_time(qapp):
    timer = PomodoroTimer()
    timer._remaining = 12 * 60

    timer.set_mode(TimerMode.SHORT_BREAK)
    assert timer.remaining_seconds == 5 * 60

    timer.set_mode(TimerMode.FOCUS)
    assert timer.remaining_seconds == 12 * 60


def test_each_mode_keeps_its_own_remaining_time(qapp):
    timer = PomodoroTimer()

    timer.set_mode(TimerMode.SHORT_BREAK)
    timer._remaining = 3 * 60

    timer.set_mode(TimerMode.FOCUS)
    timer.set_mode(TimerMode.SHORT_BREAK)

    assert timer.remaining_seconds == 3 * 60

def test_focus_completion_switches_to_short_break(qapp):
    timer = PomodoroTimer()

    timer._complete_phase()

    assert timer.mode == TimerMode.SHORT_BREAK
    assert timer.remaining_seconds == 5 * 60
    assert timer.session_count == 1


def test_fourth_focus_completion_switches_to_long_break(qapp):
    timer = PomodoroTimer(sessions_before_long_break=4)
    timer._session_count = 3

    timer._complete_phase()

    assert timer.mode == TimerMode.LONG_BREAK
    assert timer.remaining_seconds == 15 * 60
    assert timer.session_count == 4


def test_apply_settings_updates_mode_durations(qapp):
    timer = PomodoroTimer()

    timer.apply_settings(
        focus_minutes=30,
        short_break_minutes=7,
        long_break_minutes=20,
        sessions_before_long_break=3,
    )

    assert timer.duration_for(TimerMode.FOCUS) == 30 * 60
    assert timer.duration_for(TimerMode.SHORT_BREAK) == 7 * 60
    assert timer.duration_for(TimerMode.LONG_BREAK) == 20 * 60
    assert timer.sessions_before_long_break == 3
    assert timer.remaining_seconds == 30 * 60
