"""批量改后缀插件主组件：整合各子组件，管理整体布局和事件连接。"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QMessageBox, QProgressBar, QPushButton,
    QVBoxLayout, QWidget
)

from app.base_plugin import BasePlugin
from app.utils.logger import get_logger
from app.utils.ui_helpers import ButtonSpinner, open_in_file_manager

from .components import FileTable, SourcePanel, ExtensionPanel
from .logic import BatchRenameLogic

logger = get_logger("BatchRenamePlugin")


class BatchRenamePlugin(BasePlugin):
    plugin_id = "batch_rename"
    plugin_name = "批量改后缀"

    def __init__(self) -> None:
        self._widget: Optional[QWidget] = None
        self._file_table: Optional[FileTable] = None
        self._source_panel: Optional[SourcePanel] = None
        self._extension_panel: Optional[ExtensionPanel] = None
        self._logic: BatchRenameLogic = BatchRenameLogic()
        self._progress: Optional[QProgressBar] = None
        self._status_label: Optional[QLabel] = None
        self._btn_exec: Optional[QPushButton] = None
        self._btn_preview: Optional[QPushButton] = None
        self._btn_open_dir: Optional[QPushButton] = None
        self._last_output_dir: Optional[Path] = None
        self._spinner_exec: Optional[ButtonSpinner] = None
        self._spinner_preview: Optional[ButtonSpinner] = None

    def get_widget(self) -> QWidget:
        if self._widget is not None:
            return self._widget

        w = QWidget()
        root = QVBoxLayout(w)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        # 标题
        title = QLabel("✏️  批量改后缀")
        title.setObjectName("title")
        root.addWidget(title)

        subtitle = QLabel("选择目录或多选文件，将指定后缀替换为新后缀")
        subtitle.setObjectName("subtitle")
        root.addWidget(subtitle)

        # 来源 + 后缀（并排）
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        # 左：来源
        self._source_panel = SourcePanel()
        top_row.addWidget(self._source_panel, 1)

        # 右：后缀
        self._extension_panel = ExtensionPanel()
        top_row.addWidget(self._extension_panel, 1)

        root.addLayout(top_row)

        # 文件列表
        self._file_table = FileTable()
        root.addWidget(self._file_table, 1)

        # 进度条
        self._progress = QProgressBar()
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(4)
        root.addWidget(self._progress)

        # 底部操作
        action_row = QHBoxLayout()
        self._status_label = QLabel("就绪")
        self._status_label.setObjectName("subtitle")
        action_row.addWidget(self._status_label)
        action_row.addStretch()

        # 打开目录按钮（初始隐藏）
        self._btn_open_dir = QPushButton("📁 打开所在目录")
        self._btn_open_dir.setVisible(False)
        self._btn_open_dir.clicked.connect(self._on_open_dir)
        action_row.addWidget(self._btn_open_dir)

        btn_clear = QPushButton("清空")
        btn_clear.setFixedHeight(30)
        btn_clear.clicked.connect(self._on_clear)
        action_row.addWidget(btn_clear)

        self._btn_preview = QPushButton("👁 预览")
        self._btn_preview.setFixedHeight(30)
        self._btn_preview.clicked.connect(self._on_preview)
        action_row.addWidget(self._btn_preview)

        self._btn_exec = QPushButton("🚀 执行重命名")
        self._btn_exec.setObjectName("primary")
        self._btn_exec.setFixedHeight(30)
        self._btn_exec.clicked.connect(self._on_execute)
        action_row.addWidget(self._btn_exec)

        # 初始化 spinner
        self._spinner_preview = ButtonSpinner(self._btn_preview, "预览中", "👁 预览")
        self._spinner_exec = ButtonSpinner(self._btn_exec, "处理中", "🚀 执行重命名")

        root.addLayout(action_row)

        self._widget = w
        self._connect_signals()
        return w

    def _connect_signals(self) -> None:
        if self._source_panel:
            self._source_panel.directory_selected.connect(self._on_directory_selected)
            self._source_panel.files_selected.connect(self._on_files_selected)
    
    def get_control_widget(self) -> Optional[QWidget]:
        return None

    # ── 浏览 ─────────────────────────────────────────────

    def _on_directory_selected(self, directory: Path) -> None:
        count, msg = self._logic.load_directory(directory)
        self._file_table.set_files(self._logic.get_files())
        self._set_status(f"{msg}，共 {count} 个文件")

    def _on_files_selected(self, files: list[Path]) -> None:
        count, msg = self._logic.load_files(files)
        self._file_table.set_files(self._logic.get_files())
        self._set_status(f"{msg}，共 {count} 个文件")

    def _on_clear(self) -> None:
        self._logic.clear_files()
        self._file_table.clear()
        self._set_status("已清空")
        if self._btn_open_dir:
            self._btn_open_dir.setVisible(False)

    def _on_filter(self) -> None:
        ext = self._extension_panel.get_source_ext() if self._extension_panel else ""
        if not ext:
            self._set_status("⚠️ 请先填写源后缀")
            return
        count, msg = self._logic.filter_by_extension(ext)
        self._file_table.set_files(self._logic.get_files())
        self._set_status(msg)

    # ── 预览 ─────────────────────────────────────────────

    def _on_preview(self) -> None:
        src = self._extension_panel.get_source_ext() if self._extension_panel else ""
        dst = self._extension_panel.get_target_ext() if self._extension_panel else ""
        
        if not src or not dst:
            self._set_status("⚠️ 请填写源后缀和目标后缀")
            return

        results = self._logic.preview_rename(src, dst)
        matched_count = sum(1 for _, _, new_name in results if new_name != "跳过")
        
        for row, old_name, new_name in results:
            if new_name != "跳过":
                self._file_table.update_row_status(row, f"{old_name} → {new_name}")
            else:
                self._file_table.update_row_status(row, "跳过")

        self._set_status(f"预览: {matched_count} 个文件将被重命名")

    # ── 执行 ─────────────────────────────────────────────

    def _on_execute(self) -> None:
        src = self._extension_panel.get_source_ext() if self._extension_panel else ""
        dst = self._extension_panel.get_target_ext() if self._extension_panel else ""
        
        if not src or not dst:
            self._set_status("⚠️ 请填写源后缀和目标后缀")
            return

        matched_count = sum(1 for f in self._logic.get_files() if f.suffix.lower() == src.lower())
        if matched_count == 0:
            self._set_status(f"没有找到 {src} 文件")
            return

        reply = QMessageBox.question(
            None, "确认",
            f"即将重命名 {matched_count} 个文件 ({src} → {dst})，确认？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        if self._spinner_exec:
            self._spinner_exec.start()

        success, errors, last_dir, error_messages = self._logic.execute_rename(src, dst)
        files = self._logic.get_files()
        total = matched_count

        for i, f in enumerate(files):
            if f.suffix.lower() == dst.lower():
                self._file_table.update_row_filename(i, f.name)
                self._file_table.update_row_status(i, "✅")
            if self._progress:
                self._progress.setValue(int((i + 1) / len(files) * 100))

        if self._spinner_exec:
            self._spinner_exec.stop("🚀 执行重命名")

        if errors > 0 and error_messages:
            self._set_status(f"⚠️ 完成: {success} 成功, {errors} 失败")
            error_text = "\n".join(error_messages)
            QMessageBox.warning(None, "重命名失败", f"以下文件重命名失败:\n\n{error_text}")
        else:
            self._set_status(f"✅ 完成: {success} 成功, {errors} 失败")

        if self._btn_open_dir and last_dir:
            self._btn_open_dir.setVisible(True)
            self._last_output_dir = last_dir

    # ── 打开目录 ─────────────────────────────────────────

    def _on_open_dir(self) -> None:
        if self._last_output_dir:
            open_in_file_manager(self._last_output_dir)

    def _set_status(self, text: str) -> None:
        if self._status_label:
            self._status_label.setText(text)