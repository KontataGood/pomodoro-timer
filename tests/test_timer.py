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


def test_switch_mode_resets_remaining_time(qapp):
    timer = PomodoroTimer()
    timer.set_mode(TimerMode.SHORT_BREAK)
    assert timer.mode == TimerMode.SHORT_BREAK
    assert timer.remaining_seconds == 5 * 60
