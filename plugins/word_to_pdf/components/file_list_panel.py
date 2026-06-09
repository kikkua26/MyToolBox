"""文件列表组件：显示和管理待转换的Word文件列表。"""

from __future__ import annotations

from pathlib import Path
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout, QListWidget, QListWidgetItem, QPushButton, QVBoxLayout, QWidget
)


class FileListPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._list: QListWidget
        self._btn_remove: QPushButton
        self._btn_clear: QPushButton
        self._files: List[Path] = []
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._list = QListWidget()
        self._list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        layout.addWidget(self._list, 1)

        sort_row = QHBoxLayout()
        
        self._btn_remove = QPushButton("🗑 移除选中")
        self._btn_remove.setObjectName("danger")
        self._btn_remove.setFixedHeight(28)
        self._btn_remove.clicked.connect(self._on_remove_selected)
        sort_row.addWidget(self._btn_remove)

        self._btn_clear = QPushButton("清空")
        self._btn_clear.setFixedHeight(28)
        self._btn_clear.clicked.connect(self._on_clear)
        sort_row.addWidget(self._btn_clear)

        sort_row.addStretch()
        layout.addLayout(sort_row)
    
    def set_files(self, files: List[Path]) -> None:
        """设置文件列表"""
        self._files = files[:]
        self._refresh_list()
    
    def get_files(self) -> List[Path]:
        """获取当前文件列表"""
        return self._files[:]
    
    def _refresh_list(self) -> None:
        self._list.clear()
        for f in self._files:
            item = QListWidgetItem(f"📄  {f.name}    ({f.parent})")
            item.setData(Qt.ItemDataRole.UserRole, str(f))
            self._list.addItem(item)
    
    def _on_remove_selected(self) -> None:
        for idx in sorted(self._list.selectedIndexes(), reverse=True):
            r = idx.row()
            self._list.takeItem(r)
            self._files.pop(r)
    
    def _on_clear(self) -> None:
        self._files.clear()
        self._list.clear()
    
    def get_count(self) -> int:
        """获取文件数量"""
        return len(self._files)