
from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QFormLayout,
    QSpinBox,
)

from pomodoro_timer.ui.translations import translate


class SettingsDialog(QDialog):
    def __init__(
        self,
        language: str = "en",
        parent=None,
        focus_minutes: int = 25,
        short_break_minutes: int = 5,
        long_break_minutes: int = 15,
        sessions_before_long_break: int = 4,
    ) -> None:
        super().__init__(parent)

        self.language = language
        self.setMinimumWidth(300)

        self.setStyleSheet("""
            QDialog {
                background: #111318;
                color: #F3F4F6;
            }
            QLabel {
                color: #F3F4F6;
                font-size: 13px;
            }
            QComboBox {
                background: #20232B;
                color: #F3F4F6;
                border: 1px solid #303440;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton {
                border: none;
                border-radius: 8px;
                padding: 9px 14px;
                font-weight: 600;
            }
            QPushButton#saveButton {
                background: #F16B66;
                color: #171719;
            }
            QPushButton#cancelButton {
                background: #252933;
                color: #E1E4EA;
            }
        """)

        self.title_label = QLabel()
        self.language_label = QLabel()

        self.language_combo = QComboBox()
        self.language_combo.addItem("Русский", "ru")
        self.language_combo.addItem("English", "en")

        index = self.language_combo.findData(language)
        self.language_combo.setCurrentIndex(max(0, index))

        self.save_button = QPushButton()
        self.save_button.setObjectName("saveButton")
        self.save_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton()
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.reject)

        self.focus_spin = QSpinBox()
        self.focus_spin.setRange(1, 180)
        self.focus_spin.setValue(focus_minutes)
        self.focus_spin.setSuffix(" min")

        self.short_break_spin = QSpinBox()
        self.short_break_spin.setRange(1, 60)
        self.short_break_spin.setValue(short_break_minutes)
        self.short_break_spin.setSuffix(" min")

        self.long_break_spin = QSpinBox()
        self.long_break_spin.setRange(1, 120)
        self.long_break_spin.setValue(long_break_minutes)
        self.long_break_spin.setSuffix(" min")

        self.sessions_spin = QSpinBox()
        self.sessions_spin.setRange(1, 12)
        self.sessions_spin.setValue(sessions_before_long_break)

        buttons = QHBoxLayout()
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.save_button)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        layout.addWidget(self.title_label)
        layout.addWidget(self.language_label)
        layout.addWidget(self.language_combo)
        self.duration_form = QFormLayout()
        self.duration_form.addRow(
            translate(self.language, "focus_duration"), self.focus_spin
        )
        self.duration_form.addRow(
            translate(self.language, "short_break_duration"), self.short_break_spin
        )
        self.duration_form.addRow(
            translate(self.language, "long_break_duration"), self.long_break_spin
        )
        self.duration_form.addRow(
            translate(self.language, "sessions_before_long_break"), self.sessions_spin
        )
        layout.addLayout(self.duration_form)

        layout.addLayout(self.duration_form)
        layout.addLayout(buttons)

        self._update_texts()

    def _update_texts(self) -> None:
        self.setWindowTitle(translate(self.language, "settings"))
        self.title_label.setText(translate(self.language, "settings"))
        self.language_label.setText(translate(self.language, "language"))
        self.save_button.setText(translate(self.language, "save"))
        self.cancel_button.setText(translate(self.language, "cancel"))

    def selected_language(self) -> str:
        return self.language_combo.currentData()

    def selected_timer_settings(self) -> dict[str, int]:
        return {
            "focus_minutes": self.focus_spin.value(),
            "short_break_minutes": self.short_break_spin.value(),
            "long_break_minutes": self.long_break_spin.value(),
            "sessions_before_long_break": self.sessions_spin.value(),
        }