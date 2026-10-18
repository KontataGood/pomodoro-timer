from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pomodoro_timer.core.timer import PomodoroTimer, TimerMode


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.timer = PomodoroTimer(self)

        self.setWindowTitle("Pomodoro Timer")
        self.setMinimumSize(420, 560)
        self.resize(460, 600)
        self.setStyleSheet(self._stylesheet())

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(30, 28, 30, 28)
        root_layout.setSpacing(18)

        header = QHBoxLayout()
        brand = QLabel("POMODORO")
        brand.setObjectName("brand")
        header.addWidget(brand)
        header.addStretch()
        self.session_badge = QLabel("0 SESSIONS")
        self.session_badge.setObjectName("sessionBadge")
        header.addWidget(self.session_badge)
        root_layout.addLayout(header)

        root_layout.addStretch(1)

        self.mode_label = QLabel("FOCUS TIME")
        self.mode_label.setObjectName("modeLabel")
        self.mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root_layout.addWidget(self.mode_label)

        timer_card = QFrame()
        timer_card.setObjectName("timerCard")
        card_layout = QVBoxLayout(timer_card)
        card_layout.setContentsMargins(20, 32, 20, 32)
        card_layout.setSpacing(10)

        self.time_label = QLabel("25:00")
        self.time_label.setObjectName("timeLabel")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.time_label)

        self.status_label = QLabel("Ready when you are")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(self.status_label)
        root_layout.addWidget(timer_card)

        modes = QHBoxLayout()
        modes.setSpacing(8)
        self.focus_button = self._mode_button("Focus", TimerMode.FOCUS)
        self.short_button = self._mode_button("Short break", TimerMode.SHORT_BREAK)
        self.long_button = self._mode_button("Long break", TimerMode.LONG_BREAK)
        modes.addWidget(self.focus_button)
        modes.addWidget(self.short_button)
        modes.addWidget(self.long_button)
        root_layout.addLayout(modes)

        controls = QHBoxLayout()
        controls.setSpacing(10)
        self.start_button = QPushButton("Start focus")
        self.start_button.setObjectName("primaryButton")
        self.start_button.setMinimumHeight(52)
        self.start_button.clicked.connect(self._toggle_timer)

        self.reset_button = QPushButton("Reset")
        self.reset_button.setObjectName("secondaryButton")
        self.reset_button.setMinimumHeight(52)
        self.reset_button.clicked.connect(self.timer.reset)

        controls.addWidget(self.start_button, 2)
        controls.addWidget(self.reset_button, 1)
        root_layout.addLayout(controls)

        root_layout.addStretch(1)

        footer = QLabel("FOCUS ON ONE THING AT A TIME")
        footer.setObjectName("footer")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root_layout.addWidget(footer)

        self.setCentralWidget(root)

        self.timer.tick.connect(self._update_time)
        self.timer.mode_changed.connect(self._update_mode)
        self.timer.running_changed.connect(self._update_running_state)
        self.timer.session_count_changed.connect(self._update_session_count)
        self.timer.phase_completed.connect(self._phase_completed)
        self._update_time(self.timer.remaining_seconds)
        self._update_mode(self.timer.mode)
        self._update_running_state(False)

    def _mode_button(self, text: str, mode: TimerMode) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("modeButton")
        button.setMinimumHeight(38)
        button.clicked.connect(lambda: self.timer.set_mode(mode))
        return button

    def _toggle_timer(self) -> None:
        if self.timer.is_running:
            self.timer.pause()
        else:
            self.timer.start()

    def _update_time(self, seconds: int) -> None:
        minutes, secs = divmod(max(0, seconds), 60)
        self.time_label.setText(f"{minutes:02d}:{secs:02d}")

    def _update_mode(self, mode: TimerMode) -> None:
        labels = {
            TimerMode.FOCUS: ("FOCUS TIME", "Start focus"),
            TimerMode.SHORT_BREAK: ("SHORT BREAK", "Start break"),
            TimerMode.LONG_BREAK: ("LONG BREAK", "Start long break"),
        }
        label, start_text = labels[mode]
        self.mode_label.setText(label)
        if not self.timer.is_running:
            self.start_button.setText(start_text)

        for button, button_mode in (
            (self.focus_button, TimerMode.FOCUS),
            (self.short_button, TimerMode.SHORT_BREAK),
            (self.long_button, TimerMode.LONG_BREAK),
        ):
            button.setProperty("active", button_mode == mode)
            button.style().unpolish(button)
            button.style().polish(button)

    def _update_running_state(self, running: bool) -> None:
        if running:
            self.start_button.setText("Pause")
            self.status_label.setText("Stay focused. You've got this.")
        else:
            labels = {
                TimerMode.FOCUS: "Ready when you are",
                TimerMode.SHORT_BREAK: "Take a breather",
                TimerMode.LONG_BREAK: "You've earned a longer break",
            }
            self.start_button.setText({
                TimerMode.FOCUS: "Start focus",
                TimerMode.SHORT_BREAK: "Start break",
                TimerMode.LONG_BREAK: "Start long break",
            }[self.timer.mode])
            self.status_label.setText(labels[self.timer.mode])

    def _update_session_count(self, count: int) -> None:
        self.session_badge.setText(f"{count} SESSION" if count == 1 else f"{count} SESSIONS")

    def _phase_completed(self, mode: TimerMode) -> None:
        # Keep the MVP dependency-free; desktop notifications can be added later.
        if mode == TimerMode.FOCUS:
            self.status_label.setText("Session complete. Time for a break!")
        else:
            self.status_label.setText("Break complete. Ready to focus?")

    @staticmethod
    def _stylesheet() -> str:
        return """
        QMainWindow, QWidget {
            background: #111318;
            color: #F3F4F6;
            font-family: Inter, "Segoe UI", Arial, sans-serif;
            font-size: 13px;
        }
        QLabel#brand {
            color: #F3F4F6;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 2px;
        }
        QLabel#sessionBadge {
            background: #20232B;
            color: #B7BBC6;
            border: 1px solid #303440;
            border-radius: 11px;
            padding: 7px 10px;
            font-size: 10px;
            font-weight: 700;
        }
        QLabel#modeLabel {
            color: #FF746F;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 3px;
        }
        QFrame#timerCard {
            background: #191C23;
            border: 1px solid #2A2E38;
            border-radius: 24px;
        }
        QLabel#timeLabel {
            color: #F9FAFB;
            font-size: 68px;
            font-weight: 700;
        }
        QLabel#statusLabel {
            color: #989EAC;
            font-size: 12px;
        }
        QPushButton {
            border: none;
            border-radius: 10px;
            padding: 9px 10px;
            font-weight: 600;
        }
        QPushButton#modeButton {
            background: #191C23;
            border: 1px solid #2A2E38;
            color: #A7ADBA;
        }
        QPushButton#modeButton[active="true"] {
            background: #332120;
            border: 1px solid #A84946;
            color: #FF8A84;
        }
        QPushButton#primaryButton {
            background: #F16B66;
            color: #171719;
            font-size: 14px;
            font-weight: 800;
        }
        QPushButton#primaryButton:hover {
            background: #FF817B;
        }
        QPushButton#secondaryButton {
            background: #252933;
            border: 1px solid #343946;
            color: #E1E4EA;
        }
        QPushButton#secondaryButton:hover {
            background: #303541;
        }
        QLabel#footer {
            color: #666D7B;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 2px;
        }
        """
