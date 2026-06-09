"""可折叠面板组件：支持收起/展开侧边栏，通过Splitter实现可拖动。"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QFrame
)


class CollapsiblePanel(QWidget):
    toggled = Signal(bool)
    
    def __init__(self, content_widget: QWidget) -> None:
        super().__init__()
        self._content_widget = content_widget
        self._is_collapsed = False
        self._expanded_width = 280
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._toggle_btn = QPushButton("◀")
        self._toggle_btn.setFixedSize(20, 50)
        self._toggle_btn.setCursor(Qt.PointingHandCursor)
        self._toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f8fafc, stop:1 #f1f5f9);
                color: #64748b;
                border: none;
                border-radius: 0 6px 6px 0;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #e2e8f0, stop:1 #cbd5e1);
                color: #334155;
            }
            QPushButton:pressed {
                background-color: #94a3b8;
                color: white;
            }
        """)
        self._toggle_btn.clicked.connect(self._toggle)
        
        content_container = QFrame()
        content_container.setObjectName("contentContainer")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self._content_widget)
        
        layout.addWidget(content_container)
        layout.addWidget(self._toggle_btn, 0, Qt.AlignTop | Qt.AlignRight)
        
        self.setMinimumWidth(200)
        self.setMaximumWidth(400)
    
    def _toggle(self) -> None:
        self._is_collapsed = not self._is_collapsed
        
        if self._is_collapsed:
            self._content_widget.hide()
            self._toggle_btn.setText("▶")
            self.setMinimumWidth(20)
            self.setMaximumWidth(20)
        else:
            self._content_widget.show()
            self._toggle_btn.setText("◀")
            self.setMinimumWidth(200)
            self.setMaximumWidth(400)
        
        self.toggled.emit(not self._is_collapsed)
    
    def is_collapsed(self) -> bool:
        return self._is_collapsed
    
    def set_collapsed(self, collapsed: bool) -> None:
        if collapsed != self._is_collapsed:
            self._toggle()
    
    def get_expanded_width(self) -> int:
        return self._expanded_width
    
    def set_expanded_width(self, width: int) -> None:
        self._expanded_width = width