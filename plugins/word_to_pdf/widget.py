"""Word转PDF插件主组件：整合各子组件，管理整体布局和事件连接。"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QThread
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.base_plugin import BasePlugin
from app.config_manager import ConfigManager
from app.utils.logger import get_logger
from app.utils.ui_helpers import ButtonSpinner, open_in_file_manager, open_file

from .components import FileListPanel, OutputSettings, SourceSelector
from .logic import ConvertWorker

logger = get_logger("WordToPdfPlugin")


class WordToPdfPlugin(BasePlugin):
    plugin_id = "word_to_pdf"
    plugin_name = "Word 转 PDF"

    def __init__(self) -> None:
        self._widget: Optional[QWidget] = None
        self._source_selector: Optional[SourceSelector] = None
        self._output_settings: Optional[OutputSettings] = None
        self._file_list: Optional[FileListPanel] = None
        self._status_label: Optional[QLabel] = None
        self._progress_bar: Optional[QProgressBar] = None
        self._btn_convert: Optional[QPushButton] = None
        self._btn_cancel: Optional[QPushButton] = None
        self._btn_open_dir: Optional[QPushButton] = None
        self._btn_open_file: Optional[QPushButton] = None
        self._last_output_dir: Optional[Path] = None
        self._spinner: Optional[ButtonSpinner] = None
        self._config = ConfigManager()
        self._worker: Optional[ConvertWorker] = None
        self._thread: Optional[QThread] = None

    def get_widget(self) -> QWidget:
        if self._widget is not None:
            return self._widget

        w = QWidget()
        root = QVBoxLayout(w)
        root.setContentsMargins(24, 16, 24, 16)
        root.setSpacing(12)

        title = QLabel("📝  Word 转 PDF")
        title.setObjectName("title")
        root.addWidget(title)

        subtitle = QLabel("批量将 Word 文档（.docx）转换为 PDF")
        subtitle.setObjectName("subtitle")
        root.addWidget(subtitle)

        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        src_group = QGroupBox("文件来源")
        self._source_selector = SourceSelector(self._on_browse)
        src_group.setLayout(QVBoxLayout())
        src_group.layout().addWidget(self._source_selector)
        top_row.addWidget(src_group, 1)

        out_group = QGroupBox("输出设置")
        self._output_settings = OutputSettings(self._on_browse_output_dir)
        out_group.setLayout(QVBoxLayout())
        out_group.layout().addWidget(self._output_settings)
        top_row.addWidget(out_group, 1)
        root.addLayout(top_row)

        list_group = QGroupBox("文件列表")
        list_lay = QVBoxLayout(list_group)
        list_lay.setContentsMargins(12, 10, 12, 8)
        list_lay.setSpacing(6)

        self._file_list = FileListPanel()
        list_lay.addWidget(self._file_list, 1)
        root.addWidget(list_group, 1)

        self._progress_bar = QProgressBar()
        self._progress_bar.setVisible(False)
        self._progress_bar.setFixedHeight(24)
        root.addWidget(self._progress_bar)

        bottom_row = QHBoxLayout()
        self._status_label = QLabel("就绪")
        self._status_label.setObjectName("subtitle")
        bottom_row.addWidget(self._status_label)
        bottom_row.addStretch()

        self._btn_cancel = QPushButton("⏹ 取消")
        self._btn_cancel.setVisible(False)
        self._btn_cancel.setFixedHeight(30)
        self._btn_cancel.clicked.connect(self._on_cancel)
        bottom_row.addWidget(self._btn_cancel)

        self._btn_open_dir = QPushButton("📁 打开所在目录")
        self._btn_open_dir.setVisible(False)
        self._btn_open_dir.clicked.connect(self._on_open_dir)
        bottom_row.addWidget(self._btn_open_dir)

        self._btn_open_file = QPushButton("📄 打开文件")
        self._btn_open_file.setObjectName("primary")
        self._btn_open_file.setVisible(False)
        self._btn_open_file.clicked.connect(self._on_open_file)
        bottom_row.addWidget(self._btn_open_file)

        self._btn_convert = QPushButton("🚀 开始转换")
        self._btn_convert.setObjectName("primary")
        self._btn_convert.setFixedHeight(30)
        self._btn_convert.clicked.connect(self._on_convert)
        bottom_row.addWidget(self._btn_convert)

        self._spinner = ButtonSpinner(self._btn_convert, "转换中", "🚀 开始转换")

        root.addLayout(bottom_row)

        self._widget = w
        return w

    def get_control_widget(self) -> Optional[QWidget]:
        return None

    def _on_browse(self) -> None:
        last_dir = self._config.get_path("word_to_pdf", "source_dir")
        if self._source_selector.is_directory_mode():
            d = QFileDialog.getExistingDirectory(None, "选择目录", last_dir)
            if d:
                self._config.set_path("word_to_pdf", "source_dir", d)
                files = sorted(Path(d).rglob("*.docx"), key=lambda p: p.name)
                self._file_list.set_files(files)
                self._set_status(f"已加载 {len(files)} 个 Word 文件")
        else:
            files, _ = QFileDialog.getOpenFileNames(None, "选择 Word", last_dir, "Word (*.docx)")
            if files:
                self._file_list.set_files([Path(f) for f in files])
                self._set_status(f"已加载 {len(files)} 个 Word 文件")

    def _on_browse_output_dir(self) -> None:
        last_dir = self._config.get_path("word_to_pdf", "output_dir")
        d = QFileDialog.getExistingDirectory(None, "选择输出目录", last_dir)
        if d:
            self._config.set_path("word_to_pdf", "output_dir", d)
            self._output_settings.set_output_dir(d)

    def _on_convert(self) -> None:
        files = self._file_list.get_files()
        if len(files) == 0:
            self._set_status("⚠️ 请先添加 Word 文件")
            return

        if self._worker is not None:
            self._set_status("⚠️ 正在转换中，请等待")
            return

        output_dir_str = self._output_settings.get_output_dir()
        output_dir = Path(output_dir_str) if output_dir_str else files[0].parent

        if self._spinner:
            self._spinner.start()
        if self._btn_convert:
            self._btn_convert.setVisible(False)
        if self._btn_cancel:
            self._btn_cancel.setVisible(True)
        if self._progress_bar:
            self._progress_bar.setVisible(True)
            self._progress_bar.setRange(0, len(files))
            self._progress_bar.setValue(0)
        self._hide_result_buttons()

        self._worker = ConvertWorker()
        self._worker.set_task(files, output_dir)

        self._thread = QThread()
        self._worker.moveToThread(self._thread)

        def on_progress(idx: int, message: str) -> None:
            if self._progress_bar:
                self._progress_bar.setValue(idx)
            self._set_status(message)

        def on_finished(success_count: int, fail_count: int, out_dir: Path) -> None:
            self._cleanup_worker()
            self._last_output_dir = out_dir

            if self._spinner:
                self._spinner.stop("🚀 开始转换")
            if self._btn_convert:
                self._btn_convert.setVisible(True)
            if self._btn_cancel:
                self._btn_cancel.setVisible(False)
            if self._progress_bar:
                self._progress_bar.setVisible(False)

            if fail_count == 0:
                self._set_status(f"✅ 转换成功: {success_count} 个文件")
            else:
                self._set_status(f"⚠️ 成功 {success_count} 个，失败 {fail_count} 个")

            if success_count > 0:
                if self._btn_open_dir:
                    self._btn_open_dir.setVisible(True)
                if self._btn_open_file:
                    self._btn_open_file.setVisible(True)

        def on_error(error_msg: str) -> None:
            self._cleanup_worker()

            if self._spinner:
                self._spinner.stop("🚀 开始转换")
            if self._btn_convert:
                self._btn_convert.setVisible(True)
            if self._btn_cancel:
                self._btn_cancel.setVisible(False)
            if self._progress_bar:
                self._progress_bar.setVisible(False)

            self._set_status(error_msg)

        self._worker.progress_updated.connect(on_progress)
        self._worker.finished.connect(on_finished)
        self._worker.error.connect(on_error)

        self._thread.started.connect(self._worker.run)
        self._thread.start()

    def _on_cancel(self) -> None:
        if self._worker:
            self._worker.stop()
        self._set_status("⏹ 正在取消...")

    def _cleanup_worker(self) -> None:
        if self._worker:
            self._worker.progress_updated.disconnect()
            self._worker.finished.disconnect()
            self._worker.error.disconnect()
            self._worker = None
        if self._thread:
            self._thread.quit()
            self._thread.wait()
            self._thread = None

    def _hide_result_buttons(self) -> None:
        if self._btn_open_dir:
            self._btn_open_dir.setVisible(False)
        if self._btn_open_file:
            self._btn_open_file.setVisible(False)
        self._last_output_dir = None

    def _on_open_dir(self) -> None:
        if self._last_output_dir:
            open_in_file_manager(self._last_output_dir)

    def _on_open_file(self) -> None:
        if self._last_output_dir:
            pdf_files = list(self._last_output_dir.glob("*.pdf"))
            if pdf_files:
                open_file(pdf_files[0])

    def _set_status(self, text: str) -> None:
        if self._status_label:
            self._status_label.setText(text)