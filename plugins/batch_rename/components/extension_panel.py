"""后缀设置面板组件：设置源后缀和目标后缀。"""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QGroupBox, QLabel, QLineEdit, QPushButton
)


class ExtensionPanel(QWidget):
    filter_requested = Signal(str)
    preview_requested = Signal(str, str)
    execute_requested = Signal(str, str)
    
    def __init__(self) -> None:
        super().__init__()
        self._src_ext: QLineEdit
        self._dst_ext: QLineEdit
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group = QGroupBox("后缀设置")
        ext_lay = QHBoxLayout(group)
        ext_lay.setContentsMargins(12, 10, 12, 8)
        ext_lay.setSpacing(8)

        ext_lay.addWidget(QLabel("从"))
        self._src_ext = QLineEdit()
        self._src_ext.setPlaceholderText(".txt")
        self._src_ext.setFixedWidth(100)
        self._src_ext.setFixedHeight(30)
        ext_lay.addWidget(self._src_ext)

        ext_lay.addWidget(QLabel("→"))

        self._dst_ext = QLineEdit()
        self._dst_ext.setPlaceholderText(".md")
        self._dst_ext.setFixedWidth(100)
        self._dst_ext.setFixedHeight(30)
        ext_lay.addWidget(self._dst_ext)

        btn_filter = QPushButton("筛选")
        btn_filter.setFixedHeight(30)
        btn_filter.clicked.connect(self._on_filter)
        ext_lay.addWidget(btn_filter)

        ext_lay.addStretch()
        layout.addWidget(group)
    
    def _on_filter(self) -> None:
        ext = self._src_ext.text().strip()
        if not ext.startswith("."):
            ext = "." + ext
        self.filter_requested.emit(ext)
    
    def get_source_ext(self) -> str:
        """获取源后缀"""
        ext = self._src_ext.text().strip()
        if ext and not ext.startswith("."):
            ext = "." + ext
        return ext
    
    def get_target_ext(self) -> str:
        """获取目标后缀"""
        ext = self._dst_ext.text().strip()
        if ext and not ext.startswith("."):
            ext = "." + ext
        return ext