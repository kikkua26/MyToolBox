"""来源选择组件：设置文件来源模式和浏览文件。"""

from __future__ import annotations

from typing import Callable

from PySide6.QtWidgets import (
    QHBoxLayout, QPushButton, QRadioButton, QVBoxLayout, QWidget
)


class SourceSelector(QWidget):
    def __init__(self, on_browse: Callable[[], None]) -> None:
        super().__init__()
        self._dir_radio: QRadioButton
        self._file_radio: QRadioButton
        self._on_browse_callback = on_browse
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 8)
        layout.setSpacing(6)

        mode_row = QHBoxLayout()
        
        self._dir_radio = QRadioButton("目录（自动筛选 Word）")
        self._dir_radio.setChecked(True)
        mode_row.addWidget(self._dir_radio)

        self._file_radio = QRadioButton("多选文件")
        mode_row.addWidget(self._file_radio)

        mode_row.addStretch()

        btn_browse = QPushButton("📂 浏览")
        btn_browse.setObjectName("primary")
        btn_browse.setFixedHeight(30)
        btn_browse.clicked.connect(self._on_browse)
        mode_row.addWidget(btn_browse)
        
        layout.addLayout(mode_row)
    
    def is_directory_mode(self) -> bool:
        """是否为目录模式"""
        return self._dir_radio.isChecked()
    
    def set_directory_mode(self, enabled: bool) -> None:
        """设置模式"""
        if enabled:
            self._dir_radio.setChecked(True)
        else:
            self._file_radio.setChecked(True)
    
    def _on_browse(self) -> None:
        if self._on_browse_callback:
            self._on_browse_callback()