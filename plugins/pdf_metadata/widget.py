"""PDF元数据编辑插件主组件：整合各子组件，管理整体布局和事件连接。"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QVBoxLayout, QWidget, QFileDialog
)

from app.base_plugin import BasePlugin
from app.config_manager import ConfigManager
from app.utils.logger import get_logger
from app.utils.ui_helpers import ButtonSpinner, open_in_file_manager, open_file

from .components import MetadataForm, SecurityOptions
from .logic import PdfMetadataLogic

logger = get_logger("PdfMetadataPlugin")


class PdfMetadataPlugin(BasePlugin):
    plugin_id = "pdf_metadata"
    plugin_name = "PDF 元数据编辑"

    def __init__(self) -> None:
        self._widget: Optional[QWidget] = None
        self._file_path: Optional[Path] = None
        self._file_label: Optional[QLabel] = None
        self._metadata_form: Optional[MetadataForm] = None
        self._security_options: Optional[SecurityOptions] = None
        self._logic: PdfMetadataLogic = PdfMetadataLogic()
        self._status_label: Optional[QLabel] = None
        self._report_label: Optional[QLabel] = None
        self._btn_save: Optional[QPushButton] = None
        self._btn_clear: Optional[QPushButton] = None
        self._btn_open_dir: Optional[QPushButton] = None
        self._btn_open_file: Optional[QPushButton] = None
        self._spinner: Optional[ButtonSpinner] = None
        self._config = ConfigManager()

    def get_widget(self) -> QWidget:
        if self._widget is not None:
            return self._widget

        w = QWidget()
        root = QVBoxLayout(w)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        title = QLabel("📋  PDF 元数据编辑")
        title.setObjectName("title")
        root.addWidget(title)

        subtitle = QLabel("读取并清理 PDF 文件的元数据信息（暗标安全处理）")
        subtitle.setObjectName("subtitle")
        root.addWidget(subtitle)

        file_group = QWidget()
        file_lay = QHBoxLayout(file_group)
        file_lay.setContentsMargins(12, 10, 12, 8)
        file_lay.setSpacing(6)

        self._file_label = QLabel("未选择文件")
        self._file_label.setObjectName("subtitle")
        file_lay.addWidget(self._file_label)
        file_lay.addStretch()

        btn_browse = QPushButton("📂 选择 PDF")
        btn_browse.setObjectName("primary")
        btn_browse.setFixedHeight(30)
        btn_browse.clicked.connect(self._on_browse)
        file_lay.addWidget(btn_browse)
        root.addWidget(file_group)

        self._metadata_form = MetadataForm()
        root.addWidget(self._metadata_form)

        self._security_options = SecurityOptions()
        root.addWidget(self._security_options)

        self._report_label = QLabel("")
        self._report_label.setObjectName("subtitle")
        root.addWidget(self._report_label)

        action_row = QHBoxLayout()
        self._btn_clear = QPushButton("🗑 一键清除所有敏感信息")
        self._btn_clear.setObjectName("danger")
        self._btn_clear.setFixedHeight(30)
        self._btn_clear.clicked.connect(self._on_clear_metadata)
        self._btn_clear.setEnabled(False)
        action_row.addWidget(self._btn_clear)
        action_row.addStretch()
        root.addLayout(action_row)

        bottom_row = QHBoxLayout()
        self._status_label = QLabel("就绪")
        self._status_label.setObjectName("subtitle")
        bottom_row.addWidget(self._status_label)
        bottom_row.addStretch()

        self._btn_open_dir = QPushButton("📁 打开所在目录")
        self._btn_open_dir.setVisible(False)
        self._btn_open_dir.clicked.connect(self._on_open_dir)
        bottom_row.addWidget(self._btn_open_dir)

        self._btn_open_file = QPushButton("📄 打开文件")
        self._btn_open_file.setObjectName("primary")
        self._btn_open_file.setVisible(False)
        self._btn_open_file.clicked.connect(self._on_open_file)
        bottom_row.addWidget(self._btn_open_file)

        self._btn_save = QPushButton("💾 保存修改（覆盖原文件）")
        self._btn_save.setObjectName("primary")
        self._btn_save.setFixedHeight(30)
        self._btn_save.clicked.connect(self._on_save)
        self._btn_save.setEnabled(False)
        bottom_row.addWidget(self._btn_save)

        self._spinner = ButtonSpinner(self._btn_save, "保存中", "💾 保存修改（覆盖原文件）")

        root.addLayout(bottom_row)

        self._widget = w
        return w

    def get_control_widget(self) -> Optional[QWidget]:
        return None

    def _on_browse(self) -> None:
        last_dir = self._config.get_path("pdf_metadata", "source_dir")
        files, _ = QFileDialog.getOpenFileNames(None, "选择 PDF", last_dir, "PDF (*.pdf)")
        if files:
            self._file_path = Path(files[0])
            self._config.set_path("pdf_metadata", "source_dir", str(self._file_path.parent))
            self._file_label.setText(f"📄  {self._file_path.name}")
            self._logic.load_file(self._file_path)
            self._load_metadata()
            self._btn_save.setEnabled(True)
            self._btn_clear.setEnabled(True)
            self._hide_result_buttons()

    def _load_metadata(self) -> None:
        success, metadata, report = self._logic.read_metadata()
        if success:
            self._metadata_form.set_metadata(metadata)
            self._report_label.setText(report)
            self._set_status("已读取元数据")
        else:
            self._set_status(f"❌ {report}")

    def _on_save(self) -> None:
        if self._spinner:
            self._spinner.start()

        metadata = self._metadata_form.get_metadata()
        options = self._security_options.get_options()
        
        success, message, report = self._logic.save_metadata(metadata, options)

        if self._spinner:
            self._spinner.stop("💾 保存清理后的文件")

        if success:
            self._set_status(f"✅ {message}")
            self._report_label.setText(report)
            if self._btn_open_dir:
                self._btn_open_dir.setVisible(True)
            if self._btn_open_file:
                self._btn_open_file.setVisible(True)
        else:
            self._set_status(f"❌ {message}")

    def _on_clear_metadata(self) -> None:
        reply = QMessageBox.question(
            None, "确认清除",
            "确定要清除所有敏感信息吗？此操作将清空所有元数据字段，并启用所有安全清理选项。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._metadata_form.clear()
        self._security_options.set_all_checked(True)

        self._report_label.setText("✅ 所有敏感信息已标记为清除")
        self._set_status("已准备好清除所有敏感信息")

    def _hide_result_buttons(self) -> None:
        if self._btn_open_dir:
            self._btn_open_dir.setVisible(False)
        if self._btn_open_file:
            self._btn_open_file.setVisible(False)

    def _on_open_dir(self) -> None:
        if self._file_path:
            open_in_file_manager(self._file_path.parent)

    def _on_open_file(self) -> None:
        output_path = self._logic.get_output_path()
        if output_path and output_path.exists():
            open_file(output_path)

    def _set_status(self, text: str) -> None:
        if self._status_label:
            self._status_label.setText(text)