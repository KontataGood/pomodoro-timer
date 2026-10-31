from __future__ import annotations

# Импорты Qt для рисования, свойств и плавной анимации.
from PySide6.QtCore import (
    Qt,
    QRectF,
    QSize,
    Property,
    QPropertyAnimation,
    QEasingCurve,
)
# Импорты Qt для рисования и плавного перехода цветов.
from PySide6.QtGui import (
    QPainter,
    QPen,
    QColor,
    QFont,
    QBrush,
)
from PySide6.QtWidgets import QWidget, QSizePolicy


class CircularTimer(QWidget):
    # Текущее значение прогресса, которое будет плавно изменяться.
    _progress = 1.0

    @Property(float)
    def progress(self) -> float:
        """Возвращает текущее значение анимируемого прогресса."""
        return self._progress

    @progress.setter
    def progress(self, value: float) -> None:
        """Обновляет прогресс и запускает перерисовку индикатора."""
        self._progress = max(0.0, min(1.0, value))
        self.update()

    """Круговой индикатор времени для Pomodoro Timer."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Создаёт круговой таймер с начальными значениями."""
        super().__init__(parent)

        # Начальные параметры таймера.
        self.remaining_seconds = 25 * 60
        self.total_seconds = 25 * 60
        self.mode = "focus"
        self.theme = "dark"

        # Текущий цвет кольца и целевой цвет для анимации.
        self.current_color = QColor("#F05252")

        # Создаём плавную анимацию изменения прогресса кольца.
        self.progress_animation = QPropertyAnimation(
            self,
            b"progress",
            self,
        )

        # Продолжительность анимации соответствует одному шагу таймера.
        self.progress_animation.setDuration(1000)

        # Используем линейное движение без ускорения и замедления.
        self.progress_animation.setEasingCurve(
            QEasingCurve.Type.Linear
        )


        # Цветовая палитра кругового таймера для каждой темы.
        self.theme_colors = {
            "dark": {
                "track": "#2A2E38",
                "text": "#F3F4F6",
                "focus": "#F05252",
                "short_break": "#55B88A",
                "long_break": "#6597E8",
            },
            "light": {
                "track": "#E0E3EB",
                "text": "#252936",
                "focus": "#E76560",
                "short_break": "#399B70",
                "long_break": "#477CCB",
            },
            "midnight": {
                "track": "#293152",
                "text": "#F0F0FF",
                "focus": "#F05252",
                "short_break": "#55B88A",
                "long_break": "#6597E8",
            },
        }

        # Разрешаем таймеру адаптироваться к размеру рабочей области.
        # Минимальный размер позволяет интерфейсу помещаться в небольшом окне.
        self.setMinimumSize(220, 220)

        # Ограничиваем рекомендуемый размер, чтобы круг не становился огромным.
        self.setMaximumSize(420, 420)

        # Разрешаем виджету занимать свободное пространство.
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding,
        )

        # Фон виджета будет прозрачным.
        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

    def animate_color(self, target_color: QColor) -> None:
        """Плавно изменяет цвет кольца до заданного оттенка."""

        # Останавливаем предыдущий переход, если он ещё выполняется.
        if hasattr(self, "color_animation"):
            self.color_animation.stop()

        # Создаём анимацию изменения цвета через промежуточные оттенки.
        self.color_animation = QPropertyAnimation(
            self,
            b"ringColor",
            self,
        )

        # Настраиваем длительность и плавность перехода.
        self.color_animation.setDuration(300)
        self.color_animation.setEasingCurve(
            QEasingCurve.Type.InOutCubic
        )

        # Задаём начальный и конечный цвета.
        self.color_animation.setStartValue(self.current_color)
        self.color_animation.setEndValue(target_color)

        # Запускаем анимацию.
        self.color_animation.start()


    # Свойство позволяет Qt плавно изменять цвет кольца.
    @Property(QColor)
    def ringColor(self) -> QColor:
        """Возвращает текущий цвет кольца."""
        return self.current_color

    @ringColor.setter
    def ringColor(self, color: QColor) -> None:
        """Устанавливает новый цвет и перерисовывает кольцо."""
        self.current_color = color
        self.update()

    def set_time(
        self,
        remaining_seconds: int,
        total_seconds: int,
        mode: str,
    ) -> None:
        """Обновляет время и плавно анимирует изменение прогресса."""

        # Запоминаем предыдущий режим и длительность фазы.
        previous_mode = self.mode
        previous_total = self.total_seconds

        # Не допускаем отрицательных значений времени.
        self.remaining_seconds = max(0, remaining_seconds)
        self.total_seconds = max(1, total_seconds)

        # Поддерживаем как строку, так и Enum.
        self.mode = getattr(mode, "value", mode)

        # Выбираем цвет кольца для текущего режима и темы.
        colors = self.theme_colors[self.theme]

        if self.mode == "short_break":
            target_color = QColor(colors["short_break"])
        elif self.mode == "long_break":
            target_color = QColor(colors["long_break"])
        else:
            target_color = QColor(colors["focus"])

        # Запускаем плавную смену цвета, если оттенок изменился.
        if target_color != self.current_color:
            self.animate_color(target_color)

        # Вычисляем новое значение прогресса.
        target_progress = (
            self.remaining_seconds / self.total_seconds
        )

        # При смене режима или длительности сразу устанавливаем прогресс.
        if (
            previous_mode != self.mode
            or previous_total != self.total_seconds
        ):
            self.progress_animation.stop()
            self.progress = target_progress
            return

        # Останавливаем предыдущую анимацию перед запуском новой.
        self.progress_animation.stop()

        # Плавно перемещаем дугу к новому значению.
        self.progress_animation.setStartValue(self.progress)
        self.progress_animation.setEndValue(target_progress)
        self.progress_animation.start()


    def set_theme(self, theme: str) -> None:
        """Меняет цветовую палитру кругового таймера."""

        # Если тема неизвестна, используем тёмную.
        if theme not in self.theme_colors:
            theme = "dark"

        self.theme = theme
        self.update()

    def sizeHint(self) -> QSize:
        """Возвращает рекомендуемый размер виджета."""
        return QSize(360, 360)

    def paintEvent(self, event) -> None:
        """Рисует круг, индикатор прогресса и оставшееся время."""

        # Создаём объект для рисования на поверхности виджета.
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Получаем доступную область виджета.
        side = min(self.width(), self.height())

        # Делаем обводку немного тоньше для более изящного вида.
        pen_width = max(6.0, side * 0.027)
        margin = pen_width / 2 + 5

        # Вычисляем квадратную область, в которой будет нарисован круг.
        diameter = side - margin * 2
        circle = QRectF(
            (self.width() - diameter) / 2,
            (self.height() - diameter) / 2,
            diameter,
            diameter,
        )

        # Получаем цвета выбранной темы.
        colors = self.theme_colors[self.theme]

        # Используем текущий цвет с учётом выполняющейся анимации.
        progress_color = self.current_color

        # Рисуем фоновую окружность.
        track_pen = QPen(
            QColor(colors["track"]),
            pen_width,
        )
        track_pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        painter.setPen(track_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawArc(circle, 90 * 16, -360 * 16)

        # Используем анимируемое значение вместо секундного шага.
        progress = self.progress

        # Вычисляем угол дуги с учётом текущего прогресса.
        progress_angle = -int(360 * progress * 16)

        # Вычисляем угол дуги с учётом текущего прогресса.
        progress_angle = -int(360 * progress * 16)

        # Создаём несколько очень прозрачных слоёв свечения.
        # Широкие слои почти незаметны и создают мягкий ореол.
        glow_layers = [
            (pen_width * 4.0, 5),
            (pen_width * 3.0, 8),
            (pen_width * 2.0, 13),
            (pen_width * 1.4, 18),
        ]

        for glow_width, alpha in glow_layers:
            # Используем копию цвета, чтобы не менять основной оттенок.
            glow_color = QColor(progress_color)
            glow_color.setAlpha(alpha)

            # Рисуем очередной полупрозрачный слой.
            glow_pen = QPen(glow_color, glow_width)
            glow_pen.setCapStyle(Qt.PenCapStyle.RoundCap)

            painter.setPen(glow_pen)
            painter.drawArc(
                circle,
                90 * 16,
                progress_angle,
            )

        # Поверх свечения рисуем чёткую основную дугу.
        progress_pen = QPen(progress_color, pen_width)
        progress_pen.setCapStyle(Qt.PenCapStyle.RoundCap)

        painter.setPen(progress_pen)
        painter.drawArc(
            circle,
            90 * 16,
            progress_angle,
        )

        # Преобразуем секунды в формат MM:SS.
        minutes, seconds = divmod(
            self.remaining_seconds,
            60,
        )
        time_text = f"{minutes:02d}:{seconds:02d}"

        # Настраиваем современную типографику центрального таймера.
        time_font = QFont("Inter")
        time_font.setBold(True)
        time_font.setWeight(QFont.Weight.DemiBold)
        time_font.setPixelSize(max(36, int(side * 0.16)))
        time_font.setLetterSpacing(
            QFont.SpacingType.AbsoluteSpacing,
            1.5,
        )

        painter.setFont(time_font)
        painter.setPen(QColor(colors["text"]))

        # Выводим время точно в центре круга.
        painter.drawText(
            self.rect(),
            Qt.AlignmentFlag.AlignCenter,
            time_text,
        )

        # Завершаем рисование.
        painter.end()
