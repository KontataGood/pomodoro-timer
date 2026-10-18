from __future__ import annotations

from enum import Enum
from time import monotonic

from PySide6.QtCore import QObject, QTimer, Signal


class TimerMode(str, Enum):
    FOCUS = "focus"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"


class PomodoroTimer(QObject):
    """Pomodoro cycle controller.

    Uses monotonic time to avoid accumulating drift if the GUI event loop is delayed.
    """

    tick = Signal(int)
    mode_changed = Signal(object)
    running_changed = Signal(bool)
    session_count_changed = Signal(int)
    phase_completed = Signal(object)

    FOCUS_SECONDS = 25 * 60
    SHORT_BREAK_SECONDS = 5 * 60
    LONG_BREAK_SECONDS = 15 * 60
    SESSIONS_BEFORE_LONG_BREAK = 4

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._mode = TimerMode.FOCUS
        self._remaining = self.FOCUS_SECONDS
        self._session_count = 0
        self._deadline: float | None = None
        self._running = False

        self._ticker = QTimer(self)
        self._ticker.setInterval(200)
        self._ticker.timeout.connect(self._update_countdown)

    @property
    def mode(self) -> TimerMode:
        return self._mode

    @property
    def remaining_seconds(self) -> int:
        if self._running and self._deadline is not None:
            return max(0, int(self._deadline - monotonic() + 0.999))
        return self._remaining

    @property
    def session_count(self) -> int:
        return self._session_count

    @property
    def is_running(self) -> bool:
        return self._running

    def duration_for(self, mode: TimerMode | None = None) -> int:
        mode = mode or self._mode
        return {
            TimerMode.FOCUS: self.FOCUS_SECONDS,
            TimerMode.SHORT_BREAK: self.SHORT_BREAK_SECONDS,
            TimerMode.LONG_BREAK: self.LONG_BREAK_SECONDS,
        }[mode]

    def start(self) -> None:
        if self._running:
            return
        self._deadline = monotonic() + self._remaining
        self._running = True
        self._ticker.start()
        self.running_changed.emit(True)
        self.tick.emit(self.remaining_seconds)

    def pause(self) -> None:
        if not self._running:
            return
        self._remaining = self.remaining_seconds
        self._deadline = None
        self._running = False
        self._ticker.stop()
        self.running_changed.emit(False)
        self.tick.emit(self._remaining)

    def reset(self) -> None:
        was_running = self._running
        self._ticker.stop()
        self._running = False
        self._deadline = None
        self._remaining = self.duration_for()
        if was_running:
            self.running_changed.emit(False)
        self.tick.emit(self._remaining)

    def set_mode(self, mode: TimerMode) -> None:
        self._ticker.stop()
        was_running = self._running
        self._running = False
        self._deadline = None
        self._mode = mode
        self._remaining = self.duration_for(mode)
        if was_running:
            self.running_changed.emit(False)
        self.mode_changed.emit(mode)
        self.tick.emit(self._remaining)

    def _update_countdown(self) -> None:
        remaining = self.remaining_seconds
        if remaining != self._remaining:
            self._remaining = remaining
            self.tick.emit(remaining)
        if remaining <= 0:
            self._complete_phase()

    def _complete_phase(self) -> None:
        completed_mode = self._mode
        self._ticker.stop()
        self._running = False
        self._deadline = None
        self._remaining = 0
        self.running_changed.emit(False)
        self.phase_completed.emit(completed_mode)

        if completed_mode == TimerMode.FOCUS:
            self._session_count += 1
            self.session_count_changed.emit(self._session_count)
            next_mode = (
                TimerMode.LONG_BREAK
                if self._session_count % self.SESSIONS_BEFORE_LONG_BREAK == 0
                else TimerMode.SHORT_BREAK
            )
        else:
            next_mode = TimerMode.FOCUS

        self._mode = next_mode
        self._remaining = self.duration_for(next_mode)
        self.mode_changed.emit(next_mode)
        self.tick.emit(self._remaining)
