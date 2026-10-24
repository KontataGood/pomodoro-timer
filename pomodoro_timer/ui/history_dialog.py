from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QMessageBox,
    QPushButton,
)

from pomodoro_timer.core.history import SessionHistory
from pomodoro_timer.core.timer import TimerMode
from pomodoro_timer.ui.translations import translate


class HistoryDialog(QDialog):
    """Диалоговое окно с историей завершённых сессий."""

    def __init__(
        self,
        history: SessionHistory,
        language: str = "en",
        theme: str = "dark",
        parent=None,
    ) -> None:
        """Инициализирует окно истории и настраивает таблицу."""
        super().__init__(parent)

        # Сохраняем историю, язык и тему, переданные из главного окна.
        self.history = history
        self.language = language
        self.theme = theme

        # Задаём минимальный размер окна и переводим его заголовок.
        self.setMinimumSize(620, 400)
        self.setWindowTitle(translate(language, "history"))

        # Метка отображается, когда в истории нет записей.
        self.empty_label = QLabel()
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.clear_button = QPushButton()
        self.clear_button.clicked.connect(self._clear_history)

        # Таблица содержит дату, тип сессии и её продолжительность.
        self.table = QTableWidget(0, 3)

        # Запрещаем редактирование записей пользователем.
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        # При выборе ячейки выделяется вся строка.
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        # Скрываем нумерацию строк и равномерно распределяем столбцы.
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        # Размещаем сообщение о пустой истории и таблицу вертикально.
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.addWidget(self.empty_label)
        layout.addWidget(self.table)
        layout.addWidget(self.clear_button)

        # Заполняем таблицу данными и применяем выбранную тему.
        self._populate_table()
        self.setStyleSheet(self._stylesheet())

    def _populate_table(self) -> None:
        """Загружает записи из базы и отображает их в таблице."""

        # Устанавливаем переведённые названия столбцов.
        self.table.setHorizontalHeaderLabels(
            [
                translate(self.language, "history_date"),
                translate(self.language, "history_type"),
                translate(self.language, "history_duration"),
            ]
        )

        # Загружаем не более 100 последних сессий.
        sessions = self.history.get_sessions(limit=100)
        self.table.setRowCount(len(sessions))

        # Если записей нет, показываем соответствующее сообщение.
        self.empty_label.setText(
            translate(self.language, "history_empty")
        )
        self.empty_label.setVisible(not sessions)
        self.table.setVisible(bool(sessions))
        self.clear_button.setText(
            translate(self.language, "clear_history")
        )

        # Сопоставляем значения режимов с локализованными названиями.
        mode_names = {
            TimerMode.FOCUS.value: translate(self.language, "focus"),
            TimerMode.SHORT_BREAK.value: translate(
                self.language, "short_break"
            ),
            TimerMode.LONG_BREAK.value: translate(
                self.language, "long_break"
            ),
        }

        # Обрабатываем каждую сессию и добавляем её в отдельную строку.
        for row, session in enumerate(sessions):
            # Преобразуем сохранённую дату из ISO-формата в datetime.
            completed_at = session["completed_at"]
            parsed_date = datetime.fromisoformat(completed_at)

            # Форматируем дату и время для отображения пользователю.
            date_format = "%d.%m.%Y, %H:%M"
            date_text = parsed_date.astimezone().strftime(date_format)

            # Переводим продолжительность из секунд в минуты и секунды.
            duration = session["duration_seconds"]
            minutes, seconds = divmod(duration, 60)

            # Не показываем секунды, если длительность кратна минуте.
            duration_text = (
                f"{minutes} min"
                if seconds == 0
                else f"{minutes} min {seconds} sec"
            )

            # Подготавливаем значения для трёх столбцов таблицы.
            values = [
                date_text,
                mode_names.get(session["mode"], session["mode"]),
                duration_text,
            ]

            # Создаём элементы таблицы и запрещаем их редактирование.
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(
                    item.flags()
                    & ~Qt.ItemFlag.ItemIsEditable
                )
                self.table.setItem(row, column, item)

    def _clear_history(self) -> None:
        """Очищает историю после подтверждения пользователя."""
        answer = QMessageBox.question(
            self,
            translate(self.language, "clear_history"),
            translate(self.language, "confirm_clear_history"),
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.history.clear_history()
        self._populate_table()

    def _stylesheet(self) -> str:
        """Формирует стили окна истории для выбранной темы."""

        # Палитры цветов для доступных тем приложения.
        themes = {
            "dark": {
                "background": "#111318",
                "text": "#F3F4F6",
                "card": "#191C23",
                "border": "#2A2E38",
                "muted": "#989EAC",
            },
            "light": {
                "background": "#F4F5F8",
                "text": "#252936",
                "card": "#FFFFFF",
                "border": "#E0E3EB",
                "muted": "#747B8B",
            },
            "midnight": {
                "background": "#0D1020",
                "text": "#F0F0FF",
                "card": "#151A30",
                "border": "#293152",
                "muted": "#929BC0",
            },
        }

        # Используем тёмную тему, если указанного варианта нет в словаре.
        c = themes.get(self.theme, themes["dark"])

        # Возвращаем таблицу стилей Qt с цветами выбранной темы.
        return f"""
            QDialog {{
                background: {c["background"]};
                color: {c["text"]};
            }}
            QLabel {{
                color: {c["muted"]};
                font-size: 13px;
            }}
            QTableWidget {{
                background: {c["card"]};
                color: {c["text"]};
                border: 1px solid {c["border"]};
                border-radius: 10px;
                gridline-color: {c["border"]};
            }}
            QHeaderView::section {{
                background: {c["background"]};
                color: {c["muted"]};
                border: none;
                border-bottom: 1px solid {c["border"]};
                padding: 8px;
                font-weight: 600;
            }}
        """
