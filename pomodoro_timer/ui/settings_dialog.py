from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QCheckBox,
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
    """Диалоговое окно настроек таймера Pomodoro."""

    def __init__(
        self,
        language: str = "en",
        theme: str = "dark",
        parent=None,
        focus_minutes: int = 25,
        short_break_minutes: int = 5,
        long_break_minutes: int = 15,
        sessions_before_long_break: int = 4,
        snap_to_edges: bool = True,
    ) -> None:
        """Создаёт элементы управления и заполняет их текущими настройками."""
        super().__init__(parent)

        # Сохраняем выбранные язык, тему и состояние прилипания мини-таймера.
        self.language = language
        self.theme = theme
        self.snap_to_edges = snap_to_edges

        self.setMinimumWidth(300)

        # Применяем оформление окна в соответствии с текущей темой.
        self.setStyleSheet(self._stylesheet())

        # Заголовок окна и подпись для выбора языка.
        self.title_label = QLabel()
        self.language_label = QLabel()

        # Список доступных языков. Код языка хранится в пользовательских данных.
        self.language_combo = QComboBox()
        self.language_combo.addItem("Русский", "ru")
        self.language_combo.addItem("English", "en")

        # Выбираем язык, переданный при создании диалога.
        index = self.language_combo.findData(language)
        self.language_combo.setCurrentIndex(max(0, index))

        # Список тем оформления.
        self.theme_label = QLabel()
        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Dark", "dark")
        self.theme_combo.addItem("Light", "light")
        self.theme_combo.addItem("Midnight", "midnight")

        # Устанавливаем текущую тему.
        theme_index = self.theme_combo.findData(theme)
        self.theme_combo.setCurrentIndex(max(0, theme_index))

        # Повторный выбор языка из исходного кода сохранён без изменений.
        index = self.language_combo.findData(language)
        self.language_combo.setCurrentIndex(max(0, index))

        # Кнопки подтверждения и отмены изменений.
        self.save_button = QPushButton()
        self.save_button.setObjectName("saveButton")
        self.save_button.clicked.connect(self.accept)

        self.cancel_button = QPushButton()
        self.cancel_button.setObjectName("cancelButton")
        self.cancel_button.clicked.connect(self.reject)

        # Продолжительность фокус-сессии: от 1 до 180 минут.
        self.focus_spin = QSpinBox()
        self.focus_spin.setRange(1, 180)
        self.focus_spin.setValue(focus_minutes)
        self.focus_spin.setSuffix(" min")

        # Продолжительность короткого перерыва: от 1 до 60 минут.
        self.short_break_spin = QSpinBox()
        self.short_break_spin.setRange(1, 60)
        self.short_break_spin.setValue(short_break_minutes)
        self.short_break_spin.setSuffix(" min")

        # Продолжительность длинного перерыва: от 1 до 120 минут.
        self.long_break_spin = QSpinBox()
        self.long_break_spin.setRange(1, 120)
        self.long_break_spin.setValue(long_break_minutes)
        self.long_break_spin.setSuffix(" min")

        # Количество фокус-сессий до длинного перерыва: от 1 до 12.
        self.sessions_spin = QSpinBox()
        self.sessions_spin.setRange(1, 12)
        self.sessions_spin.setValue(sessions_before_long_break)

        # Флажок, управляющий прилипанием мини-таймера к краям экрана.
        self.snap_checkbox = QCheckBox()
        self.snap_checkbox.setChecked(self.snap_to_edges)

        # Размещаем кнопки отмены и сохранения в одной строке.
        buttons = QHBoxLayout()
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.save_button)

        # Создаём основной вертикальный макет окна.
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        layout.addWidget(self.title_label)
        layout.addWidget(self.language_label)
        layout.addWidget(self.language_combo)

        # Добавляем выбор темы оформления.
        self.theme_label.setText(
            translate(self.language, "theme")
        )
        layout.addWidget(self.theme_label)
        layout.addWidget(self.theme_combo)

        # Группируем параметры продолжительности и частоты перерывов.
        self.duration_form = QFormLayout()
        self.duration_form.addRow(
            translate(self.language, "focus_duration"),
            self.focus_spin,
        )
        self.duration_form.addRow(
            translate(self.language, "short_break_duration"),
            self.short_break_spin,
        )
        self.duration_form.addRow(
            translate(self.language, "long_break_duration"),
            self.long_break_spin,
        )
        self.duration_form.addRow(
            translate(self.language, "sessions_before_long_break"),
            self.sessions_spin,
        )

        layout.addLayout(self.duration_form)
        layout.addLayout(buttons)

        # Добавляем настройку прилипания мини-таймера.
        layout.addWidget(self.snap_checkbox)

        # Устанавливаем переведённые подписи элементов.
        self._update_texts()

    def _update_texts(self) -> None:
        """Обновляет текстовые подписи на выбранном языке."""

        self.setWindowTitle(translate(self.language, "settings"))
        self.title_label.setText(translate(self.language, "settings"))
        self.language_label.setText(translate(self.language, "language"))
        self.save_button.setText(translate(self.language, "save"))
        self.cancel_button.setText(translate(self.language, "cancel"))
        self.snap_checkbox.setText(
            translate(self.language, "snap_to_edges")
        )

    def selected_language(self) -> str:
        """Возвращает код выбранного языка."""
        return self.language_combo.currentData()

    def selected_timer_settings(self) -> dict[str, int]:
        """Возвращает выбранные параметры таймера в виде словаря."""

        return {
            "focus_minutes": self.focus_spin.value(),
            "short_break_minutes": self.short_break_spin.value(),
            "long_break_minutes": self.long_break_spin.value(),
            "sessions_before_long_break": self.sessions_spin.value(),
        }

    def selected_theme(self) -> str:
        """Возвращает идентификатор выбранной темы."""
        return self.theme_combo.currentData()

    def selected_snap_to_edges(self) -> bool:
        """Возвращает состояние флажка прилипания мини-таймера."""
        return self.snap_checkbox.isChecked()

    def _stylesheet(self) -> str:
        """Формирует стили окна настроек для выбранной темы."""

        # Цветовые палитры доступных тем оформления.
        themes = {
            "dark": {
                "background": "#111318",
                "text": "#F3F4F6",
                "field": "#20232B",
                "border": "#303440",
                "primary": "#F16B66",
                "primary_text": "#171719",
                "secondary": "#252933",
                "secondary_text": "#E1E4EA",
            },
            "light": {
                "background": "#F4F5F8",
                "text": "#252936",
                "field": "#FFFFFF",
                "border": "#E0E3EB",
                "primary": "#E76560",
                "primary_text": "#FFFFFF",
                "secondary": "#E9ECF2",
                "secondary_text": "#343A49",
            },
            "midnight": {
                "background": "#0D1020",
                "text": "#F0F0FF",
                "field": "#1C2340",
                "border": "#293152",
                "primary": "#9585FF",
                "primary_text": "#111020",
                "secondary": "#202744",
                "secondary_text": "#E0E5FF",
            },
        }

        # При неизвестной теме используем тёмную палитру.
        c = themes.get(self.theme, themes["dark"])

        # QSS-стили для окна, подписей, полей и кнопок.
        return f"""
            QDialog {{
                background: {c["background"]};
                color: {c["text"]};
            }}
            QLabel {{
                color: {c["text"]};
                font-size: 13px;
            }}
            QComboBox, QSpinBox {{
                background: {c["field"]};
                color: {c["text"]};
                border: 1px solid {c["border"]};
                border-radius: 8px;
                padding: 8px;
            }}
            QPushButton {{
                border: none;
                border-radius: 8px;
                padding: 9px 14px;
                font-weight: 600;
            }}
            QPushButton#saveButton {{
                background: {c["primary"]};
                color: {c["primary_text"]};
            }}
            QPushButton#cancelButton {{
                background: {c["secondary"]};
                color: {c["secondary_text"]};
            }}
        """
