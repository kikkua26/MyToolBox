"""批量改后缀插件：选择目录或多选文件，将指定后缀批量改为新后缀。"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.base_plugin import BasePlugin
from app.utils.logger import get_logger
from app.utils.ui_helpers import ButtonSpinner, open_in_file_manager

logger = get_logger("BatchRenamePlugin")


class BatchRenamePlugin(BasePlugin):
    plugin_id = "batch_rename"
    plugin_name = "批量改后缀"

    def __init__(self) -> None:
        self._widget: Optional[QWidget] = None
        self._files: list[Path] = []
        self._table: Optional[QTableWidget] = None
        self._src_ext: Optional[QLineEdit] = None
        self._dst_ext: Optional[QLineEdit] = None
        self._progress: Optional[QProgressBar] = None
        self._status_label: Optional[QLabel] = None
        self._dir_radio: Optional[QRadioButton] = None
        self._file_radio: Optional[QRadioButton] = None
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
        src_group = QGroupBox("文件来源")
        src_lay = QVBoxLayout(src_group)
        src_lay.setContentsMargins(12, 10, 12, 8)
        src_lay.setSpacing(6)

        mode_row = QHBoxLayout()
        self._dir_radio = QRadioButton("目录")
        self._dir_radio.setChecked(True)
        self._file_radio = QRadioButton("文件")
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

        # 右：后缀
        ext_group = QGroupBox("后缀设置")
        ext_lay = QHBoxLayout(ext_group)
        ext_lay.setContentsMargins(12, 10, 12, 8)
        ext_lay.setSpacing(8)

        ext_lay.addWidget(QLabel("从"))
        self._src_ext = QLineEdit()
        self._src_ext.setPlaceholderText(".txt")
        self._src_ext.setFixedWidth(100)
        self._src_ext.setFixedHeight(30)
        ext_lay.addWidget(self._src_ext)

        ext_lay.addWidget(QLabel("→"))

        self._dst_ext = QLineEdit()
        self._dst_ext.setPlaceholderText(".md")
        self._dst_ext.setFixedWidth(100)
        self._dst_ext.setFixedHeight(30)
        ext_lay.addWidget(self._dst_ext)

        btn_filter = QPushButton("筛选")
        btn_filter.setFixedHeight(30)
        btn_filter.clicked.connect(self._on_filter)
        ext_lay.addWidget(btn_filter)

        ext_lay.addStretch()
        top_row.addWidget(ext_group, 1)

        root.addLayout(top_row)

        # 文件列表
        self._table = QTableWidget(0, 3)
        self._table.setHorizontalHeaderLabels(["文件名", "路径", "状态"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setVisible(False)
        root.addWidget(self._table, 1)

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
        return w

    def get_control_widget(self) -> Optional[QWidget]:
        return None

    # ── 浏览 ─────────────────────────────────────────────

    def _on_browse(self) -> None:
        if self._dir_radio and self._dir_radio.isChecked():
            d = QFileDialog.getExistingDirectory(None, "选择目录")
            if d:
                self._load_directory(Path(d))
        else:
            files, _ = QFileDialog.getOpenFileNames(None, "选择文件")
            if files:
                self._load_files([Path(f) for f in files])

    def _load_directory(self, directory: Path) -> None:
        self._files = sorted(
            [p for p in directory.rglob("*") if p.is_file()],
            key=lambda p: p.name,
        )
        self._refresh_table()
        self._set_status(f"已加载目录: {directory}，共 {len(self._files)} 个文件")

    def _load_files(self, files: list[Path]) -> None:
        self._files = sorted(files, key=lambda p: p.name)
        self._refresh_table()
        self._set_status(f"已加载 {len(self._files)} 个文件")

    def _on_clear(self) -> None:
        self._files.clear()
        self._refresh_table()
        self._set_status("已清空")
        if self._btn_open_dir:
            self._btn_open_dir.setVisible(False)

    def _on_filter(self) -> None:
        ext = self._src_ext.text().strip() if self._src_ext else ""
        if not ext:
            self._set_status("⚠️ 请先填写源后缀")
            return
        if not ext.startswith("."):
            ext = "." + ext
        before = len(self._files)
        self._files = [f for f in self._files if f.suffix.lower() == ext.lower()]
        self._refresh_table()
        self._set_status(f"已筛选 {ext}: {before} → {len(self._files)}")

    def _refresh_table(self) -> None:
        if not self._table:
            return
        self._table.setRowCount(len(self._files))
        for i, f in enumerate(self._files):
            self._table.setItem(i, 0, QTableWidgetItem(f.name))
            self._table.setItem(i, 1, QTableWidgetItem(str(f.parent)))
            self._table.setItem(i, 2, QTableWidgetItem("待处理"))
        if self._progress:
            self._progress.setValue(0)

    # ── 预览 ─────────────────────────────────────────────

    def _on_preview(self) -> None:
        src = self._src_ext.text().strip()
        dst = self._dst_ext.text().strip()
        if not src or not dst:
            self._set_status("⚠️ 请填写源后缀和目标后缀")
            return
        if not src.startswith("."):
            src = "." + src
        if not dst.startswith("."):
            dst = "." + dst

        matched = [f for f in self._files if f.suffix.lower() == src.lower()]
        if not matched:
            self._set_status(f"没有找到 {src} 文件")
            return

        for i, f in enumerate(self._files):
            if f.suffix.lower() == src.lower():
                self._table.setItem(i, 2, QTableWidgetItem(f"{f.name} → {f.stem}{dst}"))
            else:
                self._table.setItem(i, 2, QTableWidgetItem("跳过"))

        self._set_status(f"预览: {len(matched)} 个文件将被重命名")

    # ── 执行 ─────────────────────────────────────────────

    def _on_execute(self) -> None:
        src = self._src_ext.text().strip() if self._src_ext else ""
        dst = self._dst_ext.text().strip() if self._dst_ext else ""
        if not src or not dst:
            self._set_status("⚠️ 请填写源后缀和目标后缀")
            return
        if not src.startswith("."):
            src = "." + src
        if not dst.startswith("."):
            dst = "." + dst

        matched = [(i, f) for i, f in enumerate(self._files) if f.suffix.lower() == src.lower()]
        if not matched:
            self._set_status(f"没有找到 {src} 文件")
            return

        reply = QMessageBox.question(
            None, "确认",
            f"即将重命名 {len(matched)} 个文件 ({src} → {dst})，确认？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        if self._spinner_exec:
            self._spinner_exec.start()

        success = errors = 0
        total = len(matched)

        for idx, (row, f) in enumerate(matched):
            new_path = f.parent / (f.stem + dst)
            try:
                if new_path.exists():
                    raise FileExistsError("目标文件已存在")
                f.rename(new_path)
                self._files[row] = new_path
                self._table.setItem(row, 0, QTableWidgetItem(new_path.name))
                self._table.setItem(row, 2, QTableWidgetItem("✅"))
                success += 1
                self._last_output_dir = new_path.parent
            except Exception as e:
                self._table.setItem(row, 2, QTableWidgetItem(f"❌ {e}"))
                errors += 1
                logger.exception("重命名失败: %s", f)

            if self._progress:
                self._progress.setValue(int((idx + 1) / total * 100))

        if self._spinner_exec:
            self._spinner_exec.stop("🚀 执行重命名")

        self._set_status(f"完成: {success} 成功, {errors} 失败")

        if self._btn_open_dir and self._last_output_dir:
            self._btn_open_dir.setVisible(True)

    # ── 打开目录 ─────────────────────────────────────────

    def _on_open_dir(self) -> None:
        if self._last_output_dir:
            open_in_file_manager(self._last_output_dir)

    def _set_status(self, text: str) -> None:
        if self._status_label:
            self._status_label.setText(text)
