import sys

from PySide6.QtWidgets import QApplication

from pomodoro_timer.ui.main_window import MainWindow


def main() -> int:
    """Создаёт приложение и запускает главное окно."""

    # Создаём приложение Qt и передаём ему аргументы командной строки.
    app = QApplication(sys.argv)

    # Задаём имя приложения и организации для системных настроек.
    app.setApplicationName("Pomodoro Timer")
    app.setOrganizationName("PomodoroTimer")

    # Используем единый стиль Qt для стандартных элементов интерфейса.
    app.setStyle("Fusion")

    # Создаём главное окно и отображаем его.
    window = MainWindow()
    window.show()

    # Запускаем цикл обработки событий Qt.
    # Метод завершится, когда приложение будет закрыто, и вернёт код выхода.
    return app.exec()


# Запускаем приложение только при непосредственном выполнении этого файла.
if __name__ == "__main__":
    raise SystemExit(main())
