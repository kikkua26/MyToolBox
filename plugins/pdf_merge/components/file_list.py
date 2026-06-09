"""PDF文件列表组件：显示PDF列表，支持拖拽排序。"""

from __future__ import annotations

from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QListWidget, 
    QListWidgetItem, QPushButton
)


class PdfFileList(QWidget):
    order_changed = Signal(List[Path])
    
    def __init__(self) -> None:
        super().__init__()
        self._list: QListWidget
        self._files: List[Path] = []
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group = QGroupBox("文件列表 · 拖拽调整顺序")
        list_lay = QVBoxLayout(group)
        list_lay.setContentsMargins(12, 10, 12, 8)
        list_lay.setSpacing(6)

        self._list = QListWidget()
        self._list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self._list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self._list.model().rowsMoved.connect(self._sync_order_from_list)
        list_lay.addWidget(self._list, 1)

        sort_row = QHBoxLayout()
        btn_up = QPushButton("上移")
        btn_up.setFixedSize(60, 28)
        btn_up.clicked.connect(self._on_move_up)
        sort_row.addWidget(btn_up)

        btn_down = QPushButton("下移")
        btn_down.setFixedSize(60, 28)
        btn_down.clicked.connect(self._on_move_down)
        sort_row.addWidget(btn_down)

        btn_remove = QPushButton("移除")
        btn_remove.setObjectName("danger")
        btn_remove.setFixedSize(60, 28)
        btn_remove.clicked.connect(self._on_remove_selected)
        sort_row.addWidget(btn_remove)

        btn_clear = QPushButton("清空")
        btn_clear.setFixedSize(60, 28)
        btn_clear.clicked.connect(self._on_clear)
        sort_row.addWidget(btn_clear)

        sort_row.addStretch()
        list_lay.addLayout(sort_row)
        
        layout.addWidget(group)
    
    def set_files(self, files: List[Path]) -> None:
        """设置文件列表"""
        self._files = files.copy()
        self._refresh_list()
    
    def _refresh_list(self) -> None:
        self._list.clear()
        for f in self._files:
            item = QListWidgetItem(f"📄  {f.name}    ({f.parent})")
            item.setData(Qt.ItemDataRole.UserRole, str(f))
            self._list.addItem(item)
    
    def _sync_order_from_list(self) -> None:
        new_order: list[Path] = []
        for i in range(self._list.count()):
            data = self._list.item(i).data(Qt.ItemDataRole.UserRole)
            if data:
                new_order.append(Path(data))
        self._files = new_order
        self.order_changed.emit(self._files)
    
    def _on_move_up(self) -> None:
        row = self._list.currentRow()
        if row <= 0:
            return
        item = self._list.takeItem(row)
        self._list.insertItem(row - 1, item)
        self._list.setCurrentRow(row - 1)
        self._files[row], self._files[row - 1] = self._files[row - 1], self._files[row]
        self.order_changed.emit(self._files)
    
    def _on_move_down(self) -> None:
        row = self._list.currentRow()
        if row < 0 or row >= self._list.count() - 1:
            return
        item = self._list.takeItem(row)
        self._list.insertItem(row + 1, item)
        self._list.setCurrentRow(row + 1)
        self._files[row], self._files[row + 1] = self._files[row + 1], self._files[row]
        self.order_changed.emit(self._files)
    
    def _on_remove_selected(self) -> None:
        for idx in sorted(self._list.selectedIndexes(), reverse=True):
            r = idx.row()
            self._list.takeItem(r)
            self._files.pop(r)
        self.order_changed.emit(self._files)
    
    def _on_clear(self) -> None:
        self._files.clear()
        self._list.clear()
        self.order_changed.emit(self._files)
    
    def get_files(self) -> List[Path]:
        """获取当前文件列表"""
        return self._files
    
    def get_file_count(self) -> int:
        """获取文件数量"""
        return len(self._files)