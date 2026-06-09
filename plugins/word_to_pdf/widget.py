"""Word 转 PDF 插件：批量将 Word 文档转换为 PDF。"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from app.base_plugin import BasePlugin
from app.config_manager import ConfigManager
from app.utils.logger import get_logger
from app.utils.ui_helpers import ButtonSpinner, open_in_file_manager, open_file

logger = get_logger("WordToPdfPlugin")


class ConvertWorker(QObject):
    progress_updated = Signal(int, str)
    finished = Signal(int, int, Path)
    error = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._files: list[Path] = []
        self._output_dir: Path = Path(".")
        self._running = True

    def set_task(self, files: list[Path], output_dir: Path) -> None:
        self._files = files
        self._output_dir = output_dir
        self._running = True

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        success_count = 0
        fail_count = 0

        try:
            from docx2pdf import convert

            for idx, f in enumerate(self._files):
                if not self._running:
                    break

                try:
                    output_path = self._output_dir / f.with_suffix(".pdf").name
                    self.progress_updated.emit(idx, f"转换中: {f.name}")
                    convert(str(f), str(output_path))
                    success_count += 1
                    logger.info("转换成功: %s -> %s", f.name, output_path)
                except Exception as e:
                    fail_count += 1
                    logger.exception("转换失败: %s", f.name)

            self.progress_updated.emit(len(self._files), "转换完成")
            self.finished.emit(success_count, fail_count, self._output_dir)

        except ImportError:
            self.error.emit("❌ 缺少 docx2pdf，请运行: pip install docx2pdf")
        except Exception as e:
            self.error.emit(f"❌ 转换失败: {e}")
            logger.exception("Word 转 PDF 失败")


class WordToPdfPlugin(BasePlugin):
    plugin_id = "word_to_pdf"
    plugin_name = "Word 转 PDF"

    def __init__(self) -> None:
        self._widget: Optional[QWidget] = None
        self._files: list[Path] = []
        self._list: Optional[QListWidget] = None
        self._output_dir: Optional[QLineEdit] = None
        self._status_label: Optional[QLabel] = None
        self._progress_bar: Optional[QProgressBar] = None
        self._dir_radio: Optional[QRadioButton] = None
        self._file_radio: Optional[QRadioButton] = None
        self._btn_convert: Optional[QPushButton] = None
        self._btn_cancel: Optional[QPushButton] = None
        self._btn_open_dir: Optional[QPushButton] = None
        self._btn_open_file: Optional[QPushButton] = None
        self._last_output_dir: Optional[Path] = None
        self._spinner: Optional[ButtonSpinner] = None
        self._config = ConfigManager()
        self._worker: Optional[ConvertWorker] = None

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
        src_lay = QVBoxLayout(src_group)
        src_lay.setContentsMargins(12, 10, 12, 8)
        src_lay.setSpacing(6)

        mode_row = QHBoxLayout()
        self._dir_radio = QRadioButton("目录（自动筛选 Word）")
        self._dir_radio.setChecked(True)
        self._file_radio = QRadioButton("多选文件")
        mode_row.addWidget(self._dir_radio)
        mode_row.addWidget(self._file_radio)
        mode_row.addStretch()

        btn_browse = QPushButton("📂 浏览")
        btn_browse.setObjectName("primary")
        btn_browse.setFixedHeight(30)
        btn_browse.clicked.connect(self._on_browse)
        mode_row.addWidget(btn_browse)
        src_lay.addLayout(mode_row)

        top_row.addWidget(src_group, 1)

        out_group = QGroupBox("输出设置")
        out_lay = QVBoxLayout(out_group)
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

        top_row.addWidget(out_group, 1)
        root.addLayout(top_row)

        list_group = QGroupBox("文件列表")
        list_lay = QVBoxLayout(list_group)
        list_lay.setContentsMargins(12, 10, 12, 8)
        list_lay.setSpacing(6)

        self._list = QListWidget()
        self._list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        list_lay.addWidget(self._list, 1)

        sort_row = QHBoxLayout()
        btn_remove = QPushButton("🗑 移除选中")
        btn_remove.setObjectName("danger")
        btn_remove.setFixedHeight(28)
        btn_remove.clicked.connect(self._on_remove_selected)
        sort_row.addWidget(btn_remove)

        btn_clear = QPushButton("清空")
        btn_clear.setFixedHeight(28)
        btn_clear.clicked.connect(self._on_clear)
        sort_row.addWidget(btn_clear)

        sort_row.addStretch()
        list_lay.addLayout(sort_row)
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
        if self._dir_radio and self._dir_radio.isChecked():
            d = QFileDialog.getExistingDirectory(None, "选择目录", last_dir)
            if d:
                self._config.set_path("word_to_pdf", "source_dir", d)
                self._files = sorted(
                    Path(d).rglob("*.docx"), key=lambda p: p.name
                )
                self._refresh_list()
                self._set_status(f"已加载 {len(self._files)} 个 Word 文件")
        else:
            files, _ = QFileDialog.getOpenFileNames(None, "选择 Word", last_dir, "Word (*.docx)")
            if files:
                self._files = [Path(f) for f in files]
                self._refresh_list()
                self._set_status(f"已加载 {len(self._files)} 个 Word 文件")

    def _on_browse_output_dir(self) -> None:
        last_dir = self._config.get_path("word_to_pdf", "output_dir")
        d = QFileDialog.getExistingDirectory(None, "选择输出目录", last_dir)
        if d and self._output_dir:
            self._config.set_path("word_to_pdf", "output_dir", d)
            self._output_dir.setText(d)

    def _on_clear(self) -> None:
        self._files.clear()
        if self._list:
            self._list.clear()
        self._set_status("已清空")
        self._hide_result_buttons()

    def _refresh_list(self) -> None:
        if not self._list:
            return
        self._list.clear()
        for f in self._files:
            item = QListWidgetItem(f"📄  {f.name}    ({f.parent})")
            item.setData(Qt.ItemDataRole.UserRole, str(f))
            self._list.addItem(item)
        self._hide_result_buttons()

    def _on_remove_selected(self) -> None:
        if not self._list:
            return
        for idx in sorted(self._list.selectedIndexes(), reverse=True):
            r = idx.row()
            self._list.takeItem(r)
            self._files.pop(r)
        self._set_status(f"剩余 {len(self._files)} 个文件")

    def _on_convert(self) -> None:
        if len(self._files) == 0:
            self._set_status("⚠️ 请先添加 Word 文件")
            return

        if self._worker is not None:
            self._set_status("⚠️ 正在转换中，请等待")
            return

        output_dir_str = self._output_dir.text().strip() if self._output_dir else ""
        output_dir = Path(output_dir_str) if output_dir_str else self._files[0].parent

        if self._spinner:
            self._spinner.start()
        if self._btn_convert:
            self._btn_convert.setVisible(False)
        if self._btn_cancel:
            self._btn_cancel.setVisible(True)
        if self._progress_bar:
            self._progress_bar.setVisible(True)
            self._progress_bar.setRange(0, len(self._files))
            self._progress_bar.setValue(0)
        self._hide_result_buttons()

        self._worker = ConvertWorker()
        self._worker.set_task(self._files, output_dir)

        thread = QThread()
        self._worker.moveToThread(thread)

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
                self._set_status(
                    f"⚠️ 成功 {success_count} 个，失败 {fail_count} 个"
                )

            if success_count > 0:
                if self._btn_open_dir:
                    self._btn_open_dir.setVisible(True)
                if self._btn_open_file:
                    self._btn_open_file.setVisible(True)

            thread.quit()

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
            thread.quit()

        self._worker.progress_updated.connect(on_progress)
        self._worker.finished.connect(on_finished)
        self._worker.error.connect(on_error)

        thread.started.connect(self._worker.run)
        thread.start()

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
