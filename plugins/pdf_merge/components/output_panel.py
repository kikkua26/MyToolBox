"""输出设置面板组件：设置输出目录和文件名。"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit, QPushButton
)


class OutputPanel(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._output_dir: QLineEdit
        self._output_name: QLineEdit
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group = QGroupBox("输出设置")
        out_lay = QVBoxLayout(group)
        out_lay.setContentsMargins(12, 10, 12, 8)
        out_lay.setSpacing(6)

        dir_row = QHBoxLayout()
        dir_row.addWidget(QLabel("目录:"))
        self._output_dir = QLineEdit()
        self._output_dir.setPlaceholderText("默认为源文件目录")
        self._output_dir.setFixedHeight(30)
        dir_row.addWidget(self._output_dir, 1)
        btn_out = QPushButton("📂")
        btn_out.setFixedSize(30, 30)
        btn_out.clicked.connect(self._on_browse_output_dir)
        dir_row.addWidget(btn_out)
        out_lay.addLayout(dir_row)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("文件名:"))
        self._output_name = QLineEdit()
        self._output_name.setPlaceholderText("00合并版-文件夹名.pdf")
        self._output_name.setFixedHeight(30)
        name_row.addWidget(self._output_name, 1)
        out_lay.addLayout(name_row)
        
        layout.addWidget(group)
    
    def _on_browse_output_dir(self) -> None:
        from PySide6.QtWidgets import QFileDialog
        
        d = QFileDialog.getExistingDirectory(None, "选择输出目录", self._output_dir.text())
        if d:
            self._output_dir.setText(d)
    
    def get_output_dir(self) -> str:
        """获取输出目录"""
        return self._output_dir.text().strip()
    
    def get_output_name(self) -> str:
        """获取输出文件名"""
        return self._output_name.text().strip()
    
    def set_output_dir(self, path: str) -> None:
        """设置输出目录"""
        self._output_dir.setText(path)
    
    def set_output_name(self, name: str) -> None:
        """设置输出文件名"""
        self._output_name.setText(name)