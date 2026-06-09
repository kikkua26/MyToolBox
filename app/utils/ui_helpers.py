"""通用 UI 工具：加载状态、打开文件管理器等。"""

from __future__ import annotations

import os
import platform
import subprocess
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QTimer, QObject
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl


# ──────────────────────────────────────────────────────────
# 按钮加载状态
# ──────────────────────────────────────────────────────────

class ButtonSpinner(QObject):
    """让按钮显示加载动画（文字跳动），自动管理禁用/恢复。

    用法:
        spinner = ButtonSpinner(btn, "处理中", "🚀 执行")
        spinner.start()
        # ... 任务完成 ...
        spinner.stop()
    """

    _FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, button, loading_text: str = "处理中", done_text: str = "") -> None:
        super().__init__(button)
        self._btn = button
        self._loading_text = loading_text
        self._done_text = done_text or button.text()
        self._frame = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._original_text = button.text()

    def start(self) -> None:
        self._btn.setEnabled(False)
        self._frame = 0
        self._timer.start(100)

    def stop(self, success_text: str = "") -> None:
        self._timer.stop()
        self._btn.setEnabled(True)
        self._btn.setText(success_text if success_text else self._done_text)

    def _tick(self) -> None:
        icon = self._FRAMES[self._frame % len(self._FRAMES)]
        self._btn.setText(f"{icon} {self._loading_text}")
        self._frame += 1


# ──────────────────────────────────────────────────────────
# 打开文件 / 文件夹
# ──────────────────────────────────────────────────────────

def open_in_file_manager(path: Path) -> None:
    """在系统文件管理器中打开路径。

    - 如果是文件：打开所在目录并选中该文件
    - 如果是目录：直接打开该目录
    """
    path = path.resolve()

    if not path.exists():
        return

    system = platform.system()

    if system == "Windows":
        if path.is_file():
            subprocess.Popen(["explorer", "/select,", str(path)])
        else:
            os.startfile(str(path))  # type: ignore[attr-defined]
    elif system == "Darwin":
        if path.is_file():
            subprocess.Popen(["open", "-R", str(path)])
        else:
            subprocess.Popen(["open", str(path)])
    else:
        # Linux / other
        target = path.parent if path.is_file() else path
        subprocess.Popen(["xdg-open", str(target)])


def open_file(path: Path) -> None:
    """用系统默认程序打开文件。"""
    if path.exists():
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))
