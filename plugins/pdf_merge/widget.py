"""PDF合并插件主组件：整合各子组件，管理整体布局和事件连接。"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QVBoxLayout, QWidget
)

from app.base_plugin import BasePlugin
from app.config_manager import ConfigManager
from app.utils.logger import get_logger
from app.utils.ui_helpers import ButtonSpinner, open_in_file_manager, open_file

from .components import PdfFileList, SourcePanel, OutputPanel
from .logic import PdfMergeLogic

logger = get_logger("PdfMergePlugin")


class PdfMergePlugin(BasePlugin):
    plugin_id = "pdf_merge"
    plugin_name = "PDF 合并"

    def __init__(self) -> None:
        self._widget: Optional[QWidget] = None
        self._file_list: Optional[PdfFileList] = None
        self._source_panel: Optional[SourcePanel] = None
        self._output_panel: Optional[OutputPanel] = None
        self._logic: PdfMergeLogic = PdfMergeLogic()
        self._status_label: Optional[QLabel] = None
        self._btn_merge: Optional[QPushButton] = None
        self._btn_open_dir: Optional[QPushButton] = None
        self._btn_open_file: Optional[QPushButton] = None
        self._last_output_path: Optional[Path] = None
        self._spinner: Optional[ButtonSpinner] = None
        self._config = ConfigManager()

    def get_widget(self) -> QWidget:
        if self._widget is not None:
            return self._widget

        w = QWidget()
        root = QVBoxLayout(w)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        # 标题
        title = QLabel("📑  PDF 合并")
        title.setObjectName("title")
        root.addWidget(title)

        subtitle = QLabel("选择多个 PDF，调整顺序后合并为一个文件")
        subtitle.setObjectName("subtitle")
        root.addWidget(subtitle)

        # 来源 + 输出（并排）
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        # 左：来源
        self._source_panel = SourcePanel()
        top_row.addWidget(self._source_panel, 1)

        # 右：输出
        self._output_panel = OutputPanel()
        top_row.addWidget(self._output_panel, 1)

        root.addLayout(top_row)

        # 文件列表
        self._file_list = PdfFileList()
        root.addWidget(self._file_list, 1)

        # 底部
        bottom_row = QHBoxLayout()
        self._status_label = QLabel("就绪")
        self._status_label.setObjectName("subtitle")
        bottom_row.addWidget(self._status_label)
        bottom_row.addStretch()

        # 打开目录 / 打开文件（初始隐藏）
        self._btn_open_dir = QPushButton("📁 打开所在目录")
        self._btn_open_dir.setVisible(False)
        self._btn_open_dir.clicked.connect(self._on_open_dir)
        bottom_row.addWidget(self._btn_open_dir)

        self._btn_open_file = QPushButton("📄 打开文件")
        self._btn_open_file.setObjectName("primary")
        self._btn_open_file.setVisible(False)
        self._btn_open_file.clicked.connect(self._on_open_file)
        bottom_row.addWidget(self._btn_open_file)

        self._btn_merge = QPushButton("🚀 合并 PDF")
        self._btn_merge.setObjectName("primary")
        self._btn_merge.setFixedHeight(30)
        self._btn_merge.clicked.connect(self._on_merge)
        bottom_row.addWidget(self._btn_merge)

        self._spinner = ButtonSpinner(self._btn_merge, "合并中", "🚀 合并 PDF")

        root.addLayout(bottom_row)

        self._widget = w
        self._connect_signals()
        return w

    def _connect_signals(self) -> None:
        if self._source_panel:
            self._source_panel.directory_selected.connect(self._on_directory_selected)
            self._source_panel.files_selected.connect(self._on_files_selected)
        
        if self._file_list:
            self._file_list.order_changed.connect(self._on_order_changed)
    
    def get_control_widget(self) -> Optional[QWidget]:
        return None

    # ── 浏览 ─────────────────────────────────────────────

    def _on_directory_selected(self, directory: Path) -> None:
        self._config.set_path("pdf_merge", "source_dir", str(directory))
        count, msg = self._logic.load_directory(directory)
        self._file_list.set_files(self._logic.get_files())
        self._set_status(f"已加载 {count} 个 PDF")
        self._update_default_output_name()

    def _on_files_selected(self, files: list[Path]) -> None:
        count, msg = self._logic.load_files(files)
        self._file_list.set_files(self._logic.get_files())
        self._set_status(f"已加载 {count} 个 PDF")
        self._update_default_output_name()

    def _update_default_output_name(self) -> None:
        default_name = self._logic.generate_default_output_name()
        if default_name and self._output_panel:
            self._output_panel.set_output_name(default_name)

    def _on_order_changed(self, files: list[Path]) -> None:
        self._logic.set_files(files)
        self._set_status(f"顺序已更新（{len(files)} 个文件）")

    # ── 合并 ─────────────────────────────────────────────

    def _on_merge(self) -> None:
        if self._logic.get_file_count() < 2:
            self._set_status("⚠️ 至少需要 2 个 PDF")
            return

        output_dir_str = self._output_panel.get_output_dir() if self._output_panel else ""
        output_name_str = self._output_panel.get_output_name() if self._output_panel else "merged.pdf"
        if not output_name_str.lower().endswith(".pdf"):
            output_name_str += ".pdf"

        output_dir = Path(output_dir_str) if output_dir_str else (self._logic.get_files()[0].parent if self._logic.get_files() else Path("."))
        output_path = output_dir / output_name_str

        if output_path.exists():
            reply = QMessageBox.question(
                None, "文件已存在",
                f"{output_path} 已存在，覆盖？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        if self._spinner:
            self._spinner.start()

        success, msg = self._logic.merge_pdfs(output_path)

        if self._spinner:
            self._spinner.stop("🚀 合并 PDF")

        if success:
            self._last_output_path = output_path
            self._set_status(f"✅ {msg}")
            if self._btn_open_dir:
                self._btn_open_dir.setVisible(True)
            if self._btn_open_file:
                self._btn_open_file.setVisible(True)
        else:
            self._set_status(f"❌ {msg}")

    # ── 打开文件 / 目录 ─────────────────────────────────

    def _hide_result_buttons(self) -> None:
        if self._btn_open_dir:
            self._btn_open_dir.setVisible(False)
        if self._btn_open_file:
            self._btn_open_file.setVisible(False)
        self._last_output_path = None

    def _on_open_dir(self) -> None:
        if self._last_output_path:
            open_in_file_manager(self._last_output_path)

    def _on_open_file(self) -> None:
        if self._last_output_path:
            open_file(self._last_output_path)

    def _set_status(self, text: str) -> None:
        if self._status_label:
            self._status_label.setText(text)