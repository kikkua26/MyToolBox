"""来源选择面板组件：选择目录或文件。"""

from __future__ import annotations

from pathlib import Path
from typing import List

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QRadioButton, QPushButton
)


class SourcePanel(QWidget):
    directory_selected = Signal(object)
    files_selected = Signal(object)
    
    def __init__(self) -> None:
        super().__init__()
        self._dir_radio: QRadioButton
        self._file_radio: QRadioButton
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group = QGroupBox("文件来源")
        src_lay = QVBoxLayout(group)
        src_lay.setContentsMargins(12, 10, 12, 8)
        src_lay.setSpacing(6)

        mode_row = QHBoxLayout()
        self._dir_radio = QRadioButton("目录")
        self._dir_radio.setChecked(True)
        self._file_radio = QRadioButton("文件")
        mode_row.addWidget(self._dir_radio)
        mode_row.addWidget(self._file_radio)
        mode_row.addStretch()

        btn_browse = QPushButton("📂 浏览")
        btn_browse.setObjectName("primary")
        btn_browse.setFixedHeight(30)
        btn_browse.clicked.connect(self._on_browse)
        mode_row.addWidget(btn_browse)
        src_lay.addLayout(mode_row)
        
        layout.addWidget(group)
    
    def _on_browse(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        
        if self._dir_radio.isChecked():
            d = QFileDialog.getExistingDirectory(None, "选择目录")
            if d:
                self.directory_selected.emit(Path(d))
        else:
            files, _ = QFileDialog.getOpenFileNames(None, "选择文件")
            if files:
                self.files_selected.emit([Path(f) for f in files])
    
    def is_directory_mode(self) -> bool:
        """是否为目录模式"""
        return self._dir_radio.isChecked()