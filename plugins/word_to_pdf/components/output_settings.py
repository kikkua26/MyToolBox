"""输出设置组件：设置输出目录。"""

from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
)


class OutputSettings(QWidget):
    def __init__(self, on_browse: Callable[[], None]) -> None:
        super().__init__()
        self._output_dir: QLineEdit
        self._on_browse_callback = on_browse
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 8)
        layout.setSpacing(6)

        dir_row = QHBoxLayout()
        dir_row.addWidget(QLabel("目录:"))
        
        self._output_dir = QLineEdit()
        self._output_dir.setPlaceholderText("默认为源文件目录")
        self._output_dir.setFixedHeight(30)
        dir_row.addWidget(self._output_dir, 1)

        btn_out = QPushButton("📂")
        btn_out.setFixedSize(30, 30)
        btn_out.clicked.connect(self._on_browse)
        dir_row.addWidget(btn_out)
        
        layout.addLayout(dir_row)
    
    def get_output_dir(self) -> str:
        """获取输出目录"""
        return self._output_dir.text().strip()
    
    def set_output_dir(self, path: str) -> None:
        """设置输出目录"""
        self._output_dir.setText(path)
    
    def _on_browse(self) -> None:
        if self._on_browse_callback:
            self._on_browse_callback()