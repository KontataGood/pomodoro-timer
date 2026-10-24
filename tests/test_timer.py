from pomodoro_timer.core.timer import PomodoroTimer, TimerMode


def test_initial_state(qapp):
    """Проверяет начальное состояние таймера."""
    timer = PomodoroTimer()

    # По умолчанию таймер находится в режиме фокусировки.
    assert timer.mode == TimerMode.FOCUS

    # Продолжительность фокусировки по умолчанию — 25 минут.
    assert timer.remaining_seconds == 25 * 60

    # В начале ещё не завершено ни одной сессии.
    assert timer.session_count == 0

    # После создания таймер не должен быть запущен.
    assert not timer.is_running


def test_mode_durations(qapp):
    """Проверяет стандартную продолжительность каждого режима."""
    timer = PomodoroTimer()

    # Проверяем длительность фокусировки.
    assert timer.duration_for(TimerMode.FOCUS) == 25 * 60

    # Проверяем длительность короткого перерыва.
    assert timer.duration_for(TimerMode.SHORT_BREAK) == 5 * 60

    # Проверяем длительность длинного перерыва.
    assert timer.duration_for(TimerMode.LONG_BREAK) == 15 * 60


def test_switching_back_restores_previous_mode_time(qapp):
    """Проверяет восстановление оставшегося времени при возврате в режим."""
    timer = PomodoroTimer()

    # Имитируем ситуацию, когда в режиме фокусировки осталось 12 минут.
    timer._remaining = 12 * 60

    # Переключаемся на короткий перерыв.
    timer.set_mode(TimerMode.SHORT_BREAK)
    assert timer.remaining_seconds == 5 * 60

    # Возвращаемся к фокусировке и проверяем сохранённое время.
    timer.set_mode(TimerMode.FOCUS)
    assert timer.remaining_seconds == 12 * 60


def test_each_mode_keeps_its_own_remaining_time(qapp):
    """Проверяет, что оставшееся время сохраняется отдельно для каждого режима."""
    timer = PomodoroTimer()

    # Переходим к короткому перерыву и задаём оставшееся время вручную.
    timer.set_mode(TimerMode.SHORT_BREAK)
    timer._remaining = 3 * 60

    # Переключаемся между режимами.
    timer.set_mode(TimerMode.FOCUS)
    timer.set_mode(TimerMode.SHORT_BREAK)

    # Проверяем, что для короткого перерыва сохранились 3 минуты.
    assert timer.remaining_seconds == 3 * 60


def test_focus_completion_switches_to_short_break(qapp):
    """Проверяет переход к короткому перерыву после первой сессии фокусировки."""
    timer = PomodoroTimer()

    # Имитируем завершение текущей фазы.
    timer._complete_phase()

    # После первой сессии должен начаться короткий перерыв.
    assert timer.mode == TimerMode.SHORT_BREAK

    # Проверяем стандартную продолжительность короткого перерыва.
    assert timer.remaining_seconds == 5 * 60

    # Количество завершённых сессий должно увеличиться на единицу.
    assert timer.session_count == 1


def test_fourth_focus_completion_switches_to_long_break(qapp):
    """Проверяет переход к длинному перерыву после четвёртой сессии."""
    timer = PomodoroTimer(sessions_before_long_break=4)

    # Имитируем ситуацию, когда уже завершены три сессии фокусировки.
    timer._session_count = 3

    # Завершаем четвёртую сессию.
    timer._complete_phase()

    # После четвёртой сессии должен начаться длинный перерыв.
    assert timer.mode == TimerMode.LONG_BREAK

    # Проверяем продолжительность длинного перерыва.
    assert timer.remaining_seconds == 15 * 60

    # Общее количество завершённых сессий должно стать равным четырём.
    assert timer.session_count == 4


def test_apply_settings_updates_mode_durations(qapp):
    """Проверяет применение пользовательских настроек таймера."""
    timer = PomodoroTimer()

    # Устанавливаем новые значения продолжительности режимов
    # и количество сессий до длинного перерыва.
    timer.apply_settings(
        focus_minutes=30,
        short_break_minutes=7,
        long_break_minutes=20,
        sessions_before_long_break=3,
    )

    # Проверяем, что новые настройки применились.
    assert timer.duration_for(TimerMode.FOCUS) == 30 * 60
    assert timer.duration_for(TimerMode.SHORT_BREAK) == 7 * 60
    assert timer.duration_for(TimerMode.LONG_BREAK) == 20 * 60

    # Проверяем новое количество сессий до длинного перерыва.
    assert timer.sessions_before_long_break == 3

    # После изменения настроек оставшееся время должно соответствовать
    # новой продолжительности текущего режима фокусировки.
    assert timer.remaining_seconds == 30 * 60

def test_reset_restores_full_duration(qapp):
    """Проверяет восстановление полной продолжительности текущей фазы."""
    timer = PomodoroTimer()

    # Имитируем, что прошло 10 минут фокусировки.
    timer._remaining = 15 * 60

    # Сбрасываем таймер.
    timer.reset()

    # Должны восстановиться исходные 25 минут.
    assert timer.remaining_seconds == 25 * 60
    assert not timer.is_running


def test_reset_preserves_current_mode(qapp):
    """Проверяет, что сброс не меняет текущий режим."""
    timer = PomodoroTimer()

    # Переключаемся на короткий перерыв и изменяем оставшееся время.
    timer.set_mode(TimerMode.SHORT_BREAK)
    timer._remaining = 2 * 60

    # Сбрасываем текущую фазу.
    timer.reset()

    # Режим остаётся прежним, время восстанавливается до 5 минут.
    assert timer.mode == TimerMode.SHORT_BREAK
    assert timer.remaining_seconds == 5 * 60


def test_reset_preserves_session_count(qapp):
    """Проверяет, что сброс не изменяет количество завершённых сессий."""
    timer = PomodoroTimer()

    # Имитируем две завершённые сессии.
    timer._session_count = 2

    # Сбрасываем текущую фазу.
    timer.reset()

    # Счётчик завершённых сессий не должен измениться.
    assert timer.session_count == 2
