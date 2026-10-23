from __future__ import annotations

# Тип события закрытия окна.
from PySide6.QtGui import QCloseEvent

# Геометрия окна, координаты и флаги поведения окна.
from PySide6.QtCore import QPoint, Qt

# Работа с мониторами и элементы интерфейса мини-таймера.
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

# Основной таймер и перечисление его режимов.
from pomodoro_timer.core.timer import PomodoroTimer, TimerMode

# Функция перевода текстов интерфейса.
from pomodoro_timer.ui.translations import translate


class MiniTimer(QWidget):
    """Компактное окно для управления основным таймером Pomodoro."""

    def __init__(self, timer: PomodoroTimer, parent=None) -> None:
        super().__init__(parent)

        # Используем тот же объект таймера, что и в главном окне.
        # Благодаря этому оба окна показывают одинаковое состояние.
        self.timer = timer

        # По умолчанию автоматическое прилипание включено.
        # Значение может быть переопределено настройками приложения.
        self.snap_to_edges = True

        # Настраиваем поведение окна: оно остаётся поверх остальных окон.
        self.setWindowTitle("Pomodoro Mini Timer")
        self.setWindowFlags(
            Qt.WindowType.Window
            | Qt.WindowType.WindowStaysOnTopHint
        )

        # Задаём минимальный и начальный размеры мини-таймера.
        self.setMinimumSize(300, 190)
        self.resize(320, 210)

        # Оформление мини-таймера.
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

        # Основная вертикальная компоновка элементов окна.
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 14)
        layout.setSpacing(8)

        # Название текущего режима: фокус или перерыв.
        self.mode_label = QLabel()
        self.mode_label.setObjectName("modeLabel")
        self.mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.mode_label)

        # Оставшееся время в формате MM:SS.
        self.time_label = QLabel()
        self.time_label.setObjectName("timeLabel")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.time_label)

        # Горизонтальный ряд кнопок управления.
        controls = QHBoxLayout()
        controls.setSpacing(8)

        # Кнопка запуска или паузы основного таймера.
        self.toggle_button = QPushButton()
        self.toggle_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.toggle_button.clicked.connect(self._toggle_timer)
        controls.addWidget(self.toggle_button)

        # Кнопка возврата к главному окну приложения.
        self.main_window_button = QPushButton()
        self.main_window_button.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed,
        )
        self.main_window_button.clicked.connect(self._show_main_window)
        controls.addWidget(self.main_window_button)

        layout.addLayout(controls)

        # Подписываем интерфейс на сигналы основного таймера.
        # При изменении времени, режима или состояния кнопки обновляются.
        self.timer.tick.connect(self._update_time)
        self.timer.mode_changed.connect(self._update_mode)
        self.timer.running_changed.connect(self._update_running_state)

        # Заполняем интерфейс актуальными значениями при создании окна.
        self._update_time(self.timer.remaining_seconds)
        self._update_mode(self.timer.mode)
        self._update_running_state(self.timer.is_running)
        self._retranslate_ui()

    def _language(self) -> str:
        """Возвращает язык главного окна приложения."""
        main_window = self.parentWidget()

        if main_window is not None:
            return main_window.language

        # Запасной язык, если у мини-таймера нет родительского окна.
        return "en"

    def _update_time(self, seconds: int) -> None:
        """Показывает оставшееся время в формате MM:SS."""
        minutes, secs = divmod(max(0, seconds), 60)
        self.time_label.setText(f"{minutes:02d}:{secs:02d}")

    def _update_mode(self, mode: TimerMode) -> None:
        """Обновляет название текущего режима с учётом языка."""
        labels = {
            TimerMode.FOCUS: "focus",
            TimerMode.SHORT_BREAK: "short_break",
            TimerMode.LONG_BREAK: "long_break",
        }

        self.mode_label.setText(
            translate(self._language(), labels[mode])
        )

    def _update_running_state(self, running: bool) -> None:
        """Меняет текст кнопки в зависимости от состояния таймера."""
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
        """Ставит таймер на паузу или запускает его."""
        if self.timer.is_running:
            self.timer.pause()
        else:
            self.timer.start()

    def _show_main_window(self) -> None:
        """Скрывает мини-таймер и выводит главное окно на передний план."""
        main_window = self.parentWidget()

        # Без родительского окна переключиться некуда.
        if main_window is None:
            return

        self.hide()

        # Восстанавливаем главное окно, если оно было скрыто или свёрнуто.
        main_window.showNormal()
        main_window.raise_()
        main_window.activateWindow()

    def _retranslate_ui(self) -> None:
        """Обновляет переведённые надписи мини-таймера."""
        self.main_window_button.setText(
            translate(self._language(), "show_main_window")
        )

        # Повторно обновляем подписи в соответствии с текущим состоянием.
        self._update_mode(self.timer.mode)
        self._update_running_state(self.timer.is_running)

    def closeEvent(self, event: QCloseEvent) -> None:
        """Скрывает окно во время работы таймера, не останавливая его."""
        if self.timer.is_running:
            # Закрытие мини-окна не должно прерывать текущий сеанс.
            event.ignore()
            self.hide()
            return

        # Если таймер остановлен или на паузе, разрешаем закрыть окно.
        event.accept()

    def mousePressEvent(self, event) -> None:
        """Запоминает смещение курсора при начале перетаскивания окна."""
        if event.button() == Qt.MouseButton.LeftButton:
            # Смещение нужно, чтобы окно не прыгало к курсору мыши.
            self._drag_position = (
                event.globalPosition().toPoint()
                - self.frameGeometry().topLeft()
            )
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        """Перемещает окно вслед за курсором при зажатой левой кнопке."""
        if (
            event.buttons() & Qt.MouseButton.LeftButton
            and hasattr(self, "_drag_position")
        ):
            # Сохраняем исходное смещение курсора относительно окна.
            new_position = (
                event.globalPosition().toPoint()
                - self._drag_position
            )
            self.move(new_position)
            event.accept()
            return

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        """Проверяет, нужно ли приклеить окно к краю после перетаскивания."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._snap_to_screen_edge()
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def _snap_to_screen_edge(self) -> None:
        """Выравнивает окно по ближайшему краю рабочей области экрана."""
        # Если пользователь отключил прилипание, оставляем окно на месте.
        if not self.snap_to_edges:
            return

        # Определяем монитор, на котором находится центр окна.
        screen = QApplication.screenAt(self.frameGeometry().center())

        # Если монитор определить не удалось, используем основной.
        if screen is None:
            screen = QApplication.primaryScreen()

        if screen is None:
            return

        # Рабочая область не включает место, занятое панелью задач.
        available = screen.availableGeometry()
        window = self.frameGeometry()

        # Считаем расстояние от окна до каждого из четырёх краёв.
        distances = {
            "left": abs(window.left() - available.left()),
            "right": abs(available.right() - window.right()),
            "top": abs(window.top() - available.top()),
            "bottom": abs(available.bottom() - window.bottom()),
        }

        # Прилипание срабатывает, если ближайший край не дальше 40 пикселей.
        threshold = 40
        edge = min(distances, key=distances.get)

        if distances[edge] > threshold:
            return

        # По умолчанию сохраняем текущую позицию окна.
        x = window.x()
        y = window.y()

        # Выравниваем окно по ближайшему краю.
        if edge == "left":
            x = available.left()
        elif edge == "right":
            x = available.right() - window.width() + 1
        elif edge == "top":
            y = available.top()
        elif edge == "bottom":
            y = available.bottom() - window.height() + 1

        # Ограничиваем координату Y рабочей областью экрана.
        y = max(
            available.top(),
            min(y, available.bottom() - window.height() + 1),
        )

        # Ограничиваем координату X рабочей областью экрана.
        x = max(
            available.left(),
            min(x, available.right() - window.width() + 1),
        )

        # Перемещаем окно в рассчитанную позицию.
        self.move(QPoint(x, y))
