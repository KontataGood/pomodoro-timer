from __future__ import annotations

from enum import Enum
from time import monotonic

from PySide6.QtCore import QObject, QTimer, Signal


class TimerMode(str, Enum):
    """Режимы работы таймера Pomodoro."""

    FOCUS = "focus"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


class PomodoroTimer(QObject):
    """Управляет циклами фокусировки и перерывов.

    Использует monotonic(), чтобы задержки обработки событий
    интерфейса не приводили к накоплению погрешности времени.
    """

    # Сигналы для уведомления интерфейса об изменениях таймера.
    tick = Signal(int)  # Оставшееся время в секундах.
    mode_changed = Signal(object)  # Изменение текущего режима.
    running_changed = Signal(bool)  # Запуск или остановка таймера.
    session_count_changed = Signal(int)  # Изменение числа фокус-сессий.
    phase_completed = Signal(object)  # Завершение текущей фазы.

    # Стандартные значения продолжительности фаз и цикла.
    FOCUS_SECONDS = 25 * 60
    SHORT_BREAK_SECONDS = 5 * 60
    LONG_BREAK_SECONDS = 15 * 60
    SESSIONS_BEFORE_LONG_BREAK = 4

    def __init__(
        self,
        parent: QObject | None = None,
        *,
        focus_minutes: int = 25,
        short_break_minutes: int = 5,
        long_break_minutes: int = 15,
        sessions_before_long_break: int = 4,
    ) -> None:
        """Инициализирует таймер с заданными параметрами."""
        super().__init__(parent)

        # Переводим продолжительность фаз из минут в секунды.
        self.focus_seconds = focus_minutes * 60
        self.short_break_seconds = short_break_minutes * 60
        self.long_break_seconds = long_break_minutes * 60
        self.sessions_before_long_break = sessions_before_long_break

        # Начинаем с режима фокусировки.
        self._mode = TimerMode.FOCUS

        # Сохраняем оставшееся время отдельно для каждого режима.
        self._remaining_by_mode = {
            TimerMode.FOCUS: self.duration_for(TimerMode.FOCUS),
            TimerMode.SHORT_BREAK: self.duration_for(TimerMode.SHORT_BREAK),
            TimerMode.LONG_BREAK: self.duration_for(TimerMode.LONG_BREAK),
        }
        self._remaining = self._remaining_by_mode[self._mode]

        # Внутреннее состояние таймера.
        self._session_count = 0
        self._deadline: float | None = None
        self._running = False

        # QTimer периодически обновляет обратный отсчёт.
        # Само время рассчитывается через monotonic(), а не числом тиков.
        self._ticker = QTimer(self)
        self._ticker.setInterval(200)
        self._ticker.timeout.connect(self._update_countdown)

    @property
    def mode(self) -> TimerMode:
        """Возвращает текущий режим таймера."""
        return self._mode

    @property
    def remaining_seconds(self) -> int:
        """Возвращает актуальное количество оставшихся секунд."""
        if self._running and self._deadline is not None:
            # Округляем оставшееся время вверх до целой секунды.
            return max(0, int(self._deadline - monotonic() + 0.999))

        return self._remaining

    @property
    def session_count(self) -> int:
        """Возвращает число завершённых фокус-сессий."""
        return self._session_count

    @property
    def is_running(self) -> bool:
        """Показывает, запущен ли таймер."""
        return self._running

    def duration_for(self, mode: TimerMode | None = None) -> int:
        """Возвращает полную продолжительность указанного режима."""
        mode = mode or self._mode

        return {
            TimerMode.FOCUS: self.focus_seconds,
            TimerMode.SHORT_BREAK: self.short_break_seconds,
            TimerMode.LONG_BREAK: self.long_break_seconds,
        }[mode]

    def start(self) -> None:
        """Запускает обратный отсчёт."""
        # Не допускаем повторного запуска уже работающего таймера.
        if self._running:
            return

        # Вычисляем момент завершения на основе монотонных часов.
        self._deadline = monotonic() + self._remaining
        self._running = True
        self._ticker.start()

        # Сообщаем интерфейсу о запуске и текущем времени.
        self.running_changed.emit(True)
        self.tick.emit(self.remaining_seconds)

    def pause(self) -> None:
        """Приостанавливает таймер, сохраняя оставшееся время."""
        if not self._running:
            return

        # Фиксируем время, оставшееся на момент паузы.
        self._remaining = self.remaining_seconds
        self._remaining_by_mode[self._mode] = self._remaining
        self._deadline = None
        self._running = False
        self._ticker.stop()

        # Обновляем состояние интерфейса.
        self.running_changed.emit(False)
        self.tick.emit(self._remaining)

    def reset(self) -> None:
        """Сбрасывает текущую фазу до её полной продолжительности."""
        was_running = self._running

        self._ticker.stop()
        self._running = False
        self._deadline = None

        # Восстанавливаем длительность текущего режима.
        self._remaining = self.duration_for()
        self._remaining_by_mode[self._mode] = self._remaining

        # Отправляем сигнал остановки, если таймер работал.
        if was_running:
            self.running_changed.emit(False)

        self.tick.emit(self._remaining)

    def set_mode(self, mode: TimerMode) -> None:
        """Переключает таймер на другой режим."""
        if mode == self._mode:
            return

        was_running = self._running

        # При переключении работающий таймер сначала ставится на паузу.
        if was_running:
            self.pause()

        # Сохраняем оставшееся время предыдущего режима.
        self._remaining_by_mode[self._mode] = self._remaining

        # Восстанавливаем сохранённое время выбранного режима.
        self._mode = mode
        self._remaining = self._remaining_by_mode[mode]

        self.mode_changed.emit(mode)
        self.tick.emit(self._remaining)

    def _update_countdown(self) -> None:
        """Обновляет оставшееся время и проверяет завершение фазы."""
        remaining = self.remaining_seconds

        # Обновляем состояние только при изменении целого числа секунд.
        if remaining != self._remaining:
            self._remaining = remaining
            self._remaining_by_mode[self._mode] = remaining
            self.tick.emit(remaining)

        # При достижении нуля завершаем текущую фазу.
        if remaining <= 0:
            self._complete_phase()

    def _complete_phase(self) -> None:
        """Завершает текущую фазу и автоматически запускает следующую."""
        completed_mode = self._mode

        # Останавливаем обратный отсчёт и сообщаем о завершении.
        self._ticker.stop()
        self._running = False
        self._deadline = None
        self._remaining = 0

        self.running_changed.emit(False)
        self.phase_completed.emit(completed_mode)

        if completed_mode == TimerMode.FOCUS:
            # Учитываем завершённую фокус-сессию.
            self._session_count += 1
            self.session_count_changed.emit(self._session_count)

            # После заданного числа фокус-сессий назначаем длинный перерыв.
            # В остальных случаях следует короткий перерыв.
            next_mode = (
                TimerMode.LONG_BREAK
                if self._session_count % self.sessions_before_long_break == 0
                else TimerMode.SHORT_BREAK
            )
        else:
            # После любого перерыва возвращаемся к фокусировке.
            next_mode = TimerMode.FOCUS

        # Переключаем режим и устанавливаем его полную длительность.
        self._mode = next_mode
        self._remaining = self.duration_for(next_mode)
        self._remaining_by_mode[next_mode] = self._remaining

        self.mode_changed.emit(next_mode)
        self.tick.emit(self._remaining)

        # Автоматически запускаем следующую фазу.
        self.start()

    def apply_settings(
        self,
        *,
        focus_minutes: int,
        short_break_minutes: int,
        long_break_minutes: int,
        sessions_before_long_break: int,
    ) -> None:
        """Применяет новые параметры таймера."""
        # Продолжительность всех фаз и количество сессий должны быть положительными.
        if min(
            focus_minutes,
            short_break_minutes,
            long_break_minutes,
            sessions_before_long_break,
        ) < 1:
            raise ValueError("Timer settings must be positive")

        # Перед изменением параметров останавливаем работающий таймер.
        if self._running:
            self.pause()

        # Обновляем продолжительность фаз и число сессий до длинного перерыва.
        self.focus_seconds = focus_minutes * 60
        self.short_break_seconds = short_break_minutes * 60
        self.long_break_seconds = long_break_minutes * 60
        self.sessions_before_long_break = sessions_before_long_break

        # Сбрасываем текущий режим с учётом новых параметров.
        self.reset()
