"""文件列表表格组件：显示文件列表和重命名状态。"""

from __future__ import annotations

from pathlib import Path
from typing import List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHeaderView, QTableWidget, QTableWidgetItem, QWidget, QVBoxLayout
)


class FileTable(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._table: QTableWidget
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["文件名", "路径", "状态"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        layout.addWidget(self._table)
    
    def set_files(self, files: List[Path]) -> None:
        """设置文件列表"""
        self._table.setRowCount(len(files))
        for i, f in enumerate(files):
            self._table.setItem(i, 0, QTableWidgetItem(f.name))
            self._table.setItem(i, 1, QTableWidgetItem(str(f.parent)))
            self._table.setItem(i, 2, QTableWidgetItem("待处理"))
    
    def update_row_status(self, row: int, status: str) -> None:
        """更新指定行的状态"""
        if 0 <= row < self._table.rowCount():
            self._table.setItem(row, 2, QTableWidgetItem(status))
    
    def update_row_filename(self, row: int, new_name: str) -> None:
        """更新指定行的文件名"""
        if 0 <= row < self._table.rowCount():
            self._table.setItem(row, 0, QTableWidgetItem(new_name))
    
    def get_row_count(self) -> int:
        """获取行数"""
        return self._table.rowCount()
    
    def clear(self) -> None:
        """清空表格"""
        self._table.setRowCount(0)