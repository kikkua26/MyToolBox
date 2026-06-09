"""搜索结果面板组件：负责显示搜索结果列表和处理点击事件。"""

from __future__ import annotations

import fitz
from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QListWidget
)


class ClickableResultWidget(QWidget):
    """可点击的搜索结果widget，支持点击跳转"""
    def __init__(self, result: 'SearchResult', parent: 'ResultPanel'):
        super().__init__()
        self._result = result
        self._parent = parent
    
    def mousePressEvent(self, event):
        """点击时触发跳转"""
        self._parent.result_clicked.emit(self._result)


class ClickableListWidgetItem(QListWidgetItem):
    """可点击的列表项，存储关联的搜索结果"""
    def __init__(self, list_widget: QListWidget, result: 'SearchResult'):
        super().__init__()
        self._result = result
        self._list_widget = list_widget
        self.setFlags(self.flags() | Qt.ItemFlag.ItemIsSelectable)


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

        title = QLabel("搜索结果")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self._result_list = QListWidget()
        self._result_list.itemClicked.connect(self._on_result_click)
        self._result_list.setSpacing(4)  # 设置item间距
        layout.addWidget(self._result_list)

        self._stats_label = QLabel("找到 0 个匹配")
        self._stats_label.setObjectName("subtitle")
        layout.addWidget(self._stats_label)
    
    def _on_result_click(self, item: QListWidgetItem) -> None:
        if isinstance(item, ClickableListWidgetItem):
            self.result_clicked.emit(item._result)
    
    def clear_results(self) -> None:
        self._result_list.clear()
        self._stats_label.setText("找到 0 个匹配")
    
    def add_results(self, results: List[SearchResult]) -> None:
        self._result_list.clear()
        
        from PySide6.QtWidgets import QWidget, QVBoxLayout
        
        for idx, result in enumerate(results):
            # 关键词高亮样式（黄色背景+红色文字）
            highlight_start = "<span style='background-color: #FFEB3B; color: #D32F2F; font-weight: bold;'>"
            highlight_end = "</span>"
            
            page_text = f"第 {result.page_num + 1} 页"
            if result.context_before or result.context_after:
                context_text = f"...{result.context_before}{highlight_start}{result.keyword}{highlight_end}{result.context_after}..."
            else:
                context_text = f"{highlight_start}{result.keyword}{highlight_end}"
            
            # 创建自定义widget，整个区域可点击
            item_widget = ClickableResultWidget(result, self)
            item_layout = QVBoxLayout(item_widget)
            item_layout.setContentsMargins(8, 6, 8, 6)
            item_layout.setSpacing(4)
            
            page_label = QLabel(page_text)
            page_label.setStyleSheet("font-size: 12px; font-weight: bold;")
            item_layout.addWidget(page_label)
            
            context_label = QLabel()
            context_label.setTextFormat(Qt.RichText)
            context_label.setText(context_text)
            context_label.setWordWrap(True)
            context_label.setStyleSheet("font-size: 13px;")
            context_label.setMinimumWidth(260)
            item_layout.addWidget(context_label)
            
            # 设置最小高度确保不太小，最大高度避免过高
            item_widget.setMinimumHeight(50)
            item_widget.setMaximumHeight(120)
            
            # 创建可点击的list item
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, result)
            self._result_list.addItem(item)
            self._result_list.setItemWidget(item, item_widget)
            
            # 根据内容自动计算高度
            item.setSizeHint(item_widget.sizeHint())
        
        self._stats_label.setText(f"找到 {len(results)} 个匹配")
    
    def get_result_count(self) -> int:
        return self._result_list.count()