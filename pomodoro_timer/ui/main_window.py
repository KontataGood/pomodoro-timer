from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtCore import QSettings

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QDialog,
)

from pomodoro_timer.core.timer import PomodoroTimer, TimerMode
from pomodoro_timer.ui.settings_dialog import SettingsDialog
from pomodoro_timer.ui.translations import translate


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.settings = QSettings("KontataGood", "PomodoroTimer")
        self.language = self.settings.value("language", "en", type=str)

        self.timer_settings = {
            "focus_minutes": self.settings.value("focus_minutes", 25, type=int),
            "short_break_minutes": self.settings.value(
                "short_break_minutes", 5, type=int
            ),
            "long_break_minutes": self.settings.value(
                "long_break_minutes", 15, type=int
            ),
            "sessions_before_long_break": self.settings.value(
                "sessions_before_long_break", 4, type=int
            ),
        }

        self.timer = PomodoroTimer(self, **self.timer_settings)

        self.setWindowTitle("Pomodoro Timer")
        self.setMinimumSize(440, 600)
        self.resize(480, 640)
        self.setStyleSheet(self._stylesheet())

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(28, 26, 28, 26)
        root_layout.setSpacing(20)

        header = QHBoxLayout()
        brand = QLabel("POMODORO")
        brand.setObjectName("brand")
        header.addWidget(brand)
        header.addStretch()
        self.session_badge = QLabel("0 SESSIONS")
        self.session_badge.setObjectName("sessionBadge")
        header.addWidget(self.session_badge)
        self.settings_button = QPushButton("⚙")
        self.settings_button.setObjectName("secondaryButton")
        self.settings_button.setFixedSize(38, 38)
        self.settings_button.clicked.connect(self._open_settings)
        header.addWidget(self.settings_button)
        root_layout.addLayout(header)

        root_layout.addStretch(1)

        self.mode_label = QLabel("FOCUS TIME")
        self.mode_label.setObjectName("modeLabel")
        self.mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root_layout.addWidget(self.mode_label)

        timer_card = QFrame()
        timer_card.setObjectName("timerCard")
        card_layout = QVBoxLayout(timer_card)
        card_layout.setContentsMargins(22, 38, 22, 38)
        card_layout.setSpacing(14)

        self.time_label = QLabel("25:00")
        self.time_label.setObjectName("timeLabel")
        self.time_label.setMinimumHeight(88)
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

        self.footer_label = QLabel()
        self.footer_label.setObjectName("footer")
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root_layout.addWidget(self.footer_label)

        self.setCentralWidget(root)

        self.timer.tick.connect(self._update_time)
        self.timer.mode_changed.connect(self._update_mode)
        self.timer.running_changed.connect(self._update_running_state)
        self.timer.session_count_changed.connect(self._update_session_count)
        self.timer.phase_completed.connect(self._phase_completed)
        self._update_time(self.timer.remaining_seconds)
        self._update_mode(self.timer.mode)
        self._update_running_state(False)

        self._retranslate_ui()

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

    def _open_settings(self) -> None:
        dialog = SettingsDialog(
            language=self.language,
            **self.timer_settings,
            parent=self,
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        new_language = dialog.selected_language()
        new_timer_settings = dialog.selected_timer_settings()

        self.language = new_language
        self.timer_settings = new_timer_settings

        self.settings.setValue("language", self.language)

        for key, value in self.timer_settings.items():
            self.settings.setValue(key, value)

        self.timer.apply_settings(**self.timer_settings)
        self._retranslate_ui()

    def _retranslate_ui(self) -> None:
        self.setWindowTitle(translate(self.language, "window_title"))

        self.focus_button.setText(translate(self.language, "focus"))
        self.short_button.setText(translate(self.language, "short_break"))
        self.long_button.setText(translate(self.language, "long_break"))
        self.reset_button.setText(translate(self.language, "reset"))
        self.footer_label.setText(translate(self.language, "footer"))

        self._update_mode(self.timer.mode)
        self._update_running_state(self.timer.is_running)
        self._update_session_count(self.timer.session_count)

    def _update_mode(self, mode: TimerMode) -> None:
        labels = {
            TimerMode.FOCUS: (
                "focus",
                "start_focus",
            ),
            TimerMode.SHORT_BREAK: (
                "short_break",
                "start_break",
            ),
            TimerMode.LONG_BREAK: (
                "long_break",
                "start_long_break",
            ),
        }

        mode_key, start_key = labels[mode]
        self.mode_label.setText(translate(self.language, mode_key))

        if not self.timer.is_running:
            self.start_button.setText(translate(self.language, start_key))

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
            self.start_button.setText(translate(self.language, "pause"))
            self.status_label.setText(
                translate(self.language, "stay_focused")
            )
            return

        start_keys = {
            TimerMode.FOCUS: "start_focus",
            TimerMode.SHORT_BREAK: "start_break",
            TimerMode.LONG_BREAK: "start_long_break",
        }

        status_keys = {
            TimerMode.FOCUS: "ready",
            TimerMode.SHORT_BREAK: "take_a_breather",
            TimerMode.LONG_BREAK: "long_break_ready",
        }

        self.start_button.setText(
            translate(self.language, start_keys[self.timer.mode])
        )
        self.status_label.setText(
            translate(self.language, status_keys[self.timer.mode])
        )

    def _update_session_count(self, count: int) -> None:
        key = "sessions_one" if count == 1 else "sessions_many"
        self.session_badge.setText(
            translate(self.language, key, count=count)
        )

    def _phase_completed(self, mode: TimerMode) -> None:
        if mode == TimerMode.FOCUS:
            key = "focus_completed"
        else:
            key = "break_completed"

        self.status_label.setText(translate(self.language, key))

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
