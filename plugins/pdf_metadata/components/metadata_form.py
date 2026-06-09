"""元数据表单组件：显示和编辑PDF元数据。"""

from __future__ import annotations

from typing import Dict, Optional

from PySide6.QtWidgets import (
    QWidget, QFormLayout, QGroupBox, QLineEdit
)


class MetadataForm(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._title_input: QLineEdit
        self._author_input: QLineEdit
        self._subject_input: QLineEdit
        self._keywords_input: QLineEdit
        self._creator_input: QLineEdit
        self._producer_input: QLineEdit
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QFormLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group = QGroupBox("基本元数据")
        meta_lay = QFormLayout(group)
        meta_lay.setContentsMargins(12, 10, 12, 8)
        meta_lay.setSpacing(6)

        self._title_input = QLineEdit()
        self._title_input.setPlaceholderText("标题")
        self._title_input.setFixedHeight(30)
        meta_lay.addRow("标题:", self._title_input)

        self._author_input = QLineEdit()
        self._author_input.setPlaceholderText("作者")
        self._author_input.setFixedHeight(30)
        meta_lay.addRow("作者:", self._author_input)

        self._subject_input = QLineEdit()
        self._subject_input.setPlaceholderText("主题")
        self._subject_input.setFixedHeight(30)
        meta_lay.addRow("主题:", self._subject_input)

        self._keywords_input = QLineEdit()
        self._keywords_input.setPlaceholderText("关键词（逗号分隔）")
        self._keywords_input.setFixedHeight(30)
        meta_lay.addRow("关键词:", self._keywords_input)

        self._creator_input = QLineEdit()
        self._creator_input.setPlaceholderText("创建者")
        self._creator_input.setFixedHeight(30)
        meta_lay.addRow("创建者:", self._creator_input)

        self._producer_input = QLineEdit()
        self._producer_input.setPlaceholderText("生产者")
        self._producer_input.setFixedHeight(30)
        meta_lay.addRow("生产者:", self._producer_input)
        
        layout.addWidget(group)
    
    def set_metadata(self, metadata: Dict[str, str]) -> None:
        """设置元数据"""
        self._title_input.setText(metadata.get("title", ""))
        self._author_input.setText(metadata.get("author", ""))
        self._subject_input.setText(metadata.get("subject", ""))
        self._keywords_input.setText(metadata.get("keywords", ""))
        self._creator_input.setText(metadata.get("creator", ""))
        self._producer_input.setText(metadata.get("producer", ""))
    
    def get_metadata(self) -> Dict[str, Optional[str]]:
        """获取元数据"""
        return {
            "/Title": self._title_input.text().strip() or None,
            "/Author": self._author_input.text().strip() or None,
            "/Subject": self._subject_input.text().strip() or None,
            "/Keywords": self._keywords_input.text().strip() or None,
            "/Creator": self._creator_input.text().strip() or None,
            "/Producer": self._producer_input.text().strip() or None,
        }
    
    def clear(self) -> None:
        """清空所有字段"""
        self._title_input.clear()
        self._author_input.clear()
        self._subject_input.clear()
        self._keywords_input.clear()
        self._creator_input.clear()
        self._producer_input.clear()