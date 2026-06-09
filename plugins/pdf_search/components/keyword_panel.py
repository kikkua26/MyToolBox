"""关键词面板组件：负责关键词的添加、删除和管理。"""

from __future__ import annotations

from typing import List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem, QSpinBox
)


class KeywordPanel(QWidget):
    keyword_added = Signal(str)
    keyword_deleted = Signal(str)
    keywords_cleared = Signal()
    search_requested = Signal(object, int)
    
    def __init__(self) -> None:
        super().__init__()
        self._keyword_input: QLineEdit
        self._keyword_list: QListWidget
        self._context_spin: QSpinBox
        self._status_label: QLabel
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        self._create_keyword_group(layout)
        self._create_context_group(layout)
        self._create_file_group(layout)
        self._create_search_button(layout)
        self._create_status_label(layout)
        
        layout.addStretch()
    
    def _create_keyword_group(self, parent_layout: QVBoxLayout) -> None:
        group = QGroupBox("🔍 关键词组")
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(12, 10, 12, 8)
        group_layout.setSpacing(6)

        input_row = QHBoxLayout()
        self._keyword_input = QLineEdit()
        self._keyword_input.setPlaceholderText("输入关键词")
        self._keyword_input.setFixedHeight(30)
        self._keyword_input.returnPressed.connect(self._on_add_keyword)
        input_row.addWidget(self._keyword_input)
        
        add_btn = QPushButton("+")
        add_btn.setFixedSize(36, 30)
        add_btn.setToolTip("添加关键词")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #60a5fa;
            }
            QPushButton:pressed {
                background-color: #2563eb;
            }
        """)
        add_btn.clicked.connect(self._on_add_keyword)
        input_row.addWidget(add_btn)
        group_layout.addLayout(input_row)

        self._keyword_list = QListWidget()
        self._keyword_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        group_layout.addWidget(self._keyword_list)

        btn_row = QHBoxLayout()
        del_btn = QPushButton("删除")
        del_btn.setFixedSize(60, 28)
        del_btn.clicked.connect(self._on_delete_keyword)
        btn_row.addWidget(del_btn)
        
        clear_btn = QPushButton("清空")
        clear_btn.setFixedSize(60, 28)
        clear_btn.clicked.connect(self._on_clear_keywords)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        group_layout.addLayout(btn_row)
        parent_layout.addWidget(group)
    
    def _create_context_group(self, parent_layout: QVBoxLayout) -> None:
        context_group = QGroupBox("📝 前后文设置")
        context_layout = QVBoxLayout(context_group)
        context_layout.setContentsMargins(12, 10, 12, 8)
        context_layout.setSpacing(6)

        context_row = QHBoxLayout()
        context_row.addWidget(QLabel("前后文字数:"))
        self._context_spin = QSpinBox()
        self._context_spin.setRange(0, 50)
        self._context_spin.setValue(8)
        self._context_spin.setFixedWidth(80)
        context_row.addWidget(self._context_spin)
        context_row.addStretch()
        context_layout.addLayout(context_row)
        parent_layout.addWidget(context_group)
    
    def _create_file_group(self, parent_layout: QVBoxLayout) -> None:
        self._file_label = QLabel("未选择文件")
        self._file_label.setObjectName("subtitle")
        self._file_label.setWordWrap(True)
    
    def _create_search_button(self, parent_layout: QVBoxLayout) -> None:
        search_btn = QPushButton("🚀 开始搜索")
        search_btn.setObjectName("primary")
        search_btn.setFixedHeight(36)
        search_btn.clicked.connect(self._on_search)
        parent_layout.addWidget(search_btn)
    
    def _create_status_label(self, parent_layout: QVBoxLayout) -> None:
        self._status_label = QLabel("就绪")
        self._status_label.setObjectName("subtitle")
        parent_layout.addWidget(self._status_label)
    
    def _on_add_keyword(self) -> None:
        keyword = self._keyword_input.text().strip()
        if keyword:
            items = [self._keyword_list.item(i).text() for i in range(self._keyword_list.count())]
            if keyword not in items:
                item = QListWidgetItem(f"🔤 {keyword}")
                item.setData(Qt.ItemDataRole.UserRole, keyword)
                self._keyword_list.addItem(item)
                self._keyword_input.clear()
                self.set_status(f"已添加关键词: {keyword}")
                self.keyword_added.emit(keyword)
    
    def _on_delete_keyword(self) -> None:
        for item in reversed(self._keyword_list.selectedItems()):
            keyword = item.data(Qt.ItemDataRole.UserRole)
            self._keyword_list.takeItem(self._keyword_list.row(item))
            if keyword:
                self.keyword_deleted.emit(keyword)
    
    def _on_clear_keywords(self) -> None:
        self._keyword_list.clear()
        self.keywords_cleared.emit()
    
    def _on_search(self) -> None:
        keywords = []
        for i in range(self._keyword_list.count()):
            keyword = self._keyword_list.item(i).data(Qt.ItemDataRole.UserRole)
            if keyword:
                keywords.append(keyword)
        
        context_length = self._context_spin.value()
        self.search_requested.emit(keywords, context_length)
    
    def get_keywords(self) -> List[str]:
        keywords = []
        for i in range(self._keyword_list.count()):
            keyword = self._keyword_list.item(i).data(Qt.ItemDataRole.UserRole)
            if keyword:
                keywords.append(keyword)
        return keywords
    
    def set_file_path(self, file_name: str) -> None:
        self._file_label.setText(f"📄 {file_name}")
    
    def set_status(self, text: str) -> None:
        self._status_label.setText(text)