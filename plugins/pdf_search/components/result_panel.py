"""搜索结果面板组件：负责显示搜索结果列表和处理点击事件。"""

from __future__ import annotations

import fitz
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem
)


class SearchResult:
    def __init__(self, page_num: int, text: str, rect: fitz.Rect, keyword: str, 
                 context_before: str = "", context_after: str = ""):
        self.page_num = page_num
        self.text = text
        self.rect = rect
        self.keyword = keyword
        self.context_before = context_before
        self.context_after = context_after
    
    def __str__(self):
        return f"Page {self.page_num}: {self.context_before}[{self.keyword}]{self.context_after}"


class ResultPanel(QWidget):
    result_clicked = Signal(SearchResult)
    
    def __init__(self) -> None:
        super().__init__()
        self._result_list: QListWidget
        self._stats_label: QLabel
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        title = QLabel("📋 搜索结果")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self._result_list = QListWidget()
        self._result_list.itemClicked.connect(self._on_result_click)
        self._result_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        layout.addWidget(self._result_list)

        self._stats_label = QLabel("找到 0 个匹配")
        self._stats_label.setObjectName("subtitle")
        layout.addWidget(self._stats_label)
    
    def _on_result_click(self, item: QListWidgetItem) -> None:
        result = item.data(Qt.ItemDataRole.UserRole)
        if result:
            self.result_clicked.emit(result)
    
    def clear_results(self) -> None:
        self._result_list.clear()
        self._stats_label.setText("找到 0 个匹配")
    
    def add_results(self, results: List[SearchResult]) -> None:
        self._result_list.clear()
        
        from PySide6.QtWidgets import QWidget, QVBoxLayout
        
        for result in results:
            page_text = f"📄 第{result.page_num + 1}页:"
            if result.context_before or result.context_after:
                context_text = f"...{result.context_before}" \
                              f"<span style='background-color: #FFEB3B; color: #C62828; font-weight: bold;'>{result.keyword}</span>" \
                              f"{result.context_after}..."
            else:
                context_text = f"<span style='background-color: #FFEB3B; color: #C62828; font-weight: bold;'>{result.keyword}</span>"
            
            item_widget = QWidget()
            item_layout = QVBoxLayout(item_widget)
            item_layout.setContentsMargins(4, 4, 4, 4)
            
            page_label = QLabel(page_text)
            page_label.setStyleSheet("font-size: 12px; color: #666;")
            item_layout.addWidget(page_label)
            
            context_label = QLabel()
            context_label.setTextFormat(Qt.RichText)
            context_label.setText(context_text)
            context_label.setStyleSheet("font-size: 13px;")
            context_label.setWordWrap(True)
            item_layout.addWidget(context_label)
            
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, result)
            self._result_list.addItem(item)
            self._result_list.setItemWidget(item, item_widget)
            item.setSizeHint(item_widget.sizeHint())
        
        self._stats_label.setText(f"找到 {len(results)} 个匹配")
    
    def get_result_count(self) -> int:
        return self._result_list.count()