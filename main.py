
import sys
import ctypes

from PySide6.QtWidgets import QApplication

from pomodoro_timer.ui.main_window import MainWindow


def main() -> int:
    """Создаёт приложение и запускает главное окно."""

    # Задаём Windows идентификатор приложения ДО создания QApplication.
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "KontataGood.PomodoroTimer"
        )

    # Создаём приложение Qt.
    app = QApplication(sys.argv)

    # Задаём имя приложения и организации.
    app.setApplicationName("Pomodoro Timer")
    app.setApplicationDisplayName("Pomodoro Timer")
    app.setOrganizationName("PomodoroTimer")

    # Используем единый стиль Qt.
    app.setStyle("Fusion")

    # Создаём и отображаем главное окно.
    window = MainWindow()
    window.show()

    # Запускаем цикл обработки событий.
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
