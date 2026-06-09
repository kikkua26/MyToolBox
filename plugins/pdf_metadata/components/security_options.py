"""安全清理选项组件：选择要清除的敏感信息类型。"""

from __future__ import annotations

from typing import Dict, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QCheckBox
)


class SecurityOptions(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self._chk_doc_id: QCheckBox
        self._chk_xmp: QCheckBox
        self._chk_annotations: QCheckBox
        self._chk_scripts: QCheckBox
        self._chk_attachments: QCheckBox
        self._chk_forms: QCheckBox
        self._init_ui()
    
    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group = QGroupBox("🔒 暗标安全清理（可能导致废标的隐藏信息）")
        security_lay = QVBoxLayout(group)
        security_lay.setContentsMargins(12, 10, 12, 8)
        security_lay.setSpacing(6)

        self._chk_doc_id = QCheckBox("清除文档 ID（可能包含唯一标识）")
        self._chk_doc_id.setChecked(True)
        security_lay.addWidget(self._chk_doc_id)

        self._chk_xmp = QCheckBox("清除 XMP 扩展元数据（详细作者信息）")
        self._chk_xmp.setChecked(True)
        security_lay.addWidget(self._chk_xmp)

        self._chk_annotations = QCheckBox("清除注释和标记（隐藏批注）")
        self._chk_annotations.setChecked(True)
        security_lay.addWidget(self._chk_annotations)

        self._chk_scripts = QCheckBox("清除 JavaScript 脚本")
        self._chk_scripts.setChecked(True)
        security_lay.addWidget(self._chk_scripts)

        self._chk_attachments = QCheckBox("清除附件文件")
        self._chk_attachments.setChecked(True)
        security_lay.addWidget(self._chk_attachments)

        self._chk_forms = QCheckBox("清除表单字段")
        self._chk_forms.setChecked(True)
        security_lay.addWidget(self._chk_forms)
        
        layout.addWidget(group)
    
    def get_options(self) -> Dict[str, bool]:
        """获取当前选项状态"""
        return {
            "doc_id": self._chk_doc_id.isChecked(),
            "xmp": self._chk_xmp.isChecked(),
            "annotations": self._chk_annotations.isChecked(),
            "scripts": self._chk_scripts.isChecked(),
            "attachments": self._chk_attachments.isChecked(),
            "forms": self._chk_forms.isChecked(),
        }
    
    def set_all_checked(self, checked: bool) -> None:
        """设置所有选项的选中状态"""
        self._chk_doc_id.setChecked(checked)
        self._chk_xmp.setChecked(checked)
        self._chk_annotations.setChecked(checked)
        self._chk_scripts.setChecked(checked)
        self._chk_attachments.setChecked(checked)
        self._chk_forms.setChecked(checked)
    
    def get_selected_items(self) -> List[str]:
        """获取选中的清理项名称列表"""
        items = []
        if self._chk_doc_id.isChecked():
            items.append("文档ID")
        if self._chk_xmp.isChecked():
            items.append("XMP元数据")
        if self._chk_annotations.isChecked():
            items.append("注释")
        if self._chk_scripts.isChecked():
            items.append("脚本")
        if self._chk_attachments.isChecked():
            items.append("附件")
        if self._chk_forms.isChecked():
            items.append("表单字段")
        return items