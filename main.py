
import sys

from PySide6.QtWidgets import QApplication

from pomodoro_timer.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Pomodoro Timer")
    app.setOrganizationName("PomodoroTimer")
    app.setStyle("Fusion")

    # Закрытие окна будет обрабатываться самим приложением.
    # Это позволит сворачивать его в системный трей.
    #app.setQuitOnLastWindowClosed(False)

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
