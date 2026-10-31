from __future__ import annotations

# Событие закрытия окна и инструменты для рисования круглого прогресса.
from PySide6.QtGui import QCloseEvent, QColor, QFont, QPainter, QPen
from PySide6.QtCore import (
    Property,
    QEasingCurve,
    QPoint,
    QPropertyAnimation,
    QRectF,
    Qt,
    QSize,
)
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pomodoro_timer.core.timer import PomodoroTimer, TimerMode
from pomodoro_timer.ui.translations import translate


class MiniTimerDial(QWidget):
    """Компактный круговой индикатор времени для плавающего окна."""

    def __init__(self, timer: PomodoroTimer, parent=None) -> None:
        super().__init__(parent)
        self.timer = timer
        self.remaining_seconds = timer.remaining_seconds
        self.theme = "dark"
        self.accent = QColor("#F16B66")
        self.track = QColor("#30364B")
        self.text_color = QColor("#F4F5FF")
        self._progress = 0.0
        self._ring_color = QColor(self.accent)

        # Анимации смягчают движение дуги и смену цвета между режимами.
        self.progress_animation = QPropertyAnimation(self, b"progress", self)
        self.progress_animation.setDuration(850)
        self.progress_animation.setEasingCurve(
            QEasingCurve.Type.OutCubic
        )

        self.color_animation = QPropertyAnimation(
            self, b"ringColor", self
        )
        self.color_animation.setDuration(300)
        self.color_animation.setEasingCurve(
            QEasingCurve.Type.InOutCubic
        )

        self.setMinimumSize(92, 92)
        self.setMaximumSize(92, 92)

    def _get_progress(self) -> float:
        return self._progress

    def _set_progress(self, value: float) -> None:
        self._progress = max(0.0, min(1.0, float(value)))
        self.update()

    progress = Property(float, _get_progress, _set_progress)

    def _get_ring_color(self) -> QColor:
        return QColor(self._ring_color)

    def _set_ring_color(self, value: QColor) -> None:
        self._ring_color = QColor(value)
        self.update()

    ringColor = Property(QColor, _get_ring_color, _set_ring_color)

    def set_theme(self, theme: str) -> None:
        """Обновляет цвета индикатора под тему и текущий режим."""
        self.theme = theme
        if theme == "light":
            self.track = QColor("#D7DDEA")
            self.text_color = QColor("#202536")
        elif theme == "midnight":
            self.track = QColor("#27345B")
            self.text_color = QColor("#F1F3FF")
        else:
            self.track = QColor("#30364B")
            self.text_color = QColor("#F4F5FF")
        self._update_mode_color(animated=True)
        self.update()

    def _update_mode_color(self, animated: bool = False) -> None:
        """Выбирает акцентный цвет для фокуса или перерыва."""
        if self.timer.mode == TimerMode.FOCUS:
            color = {
                "dark": "#F16B66",
                "light": "#E65B56",
                "midnight": "#8F7BFF",
            }.get(self.theme, "#F16B66")
        elif self.timer.mode == TimerMode.SHORT_BREAK:
            color = "#55B98A"
        else:
            color = "#6C9EFF"
        target_color = QColor(color)
        self.accent = QColor(target_color)

        if animated and self._ring_color != target_color:
            self.color_animation.stop()
            self.color_animation.setStartValue(self._ring_color)
            self.color_animation.setEndValue(target_color)
            self.color_animation.start()
        else:
            self._set_ring_color(target_color)

    def refresh(self, seconds: int | None = None) -> None:
        """Обновляет время и плавно перемещает дугу прогресса."""
        if seconds is not None:
            self.remaining_seconds = max(0, seconds)

        total = max(1, self.timer.duration_for(self.timer.mode))
        elapsed = max(0, min(total, total - self.remaining_seconds))
        target_progress = elapsed / total

        self.progress_animation.stop()
        self.progress_animation.setStartValue(self._progress)
        self.progress_animation.setEndValue(target_progress)
        self.progress_animation.start()
        self._update_mode_color(animated=True)
        self.update()

    def paintEvent(self, event) -> None:
        """Рисует тонкое кольцо прогресса и время в центре."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        side = min(self.width(), self.height())
        rect = QRectF(
            (self.width() - side) / 2 + 7,
            (self.height() - side) / 2 + 7,
            side - 14,
            side - 14,
        )

        # Сначала рисуем фоновую дорожку кольца.
        track_pen = QPen(self.track, 5)
        track_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(track_pen)
        painter.drawArc(rect, 90 * 16, -360 * 16)

        # Затем поверх неё — дугу, соответствующую прошедшей части фазы.
        progress_pen = QPen(self._ring_color, 5)
        progress_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(progress_pen)
        painter.drawArc(rect, 90 * 16, int(-360 * self._progress * 16))

        # Время размещается строго по центру кольца.
        minutes, seconds = divmod(self.remaining_seconds, 60)
        painter.setPen(self.text_color)
        painter.setFont(QFont("Segoe UI", 19, QFont.Weight.Bold))
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            f"{minutes:02d}:{seconds:02d}",
        )
        painter.end()


class MiniTimer(QWidget):
    """Компактное плавающее окно для управления основным Pomodoro-таймером."""

    def __init__(self, timer: PomodoroTimer, parent=None) -> None:
        super().__init__(parent)
        self.timer = timer
        self.snap_to_edges = True
        self._drag_position: QPoint | None = None

        # Убираем системную рамку и заголовок, оставляя окно поверх остальных.
        self.setWindowTitle("Pomodoro Mini Timer")
        self.setWindowFlags(
            Qt.WindowType.Tool
            | Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setMinimumSize(280, 170)
        self.setMaximumSize(280, 170)
        self.resize(280, 170)

        # Позиция мини-окна сохраняется между запусками приложения.
        self.position_settings = QSettings(
            "KontataGood", "PomodoroTimer"
        )
        self._restore_position()

        self._apply_theme()

        # Внешняя карточка с тонкой рамкой и скруглёнными углами.
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 7, 12, 8)
        layout.setSpacing(3)

        # Заголовок одновременно служит удобной областью для перетаскивания.
        header = QHBoxLayout()
        header.setContentsMargins(2, 0, 2, 0)
        self.mode_label = QLabel()
        self.mode_label.setObjectName("modeLabel")
        self.mode_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.mode_label.installEventFilter(self)
        header.addWidget(self.mode_label)
        header.addStretch(1)

        self.main_window_button = QPushButton("↗")
        self.main_window_button.setObjectName("iconButton")
        self.main_window_button.setFixedSize(25, 25)
        self.main_window_button.setToolTip(
            translate(self._language(), "show_main_window")
        )
        self.main_window_button.clicked.connect(self._show_main_window)
        header.addWidget(self.main_window_button)
        layout.addLayout(header)

        # Круговой индикатор повторно использует тот же объект таймера.
        self.dial = MiniTimerDial(self.timer, self)
        layout.addWidget(self.dial, alignment=Qt.AlignmentFlag.AlignCenter)

        # Нижняя панель управления содержит только компактные кнопки-иконки.
        controls = QHBoxLayout()
        controls.setSpacing(8)
        controls.addStretch(1)

        self.toggle_button = QPushButton("▶")
        self.toggle_button.setObjectName("primaryIconButton")
        self.toggle_button.setFixedSize(70, 30)
        self.toggle_button.clicked.connect(self._toggle_timer)
        controls.addWidget(self.toggle_button)

        self.reset_button = QPushButton("↻")
        self.reset_button.setObjectName("iconButton")
        self.reset_button.setFixedSize(54, 30)
        self.reset_button.setToolTip(
            translate(self._language(), "restart")
        )
        self.reset_button.clicked.connect(self._reset_timer)
        controls.addWidget(self.reset_button)
        controls.addStretch(1)
        layout.addLayout(controls)

        # Мини-окно получает обновления от основного таймера.
        self.timer.tick.connect(self._update_time)
        self.timer.mode_changed.connect(self._update_mode)
        self.timer.running_changed.connect(self._update_running_state)

        self._update_time(self.timer.remaining_seconds)
        self._update_mode(self.timer.mode)
        self._update_running_state(self.timer.is_running)
        self._retranslate_ui()

    def _restore_position(self) -> None:
        """Восстанавливает позицию, если она находится на доступном экране."""
        saved_position = self.position_settings.value("mini_timer/position")
        if not isinstance(saved_position, QPoint):
            return

        screen = QApplication.screenAt(saved_position)
        if screen is None:
            screen = QApplication.primaryScreen()
        if screen is None:
            return

        available = screen.availableGeometry()
        x = max(
            available.left(),
            min(
                saved_position.x(),
                available.right() - self.width() + 1,
            ),
        )
        y = max(
            available.top(),
            min(
                saved_position.y(),
                available.bottom() - self.height() + 1,
            ),
        )
        self.move(QPoint(x, y))

    def _save_position(self) -> None:
        """Записывает координаты окна в настройки приложения."""
        self.position_settings.setValue(
            "mini_timer/position", self.pos()
        )

    def _apply_theme(self) -> None:
        """Подбирает цвета карточки и кнопок под текущую тему приложения."""
        main_window = self.parentWidget()
        theme = getattr(main_window, "theme", "dark")

        palettes = {
            "dark": {
                "background": "#111522",
                "surface": "#171E32",
                "border": "#303B5C",
                "text": "#F3F4FF",
                "muted": "#AAB5D6",
                "button": "#242D49",
                "hover": "#303C60",
                "accent": "#8F7BFF",
            },
            "light": {
                "background": "#F4F6FB",
                "surface": "#FFFFFF",
                "border": "#CBD3E2",
                "text": "#202536",
                "muted": "#69738A",
                "button": "#E8ECF5",
                "hover": "#DDE3EF",
                "accent": "#7460E8",
            },
            "midnight": {
                "background": "#090D1B",
                "surface": "#111A33",
                "border": "#303D68",
                "text": "#F1F3FF",
                "muted": "#9BA8D0",
                "button": "#1B284B",
                "hover": "#293960",
                "accent": "#8F7BFF",
            },
        }
        c = palettes.get(theme, palettes["dark"])
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {c["background"]};
                color: {c["text"]};
                font-family: "Segoe UI", Arial, sans-serif;
            }}
            MiniTimer {{
                background-color: {c["surface"]};
                border: 1px solid {c["border"]};
                border-radius: 14px;
            }}
            QLabel#modeLabel {{
                color: {c["muted"]};
                background: transparent;
                font-size: 10px;
                font-weight: 700;
                letter-spacing: 2px;
            }}
            MiniTimerDial {{
                background: transparent;
                border: none;
            }}
            QPushButton {{
                background-color: {c["button"]};
                color: {c["text"]};
                border: 1px solid {c["border"]};
                border-radius: 9px;
                font-size: 15px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {c["hover"]};
                border-color: {c["accent"]};
            }}
            QPushButton:pressed {{
                background-color: {c["accent"]};
                color: white;
            }}
            QPushButton#primaryIconButton {{
                background-color: {c["accent"]};
                color: white;
                border: none;
                font-size: 14px;
            }}
            QPushButton#primaryIconButton:hover {{
                background-color: {c["hover"]};
                border: 1px solid {c["accent"]};
            }}
        """)

    def _language(self) -> str:
        """Возвращает язык главного окна приложения."""
        main_window = self.parentWidget()
        if main_window is not None:
            return main_window.language
        return "en"

    def _update_time(self, seconds: int) -> None:
        """Обновляет круговой индикатор времени."""
        self.dial.refresh(seconds)

    def _update_mode(self, mode: TimerMode) -> None:
        """Обновляет подпись режима и цвет кольца."""
        labels = {
            TimerMode.FOCUS: "focus",
            TimerMode.SHORT_BREAK: "short_break",
            TimerMode.LONG_BREAK: "long_break",
        }
        self.mode_label.setText(
            translate(self._language(), labels[mode]).upper()
        )
        self.dial.refresh(self.timer.remaining_seconds)

    def _update_running_state(self, running: bool) -> None:
        """Меняет символ основной кнопки в зависимости от состояния."""
        self.toggle_button.setText("Ⅱ" if running else "▶")
        self.toggle_button.setToolTip(
            translate(
                self._language(),
                "pause" if running else (
                    "start_focus"
                    if self.timer.mode == TimerMode.FOCUS
                    else "start_long_break"
                    if self.timer.mode == TimerMode.LONG_BREAK
                    else "start_break"
                ),
            )
        )

    def _toggle_timer(self) -> None:
        """Ставит основной таймер на паузу или запускает его."""
        if self.timer.is_running:
            self.timer.pause()
        else:
            self.timer.start()

    def _reset_timer(self) -> None:
        """Сбрасывает текущую фазу основного таймера."""
        self.timer.reset()

    def _show_main_window(self) -> None:
        """Скрывает мини-окно и выводит главное окно на передний план."""
        main_window = self.parentWidget()
        if main_window is None:
            return
        self.hide()
        main_window.showNormal()
        main_window.raise_()
        main_window.activateWindow()

    def _retranslate_ui(self) -> None:
        """Обновляет подсказки кнопок после смены языка."""
        self.main_window_button.setToolTip(
            translate(self._language(), "show_main_window")
        )
        self.reset_button.setToolTip(
            translate(self._language(), "restart")
        )
        self._update_mode(self.timer.mode)
        self._update_running_state(self.timer.is_running)

    def eventFilter(self, watched, event) -> bool:
        """Позволяет перетаскивать окно за верхнюю строку режима."""
        if watched is self.mode_label:
            if event.type() == event.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    self._drag_position = (
                        event.globalPosition().toPoint()
                        - self.frameGeometry().topLeft()
                    )
                    return True
            elif event.type() == event.Type.MouseMove:
                if (
                    event.buttons() & Qt.MouseButton.LeftButton
                    and self._drag_position is not None
                ):
                    self.move(
                        event.globalPosition().toPoint()
                        - self._drag_position
                    )
                    return True
            elif event.type() == event.Type.MouseButtonRelease:
                if event.button() == Qt.MouseButton.LeftButton:
                    self._drag_position = None
                    self._snap_to_screen_edge()
                    self._save_position()
                    return True
        return super().eventFilter(watched, event)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Сохраняет позицию и закрывает окно, не останавливая таймер."""
        self._save_position()
        if self.timer.is_running:
            event.ignore()
            self.hide()
            return
        event.accept()

    def mousePressEvent(self, event) -> None:
        """Начинает перемещение окна при захвате свободной области."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = (
                event.globalPosition().toPoint()
                - self.frameGeometry().topLeft()
            )
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """Перемещает окно вслед за курсором."""
        if (
            event.buttons() & Qt.MouseButton.LeftButton
            and self._drag_position is not None
        ):
            self.move(
                event.globalPosition().toPoint() - self._drag_position
            )
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """При отпускании мыши приклеивает окно к ближайшему краю."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_position = None
            self._snap_to_screen_edge()
            self._save_position()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def _snap_to_screen_edge(self) -> None:
        """Выравнивает окно по ближайшему краю рабочей области экрана."""
        if not self.snap_to_edges:
            return

        screen = QApplication.screenAt(self.frameGeometry().center())
        if screen is None:
            screen = QApplication.primaryScreen()
        if screen is None:
            return

        available = screen.availableGeometry()
        window = self.frameGeometry()
        distances = {
            "left": abs(window.left() - available.left()),
            "right": abs(available.right() - window.right()),
            "top": abs(window.top() - available.top()),
            "bottom": abs(available.bottom() - window.bottom()),
        }
        edge = min(distances, key=distances.get)
        if distances[edge] > 40:
            return

        x, y = window.x(), window.y()
        if edge == "left":
            x = available.left()
        elif edge == "right":
            x = available.right() - window.width() + 1
        elif edge == "top":
            y = available.top()
        elif edge == "bottom":
            y = available.bottom() - window.height() + 1

        x = max(
            available.left(),
            min(x, available.right() - window.width() + 1),
        )
        y = max(
            available.top(),
            min(y, available.bottom() - window.height() + 1),
        )
        self.move(QPoint(x, y))
