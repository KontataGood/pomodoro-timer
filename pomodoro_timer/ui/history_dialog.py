
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
)

from pomodoro_timer.core.history import SessionHistory
from pomodoro_timer.core.timer import TimerMode
from pomodoro_timer.ui.translations import translate


class HistoryDialog(QDialog):
    def __init__(
        self,
        history: SessionHistory,
        language: str = "en",
        theme: str = "dark",
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.history = history
        self.language = language
        self.theme = theme

        self.setMinimumSize(620, 400)
        self.setWindowTitle(translate(language, "history"))

        self.empty_label = QLabel()
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.table = QTableWidget(0, 3)
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)
        layout.addWidget(self.empty_label)
        layout.addWidget(self.table)

        self._populate_table()
        self.setStyleSheet(self._stylesheet())

    def _populate_table(self) -> None:
        self.table.setHorizontalHeaderLabels(
            [
                translate(self.language, "history_date"),
                translate(self.language, "history_type"),
                translate(self.language, "history_duration"),
            ]
        )

        sessions = self.history.get_sessions(limit=100)
        self.table.setRowCount(len(sessions))
        self.empty_label.setText(
            translate(self.language, "history_empty")
        )
        self.empty_label.setVisible(not sessions)
        self.table.setVisible(bool(sessions))

        mode_names = {
            TimerMode.FOCUS.value: translate(self.language, "focus"),
            TimerMode.SHORT_BREAK.value: translate(
                self.language, "short_break"
            ),
            TimerMode.LONG_BREAK.value: translate(
                self.language, "long_break"
            ),
        }

        for row, session in enumerate(sessions):
            completed_at = session["completed_at"]
            parsed_date = datetime.fromisoformat(completed_at)

            date_format = "%d.%m.%Y, %H:%M"
            date_text = parsed_date.astimezone().strftime(date_format)

            duration = session["duration_seconds"]
            minutes, seconds = divmod(duration, 60)
            duration_text = (
                f"{minutes} min"
                if seconds == 0
                else f"{minutes} min {seconds} sec"
            )

            values = [
                date_text,
                mode_names.get(session["mode"], session["mode"]),
                duration_text,
            ]

            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(
                    item.flags()
                    & ~Qt.ItemFlag.ItemIsEditable
                )
                self.table.setItem(row, column, item)

    def _stylesheet(self) -> str:
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

        c = themes.get(self.theme, themes["dark"])

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
