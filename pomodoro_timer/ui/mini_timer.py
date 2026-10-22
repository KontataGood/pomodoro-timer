
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from pomodoro_timer.core.timer import PomodoroTimer, TimerMode
from pomodoro_timer.ui.translations import translate


class MiniTimer(QWidget):
    def __init__(self, timer: PomodoroTimer, parent=None) -> None:
        super().__init__(parent)

        self.timer = timer

        self.setWindowTitle("Pomodoro Mini Timer")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setMinimumSize(300, 190)
        self.resize(320, 210)

        self.setStyleSheet("""
            QWidget {
                background-color: #111318;
                color: #F3F4F6;
                font-family: "Segoe UI", Arial, sans-serif;
            }
            QLabel#modeLabel {
                color: #F16B66;
                font-size: 12px;
                font-weight: 700;
                letter-spacing: 2px;
            }
            QLabel#timeLabel {
                font-size: 42px;
                font-weight: 700;
            }
            QPushButton {
                background-color: #252933;
                color: #E1E4EA;
                border: 1px solid #2A2E38;
                border-radius: 8px;
                padding: 8px 10px;
                min-height: 22px;
            }
            QPushButton:hover {
                background-color: #303541;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 14)
        layout.setSpacing(8)

        self.mode_label = QLabel()
        self.mode_label.setObjectName("modeLabel")
        self.mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.mode_label)

        self.time_label = QLabel()
        self.time_label.setObjectName("timeLabel")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.time_label)

        controls = QHBoxLayout()
        controls.setSpacing(8)

        self.toggle_button = QPushButton()
        self.toggle_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.toggle_button.clicked.connect(self._toggle_timer)
        controls.addWidget(self.toggle_button)

        self.main_window_button = QPushButton()
        self.main_window_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.main_window_button.clicked.connect(self._show_main_window)
        controls.addWidget(self.main_window_button)

        layout.addLayout(controls)

        self.timer.tick.connect(self._update_time)
        self.timer.mode_changed.connect(self._update_mode)
        self.timer.running_changed.connect(self._update_running_state)

        self._update_time(self.timer.remaining_seconds)
        self._update_mode(self.timer.mode)
        self._update_running_state(self.timer.is_running)
        self._retranslate_ui()

    def _language(self) -> str:
        if self.parentWidget() is not None:
            return self.parentWidget().language
        return "en"

    def _update_time(self, seconds: int) -> None:
        minutes, secs = divmod(max(0, seconds), 60)
        self.time_label.setText(f"{minutes:02d}:{secs:02d}")

    def _update_mode(self, mode: TimerMode) -> None:
        labels = {
            TimerMode.FOCUS: "focus",
            TimerMode.SHORT_BREAK: "short_break",
            TimerMode.LONG_BREAK: "long_break",
        }
        self.mode_label.setText(
            translate(self._language(), labels[mode])
        )

    def _update_running_state(self, running: bool) -> None:
        if running:
            key = "pause"
        elif self.timer.mode == TimerMode.FOCUS:
            key = "start_focus"
        elif self.timer.mode == TimerMode.LONG_BREAK:
            key = "start_long_break"
        else:
            key = "start_break"

        self.toggle_button.setText(
            translate(self._language(), key)
        )

    def _toggle_timer(self) -> None:
        if self.timer.is_running:
            self.timer.pause()
        else:
            self.timer.start()

    def _show_main_window(self) -> None:
        if self.parentWidget() is not None:
            self.parentWidget().showNormal()
            self.parentWidget().raise_()
            self.parentWidget().activateWindow()

    def _retranslate_ui(self) -> None:
        self.main_window_button.setText(
            translate(self._language(), "show_main_window")
        )
        self._update_mode(self.timer.mode)
        self._update_running_state(self.timer.is_running)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.timer.is_running:
            event.ignore()
            self.hide()
            return

        event.accept()
