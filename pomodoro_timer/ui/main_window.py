from __future__ import annotations

# Импорты стандартной библиотеки и компонентов PySide6.

from pathlib import Path
from datetime import datetime, timedelta
import sys
import subprocess

from PySide6.QtCore import QSettings
from PySide6.QtCore import (
    Qt,
    QTimer,
    QPropertyAnimation,
    QRectF,  # Геометрия прямоугольников для столбцов графика
)
from PySide6.QtGui import (
    QAction, QCloseEvent, QIcon, QPainter, QPen, QBrush, QColor, QFont,
    QPalette, QPixmap,
)
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QDialog,
    QSystemTrayIcon,
    QMenu,
    QApplication,
    QStackedWidget,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QComboBox,
    QCheckBox,
    QFormLayout,
    QScrollArea,
    QSpinBox,  # Поля ввода числовых настроек
    QProgressBar,  # Индикатор текущего Pomodoro-цикла
    QGraphicsOpacityEffect,  # Плавное появление подписей
)

# Импорты логики таймера, истории и окон интерфейса проекта.
from pomodoro_timer.core.history import SessionHistory
from pomodoro_timer.core.timer import PomodoroTimer, TimerMode
from pomodoro_timer.ui.history_dialog import HistoryDialog
from pomodoro_timer.ui.mini_timer import MiniTimer
from pomodoro_timer.ui.settings_dialog import SettingsDialog
from pomodoro_timer.ui.translations import translate

# Импорт боковой панели навигации.
from pomodoro_timer.ui.sidebar import Sidebar

# Импорт кругового индикатора времени.
from pomodoro_timer.ui.circular_timer import CircularTimer

from pomodoro_timer.core.autostart import set_autostart


class DailyFocusChart(QWidget):
    """Рисует столбчатый график фокусировки за последние семь дней."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.daily_values: list[tuple[str, int, int]] = []
        self.setMinimumHeight(260)

    def set_data(self, values: list[tuple[str, int, int]]) -> None:
        """Принимает подпись дня, секунды фокусировки и число сессий."""
        self.daily_values = values
        self.update()

    def paintEvent(self, event) -> None:
        """Отрисовывает сетку, столбцы и подписи дней."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect().adjusted(18, 14, -18, -12)
        if rect.width() <= 0 or rect.height() <= 0:
            return

        text_color = self.palette().color(QPalette.ColorRole.Text)
        muted_color = self.palette().color(QPalette.ColorRole.Mid)
        accent_color = QColor("#F16B66")

        # Оставляем место для подписей значений и дней недели.
        plot = rect.adjusted(34, 8, -8, -34)
        if plot.width() <= 0 or plot.height() <= 0:
            return

        values = self.daily_values or [
            ("", 0, 0) for _ in range(7)
        ]
        max_value = max((seconds for _, seconds, _ in values), default=0)
        scale_max = max(max_value, 3600)

        # Рисуем четыре горизонтальные линии сетки.
        painter.setPen(QPen(muted_color, 1, Qt.PenStyle.DotLine))
        for step in range(4):
            y = plot.bottom() - (plot.height() * step / 3)
            painter.drawLine(
                int(plot.left()), int(y), int(plot.right()), int(y)
            )

            minutes = int(scale_max * step / 3 / 60)
            painter.setPen(muted_color)
            painter.drawText(
                int(rect.left()), int(y - 8), 28, 16,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
                f"{minutes}м",
            )
            painter.setPen(QPen(muted_color, 1, Qt.PenStyle.DotLine))

        slot_width = plot.width() / max(len(values), 1)
        bar_width = min(34.0, slot_width * 0.48)

        for index, (day_label, seconds, session_count) in enumerate(values):
            center_x = plot.left() + slot_width * (index + 0.5)
            bar_height = (
                plot.height() * seconds / scale_max if seconds > 0 else 0
            )
            bar_rect = QRectF(
                center_x - bar_width / 2,
                plot.bottom() - bar_height,
                bar_width,
                max(bar_height, 2),
            )

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(accent_color))
            painter.drawRoundedRect(bar_rect, 5, 5)

            # Над столбцом показываем количество завершённых фокус-сессий.
            painter.setPen(muted_color if session_count == 0 else text_color)
            painter.setFont(QFont("Segoe UI", 8))
            count_text = str(session_count)
            count_rect = QRectF(
                center_x - slot_width / 2,
                max(plot.top(), plot.bottom() - bar_height - 22),
                slot_width,
                18,
            )
            painter.drawText(
                count_rect,
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignVCenter,
                count_text,
            )

            painter.setPen(text_color)
            painter.setFont(QFont("Segoe UI", 9))
            painter.drawText(
                int(center_x - slot_width / 2),
                int(plot.bottom() + 8),
                int(slot_width),
                22,
                Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                day_label,
            )

        painter.end()


