from __future__ import annotations

# Импорты стандартной библиотеки и компонентов PySide6.

from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent
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
)

# Импорты логики таймера, истории и окон интерфейса проекта.
from pomodoro_timer.core.history import SessionHistory
from pomodoro_timer.core.timer import PomodoroTimer, TimerMode
from pomodoro_timer.ui.history_dialog import HistoryDialog
from pomodoro_timer.ui.mini_timer import MiniTimer
from pomodoro_timer.ui.settings_dialog import SettingsDialog
from pomodoro_timer.ui.translations import translate


class MainWindow(QMainWindow):
    """Главное окно: таймер, настройки, история и системный трей."""

    def __init__(self) -> None:
        """Создаёт окно, загружает настройки и собирает интерфейс."""
        super().__init__()

        # QSettings хранит пользовательские параметры между запусками.
        self.settings = QSettings("KontataGood", "PomodoroTimer")
        # База истории хранится в домашней папке пользователя.
        data_dir = Path.home() / ".pomodoro_timer"
        self.history = SessionHistory(data_dir / "history.db")
        # Загружаем срок хранения истории. 0 означает бессрочное хранение.
        self.history_retention_days = self.settings.value(
            "history_retention_days", 0, type=int
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
        self.setMinimumSize(440, 600)
        self.resize(480, 640)
        self.setStyleSheet(self._stylesheet())

        # Центральный виджет содержит все элементы главного окна.
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(28, 26, 28, 26)
        root_layout.setSpacing(20)

        # Верхняя панель: название, счётчик, настройки, история и мини-таймер.
        header = QHBoxLayout()
        brand = QLabel("POMODORO")
        brand.setObjectName("brand")
        header.addWidget(brand)
        header.addStretch(1)
        self.session_badge = QLabel("0 SESSIONS")
        self.session_badge.setObjectName("sessionBadge")
        header.addWidget(self.session_badge)
        self.settings_button = QPushButton("⚙")
        self.settings_button.setObjectName("secondaryButton")
        self.settings_button.setFixedSize(38, 38)
        self.settings_button.clicked.connect(self._open_settings)
        header.addWidget(self.settings_button)
        self.history_button = QPushButton()
        self.history_button.setObjectName("secondaryButton")
        self.history_button.setFixedHeight(38)
        self.history_button.clicked.connect(self._open_history)
        header.addWidget(self.history_button)
        self.mini_timer_button = QPushButton("◷")
        self.mini_timer_button.setObjectName("secondaryButton")
        self.mini_timer_button.setFixedSize(38, 38)
        self.mini_timer_button.setToolTip(
            translate(self.language, "mini_timer")
        )
        self.mini_timer_button.clicked.connect(self._open_mini_timer)
        header.addWidget(self.mini_timer_button)
        root_layout.addLayout(header)

        root_layout.addStretch(1)

        # Заголовок текущего режима и карточка с оставшимся временем.
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

        # Переключатели режима: фокус, короткий и длинный перерыв.
        modes = QHBoxLayout()
        modes.setSpacing(8)
        self.focus_button = self._mode_button("Focus", TimerMode.FOCUS)
        self.short_button = self._mode_button("Short break", TimerMode.SHORT_BREAK)
        self.long_button = self._mode_button("Long break", TimerMode.LONG_BREAK)
        modes.addWidget(self.focus_button)
        modes.addWidget(self.short_button)
        modes.addWidget(self.long_button)
        root_layout.addLayout(modes)

        # Основные действия пользователя — запуск/пауза и сброс.
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

    def _setup_tray(self) -> None:
        """Настраивает значок и меню приложения в системном трее."""
        self.tray_icon = QSystemTrayIcon(self)

        # Пока используем стандартную иконку приложения.
        self.tray_icon.setIcon(self.style().standardIcon(
            self.style().StandardPixmap.SP_ComputerIcon
        ))

        self.tray_menu = QMenu(self)

        self.show_action = QAction("Открыть", self)
        self.show_action.triggered.connect(self._show_main_window)
        self.tray_menu.addAction(self.show_action)

        self.mini_timer_action = QAction("Мини-таймер", self)
        self.mini_timer_action.triggered.connect(self._open_mini_timer)
        self.tray_menu.addAction(self.mini_timer_action)

        self.tray_menu.addSeparator()

        self.quit_action = QAction("Выход", self)
        self.quit_action.triggered.connect(self._quit_application)
        self.tray_menu.addAction(self.quit_action)

        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self._tray_activated)
        self.tray_icon.show()

    def _show_main_window(self) -> None:
        """Возвращает главное окно на экран и активирует его."""
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Обрабатывает щелчок по значку приложения в системном трее."""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
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
        """Форматирует оставшееся время и показывает его как MM:SS."""
        minutes, secs = divmod(max(0, seconds), 60)
        self.time_label.setText(f"{minutes:02d}:{secs:02d}")

    def _open_settings(self) -> None:
        """Открывает настройки и сохраняет изменения после подтверждения."""
        # Читаем сохранённую настройку прилипания.
        # Если пользователь ещё не менял её, по умолчанию прилипание включено.
        snap_to_edges = self.settings.value(
            "snap_to_edges", True, type=bool
        )

        # Создаём диалог настроек и передаём ему текущие параметры приложения.
        dialog = SettingsDialog(
            language=self.language,
            theme=self.theme,
            parent=self,
            snap_to_edges=snap_to_edges,
            history_retention_days=self.history_retention_days,
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
        self.history_retention_days = new_history_retention_days

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

        self._update_mode(self.timer.mode)
        self._update_running_state(self.timer.is_running)
        self._update_session_count(self.timer.session_count)
        self.history_button.setText(
            translate(self.language, "history_button")
        )
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

    def _update_session_count(self, count: int | None = None) -> None:
        """Показывает число завершённых фокус-сессий из базы истории."""
        completed_count = self.history.count_completed_focus_sessions()
        key = "sessions_one" if completed_count == 1 else "sessions_many"
        self.session_badge.setText(
            translate(self.language, key, count=completed_count)
        )


    def _phase_completed(self, mode: TimerMode) -> None:
        """Записывает завершённую фазу в историю и обновляет статус."""
        duration = self.timer.duration_for(mode)

        self.history.add_session(
            mode=mode.value,
            duration_seconds=duration,
        )

        if mode == TimerMode.FOCUS:
            self._update_session_count()
            key = "focus_completed"
        else:
            key = "break_completed"

        self.status_label.setText(
            translate(self.language, key)
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
        QPushButton#secondaryButton {{
            background: {c["button"]};
            border: 1px solid {c["border"]};
            color: {c["button_text"]};
        }}
        QPushButton#secondaryButton:hover {{
            background: {c["button_hover"]};
        }}
        QLabel#footer {{
            color: {c["footer"]};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 2px;
        }}
        """
