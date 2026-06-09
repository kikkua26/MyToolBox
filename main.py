"""入口文件：启动桌面工具集。"""

import sys

from PySide6.QtWidgets import QApplication

from app.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Python 插件化工具集")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
