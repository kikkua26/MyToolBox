"""PDF 检查插件：支持关键词搜索、批量搜索、PDF预览和高亮显示。"""

from __future__ import annotations

import fitz
from pathlib import Path
from typing import Optional, List, Tuple, Dict

from PySide6.QtCore import Qt, QRectF, QPoint, Signal, QSize
from PySide6.QtGui import QPixmap, QPainter, QColor, QBrush, QPen
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
    QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QScrollArea, QFileDialog, QTextEdit, QSplitter,
    QCheckBox, QMessageBox, QSizePolicy, QSpinBox
)

from app.base_plugin import BasePlugin
from app.config_manager import ConfigManager
from app.utils.logger import get_logger

logger = get_logger("PdfSearchPlugin")


class SearchResult:
    def __init__(self, page_num: int, text: str, rect: fitz.Rect, keyword: str, context_before: str = "", context_after: str = ""):
        self.page_num = page_num
        self.text = text
        self.rect = rect
        self.keyword = keyword
        self.context_before = context_before
        self.context_after = context_after
    
    def __str__(self):
        return f"Page {self.page_num}: {self.context_before}[{self.keyword}]{self.context_after}"


class PdfCanvas(QWidget):
    page_changed = Signal(int)
    
    def __init__(self) -> None:
        super().__init__()
        self._pdf_doc: Optional[fitz.Document] = None
        self._current_page = 0
        self._pixmap: Optional[QPixmap] = None
        self._search_highlights: Dict[int, List[fitz.Rect]] = {}
        self._scale = 1.0
        self._offset = QPoint(0, 0)
        self._is_dragging = False
        self._drag_start = QPoint(0, 0)
        self._base_matrix = fitz.Matrix(2.0, 2.0)
        self.setMinimumSize(400, 500)
        self.setMouseTracking(True)
    
    def load_pdf(self, filepath: str) -> Tuple[bool, str]:
        try:
            self._pdf_doc = fitz.open(filepath)
            self._current_page = 0
            self._search_highlights = {}
            self._scale = 1.0
            self._offset = QPoint(0, 0)
            self.render_page()
            return True, ""
        except fitz.FileDataError as e:
            logger.exception("加载PDF失败")
            return False, f"PDF文件格式错误或已损坏: {str(e)}"
        except FileNotFoundError:
            logger.exception("文件未找到")
            return False, "文件不存在，请检查路径"
        except Exception as e:
            logger.exception("加载PDF失败")
            return False, f"加载失败: {str(e)}"
    
    def render_page(self) -> None:
        if not self._pdf_doc:
            return
        
        page = self._pdf_doc[self._current_page]
        pix = page.get_pixmap(matrix=self._base_matrix)
        
        img_data = pix.tobytes("png")
        self._pixmap = QPixmap()
        self._pixmap.loadFromData(img_data)
        self._offset = QPoint(0, 0)
        self.update()
        self.page_changed.emit(self._current_page + 1)
    
    def set_page(self, page_num: int) -> None:
        if self._pdf_doc and 0 <= page_num < len(self._pdf_doc):
            self._current_page = page_num
            self.render_page()
    
    def get_current_page(self) -> int:
        return self._current_page
    
    def get_page_count(self) -> int:
        return len(self._pdf_doc) if self._pdf_doc else 0
    
    def add_highlights(self, page_num: int, rects: List[fitz.Rect]) -> None:
        if page_num in self._search_highlights:
            self._search_highlights[page_num].extend(rects)
        else:
            self._search_highlights[page_num] = list(rects)
        self.update()
    
    def clear_highlights(self) -> None:
        self._search_highlights = {}
        self.update()
    
    def scroll_to_highlight(self, page_num: int, rect: fitz.Rect) -> None:
        self.set_page(page_num)
        self._highlight_rect = rect
        self.center_on_rect(rect)
        self.update()
    
    def center_on_rect(self, rect: fitz.Rect) -> None:
        if not self._pixmap:
            return
        
        container_width = self.width()
        container_height = self.height()
        
        pix_width = self._pixmap.width()
        pix_height = self._pixmap.height()
        
        scale_x = container_width / pix_width if pix_width > 0 else 1.0
        scale_y = container_height / pix_height if pix_height > 0 else 1.0
        fit_scale = min(scale_x, scale_y)
        final_scale = fit_scale * self._scale
        
        base_scale = self._base_matrix.a
        matrix = fitz.Matrix(final_scale * base_scale, final_scale * base_scale)
        scaled = rect * matrix
        rect_center_x = (scaled.x0 + scaled.x1) / 2
        rect_center_y = (scaled.y0 + scaled.y1) / 2
        
        target_x = container_width / 2 - rect_center_x
        target_y = container_height / 2 - rect_center_y
        
        self._offset = QPoint(int(target_x), int(target_y))
        self._clamp_offset()
    
    def _clamp_offset(self) -> None:
        if not self._pixmap:
            return
        
        container_width = self.width()
        container_height = self.height()
        
        pix_width = self._pixmap.width()
        pix_height = self._pixmap.height()
        
        scale_x = container_width / pix_width if pix_width > 0 else 1.0
        scale_y = container_height / pix_height if pix_height > 0 else 1.0
        fit_scale = min(scale_x, scale_y)
        final_scale = fit_scale * self._scale
        
        scaled_width = pix_width * final_scale
        scaled_height = pix_height * final_scale
        
        max_x = max(0, scaled_width - container_width)
        max_y = max(0, scaled_height - container_height)
        
        self._offset.setX(max(-max_x, min(0, self._offset.x())))
        self._offset.setY(max(-max_y, min(0, self._offset.y())))
    
    def wheelEvent(self, event) -> None:
        if event.modifiers() == Qt.ControlModifier:
            delta = event.angleDelta().y()
            old_scale = self._scale
            
            if delta > 0:
                self._scale = min(self._scale + 0.1, 3.0)
            else:
                self._scale = max(self._scale - 0.1, 0.5)
            
            if self._scale != old_scale:
                cursor_pos = event.position().toPoint()
                pix_width = self._pixmap.width() if self._pixmap else 1
                
                scale_x = self.width() / pix_width if pix_width > 0 else 1.0
                fit_scale = min(scale_x, self.height() / (self._pixmap.height() if self._pixmap else 1))
                
                scale_diff = self._scale / old_scale
                self._offset.setX(int((self._offset.x() - cursor_pos.x()) * scale_diff + cursor_pos.x()))
                self._offset.setY(int((self._offset.y() - cursor_pos.y()) * scale_diff + cursor_pos.y()))
                
                self._clamp_offset()
                self.update()
        else:
            delta = event.angleDelta().y()
            if delta < 0 and self._current_page < self.get_page_count() - 1:
                self.set_page(self._current_page + 1)
            elif delta > 0 and self._current_page > 0:
                self.set_page(self._current_page - 1)
    
    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            self._drag_start = event.pos() - self._offset
            self.setCursor(Qt.ClosedHandCursor)
    
    def mouseMoveEvent(self, event) -> None:
        if self._is_dragging:
            self._offset = event.pos() - self._drag_start
            self._clamp_offset()
            self.update()
    
    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self._is_dragging = False
            self.setCursor(Qt.ArrowCursor)
    
    def get_scale(self) -> float:
        return self._scale
    
    def set_scale(self, scale: float) -> None:
        self._scale = max(0.5, min(scale, 3.0))
        self._clamp_offset()
        self.update()
    
    def reset_scale(self) -> None:
        self._scale = 1.0
        self._offset = QPoint(0, 0)
        self.update()
    
    def sizeHint(self) -> QSize:
        if self._pixmap:
            return QSize(self._pixmap.width(), self._pixmap.height())
        return super().sizeHint()
    
    def paintEvent(self, event) -> None:
        if not self._pixmap:
            painter = QPainter(self)
            painter.fillRect(self.rect(), QColor(245, 245, 245))
            painter.drawText(self.rect(), Qt.AlignCenter, "请选择PDF文件")
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        
        container_width = self.width()
        container_height = self.height()
        
        pix_width = self._pixmap.width()
        pix_height = self._pixmap.height()
        
        scale_x = container_width / pix_width if pix_width > 0 else 1.0
        scale_y = container_height / pix_height if pix_height > 0 else 1.0
        
        fit_scale = min(scale_x, scale_y)
        final_scale = fit_scale * self._scale
        
        scaled_pixmap = self._pixmap.scaled(
            int(pix_width * final_scale),
            int(pix_height * final_scale),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        painter.fillRect(0, 0, container_width, container_height, QColor(245, 245, 245))
        painter.drawPixmap(self._offset.x(), self._offset.y(), scaled_pixmap)
        
        if self._current_page in self._search_highlights:
            rects = self._search_highlights[self._current_page]
            base_scale = self._base_matrix.a
            matrix = fitz.Matrix(final_scale * base_scale, final_scale * base_scale)
            for r in rects:
                scaled = r * matrix
                x0 = self._offset.x() + scaled.x0
                y0 = self._offset.y() + scaled.y0
                x1 = self._offset.x() + scaled.x1
                y1 = self._offset.y() + scaled.y1
                painter.fillRect(x0, y0, x1 - x0, y1 - y0, 
                               QBrush(QColor(255, 255, 0, 120)))
                painter.setPen(QPen(QColor(255, 100, 100, 200), max(1, int(final_scale))))
                painter.drawRect(x0, y0, x1 - x0, y1 - y0)


class PdfSearchPlugin(BasePlugin):
    plugin_id = "pdf_search"
    plugin_name = "PDF 检查"

    def __init__(self) -> None:
        self._widget: Optional[QWidget] = None
        self._pdf_canvas: Optional[PdfCanvas] = None
        self._search_results: List[SearchResult] = []
        self._result_list: Optional[QListWidget] = None
        self._keyword_input: Optional[QLineEdit] = None
        self._keyword_list: Optional[QListWidget] = None
        self._file_label: Optional[QLabel] = None
        self._page_label: Optional[QLabel] = None
        self._status_label: Optional[QLabel] = None
        self._scale_label: Optional[QLabel] = None
        self._context_spin: Optional[QSpinBox] = None
        self._config = ConfigManager()
    
    def get_widget(self) -> QWidget:
        if self._widget is not None:
            return self._widget

        w = QWidget()
        root = QHBoxLayout(w)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)

        left_panel = self._create_left_panel()
        middle_panel = self._create_middle_panel()
        right_panel = self._create_right_panel()

        splitter.addWidget(left_panel)
        splitter.addWidget(middle_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([280, 600, 320])

        root.addWidget(splitter)
        self._widget = w
        return w
    
    def _create_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        group = QGroupBox("🔍 关键词组")
        group_layout = QVBoxLayout(group)
        group_layout.setContentsMargins(12, 10, 12, 8)
        group_layout.setSpacing(6)

        input_row = QHBoxLayout()
        self._keyword_input = QLineEdit()
        self._keyword_input.setPlaceholderText("输入关键词")
        self._keyword_input.setFixedHeight(30)
        input_row.addWidget(self._keyword_input)
        
        add_btn = QPushButton("➕ 添加")
        add_btn.setFixedSize(60, 30)
        add_btn.clicked.connect(self._add_keyword)
        input_row.addWidget(add_btn)
        group_layout.addLayout(input_row)

        self._keyword_list = QListWidget()
        self._keyword_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        group_layout.addWidget(self._keyword_list)

        btn_row = QHBoxLayout()
        del_btn = QPushButton("🗑 删除选中")
        del_btn.setFixedHeight(28)
        del_btn.clicked.connect(self._delete_keyword)
        btn_row.addWidget(del_btn)
        
        clear_btn = QPushButton("清空")
        clear_btn.setFixedHeight(28)
        clear_btn.clicked.connect(self._clear_keywords)
        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        group_layout.addLayout(btn_row)
        layout.addWidget(group)

        context_group = QGroupBox("📝 前后文设置")
        context_layout = QVBoxLayout(context_group)
        context_layout.setContentsMargins(12, 10, 12, 8)
        context_layout.setSpacing(6)

        context_row = QHBoxLayout()
        context_row.addWidget(QLabel("前后文字数:"))
        self._context_spin = QSpinBox()
        self._context_spin.setRange(0, 50)
        self._context_spin.setValue(8)
        self._context_spin.setFixedWidth(80)
        context_row.addWidget(self._context_spin)
        context_row.addStretch()
        context_layout.addLayout(context_row)
        layout.addWidget(context_group)

        file_group = QGroupBox("📂 PDF文件")
        file_layout = QVBoxLayout(file_group)
        file_layout.setContentsMargins(12, 10, 12, 8)
        file_layout.setSpacing(6)

        self._file_label = QLabel("未选择文件")
        self._file_label.setObjectName("subtitle")
        self._file_label.setWordWrap(True)
        file_layout.addWidget(self._file_label)

        browse_btn = QPushButton("📂 选择PDF")
        browse_btn.setObjectName("primary")
        browse_btn.setFixedHeight(30)
        browse_btn.clicked.connect(self._browse_pdf)
        file_layout.addWidget(browse_btn)
        layout.addWidget(file_group)

        search_btn = QPushButton("🚀 开始搜索")
        search_btn.setObjectName("primary")
        search_btn.setFixedHeight(36)
        search_btn.clicked.connect(self._run_search)
        layout.addWidget(search_btn)

        self._status_label = QLabel("就绪")
        self._status_label.setObjectName("subtitle")
        layout.addWidget(self._status_label)

        layout.addStretch()
        return panel
    
    def _create_middle_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background-color: white;")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(12, 8, 12, 8)
        toolbar.setSpacing(8)
        
        prev_btn = QPushButton("⬅ 上一页")
        prev_btn.setFixedHeight(28)
        prev_btn.clicked.connect(self._prev_page)
        toolbar.addWidget(prev_btn)
        
        self._page_label = QLabel("0 / 0")
        self._page_label.setObjectName("subtitle")
        toolbar.addWidget(self._page_label)
        
        next_btn = QPushButton("下一页 ➡")
        next_btn.setFixedHeight(28)
        next_btn.clicked.connect(self._next_page)
        toolbar.addWidget(next_btn)
        
        toolbar.addStretch()
        
        zoom_out_btn = QPushButton("🔍 -")
        zoom_out_btn.setFixedSize(36, 28)
        zoom_out_btn.clicked.connect(self._zoom_out)
        toolbar.addWidget(zoom_out_btn)
        
        self._scale_label = QLabel("100%")
        self._scale_label.setFixedWidth(50)
        self._scale_label.setAlignment(Qt.AlignCenter)
        toolbar.addWidget(self._scale_label)
        
        zoom_in_btn = QPushButton("🔍 +")
        zoom_in_btn.setFixedSize(36, 28)
        zoom_in_btn.clicked.connect(self._zoom_in)
        toolbar.addWidget(zoom_in_btn)
        
        reset_btn = QPushButton("🔄 重置")
        reset_btn.setFixedHeight(28)
        reset_btn.clicked.connect(self._reset_zoom)
        toolbar.addWidget(reset_btn)
        
        layout.addLayout(toolbar)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #f5f5f5; }")
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self._pdf_canvas = PdfCanvas()
        self._pdf_canvas.page_changed.connect(self._update_page_label)
        scroll_area.setWidget(self._pdf_canvas)
        layout.addWidget(scroll_area, 1)

        return panel
    
    def _create_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        title = QLabel("📋 搜索结果")
        title.setObjectName("sectionTitle")
        layout.addWidget(title)

        self._result_list = QListWidget()
        self._result_list.itemClicked.connect(self._on_result_click)
        self._result_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
        """)
        layout.addWidget(self._result_list)

        stats_label = QLabel("找到 0 个匹配")
        stats_label.setObjectName("subtitle")
        layout.addWidget(stats_label)
        self._stats_label = stats_label

        return panel
    
    def get_control_widget(self) -> Optional[QWidget]:
        return None
    
    def _browse_pdf(self) -> None:
        last_dir = self._config.get_path("pdf_search", "source_dir")
        files, _ = QFileDialog.getOpenFileNames(None, "选择PDF", last_dir, "PDF (*.pdf)")
        if files:
            filepath = files[0]
            self._config.set_path("pdf_search", "source_dir", str(Path(filepath).parent))
            self._file_label.setText(f"📄 {Path(filepath).name}")
            
            if self._pdf_canvas:
                success, msg = self._pdf_canvas.load_pdf(filepath)
                if success:
                    self._set_status(f"已加载 PDF，共 {self._pdf_canvas.get_page_count()} 页")
                else:
                    self._set_status(f"❌ {msg}")
    
    def _add_keyword(self) -> None:
        keyword = self._keyword_input.text().strip()
        if keyword and self._keyword_list:
            items = [self._keyword_list.item(i).text() for i in range(self._keyword_list.count())]
            if keyword not in items:
                item = QListWidgetItem(f"🔤 {keyword}")
                item.setData(Qt.ItemDataRole.UserRole, keyword)
                self._keyword_list.addItem(item)
                self._keyword_input.clear()
                self._set_status(f"已添加关键词: {keyword}")
    
    def _delete_keyword(self) -> None:
        if self._keyword_list:
            for item in reversed(self._keyword_list.selectedItems()):
                self._keyword_list.takeItem(self._keyword_list.row(item))
    
    def _clear_keywords(self) -> None:
        if self._keyword_list:
            self._keyword_list.clear()
    
    def _run_search(self) -> None:
        if not self._pdf_canvas or not self._pdf_canvas.get_page_count():
            self._set_status("⚠️ 请先加载PDF")
            return
        
        keywords = []
        if self._keyword_list:
            for i in range(self._keyword_list.count()):
                keyword = self._keyword_list.item(i).data(Qt.ItemDataRole.UserRole)
                if keyword:
                    keywords.append(keyword)
        
        if not keywords:
            self._set_status("⚠️ 请先添加关键词")
            return
        
        context_length = self._context_spin.value() if self._context_spin else 8
        
        self._search_results = []
        if self._result_list:
            self._result_list.clear()
        
        if self._pdf_canvas:
            self._pdf_canvas.clear_highlights()
        
        doc = self._pdf_canvas._pdf_doc
        highlights_by_page: Dict[int, List[fitz.Rect]] = {}
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            words = page.get_text("words")
            
            for keyword in keywords:
                rects = page.search_for(keyword)
                for rect in rects:
                    context_before, context_after = self._extract_context(page, rect, context_length)
                    result = SearchResult(page_num, keyword, rect, keyword, context_before, context_after)
                    self._search_results.append(result)
                    
                    if page_num not in highlights_by_page:
                        highlights_by_page[page_num] = []
                    highlights_by_page[page_num].append(rect)
        
        for page_num, rects in highlights_by_page.items():
            if self._pdf_canvas:
                self._pdf_canvas.add_highlights(page_num, rects)
        
        if self._result_list:
            self._result_list.clear()
            for result in self._search_results:
                page_text = f"📄 第{result.page_num + 1}页:"
                if result.context_before or result.context_after:
                    context_text = f"...{result.context_before}<span style='background-color: #FFEB3B; color: #C62828; font-weight: bold;'>{result.keyword}</span>{result.context_after}..."
                else:
                    context_text = f"<span style='background-color: #FFEB3B; color: #C62828; font-weight: bold;'>{result.keyword}</span>"
                
                item_widget = QWidget()
                item_layout = QVBoxLayout(item_widget)
                item_layout.setContentsMargins(4, 4, 4, 4)
                
                page_label = QLabel(page_text)
                page_label.setStyleSheet("font-size: 12px; color: #666;")
                item_layout.addWidget(page_label)
                
                context_label = QLabel()
                context_label.setTextFormat(Qt.RichText)
                context_label.setText(context_text)
                context_label.setStyleSheet("font-size: 13px;")
                context_label.setWordWrap(True)
                item_layout.addWidget(context_label)
                
                item = QListWidgetItem()
                item.setData(Qt.ItemDataRole.UserRole, result)
                self._result_list.addItem(item)
                self._result_list.setItemWidget(item, item_widget)
                item.setSizeHint(item_widget.sizeHint())
        
        if self._stats_label:
            self._stats_label.setText(f"找到 {len(self._search_results)} 个匹配")
        
        self._set_status(f"✅ 搜索完成，找到 {len(self._search_results)} 个匹配")
    
    def _extract_context(self, page: fitz.Page, rect: fitz.Rect, context_length: int) -> Tuple[str, str]:
        try:
            words = page.get_text("words")
            keyword_center_x = (rect.x0 + rect.x1) / 2
            keyword_center_y = (rect.y0 + rect.y1) / 2
            
            found_idx = -1
            for i, word in enumerate(words):
                word_rect = fitz.Rect(word[:4])
                if word_rect.contains(fitz.Point(keyword_center_x, keyword_center_y)):
                    found_idx = i
                    break
            
            if found_idx == -1:
                return "", ""
            
            start_idx = max(0, found_idx - context_length)
            end_idx = min(len(words), found_idx + context_length + 1)
            
            before_words = words[start_idx:found_idx]
            after_words = words[found_idx + 1:end_idx]
            
            context_before = "".join([w[4] for w in before_words])[-context_length:]
            context_after = "".join([w[4] for w in after_words])[:context_length]
            
            return context_before, context_after
        except Exception as e:
            logger.exception("提取上下文失败")
            return "", ""
    
    def _extract_context_from_words(self, words: List[List], target_word: List, context_length: int) -> Tuple[str, str]:
        try:
            found_idx = -1
            for i, word in enumerate(words):
                if word[4] == target_word[4] and abs(word[0] - target_word[0]) < 1 and abs(word[1] - target_word[1]) < 1:
                    found_idx = i
                    break
            
            if found_idx == -1:
                return "", ""
            
            start_idx = max(0, found_idx - context_length)
            end_idx = min(len(words), found_idx + context_length + 1)
            
            before_words = words[start_idx:found_idx]
            after_words = words[found_idx + 1:end_idx]
            
            context_before = "".join([w[4] for w in before_words])[-context_length:]
            context_after = "".join([w[4] for w in after_words])[:context_length]
            
            return context_before, context_after
        except Exception as e:
            logger.exception("提取上下文失败")
            return "", ""
    
    def _on_result_click(self, item: QListWidgetItem) -> None:
        result = item.data(Qt.ItemDataRole.UserRole)
        if result and self._pdf_canvas:
            self._pdf_canvas.scroll_to_highlight(result.page_num, result.rect)
    
    def _prev_page(self) -> None:
        if self._pdf_canvas:
            current = self._pdf_canvas.get_current_page()
            if current > 0:
                self._pdf_canvas.set_page(current - 1)
    
    def _next_page(self) -> None:
        if self._pdf_canvas:
            current = self._pdf_canvas.get_current_page()
            total = self._pdf_canvas.get_page_count()
            if current < total - 1:
                self._pdf_canvas.set_page(current + 1)
    
    def _update_page_label(self, page_num: int) -> None:
        if self._pdf_canvas and self._page_label:
            total = self._pdf_canvas.get_page_count()
            self._page_label.setText(f"{page_num} / {total}")
    
    def _set_status(self, text: str) -> None:
        if self._status_label:
            self._status_label.setText(text)
    
    def _zoom_in(self) -> None:
        if self._pdf_canvas:
            current_scale = self._pdf_canvas.get_scale()
            self._pdf_canvas.set_scale(current_scale + 0.1)
            self._update_scale_label()
    
    def _zoom_out(self) -> None:
        if self._pdf_canvas:
            current_scale = self._pdf_canvas.get_scale()
            self._pdf_canvas.set_scale(current_scale - 0.1)
            self._update_scale_label()
    
    def _reset_zoom(self) -> None:
        if self._pdf_canvas:
            self._pdf_canvas.reset_scale()
            self._update_scale_label()
    
    def _update_scale_label(self) -> None:
        if self._pdf_canvas and self._scale_label:
            scale = int(self._pdf_canvas.get_scale() * 100)
            self._scale_label.setText(f"{scale}%")
