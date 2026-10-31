
from __future__ import annotations

# Инструменты Qt для анимации, сигналов и плавного изменения интерфейса.
from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    Signal,
)

# Виджеты Qt, используемые для построения боковой панели.
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class Sidebar(QFrame):
    """Компактная боковая панель навигации приложения."""

    # Сигнал передаёт идентификатор выбранного раздела главному окну.
    navigation_requested = Signal(str)

    # Сигнал сообщает главному окну об изменении состояния панели.
    toggle_requested = Signal()

    # Ширина панели в компактном и раскрытом состояниях (пиксели).
    COLLAPSED_WIDTH = 64
    EXPANDED_WIDTH = 210

    def __init__(self, parent: QWidget | None = None) -> None:
        """Создаёт панель навигации и размещает её элементы."""
        super().__init__(parent)

        self.setObjectName("sidebar")

        # По умолчанию панель запускается в компактном состоянии.
        self.setFixedWidth(self.COLLAPSED_WIDTH)
        self.expanded = False

        # Храним идентификатор текущего активного раздела.
        self.active_page = "timer"

        # Создаём две анимации: для минимальной и максимальной ширины.
        # Совместное изменение ограничений позволяет плавно менять размер.
        self.animation = QPropertyAnimation(
            self,
            b"minimumWidth",
            self,
        )
        self.maximum_animation = QPropertyAnimation(
            self,
            b"maximumWidth",
            self,
        )

        # Настраиваем одинаковую продолжительность и характер анимации.
        for animation in (
            self.animation,
            self.maximum_animation,
        ):
            animation.setDuration(200)
            animation.setEasingCurve(
                QEasingCurve.Type.InOutCubic
            )

        # Основной вертикальный контейнер боковой панели.
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 12, 8, 12)
        self.main_layout.setSpacing(8)

        # Кнопка раскрытия и сворачивания боковой панели.
        self.toggle_button = QPushButton("☰")
        self.toggle_button.setObjectName("sidebarToggle")
        self.toggle_button.setFixedHeight(42)
        self.toggle_button.setToolTip(
            "Свернуть или раскрыть меню"
        )
        self.toggle_button.clicked.connect(self.toggle)

        self.main_layout.addWidget(self.toggle_button)
        self.main_layout.addSpacing(12)

        # Словари позволяют обращаться к кнопкам и подписям по имени раздела.
        self.buttons: dict[str, QPushButton] = {}
        self.labels: dict[str, QLabel] = {}

        # Основные разделы приложения.
        self._add_navigation_button("timer", "◷", "Timer")
        self._add_navigation_button("statistics", "▥", "Statistics")
        self._add_navigation_button("history", "◴", "History")

        # Раздел настроек размещается в нижней части панели.
        self.main_layout.addStretch(1)
        self._add_navigation_button("settings", "⚙", "Settings")

        # При первом запуске активным считается экран таймера.
        self.set_active_page("timer")

    def _add_navigation_button(
        self,
        page: str,
        icon: str,
        title: str,
    ) -> None:
        """Создаёт кнопку навигации с иконкой и текстовой подписью."""

        # Контейнер объединяет кнопку и её текстовую подпись.
        container = QWidget()
        container.setObjectName("sidebarItem")

        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Кнопка с иконкой остаётся видимой в компактном режиме.
        button = QPushButton(icon)
        button.setObjectName("sidebarButton")
        button.setFixedSize(42, 42)
        button.setToolTip(title)

        # Подпись отображается только в раскрытом режиме.
        label = QLabel(title)
        label.setObjectName("sidebarLabel")
        label.setVisible(False)

        # При нажатии передаём идентификатор выбранного раздела.
        button.clicked.connect(
            lambda checked=False, name=page:
            self._on_navigation_clicked(name)
        )

        layout.addWidget(button)
        layout.addWidget(label)
        layout.addStretch(1)

        # Сохраняем ссылки на элементы для последующего обновления.
        self.buttons[page] = button
        self.labels[page] = label

        self.main_layout.addWidget(container)

    def _on_navigation_clicked(self, page: str) -> None:
        """Обрабатывает выбор раздела и уведомляет главное окно."""

        self.set_active_page(page)
        self.navigation_requested.emit(page)

    def set_active_page(self, page: str) -> None:
        """Выделяет кнопку, соответствующую текущему разделу."""

        # Игнорируем неизвестные идентификаторы разделов.
        if page not in self.buttons:
            return

        self.active_page = page

        # Обновляем свойство active для каждой кнопки.
        for name, button in self.buttons.items():
            button.setProperty("active", name == page)

            # Повторно применяем стили, чтобы сразу обновить подсветку.
            button.style().unpolish(button)
            button.style().polish(button)

    def toggle(self) -> None:
        """Переключает панель между компактным и раскрытым состояниями."""

        self.set_expanded(not self.expanded)

        # Сообщаем главному окну об изменении состояния панели.
        self.toggle_requested.emit()

    def set_expanded(self, expanded: bool) -> None:
        """Устанавливает состояние панели и запускает анимацию ширины."""

        # Не запускаем повторную анимацию, если состояние не изменилось.
        if self.expanded == expanded:
            return

        self.expanded = expanded

        # Определяем конечную ширину в зависимости от состояния панели.
        target_width = (
            self.EXPANDED_WIDTH
            if expanded
            else self.COLLAPSED_WIDTH
        )

        # Останавливаем предыдущую анимацию, если пользователь
        # переключил состояние до её завершения.
        self.animation.stop()
        self.maximum_animation.stop()

        # Задаём начальную и конечную ширину для обеих анимаций.
        for animation in (
            self.animation,
            self.maximum_animation,
        ):
            animation.setStartValue(self.width())
            animation.setEndValue(target_width)

        # Запускаем обе анимации одновременно.
        self.animation.start()
        self.maximum_animation.start()

        # Показываем или скрываем названия разделов.
        for label in self.labels.values():
            label.setVisible(expanded)

        # Меняем символ кнопки в зависимости от состояния панели.
        self.toggle_button.setText("‹" if expanded else "☰")