class MainWindow(QMainWindow):
    """Главное окно: таймер, настройки, история и системный трей."""

    def __init__(self) -> None:
        """Создаёт окно, загружает настройки и собирает интерфейс."""
        super().__init__()

        # Пути к графическим ресурсам приложения.
        assets_dir = Path(__file__).resolve().parents[2] / "assets"

        self.app_icon_path = assets_dir / "pomodoro_icon.ico"
        self.tray_icon_path = assets_dir / "pomodoro_tray_64.png"

        # QSettings хранит пользовательские параметры между запусками.
        self.settings = QSettings("KontataGood", "PomodoroTimer")
        # База истории хранится в домашней папке пользователя.
        data_dir = Path.home() / ".pomodoro_timer"
        self.history = SessionHistory(data_dir / "history.db")
        # Загружаем срок хранения истории. 0 означает бессрочное хранение.
        self.history_retention_days = self.settings.value(
            "history_retention_days", 0, type=int
        )

        # Загружаем настройку звуковых сигналов.
        self.sound_enabled = self.settings.value(
            "sound_enabled", True, type=bool
        )

        # Загружаем настройку системных уведомлений.
        self.notifications_enabled = self.settings.value(
            "notifications_enabled", True, type=bool
        )

        # Удаляем старые записи, если пользователь включил ограничение.
        if self.history_retention_days > 0:
            self.history.delete_sessions_older_than(
                self.history_retention_days
            )
        self.language = self.settings.value("language", "en", type=str)
        self.theme = self.settings.value("theme", "dark", type=str)

        # Читаем длительность фаз и число фокус-сессий до длинного перерыва.
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

        # Создаём основной таймер и отдельное компактное окно таймера.
        self.timer = PomodoroTimer(self, **self.timer_settings)
        self.mini_timer = MiniTimer(self.timer, self)

        self.setWindowTitle("Pomodoro Timer")

        # Устанавливаем иконку главного окна.
        self.setWindowIcon(QIcon(str(self.app_icon_path)))

        # Увеличиваем минимальный размер с учётом боковой навигации.
        self.setMinimumSize(760, 620)
        self.resize(820, 720)
        self.setStyleSheet(self._stylesheet())

        # Центральный виджет объединяет боковую панель и рабочую область.
        root = QWidget()

        # Горизонтальная компоновка размещает навигацию слева, а контент справа.
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Создаём боковую панель навигации.
        self.sidebar = Sidebar()

        # Добавляем боковую панель в левую часть главного окна.
        root_layout.addWidget(self.sidebar)

        # Создаём контейнер страниц: в нём будет отображаться только один раздел.
        self.pages = QStackedWidget()
        root_layout.addWidget(self.pages, 1)

        # Создаём главную страницу таймера.
        content = QWidget()
        content.setObjectName("timerPage")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(28, 22, 28, 22)
        content_layout.setSpacing(14)

        # Сохраняем страницу и её индекс для дальнейшего переключения.
        self.pages.addWidget(content)
        self.page_indices = {"timer": 0}

        # Верхняя панель: название, счётчик сессий и мини-таймер.
        header = QHBoxLayout()
        header.setSpacing(12)

        brand = QLabel("POMODORO")
        brand.setObjectName("brand")
        header.addWidget(brand)
        header.addStretch(1)

        self.session_badge = QLabel("0 SESSIONS")
        self.session_badge.setObjectName("sessionBadge")
        header.addWidget(self.session_badge)

        self.mini_timer_button = QPushButton("◷")
        self.mini_timer_button.setObjectName("secondaryButton")
        self.mini_timer_button.setFixedSize(40, 40)
        self.mini_timer_button.setToolTip(
            translate(self.language, "mini_timer")
        )
        self.mini_timer_button.clicked.connect(self._open_mini_timer)
        header.addWidget(self.mini_timer_button)
        content_layout.addLayout(header)

        # Центральная карточка объединяет режим, круговой таймер и статус.
        self.timer_card = QFrame()
        self.timer_card.setObjectName("timerCard")
        self.timer_card.setMaximumWidth(620)

        timer_card_layout = QVBoxLayout(self.timer_card)
        timer_card_layout.setContentsMargins(28, 20, 28, 18)
        timer_card_layout.setSpacing(14)

        self.mode_label = QLabel("FOCUS TIME")
        self.mode_label.setObjectName("modeLabel")
        self.mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # При переключении режима заголовок будет мягко появляться.
        self.mode_label_effect = QGraphicsOpacityEffect(self.mode_label)
        self.mode_label.setGraphicsEffect(self.mode_label_effect)
        self.mode_label_animation = QPropertyAnimation(
            self.mode_label_effect, b"opacity", self
        )
        self.mode_label_animation.setDuration(180)

        timer_card_layout.addWidget(self.mode_label)

        # Сохраняем существующий круговой индикатор и его анимации.
        self.circular_timer = CircularTimer()
        self.circular_timer.set_theme(self.theme)
        self.circular_timer.setFixedSize(280, 280)
        timer_card_layout.addWidget(
            self.circular_timer,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        self.circular_timer.set_time(
            self.timer.remaining_seconds,
            self.timer.duration_for(self.timer.mode),
            self.timer.mode,
        )
        self._update_tray_status()

        self.status_label = QLabel("Ready when you are")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Статус также плавно появляется при старте, паузе и смене режима.
        self.status_label_effect = QGraphicsOpacityEffect(self.status_label)
        self.status_label.setGraphicsEffect(self.status_label_effect)
        self.status_label_animation = QPropertyAnimation(
            self.status_label_effect, b"opacity", self
        )
        self.status_label_animation.setDuration(180)

        timer_card_layout.addWidget(self.status_label)

        # Индикатор показывает место текущей фокус-сессии в цикле.
        self.cycle_label = QLabel()
        self.cycle_label.setObjectName("cycleLabel")
        self.cycle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        timer_card_layout.addWidget(self.cycle_label)

        self.cycle_progress = QProgressBar()
        self.cycle_progress.setObjectName("cycleProgress")
        self.cycle_progress.setTextVisible(False)
        self.cycle_progress.setFixedHeight(6)
        self.cycle_progress.setMaximumWidth(260)
        timer_card_layout.addWidget(
            self.cycle_progress,
            alignment=Qt.AlignmentFlag.AlignCenter,
        )

        content_layout.addWidget(
            self.timer_card,
            alignment=Qt.AlignmentFlag.AlignHCenter,
        )

        # Переключатели режимов располагаются отдельной компактной группой.
        modes = QHBoxLayout()
        modes.setSpacing(8)

        self.focus_button = self._mode_button("Focus", TimerMode.FOCUS)
        self.short_button = self._mode_button(
            "Short break", TimerMode.SHORT_BREAK
        )
        self.long_button = self._mode_button(
            "Long break", TimerMode.LONG_BREAK
        )

        for mode_button in (
            self.focus_button,
            self.short_button,
            self.long_button,
        ):
            mode_button.setMinimumHeight(42)
            modes.addWidget(mode_button)

        modes_container = QWidget()
        modes_container.setMaximumWidth(520)
        modes_container.setLayout(modes)
        content_layout.addWidget(
            modes_container,
            alignment=Qt.AlignmentFlag.AlignHCenter,
        )

        # Основная кнопка шире вторичной, чтобы выделить главное действие.
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

        controls_container = QWidget()
        controls_container.setMaximumWidth(520)
        controls_container.setLayout(controls)
        content_layout.addWidget(
            controls_container,
            alignment=Qt.AlignmentFlag.AlignHCenter,
        )

        content_layout.addStretch(1)

        self.footer_label = QLabel()
        self.footer_label.setObjectName("footer")
        self.footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(self.footer_label)

        # Добавляем временные страницы для будущих разделов приложения.
        # Их содержимое заменим полноценными экранами на следующих этапах.
        self._create_statistics_page()
        # Создаём полноценную страницу истории в центральной области.
        self._create_history_page()
        # Создаём полноценную страницу настроек вместо временной заглушки.
        self._create_settings_page()

        # Подключаем боковую панель к переключению страниц.
        self.sidebar.navigation_requested.connect(self._switch_page)
        self.sidebar.toggle_requested.connect(self._save_sidebar_state)

        # Восстанавливаем состояние панели и последний открытый раздел.
        sidebar_expanded = self.settings.value(
            "sidebar_expanded", False, type=bool
        )
        if sidebar_expanded:
            self.sidebar.set_expanded(True)

        saved_page = self.settings.value("last_page", "timer", type=str)
        if saved_page not in self.page_indices:
            saved_page = "timer"
        self._switch_page(saved_page)

        self.setCentralWidget(root)

        # Связываем сигналы таймера с обновлением элементов интерфейса.
        self.timer.tick.connect(self._update_time)
        self.timer.mode_changed.connect(self._update_mode)
        self.timer.running_changed.connect(self._update_running_state)
        self.timer.session_count_changed.connect(self._update_session_count)
        self.timer.phase_completed.connect(self._phase_completed)
        self._update_time(self.timer.remaining_seconds)
        self._update_mode(self.timer.mode)
        self._update_running_state(False)

        self._retranslate_ui()
        self._setup_tray()

    def _create_statistics_page(self) -> None:
        """Создаёт страницу общей статистики и графика активности."""

        page = QWidget()
        page.setObjectName("statisticsPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(18)

        self.statistics_heading = QLabel()
        self.statistics_heading.setObjectName("pageHeading")
        layout.addWidget(self.statistics_heading)

        self.statistics_description = QLabel()
        self.statistics_description.setObjectName("pageDescription")
        layout.addWidget(self.statistics_description)

        # Три показателя за всё время.
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(12)

        self.stats_focus_card, self.stats_focus_value = (
            self._create_history_stat_card("ФОКУС-СЕССИИ")
        )
        self.stats_time_card, self.stats_time_value = (
            self._create_history_stat_card("ВРЕМЯ ФОКУСИРОВКИ")
        )
        self.stats_average_card, self.stats_average_value = (
            self._create_history_stat_card("СРЕДНЕЕ ЗА СЕССИЮ")
        )

        # Вторичная строка показывает сравнение с предыдущими семью днями.
        self.stats_focus_detail = QLabel()
        self.stats_focus_detail.setObjectName("historyStatDetail")
        self.stats_focus_card.layout().addWidget(self.stats_focus_detail)

        self.stats_time_detail = QLabel()
        self.stats_time_detail.setObjectName("historyStatDetail")
        self.stats_time_card.layout().addWidget(self.stats_time_detail)

        self.stats_average_detail = QLabel()
        self.stats_average_detail.setObjectName("historyStatDetail")
        self.stats_average_card.layout().addWidget(self.stats_average_detail)

        cards_layout.addWidget(self.stats_focus_card)
        cards_layout.addWidget(self.stats_time_card)
        cards_layout.addWidget(self.stats_average_card)
        layout.addLayout(cards_layout)

        self.statistics_chart_title = QLabel()
        self.statistics_chart_title.setObjectName("sectionHeading")
        layout.addWidget(self.statistics_chart_title)

        self.statistics_chart_card = QFrame()
        self.statistics_chart_card.setObjectName("historyStatCard")
        chart_layout = QVBoxLayout(self.statistics_chart_card)
        chart_layout.setContentsMargins(14, 12, 14, 12)

        self.statistics_chart = DailyFocusChart()
        chart_layout.addWidget(self.statistics_chart)
        layout.addWidget(self.statistics_chart_card, 1)

        self.statistics_footer = QLabel()
        self.statistics_footer.setObjectName("historySummary")
        layout.addWidget(self.statistics_footer)

        self.page_indices["statistics"] = self.pages.addWidget(page)
        self._retranslate_statistics_page()
        self._refresh_statistics_page()

    def _retranslate_statistics_page(self) -> None:
        """Обновляет тексты страницы статистики на выбранном языке."""

        if self.language == "ru":
            self.statistics_heading.setText("Статистика")
            self.statistics_description.setText(
                "Твоя продуктивность на основе завершённых сессий"
            )
            self.statistics_chart_title.setText(
                "Фокусировка за последние 7 дней"
            )
            self.statistics_footer.setText(
                "Столбцы показывают время фокусировки, число над ними — "
                "завершённые сессии. Учитываются только фокус-сессии."
            )
            labels = (
                "◷  ФОКУС-СЕССИИ",
                "◉  ВСЕГО ФОКУСИРОВКИ",
                "↗  СРЕДНЕЕ ЗА СЕССИЮ",
            )
        else:
            self.statistics_heading.setText("Statistics")
            self.statistics_description.setText(
                "Your productivity based on completed sessions"
            )
            self.statistics_chart_title.setText(
                "Focus time over the last 7 days"
            )
            self.statistics_footer.setText(
                "Bars show focus time; numbers above them show completed "
                "sessions. Only focus sessions are included."
            )
            labels = (
                "◷  FOCUS SESSIONS",
                "◉  ALL-TIME FOCUS",
                "↗  AVERAGE SESSION",
            )

        for card, text in zip(
            (
                self.stats_focus_card,
                self.stats_time_card,
                self.stats_average_card,
            ),
            labels,
        ):
            title = card.findChild(QLabel)
            if title is not None:
                title.setText(text)

    def _refresh_statistics_page(self) -> None:
        """Пересчитывает показатели и обновляет график за семь дней."""

        if not hasattr(self, "statistics_chart"):
            return

        # Берём записи из той же SQLite-базы, что используется историей.
        sessions = self.history.get_sessions(limit=1_000_000)
        focus_sessions = [
            session for session in sessions
            if session["mode"] == TimerMode.FOCUS.value
        ]

        total_seconds = sum(
            int(session["duration_seconds"])
            for session in focus_sessions
        )
        focus_count = len(focus_sessions)
        average_seconds = (
            total_seconds // focus_count if focus_count else 0
        )

        # Сравниваем последние семь календарных дней с предыдущими семью.
        today = datetime.now().astimezone().date()
        current_start = today - timedelta(days=6)
        previous_start = today - timedelta(days=13)
        previous_end = current_start

        current_week_sessions = []
        previous_week_sessions = []
        for session in focus_sessions:
            session_day = datetime.fromisoformat(
                session["completed_at"]
            ).astimezone().date()
            if current_start <= session_day <= today:
                current_week_sessions.append(session)
            elif previous_start <= session_day < previous_end:
                previous_week_sessions.append(session)

        current_week_count = len(current_week_sessions)
        previous_week_count = len(previous_week_sessions)
        current_week_seconds = sum(
            int(session["duration_seconds"])
            for session in current_week_sessions
        )
        previous_week_seconds = sum(
            int(session["duration_seconds"])
            for session in previous_week_sessions
        )

        def comparison_text(current: int, previous: int) -> str:
            if previous == 0:
                if current == 0:
                    return "Нет изменений" if self.language == "ru" else "No change"
                return "Больше, чем ранее" if self.language == "ru" else "More than before"
            difference = current - previous
            percent = round(abs(difference) / previous * 100)
            if difference > 0:
                return (
                    f"↑ {percent}% к прошлой неделе"
                    if self.language == "ru"
                    else f"↑ {percent}% vs last week"
                )
            if difference < 0:
                return (
                    f"↓ {percent}% к прошлой неделе"
                    if self.language == "ru"
                    else f"↓ {percent}% vs last week"
                )
            return "Без изменений" if self.language == "ru" else "No change"

        def format_duration(seconds: int) -> str:
            total_minutes = seconds // 60
            hours, minutes = divmod(total_minutes, 60)
            if hours:
                return f"{hours} ч {minutes} мин" if self.language == "ru" else f"{hours} h {minutes} min"
            return f"{minutes} мин" if self.language == "ru" else f"{minutes} min"

        self.stats_focus_value.setText(str(focus_count))
        self.stats_time_value.setText(format_duration(total_seconds))
        self.stats_average_value.setText(format_duration(average_seconds))

        if self.language == "ru":
            self.stats_focus_detail.setText(
                comparison_text(current_week_count, previous_week_count)
            )
            self.stats_time_detail.setText(
                comparison_text(current_week_seconds, previous_week_seconds)
            )
            self.stats_average_detail.setText("За всё время")
        else:
            self.stats_focus_detail.setText(
                comparison_text(current_week_count, previous_week_count)
            )
            self.stats_time_detail.setText(
                comparison_text(current_week_seconds, previous_week_seconds)
            )
            self.stats_average_detail.setText("All time")

        # Собираем секунды фокусировки по локальным календарным датам.
        daily_totals: dict[object, int] = {}
        daily_counts: dict[object, int] = {}

        for session in focus_sessions:
            completed_at = datetime.fromisoformat(
                session["completed_at"]
            ).astimezone()
            session_day = completed_at.date()
            daily_totals[session_day] = (
                daily_totals.get(session_day, 0)
                + int(session["duration_seconds"])
            )
            daily_counts[session_day] = daily_counts.get(session_day, 0) + 1

        chart_values = []
        weekday_ru = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")
        weekday_en = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

        for offset in range(6, -1, -1):
            day = today - timedelta(days=offset)
            label = (
                f"{weekday_ru[day.weekday()]} {day.day:02d}"
                if self.language == "ru"
                else f"{weekday_en[day.weekday()]} {day.day:02d}"
            )
            chart_values.append((
                label,
                daily_totals.get(day, 0),
                daily_counts.get(day, 0),
            ))

        self.statistics_chart.set_data(chart_values)

    def _create_settings_page(self) -> None:
        """Создаёт встроенную страницу настроек приложения."""

        # Обёртка с прокруткой нужна для небольших экранов.
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        page = QWidget()
        page.setObjectName("settingsPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(36, 32, 36, 28)
        layout.setSpacing(18)

        self.settings_heading = QLabel()
        self.settings_heading.setObjectName("pageHeading")
        layout.addWidget(self.settings_heading)

        self.settings_description = QLabel()
        self.settings_description.setObjectName("pageDescription")
        layout.addWidget(self.settings_description)

        # Основная карточка содержит все доступные параметры.
        card = QFrame()
        card.setObjectName("settingsCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(22, 20, 22, 20)
        card_layout.setSpacing(18)

        # Общие параметры приложения.
        self.settings_general_heading = QLabel()
        self.settings_general_heading.setObjectName("sectionHeading")
        card_layout.addWidget(self.settings_general_heading)

        general_form = QFormLayout()
        general_form.setHorizontalSpacing(24)
        general_form.setVerticalSpacing(14)

        self.settings_language_label = QLabel()
        self.settings_language_combo = QComboBox()
        self.settings_language_combo.addItem("Русский", "ru")
        self.settings_language_combo.addItem("English", "en")
        general_form.addRow(
            self.settings_language_label, self.settings_language_combo
        )

        self.settings_theme_label = QLabel()
        self.settings_theme_combo = QComboBox()
        self.settings_theme_combo.addItem("Dark", "dark")
        self.settings_theme_combo.addItem("Light", "light")
        self.settings_theme_combo.addItem("Midnight", "midnight")
        general_form.addRow(
            self.settings_theme_label, self.settings_theme_combo
        )

        card_layout.addLayout(general_form)

        # Длительность рабочих и восстановительных интервалов.
        self.settings_timer_heading = QLabel()
        self.settings_timer_heading.setObjectName("sectionHeading")
        card_layout.addWidget(self.settings_timer_heading)

        timer_form = QFormLayout()
        timer_form.setHorizontalSpacing(24)
        timer_form.setVerticalSpacing(14)

        self.settings_focus_label = QLabel()
        self.settings_focus_spin = QSpinBox()
        self.settings_focus_spin.setRange(1, 180)
        timer_form.addRow(self.settings_focus_label, self.settings_focus_spin)

        self.settings_short_break_label = QLabel()
        self.settings_short_break_spin = QSpinBox()
        self.settings_short_break_spin.setRange(1, 60)
        timer_form.addRow(
            self.settings_short_break_label, self.settings_short_break_spin
        )

        self.settings_long_break_label = QLabel()
        self.settings_long_break_spin = QSpinBox()
        self.settings_long_break_spin.setRange(1, 120)
        timer_form.addRow(
            self.settings_long_break_label, self.settings_long_break_spin
        )

        self.settings_sessions_label = QLabel()
        self.settings_sessions_spin = QSpinBox()
        self.settings_sessions_spin.setRange(1, 12)
        timer_form.addRow(
            self.settings_sessions_label, self.settings_sessions_spin
        )

        card_layout.addLayout(timer_form)

        # Поведение приложения, уведомления и хранение истории.
        self.settings_behavior_heading = QLabel()
        self.settings_behavior_heading.setObjectName("sectionHeading")
        card_layout.addWidget(self.settings_behavior_heading)

        behavior_form = QFormLayout()
        behavior_form.setHorizontalSpacing(24)
        behavior_form.setVerticalSpacing(14)

        self.settings_retention_label = QLabel()
        self.settings_retention_combo = QComboBox()
        self.settings_retention_combo.addItem("", 0)
        self.settings_retention_combo.addItem("", 30)
        self.settings_retention_combo.addItem("", 90)
        self.settings_retention_combo.addItem("", 180)
        behavior_form.addRow(
            self.settings_retention_label, self.settings_retention_combo
        )

        self.settings_snap_checkbox = QCheckBox()
        behavior_form.addRow(self.settings_snap_checkbox)

        self.settings_sound_checkbox = QCheckBox()
        behavior_form.addRow(self.settings_sound_checkbox)

        self.settings_notifications_checkbox = QCheckBox()
        behavior_form.addRow(self.settings_notifications_checkbox)

        self.settings_autostart_checkbox = QCheckBox()
        self.settings_autostart_checkbox.setEnabled(
            sys.platform in ("win32", "darwin")
        )
        behavior_form.addRow(self.settings_autostart_checkbox)

        card_layout.addLayout(behavior_form)
        layout.addWidget(card)

        # Кнопки сохранения и отмены несохранённых изменений.
        buttons = QHBoxLayout()
        buttons.addStretch(1)

        self.settings_cancel_button = QPushButton()
        self.settings_cancel_button.setObjectName("secondaryButton")
        self.settings_cancel_button.clicked.connect(
            self._reload_settings_page
        )
        buttons.addWidget(self.settings_cancel_button)

        self.settings_save_button = QPushButton()
        self.settings_save_button.setObjectName("primaryButton")
        self.settings_save_button.clicked.connect(
            self._save_settings_page
        )
        buttons.addWidget(self.settings_save_button)

        layout.addLayout(buttons)
        layout.addStretch(1)

        scroll.setWidget(page)
        self.page_indices["settings"] = self.pages.addWidget(scroll)

        self._reload_settings_page()
        self._retranslate_settings_page()

    def _reload_settings_page(self) -> None:
        """Возвращает элементы страницы к сохранённым настройкам."""

        if not hasattr(self, "settings_language_combo"):
            return

        # Читаем актуальные значения из QSettings.
        language = self.settings.value("language", self.language, type=str)
        theme = self.settings.value("theme", self.theme, type=str)

        self.settings_language_combo.setCurrentIndex(
            max(0, self.settings_language_combo.findData(language))
        )
        self.settings_theme_combo.setCurrentIndex(
            max(0, self.settings_theme_combo.findData(theme))
        )

        self.settings_focus_spin.setValue(
            self.settings.value("focus_minutes", 25, type=int)
        )
        self.settings_short_break_spin.setValue(
            self.settings.value("short_break_minutes", 5, type=int)
        )
        self.settings_long_break_spin.setValue(
            self.settings.value("long_break_minutes", 15, type=int)
        )
        self.settings_sessions_spin.setValue(
            self.settings.value("sessions_before_long_break", 4, type=int)
        )

        retention = self.settings.value(
            "history_retention_days", 0, type=int
        )
        self.settings_retention_combo.setCurrentIndex(
            max(0, self.settings_retention_combo.findData(retention))
        )

        self.settings_snap_checkbox.setChecked(
            self.settings.value("snap_to_edges", True, type=bool)
        )
        self.settings_sound_checkbox.setChecked(
            self.settings.value("sound_enabled", True, type=bool)
        )
        self.settings_notifications_checkbox.setChecked(
            self.settings.value("notifications_enabled", True, type=bool)
        )
        self.settings_autostart_checkbox.setChecked(
            self.settings.value("autostart_enabled", False, type=bool)
        )

    def _retranslate_settings_page(self) -> None:
        """Обновляет подписи страницы настроек на выбранном языке."""

        if not hasattr(self, "settings_heading"):
            return

        is_ru = self.language == "ru"

        self.settings_heading.setText(
            translate(self.language, "settings")
        )
        self.settings_description.setText(
            "Параметры таймера и поведения приложения"
            if is_ru
            else "Configure your timer and app behavior"
        )
        self.settings_general_heading.setText(
            "Общие" if is_ru else "General"
        )
        self.settings_timer_heading.setText(
            "Интервалы Pomodoro" if is_ru else "Pomodoro intervals"
        )
        self.settings_behavior_heading.setText(
            "Поведение и уведомления" if is_ru else "Behavior and notifications"
        )

        # Обновляем подписи полей формы.
        self.settings_language_label.setText(
            translate(self.language, "language")
        )
        self.settings_theme_label.setText(
            translate(self.language, "theme")
        )
        self.settings_focus_label.setText(
            translate(self.language, "focus_duration")
        )
        self.settings_short_break_label.setText(
            translate(self.language, "short_break_duration")
        )
        self.settings_long_break_label.setText(
            translate(self.language, "long_break_duration")
        )
        self.settings_sessions_label.setText(
            translate(self.language, "sessions_before_long_break")
        )
        self.settings_retention_label.setText(
            translate(self.language, "history_retention")
        )

        self.settings_retention_combo.setItemText(
            0, translate(self.language, "retention_unlimited")
        )
        self.settings_retention_combo.setItemText(
            1, translate(self.language, "retention_30_days")
        )
        self.settings_retention_combo.setItemText(
            2, translate(self.language, "retention_90_days")
        )
        self.settings_retention_combo.setItemText(
            3, translate(self.language, "retention_180_days")
        )

        self.settings_snap_checkbox.setText(
            translate(self.language, "snap_to_edges")
        )
        self.settings_sound_checkbox.setText(
            translate(self.language, "sound_enabled")
        )
        self.settings_notifications_checkbox.setText(
            translate(self.language, "notifications_enabled")
        )
        self.settings_autostart_checkbox.setText(
            "Запускать вместе с системой"
            if is_ru
            else "Start with system"
        )
        self.settings_save_button.setText(
            translate(self.language, "save")
        )
        self.settings_cancel_button.setText(
            translate(self.language, "cancel")
        )

        suffix = " мин" if is_ru else " min"
        self.settings_focus_spin.setSuffix(suffix)
        self.settings_short_break_spin.setSuffix(suffix)
        self.settings_long_break_spin.setSuffix(suffix)

    def _save_settings_page(self) -> None:
        """Проверяет, сохраняет и сразу применяет настройки страницы."""

        # Получаем выбранные значения из элементов управления.
        new_language = self.settings_language_combo.currentData()
        new_theme = self.settings_theme_combo.currentData()

        new_timer_settings = {
            "focus_minutes": self.settings_focus_spin.value(),
            "short_break_minutes": self.settings_short_break_spin.value(),
            "long_break_minutes": self.settings_long_break_spin.value(),
            "sessions_before_long_break": self.settings_sessions_spin.value(),
        }

        new_retention_days = int(
            self.settings_retention_combo.currentData()
        )
        new_snap_to_edges = self.settings_snap_checkbox.isChecked()
        new_sound_enabled = self.settings_sound_checkbox.isChecked()
        new_notifications_enabled = (
            self.settings_notifications_checkbox.isChecked()
        )
        new_autostart_enabled = self.settings_autostart_checkbox.isChecked()

        # Изменяем автозагрузку до сохранения остальных настроек.
        # Если Windows отклонит операцию, остальные параметры не будут частично сохранены.
        if sys.platform in ("win32", "darwin"):
            try:
                set_autostart(new_autostart_enabled)
            except (OSError, subprocess.SubprocessError) as error:
                QMessageBox.warning(
                    self,
                    "Pomodoro Timer",
                    (
                        f"Не удалось изменить автозапуск:\n{error}"
                        if self.language == "ru"
                        else f"Could not update system startup:\n{error}"
                    ),
                )
                return

        # Обновляем состояние главного окна.
        self.language = new_language
        self.theme = new_theme
        self.timer_settings = new_timer_settings
        self.history_retention_days = new_retention_days
        self.sound_enabled = new_sound_enabled
        self.notifications_enabled = new_notifications_enabled

        # Сохраняем параметры в том же хранилище QSettings.
        self.settings.setValue("language", self.language)
        self.settings.setValue("theme", self.theme)
        self.settings.setValue("sound_enabled", self.sound_enabled)
        self.settings.setValue(
            "notifications_enabled", self.notifications_enabled
        )
        if sys.platform in ("win32", "darwin"):
            self.settings.setValue("autostart_enabled", new_autostart_enabled)
        self.settings.setValue("snap_to_edges", new_snap_to_edges)

        for key, value in self.timer_settings.items():
            self.settings.setValue(key, value)

        # Применяем срок хранения истории, если он ограничен.
        if self.history_retention_days > 0:
            self.history.delete_sessions_older_than(
                self.history_retention_days
            )

        # Применяем настройки к уже работающим объектам приложения.
        self.mini_timer.snap_to_edges = new_snap_to_edges
        self.timer.apply_settings(**self.timer_settings)
        self.setStyleSheet(self._stylesheet())
        self.circular_timer.set_theme(self.theme)

        # Переводим интерфейс и обновляем статистику после возможной очистки.
        self._retranslate_ui()
        self._refresh_history_page()
        self._refresh_statistics_page()
        self._retranslate_settings_page()

    def _create_history_page(self) -> None:
        """Создаёт встроенную страницу со списком завершённых сессий."""

        # Создаём корневой виджет и компоновку страницы.
        page = QWidget()
        page.setObjectName("historyPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(36, 32, 36, 32)
        layout.setSpacing(18)

        # Заголовок и пояснение страницы.
        self.history_heading = QLabel()
        self.history_heading.setObjectName("pageHeading")
        layout.addWidget(self.history_heading)

        self.history_description = QLabel()
        self.history_description.setObjectName("pageDescription")
        layout.addWidget(self.history_description)

        # Карточки со сводной статистикой по всей истории.
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(12)

        self.history_focus_card, self.history_focus_value = (
            self._create_history_stat_card("ФОКУС-СЕССИИ")
        )
        self.history_time_card, self.history_time_value = (
            self._create_history_stat_card("ВРЕМЯ ФОКУСИРОВКИ")
        )
        self.history_breaks_card, self.history_breaks_value = (
            self._create_history_stat_card("ПЕРЕРЫВЫ")
        )

        stats_layout.addWidget(self.history_focus_card)
        stats_layout.addWidget(self.history_time_card)
        stats_layout.addWidget(self.history_breaks_card)
        layout.addLayout(stats_layout)

        # Фильтры истории: тип сессии и период.
        filters_layout = QHBoxLayout()
        filters_layout.setSpacing(10)

        self.history_type_filter = QComboBox()
        self.history_type_filter.setObjectName("historyFilter")
        self.history_type_filter.addItem("Все типы", "all")
        self.history_type_filter.addItem("Фокус", TimerMode.FOCUS.value)
        self.history_type_filter.addItem(
            "Короткий перерыв", TimerMode.SHORT_BREAK.value
        )
        self.history_type_filter.addItem(
            "Длинный перерыв", TimerMode.LONG_BREAK.value
        )
        self.history_type_filter.currentIndexChanged.connect(
            lambda _index: self._refresh_history_page()
        )
        filters_layout.addWidget(self.history_type_filter)

        self.history_period_filter = QComboBox()
        self.history_period_filter.setObjectName("historyFilter")
        self.history_period_filter.addItem("За всё время", "all")
        self.history_period_filter.addItem("Последние 7 дней", "7")
        self.history_period_filter.addItem("Последние 30 дней", "30")
        self.history_period_filter.currentIndexChanged.connect(
            lambda _index: self._refresh_history_page()
        )
        filters_layout.addWidget(self.history_period_filter)
        filters_layout.addStretch(1)
        layout.addLayout(filters_layout)

        # Подпись с количеством записей, показанных в таблице.
        self.history_summary = QLabel()
        self.history_summary.setObjectName("historySummary")
        layout.addWidget(self.history_summary)

        # Таблица: дата, тип сессии и продолжительность.
        self.history_table = QTableWidget(0, 3)
        self.history_table.setObjectName("historyTable")
        self.history_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.history_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.history_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.history_table.setAlternatingRowColors(False)
        layout.addWidget(self.history_table, 1)

        # Нижняя панель действий.
        actions = QHBoxLayout()
        actions.addStretch(1)

        self.history_clear_button = QPushButton()
        self.history_clear_button.setObjectName("secondaryButton")
        self.history_clear_button.clicked.connect(self._clear_history_page)
        actions.addWidget(self.history_clear_button)

        layout.addLayout(actions)

        # Регистрируем страницу в общем стеке навигации.
        self.page_indices["history"] = self.pages.addWidget(page)

        # Первичное заполнение таблицы и перевод подписей.
        self._refresh_history_page()

    def _create_history_stat_card(
        self, title: str
    ) -> tuple[QFrame, QLabel]:
        """Создаёт небольшую карточку с названием и значением показателя."""

        card = QFrame()
        card.setObjectName("historyStatCard")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(7)

        title_label = QLabel(title)
        title_label.setObjectName("historyStatTitle")
        card_layout.addWidget(title_label)

        value_label = QLabel("0")
        value_label.setObjectName("historyStatValue")
        card_layout.addWidget(value_label)

        return card, value_label

    def _refresh_history_page(self) -> None:
        """Заново загружает записи из SQLite и обновляет таблицу."""

        if not hasattr(self, "history_table"):
            return

        # Заголовки столбцов берём из существующего словаря переводов.
        self.history_table.setHorizontalHeaderLabels(
            [
                translate(self.language, "history_date"),
                translate(self.language, "history_type"),
                translate(self.language, "history_duration"),
            ]
        )

        # Загружаем историю для точной статистики.
        # В таблице по-прежнему показываем только 100 последних записей.
        all_sessions = self.history.get_sessions(limit=1_000_000)

        # Применяем выбранные фильтры только к таблице, не к общей статистике.
        selected_type = self.history_type_filter.currentData()
        selected_period = self.history_period_filter.currentData()
        filtered_sessions = all_sessions

        if selected_type != "all":
            filtered_sessions = [
                session for session in filtered_sessions
                if session["mode"] == selected_type
            ]

        if selected_period != "all":
            days = int(selected_period)
            period_start = (
                datetime.now().astimezone().date()
                - timedelta(days=days - 1)
            )
            filtered_sessions = [
                session for session in filtered_sessions
                if datetime.fromisoformat(
                    session["completed_at"]
                ).astimezone().date() >= period_start
            ]

        sessions = filtered_sessions[:100]

        focus_sessions = [
            session for session in all_sessions
            if session["mode"] == TimerMode.FOCUS.value
        ]
        break_sessions = len(all_sessions) - len(focus_sessions)
        focus_seconds = sum(
            int(session["duration_seconds"])
            for session in focus_sessions
        )

        # Обновляем три карточки по всем сохранённым записям.
        self.history_focus_value.setText(str(len(focus_sessions)))

        total_minutes = focus_seconds // 60
        hours, minutes = divmod(total_minutes, 60)
        if hours:
            focus_time_text = f"{hours} ч {minutes} мин"
        else:
            focus_time_text = f"{minutes} мин"
        self.history_time_value.setText(focus_time_text)

        self.history_breaks_value.setText(str(break_sessions))

        self.history_table.setRowCount(len(sessions))

        # Подписи режимов совпадают с теми, что использует старое окно истории.
        mode_names = {
            TimerMode.FOCUS.value: translate(self.language, "focus"),
            TimerMode.SHORT_BREAK.value: translate(
                self.language, "short_break"
            ),
            TimerMode.LONG_BREAK.value: translate(
                self.language, "long_break"
            ),
        }

        # Заполняем таблицу от новых записей к старым.
        for row, session in enumerate(sessions):
            completed_at = datetime.fromisoformat(session["completed_at"])
            date_text = completed_at.astimezone().strftime(
                "%d.%m.%Y, %H:%M"
            )

            duration = int(session["duration_seconds"])
            minutes, seconds = divmod(duration, 60)
            duration_text = (
                f"{minutes} min"
                if seconds == 0
                else f"{minutes} min {seconds} sec"
            )

            values = (
                date_text,
                mode_names.get(session["mode"], session["mode"]),
                duration_text,
            )

            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.history_table.setItem(row, column, item)

        # Показываем число всех записей и сколько из них выведено в таблицу.
        if sessions:
            if self.language == "ru":
                self.history_summary.setText(
                    f"Записей по фильтру: {len(filtered_sessions)}"
                    + (f" · показаны последние {len(sessions)}"
                       if len(filtered_sessions) > len(sessions) else "")
                )
            else:
                self.history_summary.setText(
                    f"Sessions matching filters: {len(filtered_sessions)}"
                    + (f" · showing latest {len(sessions)}"
                       if len(filtered_sessions) > len(sessions) else "")
                )
            self.history_table.setVisible(True)
        else:
            self.history_summary.setText(
                translate(self.language, "history_empty")
            )
            self.history_table.setVisible(False)

        self.history_heading.setText(
            translate(self.language, "history")
        )
        if self.language == "ru":
            self.history_focus_card.findChild(QLabel).setText("ФОКУС-СЕССИИ")
            self.history_time_card.findChild(QLabel).setText(
                "ВРЕМЯ ФОКУСИРОВКИ"
            )
            self.history_breaks_card.findChild(QLabel).setText("ПЕРЕРЫВЫ")
        else:
            self.history_focus_card.findChild(QLabel).setText("FOCUS SESSIONS")
            self.history_time_card.findChild(QLabel).setText("FOCUS TIME")
            self.history_breaks_card.findChild(QLabel).setText("BREAKS")
        self.history_description.setText(
            translate(self.language, "history_description")
            if self.language == "en"
            else "Завершённые фокус-сессии и перерывы"
        )
        self.history_clear_button.setText(
            translate(self.language, "clear_history")
        )

        if self.language == "ru":
            type_labels = [
                "Все типы", "Фокус", "Короткий перерыв", "Длинный перерыв"
            ]
            period_labels = [
                "За всё время", "Последние 7 дней", "Последние 30 дней"
            ]
        else:
            type_labels = [
                "All types", "Focus", "Short break", "Long break"
            ]
            period_labels = ["All time", "Last 7 days", "Last 30 days"]

        for index, label in enumerate(type_labels):
            self.history_type_filter.setItemText(index, label)
        for index, label in enumerate(period_labels):
            self.history_period_filter.setItemText(index, label)

        self.history_clear_button.setEnabled(bool(all_sessions))

    def _clear_history_page(self) -> None:
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

        # Удаляем записи из той же базы, которую использует таймер.
        self.history.clear_history()
        self._refresh_history_page()
        self._update_session_count()

    def _add_placeholder_page(
        self,
        page_id: str,
        title: str,
        description: str,
    ) -> None:
        """Добавляет временную страницу раздела в стек экранов."""

        # Создаём отдельный виджет для будущего содержимого раздела.
        page = QWidget()
        page.setObjectName(f"{page_id}Page")

        # Размещаем заголовок и пояснение по центру страницы.
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.addStretch(1)

        heading = QLabel(title)
        heading.setObjectName("pageHeading")
        heading.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(heading)

        description_label = QLabel(description)
        description_label.setObjectName("pageDescription")
        description_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(description_label)

        layout.addStretch(1)

        # Запоминаем индекс страницы для быстрого переключения.
        self.page_indices[page_id] = self.pages.addWidget(page)

    def _switch_page(self, page_id: str) -> None:
        """Переключает центральную область на выбранный раздел."""

        # Не переключаемся на неизвестный раздел.
        if page_id not in self.page_indices:
            return

        self.pages.setCurrentIndex(self.page_indices[page_id])
        self.sidebar.set_active_page(page_id)

        # Обновляем записи при каждом открытии страницы истории.
        if page_id == "history":
            self._refresh_history_page()
        elif page_id == "statistics":
            self._refresh_statistics_page()

        # Запоминаем последний открытый раздел.
        self.settings.setValue("last_page", page_id)

    def _save_sidebar_state(self) -> None:
        """Сохраняет состояние раскрытия боковой панели."""
        self.settings.setValue(
            "sidebar_expanded",
            self.sidebar.expanded,
        )

    def _setup_tray(self) -> None:
        """Настраивает значок и расширенное меню системного трея."""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(QIcon(str(self.tray_icon_path)))

        self.tray_menu = QMenu(self)

        # Основные действия меню.
        self.show_action = QAction(self)
        self.show_action.triggered.connect(self._show_main_window)
        self.tray_menu.addAction(self.show_action)

        self.mini_timer_action = QAction(self)
        self.mini_timer_action.triggered.connect(self._open_mini_timer)
        self.tray_menu.addAction(self.mini_timer_action)

        self.tray_menu.addSeparator()

        # Неактивная строка показывает время и режим без открытия окна.
        self.tray_status_action = QAction(self)
        self.tray_status_action.setEnabled(False)
        self.tray_menu.addAction(self.tray_status_action)

        self.tray_toggle_action = QAction(self)
        self.tray_toggle_action.triggered.connect(self._toggle_timer)
        self.tray_menu.addAction(self.tray_toggle_action)

        self.tray_reset_action = QAction(self)
        self.tray_reset_action.triggered.connect(self.timer.reset)
        self.tray_menu.addAction(self.tray_reset_action)

        self.tray_menu.addSeparator()

        self.quit_action = QAction(self)
        self.quit_action.triggered.connect(self._quit_application)
        self.tray_menu.addAction(self.quit_action)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self._tray_activated)
        self.tray_icon.show()

        self.notifications_available = QSystemTrayIcon.supportsMessages()
        self._retranslate_tray_menu()
        self._update_tray_status()
        self._update_tray_icon()

    def _retranslate_tray_menu(self) -> None:
        """Обновляет подписи меню трея на текущем языке."""
        if not hasattr(self, "tray_icon"):
            return

        if self.language == "ru":
            self.show_action.setText("Открыть Pomodoro Timer")
            self.mini_timer_action.setText("Открыть мини-таймер")
            self.tray_reset_action.setText("Сбросить текущую сессию")
            self.quit_action.setText("Выход")
        else:
            self.show_action.setText("Open Pomodoro Timer")
            self.mini_timer_action.setText("Open mini timer")
            self.tray_reset_action.setText("Reset current session")
            self.quit_action.setText("Quit")

        self._update_tray_status()

    def _update_tray_status(self) -> None:
        """Обновляет время, режим и действие запуска/паузы в меню трея."""
        if not hasattr(self, "tray_status_action"):
            return

        minutes, seconds = divmod(
            max(0, self.timer.remaining_seconds), 60
        )
        time_text = f"{minutes:02d}:{seconds:02d}"

        mode_labels = {
            TimerMode.FOCUS: ("Фокус", "Focus"),
            TimerMode.SHORT_BREAK: ("Короткий перерыв", "Short break"),
            TimerMode.LONG_BREAK: ("Длинный перерыв", "Long break"),
        }
        ru_mode, en_mode = mode_labels[self.timer.mode]
        mode_text = ru_mode if self.language == "ru" else en_mode

        if self.language == "ru":
            state = "Пауза" if self.timer.is_running else "Остановлен"
            action_text = "Пауза" if self.timer.is_running else "Продолжить"
        else:
            state = "Running" if self.timer.is_running else "Paused"
            action_text = "Pause" if self.timer.is_running else "Resume"

        self.tray_status_action.setText(
            f"{mode_text} · {time_text} · {state}"
        )
        self.tray_toggle_action.setText(action_text)
        self._update_tray_icon()

    def _update_tray_icon(self) -> None:
        """Обновляет значок трея по режиму и состоянию таймера."""
        if not hasattr(self, "tray_icon"):
            return

        pixmap = QPixmap(str(self.tray_icon_path))
        if pixmap.isNull():
            # Не подменяем иконку пустым изображением, если ресурс не найден.
            return

        # Цветной маркер различает фокус и два типа перерыва.
        mode_colors = {
            TimerMode.FOCUS: QColor("#F16B66"),
            TimerMode.SHORT_BREAK: QColor("#43B581"),
            TimerMode.LONG_BREAK: QColor("#4A90E2"),
        }
        marker_color = mode_colors.get(self.timer.mode, QColor("#989EAC"))

        # Рисуем небольшой индикатор в правом нижнем углу базовой иконки.
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        diameter = max(18, pixmap.width() // 3)
        margin = max(1, pixmap.width() // 32)
        badge = QRectF(
            pixmap.width() - diameter - margin,
            pixmap.height() - diameter - margin,
            diameter,
            diameter,
        )
        painter.setPen(QPen(QColor("#171A21"), max(1, diameter // 12)))
        painter.setBrush(QBrush(marker_color))
        painter.drawEllipse(badge)

        # На паузе рисуем две полосы; во время работы — белую точку.
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        if self.timer.is_running:
            dot_size = diameter * 0.22
            painter.drawEllipse(
                QRectF(
                    badge.center().x() - dot_size / 2,
                    badge.center().y() - dot_size / 2,
                    dot_size,
                    dot_size,
                )
            )
        else:
            bar_width = max(2, diameter * 0.13)
            bar_height = diameter * 0.42
            gap = diameter * 0.12
            first_x = badge.center().x() - gap / 2 - bar_width
            second_x = badge.center().x() + gap / 2
            top = badge.center().y() - bar_height / 2
            painter.drawRoundedRect(
                QRectF(first_x, top, bar_width, bar_height), 1, 1
            )
            painter.drawRoundedRect(
                QRectF(second_x, top, bar_width, bar_height), 1, 1
            )

        painter.end()
        self.tray_icon.setIcon(QIcon(pixmap))

    def _show_main_window(self) -> None:
        """Возвращает главное окно на экран и активирует его."""
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Открывает главное окно двойным или одиночным кликом по значку."""
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._show_main_window()

    def closeEvent(self, event: QCloseEvent) -> None:
        """При работающем таймере скрывает окно вместо завершения приложения."""
        if self.timer.is_running:
            self.hide()
            event.ignore()
            return

        self.tray_icon.hide()
        event.accept()

    def _quit_application(self) -> None:
        """Полностью завершает приложение из меню системного трея."""
        self.tray_icon.hide()
        self.mini_timer.close()
        self.close()
        QApplication.instance().quit()

    def _mode_button(self, text: str, mode: TimerMode) -> QPushButton:
        """Создаёт кнопку переключения на заданный режим таймера."""
        button = QPushButton(text)
        button.setObjectName("modeButton")
        button.setMinimumHeight(38)
        button.clicked.connect(lambda: self.timer.set_mode(mode))
        return button

    def _toggle_timer(self) -> None:
        """Переключает таймер между запуском и паузой."""
        if self.timer.is_running:
            self.timer.pause()
        else:
            self.timer.start()

    def _update_time(self, seconds: int) -> None:
        """Обновляет отображение времени в круговом индикаторе."""

        # Передаём виджету оставшееся время и полную длительность фазы.
        self.circular_timer.set_time(
            seconds,
            self.timer.duration_for(self.timer.mode),
            self.timer.mode,
        )
        self._update_tray_status()


    def _open_settings(self) -> None:
        """Открывает настройки и сохраняет изменения после подтверждения."""
        # Читаем сохранённую настройку прилипания.
        # Если пользователь ещё не менял её, по умолчанию прилипание включено.
        snap_to_edges = self.settings.value(
            "snap_to_edges", True, type=bool
        )

        sound_enabled = self.settings.value(
            "sound_enabled", True, type=bool
        )

        # Создаём диалог настроек и передаём ему текущие параметры приложения.
        dialog = SettingsDialog(
            language=self.language,
            theme=self.theme,
            parent=self,
            history_retention_days=self.history_retention_days,
            snap_to_edges=snap_to_edges,
            sound_enabled=sound_enabled,
            notifications_enabled=self.notifications_enabled,
            **self.timer_settings,
        )

        # Если пользователь нажал «Отмена», ничего не меняем и не сохраняем.
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        # Получаем значения, выбранные пользователем в диалоге.
        new_language = dialog.selected_language()
        new_timer_settings = dialog.selected_timer_settings()
        new_theme = dialog.selected_theme()
        new_snap_to_edges = dialog.selected_snap_to_edges()
        new_sound_enabled = dialog.selected_sound_enabled()
        new_notifications_enabled = (
            dialog.selected_notifications_enabled()
        )
        new_history_retention_days = (
            dialog.selected_history_retention()
        )

        # Обновляем настройки в текущем экземпляре приложения.
        self.language = new_language
        self.timer_settings = new_timer_settings
        self.theme = new_theme

        # Сохраняем язык и тему, чтобы они восстановились при следующем запуске.
        self.settings.setValue("language", self.language)
        self.settings.setValue("theme", self.theme)
        self.sound_enabled = new_sound_enabled
        self.settings.setValue("sound_enabled", self.sound_enabled)
        self.notifications_enabled = new_notifications_enabled
        self.settings.setValue(
            "notifications_enabled",
            self.notifications_enabled,
        )
        self.history_retention_days = new_history_retention_days

        # Загружаем настройку звуковых сигналов.
        self.sound_enabled = self.settings.value(
            "sound_enabled", True, type=bool
        )

        self.settings.setValue(
            "history_retention_days",
            self.history_retention_days,
        )

        # Применяем новый срок хранения сразу после сохранения настроек.
        if self.history_retention_days > 0:
            self.history.delete_sessions_older_than(
                self.history_retention_days
            )

        # Сохраняем продолжительность фокуса и перерывов.
        for key, value in self.timer_settings.items():
            self.settings.setValue(key, value)

        # Сохраняем настройку прилипания в постоянное хранилище QSettings.
        self.settings.setValue("snap_to_edges", new_snap_to_edges)

        # Сразу применяем новое поведение к открытому мини-таймеру.
        self.mini_timer.snap_to_edges = new_snap_to_edges

        # Применяем продолжительность таймера и обновляем интерфейс.
        self.timer.apply_settings(**self.timer_settings)
        self.setStyleSheet(self._stylesheet())
        # Применяем новую цветовую тему к круговому таймеру.
        self.circular_timer.set_theme(self.theme)
        self._retranslate_ui()

    def _open_history(self) -> None:
        """Открывает окно с историей завершённых сессий."""
        dialog = HistoryDialog(
            history=self.history,
            language=self.language,
            theme=self.theme,
            parent=self,
        )
        dialog.exec()

    def _open_mini_timer(self) -> None:
        """Показывает мини-таймер и переводит его на передний план."""
        self.mini_timer.show()
        self.mini_timer.raise_()
        self.mini_timer.activateWindow()

    def _retranslate_ui(self) -> None:
        """Обновляет подписи интерфейса на выбранном языке."""
        self.setWindowTitle(translate(self.language, "window_title"))

        self.focus_button.setText(translate(self.language, "focus"))
        self.short_button.setText(translate(self.language, "short_break"))
        self.long_button.setText(translate(self.language, "long_break"))
        self.reset_button.setText(translate(self.language, "reset"))
        self.footer_label.setText(translate(self.language, "footer"))

        # Обновляем подписи таблицы истории при смене языка.
        if hasattr(self, "history_table"):
            self._refresh_history_page()
        if hasattr(self, "statistics_heading"):
            self._retranslate_statistics_page()
            self._refresh_statistics_page()
        if hasattr(self, "settings_heading"):
            self._retranslate_settings_page()

        self._update_mode(self.timer.mode)
        self._update_running_state(self.timer.is_running)
        self._update_session_count(self.timer.session_count)
        self._retranslate_tray_menu()
        self.mini_timer_button.setToolTip(
            translate(self.language, "mini_timer")
        )
        self.mini_timer.main_window_button.setText(
            translate(self.language, "show_main_window")
        )
        self.mini_timer._update_running_state(self.timer.is_running)

    def _update_mode(self, mode: TimerMode) -> None:
        """Обновляет заголовок и визуальное выделение выбранного режима."""
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
        self._update_tray_status()

        # Перезапускаем короткое появление, даже если режимы быстро щёлкают.
        self.mode_label_animation.stop()
        self.mode_label_effect.setOpacity(0.35)
        self.mode_label_animation.setStartValue(0.35)
        self.mode_label_animation.setEndValue(1.0)
        self.mode_label_animation.start()

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
        """Меняет подписи кнопки и статуса в зависимости от состояния таймера."""
        self._update_tray_status()
        if running:
            self.start_button.setText(translate(self.language, "pause"))
            self.status_label.setText(
                translate(self.language, "stay_focused")
            )
            self._animate_status_label()
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
        self._animate_status_label()

    def _animate_status_label(self) -> None:
        """Плавно проявляет статус после изменения его текста."""
        self.status_label_animation.stop()
        self.status_label_effect.setOpacity(0.35)
        self.status_label_animation.setStartValue(0.35)
        self.status_label_animation.setEndValue(1.0)
        self.status_label_animation.start()

    def _update_session_count(self, count: int | None = None) -> None:
        """Показывает число завершённых фокус-сессий из базы истории."""
        completed_count = self.history.count_completed_focus_sessions()
        key = "sessions_one" if completed_count == 1 else "sessions_many"
        self.session_badge.setText(
            translate(self.language, key, count=completed_count)
        )

        # Цикл состоит из заданного числа завершённых фокус-сессий.
        cycle_length = max(
            1, int(self.timer_settings["sessions_before_long_break"])
        )
        completed_in_cycle = completed_count % cycle_length
        cycle_number = completed_in_cycle + 1

        self.cycle_progress.setRange(0, cycle_length)
        self.cycle_progress.setValue(cycle_number)

        if self.language == "ru":
            cycle_text = (
                f"Цикл · сессия {cycle_number} из {cycle_length}"
                if completed_in_cycle < cycle_length
                else f"Цикл · {cycle_length} из {cycle_length}"
            )
        else:
            cycle_text = (
                f"Cycle · session {cycle_number} of {cycle_length}"
                if completed_in_cycle < cycle_length
                else f"Cycle · {cycle_length} of {cycle_length}"
            )
        self.cycle_label.setText(cycle_text)


    def _phase_completed(self, mode: TimerMode) -> None:
        """Записывает завершённую фазу в историю и обновляет статус."""
        duration = self.timer.duration_for(mode)

        self.history.add_session(
            mode=mode.value,
            duration_seconds=duration,
        )

        # Если пользователь сейчас смотрит историю, показываем новую запись.
        if self.pages.currentIndex() == self.page_indices.get("history"):
            self._refresh_history_page()
        elif self.pages.currentIndex() == self.page_indices.get("statistics"):
            self._refresh_statistics_page()

        if mode == TimerMode.FOCUS:
            self._update_session_count()
            key = "focus_completed"
        else:
            key = "break_completed"

        self.status_label.setText(
            translate(self.language, key)
        )

        if self.sound_enabled:
            QApplication.beep()

        # Показываем системное уведомление, если настройка включена.
        if (
                self.notifications_enabled
                and self.tray_icon.supportsMessages()
        ):
            self.tray_icon.showMessage(
                translate(self.language, "notification_title"),
                translate(self.language, key),
                QSystemTrayIcon.MessageIcon.Information,
                5000,
            )


    def _stylesheet(self) -> str:
        """Формирует CSS-стили для выбранной темы оформления."""
        # Для каждой темы задаём палитру; ниже эти значения подставляются в QSS.
        themes = {
            "dark": {
                "background": "#111318",
                "text": "#F3F4F6",
                "card": "#191C23",
                "border": "#2A2E38",
                "muted": "#989EAC",
                "badge": "#20232B",
                "badge_text": "#B7BBC6",
                "button": "#252933",
                "button_hover": "#303541",
                "button_text": "#E1E4EA",
                "mode_text": "#A7ADBA",
                "active_bg": "#332120",
                "active_border": "#A84946",
                "accent": "#F16B66",
                "accent_hover": "#FF817B",
                "accent_text": "#171719",
                "active_text": "#FF8A84",
                "footer": "#666D7B",
            },
            "light": {
                "background": "#F4F5F8",
                "text": "#252936",
                "card": "#FFFFFF",
                "border": "#E0E3EB",
                "muted": "#747B8B",
                "badge": "#E9ECF2",
                "badge_text": "#596174",
                "button": "#E9ECF2",
                "button_hover": "#DDE1EA",
                "button_text": "#343A49",
                "mode_text": "#626A7B",
                "active_bg": "#FFE7E5",
                "active_border": "#E77B75",
                "accent": "#E76560",
                "accent_hover": "#D95752",
                "accent_text": "#FFFFFF",
                "active_text": "#C94F4A",
                "footer": "#858B99",
            },
            "midnight": {
                "background": "#0D1020",
                "text": "#F0F0FF",
                "card": "#151A30",
                "border": "#293152",
                "muted": "#929BC0",
                "badge": "#1C2340",
                "badge_text": "#B5BDE0",
                "button": "#202744",
                "button_hover": "#2B3457",
                "button_text": "#E0E5FF",
                "mode_text": "#A8A5FF",
                "active_bg": "#30264F",
                "active_border": "#8275E8",
                "accent": "#9585FF",
                "accent_hover": "#AA9DFF",
                "accent_text": "#111020",
                "active_text": "#C0B5FF",
                "footer": "#747DA4",
            },
        }

        # Если тема неизвестна, используем тёмную палитру по умолчанию.
        c = themes.get(self.theme, themes["dark"])

        return f"""
        QMainWindow, QWidget {{
            background: {c["background"]};
            color: {c["text"]};
            font-family: Inter, "Segoe UI", Arial, sans-serif;
            font-size: 13px;
        }}
        QLabel#brand {{
            color: {c["text"]};
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 2px;
        }}
        QLabel#sessionBadge {{
            background: {c["badge"]};
            color: {c["badge_text"]};
            border: 1px solid {c["border"]};
            border-radius: 11px;
            padding: 7px 10px;
            font-size: 10px;
            font-weight: 700;
        }}
        QLabel#modeLabel {{
            color: {c["accent"]};
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 3px;
        }}
        QFrame#timerCard {{
            background: {c["card"]};
            border: 1px solid {c["border"]};
            border-radius: 24px;
        }}
        QLabel#cycleLabel {{
            color: {c["muted"]};
            font-size: 11px;
            font-weight: 600;
            padding-top: 2px;
        }}
        QProgressBar#cycleProgress {{
            background: {c["badge"]};
            border: none;
            border-radius: 3px;
        }}
        QProgressBar#cycleProgress::chunk {{
            background: {c["accent"]};
            border-radius: 3px;
        }}
        QLabel#timeLabel {{
            color: {c["text"]};
            font-size: 68px;
            font-weight: 700;
        }}
        QLabel#statusLabel {{
            color: {c["muted"]};
            font-size: 12px;
        }}
        QPushButton {{
            border: none;
            border-radius: 10px;
            padding: 9px 10px;
            font-weight: 600;
        }}
        QPushButton#modeButton {{
            background: {c["card"]};
            border: 1px solid {c["border"]};
            color: {c["mode_text"]};
        }}
        QPushButton#modeButton[active="true"] {{
            background: {c["active_bg"]};
            border: 1px solid {c["active_border"]};
            color: {c["active_text"]};
        }}
        QPushButton#primaryButton {{
            background: {c["accent"]};
            color: {c["accent_text"]};
            font-size: 14px;
            font-weight: 800;
        }}
        QPushButton#primaryButton:hover {{
            background: {c["accent_hover"]};
        }}
        QPushButton#primaryButton:pressed {{
            background: {c["accent"]};
            border: 2px solid {c["active_border"]};
            padding-top: 2px;
        }}
        QPushButton#secondaryButton {{
            background: {c["button"]};
            border: 1px solid {c["border"]};
            color: {c["button_text"]};
        }}
        QPushButton#secondaryButton:hover {{
            background: {c["button_hover"]};
        }}
        QPushButton#secondaryButton:pressed {{
            background: {c["button"]};
            border: 2px solid {c["active_border"]};
        }}
        QPushButton#modeButton:pressed {{
            background: {c["active_bg"]};
            border: 2px solid {c["active_border"]};
        }}
        QLabel#footer {{
            color: {c["footer"]};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 2px;
        }}
        QLabel#pageHeading {{
            color: {c["text"]};
            font-size: 28px;
            font-weight: 700;
        }}
        QLabel#pageDescription {{
            color: {c["muted"]};
            font-size: 13px;
        }}
        QLabel#historySummary {{
            color: {c["muted"]};
            font-size: 12px;
            padding: 4px 0;
        }}
        QFrame#historyStatCard {{
            background: {c["card"]};
            border: 1px solid {c["border"]};
            border-radius: 12px;
        }}
        QFrame#settingsCard {{
            background: {c["card"]};
            border: 1px solid {c["border"]};
            border-radius: 14px;
        }}
        QWidget#settingsPage {{
            background: {c["background"]};
        }}
        QFrame#settingsCard QLabel {{
            background: transparent;
        }}
        /* Подписи должны оставаться прозрачными на фоне страницы. */
        QLabel {{
            background: transparent;
            color: {c["text"]};
        }}
        QLabel#sectionHeading {{
            background: transparent;
            color: {c["text"]};
            font-size: 17px;
            font-weight: 700;
            padding: 3px 0;
            border: none;
        }}
        QComboBox#historyFilter {{
            min-width: 150px;
            padding: 8px 12px;
            border: 1px solid {c["border"]};
            border-radius: 10px;
            background: {c["card"]};
            color: {c["text"]};
        }}
        QComboBox#historyFilter:hover {{
            border-color: {c["active_border"]};
        }}
        QComboBox, QSpinBox {{
            background: {c["badge"]};
            color: {c["text"]};
            border: 1px solid {c["border"]};
            border-radius: 8px;
            padding: 7px 10px;
            min-width: 120px;
            min-height: 22px;
            selection-background-color: {c["active_bg"]};
        }}
        QComboBox:hover, QSpinBox:hover {{
            border-color: {c["active_border"]};
        }}
        QComboBox:focus, QSpinBox:focus {{
            border-color: {c["accent"]};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 28px;
            border: none;
            border-left: 1px solid {c["border"]};
            border-top-right-radius: 8px;
            border-bottom-right-radius: 8px;
            background: {c["button"]};
        }}
        QComboBox QAbstractItemView {{
            background: {c["card"]};
            color: {c["text"]};
            border: 1px solid {c["border"]};
            selection-background-color: {c["active_bg"]};
            selection-color: {c["text"]};
            outline: none;
            padding: 4px;
        }}
        QSpinBox::up-button, QSpinBox::down-button {{
            subcontrol-origin: border;
            subcontrol-position: right;
            width: 22px;
            border: none;
            background: {c["button"]};
        }}
        QSpinBox::up-button {{
            subcontrol-position: top right;
            border-top-right-radius: 7px;
        }}
        QSpinBox::down-button {{
            subcontrol-position: bottom right;
            border-bottom-right-radius: 7px;
        }}
        QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
            background: {c["button_hover"]};
        }}
        QCheckBox {{
            background: transparent;
            color: {c["text"]};
            spacing: 9px;
            padding: 2px 0;
        }}
        QCheckBox::indicator {{
            width: 17px;
            height: 17px;
            border: 1px solid {c["border"]};
            border-radius: 5px;
            background: {c["badge"]};
        }}
        QCheckBox::indicator:checked {{
            background: {c["accent"]};
            border-color: {c["accent"]};
        }}
        QCheckBox::indicator:hover {{
            border-color: {c["active_border"]};
        }}
        QLabel#historyStatTitle {{
            color: {c["muted"]};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
        }}
        QLabel#historyStatValue {{
            color: {c["text"]};
            font-size: 22px;
            font-weight: 700;
        }}
        QLabel#historyStatDetail {{
            color: {c["muted"]};
            font-size: 10px;
            font-weight: 500;
        }}
        QTableWidget#historyTable {{
            background: {c["card"]};
            color: {c["text"]};
            border: 1px solid {c["border"]};
            border-radius: 12px;
            gridline-color: {c["border"]};
            selection-background-color: {c["active_bg"]};
            selection-color: {c["text"]};
        }}
        QTableWidget#historyTable::item {{
            padding: 10px;
            border: none;
        }}
        QHeaderView::section {{
            background: {c["card"]};
            color: {c["muted"]};
            border: none;
            border-bottom: 1px solid {c["border"]};
            padding: 11px;
            font-weight: 700;
        }}
                /* Боковая панель навигации. */
        QFrame#sidebar {{
            background: {c["card"]};
            border-right: 1px solid {c["border"]};
        }}

        /* Кнопка раскрытия боковой панели. */
        QPushButton#sidebarToggle {{
            background: transparent;
            color: {c["text"]};
            font-size: 20px;
            border-radius: 10px;
        }}

        QPushButton#sidebarToggle:hover {{
            background: {c["button_hover"]};
        }}

        /* Кнопки разделов навигации. */
        QPushButton#sidebarButton {{
            background: transparent;
            color: {c["muted"]};
            font-size: 19px;
            border-radius: 10px;
            padding: 0;
        }}

        QPushButton#sidebarButton:hover {{
            background: {c["button_hover"]};
            color: {c["text"]};
        }}

        QPushButton#sidebarButton[active="true"] {{
            background: {c["active_bg"]};
            color: {c["accent"]};
            border: 1px solid {c["active_border"]};
        }}

        /* Подписи разделов в раскрытом меню. */
        QLabel#sidebarLabel {{
            color: {c["text"]};
            font-size: 12px;
            font-weight: 600;
        }}
        """


