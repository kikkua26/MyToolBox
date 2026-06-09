"""PDF 合并插件：选择多个 PDF，拖拽排序后合并输出。"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from app.base_plugin import BasePlugin
from app.config_manager import ConfigManager
from app.utils.logger import get_logger
from app.utils.ui_helpers import ButtonSpinner, open_in_file_manager, open_file

logger = get_logger("PdfMergePlugin")


class PdfMergePlugin(BasePlugin):
    plugin_id = "pdf_merge"
    plugin_name = "PDF 合并"

    def __init__(self) -> None:
        self._widget: Optional[QWidget] = None
        self._files: list[Path] = []
        self._list: Optional[QListWidget] = None
        self._output_dir: Optional[QLineEdit] = None
        self._output_name: Optional[QLineEdit] = None
        self._status_label: Optional[QLabel] = None
        self._dir_radio: Optional[QRadioButton] = None
        self._file_radio: Optional[QRadioButton] = None
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

        src_group = QGroupBox("文件来源")
        src_lay = QVBoxLayout(src_group)
        src_lay.setContentsMargins(12, 10, 12, 8)
        src_lay.setSpacing(6)

        mode_row = QHBoxLayout()
        self._dir_radio = QRadioButton("目录（自动筛选 PDF）")
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

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("文件名:"))
        self._output_name = QLineEdit()
        self._output_name.setPlaceholderText("00合并版-文件夹名.pdf")
        self._output_name.setFixedHeight(30)
        name_row.addWidget(self._output_name, 1)
        out_lay.addLayout(name_row)

        top_row.addWidget(out_group, 1)
        root.addLayout(top_row)

        # 文件列表
        list_group = QGroupBox("文件列表 · 拖拽调整顺序")
        list_lay = QVBoxLayout(list_group)
        list_lay.setContentsMargins(12, 10, 12, 8)
        list_lay.setSpacing(6)

        self._list = QListWidget()
        self._list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self._list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self._list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self._list.model().rowsMoved.connect(self._sync_order_from_list)
        list_lay.addWidget(self._list, 1)

        sort_row = QHBoxLayout()
        btn_up = QPushButton("⬆ 上移")
        btn_up.setFixedHeight(28)
        btn_up.clicked.connect(self._on_move_up)
        sort_row.addWidget(btn_up)

        btn_down = QPushButton("⬇ 下移")
        btn_down.setFixedHeight(28)
        btn_down.clicked.connect(self._on_move_down)
        sort_row.addWidget(btn_down)

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
        return w

    def get_control_widget(self) -> Optional[QWidget]:
        return None

    # ── 浏览 ─────────────────────────────────────────────

    def _on_browse(self) -> None:
        last_dir = self._config.get_path("pdf_merge", "source_dir")
        if self._dir_radio and self._dir_radio.isChecked():
            d = QFileDialog.getExistingDirectory(None, "选择目录", last_dir)
            if d:
                self._config.set_path("pdf_merge", "source_dir", d)
                self._files = sorted(Path(d).rglob("*.pdf"), key=lambda p: p.name)
                self._refresh_list()
                self._set_status(f"已加载 {len(self._files)} 个 PDF")
                self._update_default_output_name()
        else:
            files, _ = QFileDialog.getOpenFileNames(None, "选择 PDF", last_dir, "PDF (*.pdf)")
            if files:
                self._files = [Path(f) for f in files]
                self._refresh_list()
                self._set_status(f"已加载 {len(self._files)} 个 PDF")
                self._update_default_output_name()

    def _on_browse_output_dir(self) -> None:
        last_dir = self._config.get_path("pdf_merge", "output_dir")
        d = QFileDialog.getExistingDirectory(None, "选择输出目录", last_dir)
        if d and self._output_dir:
            self._config.set_path("pdf_merge", "output_dir", d)
            self._output_dir.setText(d)

    def _update_default_output_name(self) -> None:
        if self._files and self._output_name:
            parent_dir = self._files[0].parent
            parent_name = parent_dir.name
            default_name = f"00合并版-{parent_name}.pdf"
            self._output_name.setText(default_name)

    def _on_clear(self) -> None:
        self._files.clear()
        if self._list:
            self._list.clear()
        self._set_status("已清空")
        self._hide_result_buttons()

    # ── 列表 ─────────────────────────────────────────────

    def _refresh_list(self) -> None:
        if not self._list:
            return
        self._list.clear()
        for f in self._files:
            item = QListWidgetItem(f"📄  {f.name}    ({f.parent})")
            item.setData(Qt.ItemDataRole.UserRole, str(f))
            self._list.addItem(item)
        self._hide_result_buttons()

    def _sync_order_from_list(self) -> None:
        if not self._list:
            return
        new_order: list[Path] = []
        for i in range(self._list.count()):
            data = self._list.item(i).data(Qt.ItemDataRole.UserRole)
            if data:
                new_order.append(Path(data))
        self._files = new_order
        self._set_status(f"顺序已更新（{len(self._files)} 个文件）")

    def _on_move_up(self) -> None:
        if not self._list:
            return
        row = self._list.currentRow()
        if row <= 0:
            return
        item = self._list.takeItem(row)
        self._list.insertItem(row - 1, item)
        self._list.setCurrentRow(row - 1)
        self._files[row], self._files[row - 1] = self._files[row - 1], self._files[row]

    def _on_move_down(self) -> None:
        if not self._list:
            return
        row = self._list.currentRow()
        if row < 0 or row >= self._list.count() - 1:
            return
        item = self._list.takeItem(row)
        self._list.insertItem(row + 1, item)
        self._list.setCurrentRow(row + 1)
        self._files[row], self._files[row + 1] = self._files[row + 1], self._files[row]

    def _on_remove_selected(self) -> None:
        if not self._list:
            return
        for idx in sorted(self._list.selectedIndexes(), reverse=True):
            r = idx.row()
            self._list.takeItem(r)
            self._files.pop(r)
        self._set_status(f"剩余 {len(self._files)} 个文件")

    # ── 合并 ─────────────────────────────────────────────

    def _on_merge(self) -> None:
        if len(self._files) < 2:
            self._set_status("⚠️ 至少需要 2 个 PDF")
            return

        output_dir_str = self._output_dir.text().strip() if self._output_dir else ""
        output_name_str = self._output_name.text().strip() if self._output_name else "merged.pdf"
        if not output_name_str.lower().endswith(".pdf"):
            output_name_str += ".pdf"

        output_dir = Path(output_dir_str) if output_dir_str else self._files[0].parent
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

        try:
            from pypdf import PdfWriter

            writer = PdfWriter()
            for f in self._files:
                try:
                    writer.append(str(f))
                except Exception as e:
                    logger.exception("添加失败: %s", f)
                    if self._spinner:
                        self._spinner.stop("🚀 合并 PDF")
                    self._set_status(f"❌ 添加失败: {f.name}")
                    return

            output_dir.mkdir(parents=True, exist_ok=True)
            writer.write(str(output_path))
            writer.close()

            self._last_output_path = output_path

            if self._spinner:
                self._spinner.stop("🚀 合并 PDF")

            self._set_status(f"✅ 合并成功: {output_path}")

            if self._btn_open_dir:
                self._btn_open_dir.setVisible(True)
            if self._btn_open_file:
                self._btn_open_file.setVisible(True)

        except ImportError:
            if self._spinner:
                self._spinner.stop("🚀 合并 PDF")
            self._set_status("❌ 缺少 pypdf，请运行: pip install pypdf")
        except Exception as e:
            if self._spinner:
                self._spinner.stop("🚀 合并 PDF")
            self._set_status(f"❌ 合并失败: {e}")
            logger.exception("PDF 合并失败")

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
