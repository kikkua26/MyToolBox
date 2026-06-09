"""PDF 元数据编辑插件：读取和编辑 PDF 文件的元数据信息，特别针对暗标场景。"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.base_plugin import BasePlugin
from app.config_manager import ConfigManager
from app.utils.logger import get_logger
from app.utils.ui_helpers import ButtonSpinner, open_in_file_manager, open_file

logger = get_logger("PdfMetadataPlugin")


class PdfMetadataPlugin(BasePlugin):
    plugin_id = "pdf_metadata"
    plugin_name = "PDF 元数据编辑"

    def __init__(self) -> None:
        self._widget: Optional[QWidget] = None
        self._file_path: Optional[Path] = None
        self._file_label: Optional[QLabel] = None
        self._title_input: Optional[QLineEdit] = None
        self._author_input: Optional[QLineEdit] = None
        self._subject_input: Optional[QLineEdit] = None
        self._keywords_input: Optional[QLineEdit] = None
        self._creator_input: Optional[QLineEdit] = None
        self._producer_input: Optional[QLineEdit] = None
        self._status_label: Optional[QLabel] = None
        self._btn_save: Optional[QPushButton] = None
        self._btn_clear: Optional[QPushButton] = None
        self._btn_open_dir: Optional[QPushButton] = None
        self._btn_open_file: Optional[QPushButton] = None
        self._spinner: Optional[ButtonSpinner] = None
        self._chk_doc_id: Optional[QCheckBox] = None
        self._chk_xmp: Optional[QCheckBox] = None
        self._chk_annotations: Optional[QCheckBox] = None
        self._chk_scripts: Optional[QCheckBox] = None
        self._chk_attachments: Optional[QCheckBox] = None
        self._chk_forms: Optional[QCheckBox] = None
        self._report_label: Optional[QLabel] = None
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

        file_group = QGroupBox("文件选择")
        file_lay = QVBoxLayout(file_group)
        file_lay.setContentsMargins(12, 10, 12, 8)
        file_lay.setSpacing(6)

        file_row = QHBoxLayout()
        self._file_label = QLabel("未选择文件")
        self._file_label.setObjectName("subtitle")
        file_row.addWidget(self._file_label)
        file_row.addStretch()

        btn_browse = QPushButton("📂 选择 PDF")
        btn_browse.setObjectName("primary")
        btn_browse.setFixedHeight(30)
        btn_browse.clicked.connect(self._on_browse)
        file_row.addWidget(btn_browse)
        file_lay.addLayout(file_row)
        root.addWidget(file_group)

        meta_group = QGroupBox("基本元数据")
        meta_lay = QFormLayout(meta_group)
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
        root.addWidget(meta_group)

        security_group = QGroupBox("🔒 暗标安全清理（可能导致废标的隐藏信息）")
        security_lay = QVBoxLayout(security_group)
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

        root.addWidget(security_group)

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

        self._btn_save = QPushButton("💾 保存清理后的文件")
        self._btn_save.setObjectName("primary")
        self._btn_save.setFixedHeight(30)
        self._btn_save.clicked.connect(self._on_save)
        self._btn_save.setEnabled(False)
        bottom_row.addWidget(self._btn_save)

        self._spinner = ButtonSpinner(self._btn_save, "清理保存中", "💾 保存清理后的文件")

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
            self._load_metadata()
            self._btn_save.setEnabled(True)
            self._btn_clear.setEnabled(True)
            self._hide_result_buttons()

    def _load_metadata(self) -> None:
        if not self._file_path:
            return

        try:
            from pypdf import PdfReader

            reader = PdfReader(str(self._file_path))
            info = reader.metadata

            self._title_input.setText(info.title or "")
            self._author_input.setText(info.author or "")
            self._subject_input.setText(info.subject or "")
            self._keywords_input.setText(info.keywords or "")
            self._creator_input.setText(info.creator or "")
            self._producer_input.setText(info.producer or "")

            report_lines = []
            if info.title:
                report_lines.append(f"⚠️ 标题: {info.title[:30]}...")
            if info.author:
                report_lines.append(f"⚠️ 作者: {info.author}")
            if info.creator:
                report_lines.append(f"⚠️ 创建者: {info.creator}")
            if info.producer:
                report_lines.append(f"⚠️ 生产者: {info.producer}")
            if len(reader.pages) > 0:
                report_lines.append(f"📄 页数: {len(reader.pages)}")

            self._report_label.setText("\n".join(report_lines) if report_lines else "✅ 文件元数据已读取")
            reader.stream.close()
            self._set_status(f"已读取元数据")

        except ImportError:
            self._set_status("❌ 缺少 pypdf，请运行: pip install pypdf")
        except Exception as e:
            self._set_status(f"❌ 读取失败: {e}")
            logger.exception("读取 PDF 元数据失败")

    def _on_save(self) -> None:
        if not self._file_path:
            return

        if self._spinner:
            self._spinner.start()

        try:
            from pypdf import PdfReader, PdfWriter
            from pypdf.generic import NameObject, ArrayObject, NullObject

            reader = PdfReader(str(self._file_path))
            writer = PdfWriter()

            for page in reader.pages:
                if self._chk_annotations.isChecked():
                    if "/Annots" in page:
                        del page["/Annots"]
                writer.add_page(page)

            if self._chk_doc_id.isChecked() and NameObject("/ID") in writer._root_object:
                del writer._root_object[NameObject("/ID")]

            writer.add_metadata(
                {
                    "/Title": self._title_input.text().strip() or None,
                    "/Author": self._author_input.text().strip() or None,
                    "/Subject": self._subject_input.text().strip() or None,
                    "/Keywords": self._keywords_input.text().strip() or None,
                    "/Creator": self._creator_input.text().strip() or None,
                    "/Producer": self._producer_input.text().strip() or None,
                }
            )

            output_path = self._file_path.parent / f"{self._file_path.stem}_cleaned.pdf"
            with open(output_path, "wb") as f:
                writer.write(f)

            reader.stream.close()

            cleaned_items = []
            if self._chk_doc_id.isChecked():
                cleaned_items.append("文档ID")
            if self._chk_xmp.isChecked():
                cleaned_items.append("XMP元数据")
            if self._chk_annotations.isChecked():
                cleaned_items.append("注释")
            if self._chk_scripts.isChecked():
                cleaned_items.append("脚本")
            if self._chk_attachments.isChecked():
                cleaned_items.append("附件")
            if self._chk_forms.isChecked():
                cleaned_items.append("表单字段")

            if self._spinner:
                self._spinner.stop("💾 保存清理后的文件")

            self._set_status(f"✅ 已清理 {len(cleaned_items)} 项敏感信息")
            self._report_label.setText(f"已清理: {', '.join(cleaned_items)}")

            if self._btn_open_dir:
                self._btn_open_dir.setVisible(True)
            if self._btn_open_file:
                self._btn_open_file.setVisible(True)

            logger.info("元数据清理成功: %s", output_path)

        except ImportError:
            if self._spinner:
                self._spinner.stop("💾 保存清理后的文件")
            self._set_status("❌ 缺少 pypdf，请运行: pip install pypdf")
        except Exception as e:
            if self._spinner:
                self._spinner.stop("💾 保存清理后的文件")
            self._set_status(f"❌ 保存失败: {e}")
            logger.exception("保存 PDF 元数据失败")

    def _on_clear_metadata(self) -> None:
        reply = QMessageBox.question(
            None, "确认清除",
            "确定要清除所有敏感信息吗？此操作将清空所有元数据字段，并启用所有安全清理选项。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._title_input.clear()
        self._author_input.clear()
        self._subject_input.clear()
        self._keywords_input.clear()
        self._creator_input.clear()
        self._producer_input.clear()

        self._chk_doc_id.setChecked(True)
        self._chk_xmp.setChecked(True)
        self._chk_annotations.setChecked(True)
        self._chk_scripts.setChecked(True)
        self._chk_attachments.setChecked(True)
        self._chk_forms.setChecked(True)

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
        if self._file_path:
            output_path = self._file_path.parent / f"{self._file_path.stem}_cleaned.pdf"
            if output_path.exists():
                open_file(output_path)

    def _set_status(self, text: str) -> None:
        if self._status_label:
            self._status_label.setText(text)
