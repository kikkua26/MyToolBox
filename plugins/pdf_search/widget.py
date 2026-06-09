"""PDF检查插件主组件：整合各子组件，管理整体布局和事件连接。"""

from __future__ import annotations

import fitz
from pathlib import Path
from typing import Optional, List

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QPushButton, QLabel,
    QScrollArea, QSizePolicy, QFileDialog
)

from app.base_plugin import BasePlugin
from app.config_manager import ConfigManager
from app.utils.logger import get_logger

from .components import PdfCanvas, ResultPanel, SearchResult
from .components.keyword_manager import KeywordManager

logger = get_logger("PdfSearchPlugin")


class PdfSearchPlugin(BasePlugin):
    plugin_id = "pdf_search"
    plugin_name = "PDF 检查"

    def __init__(self) -> None:
        self._widget: Optional[QWidget] = None
        self._pdf_canvas: Optional[PdfCanvas] = None
        self._keyword_panel: Optional[KeywordManager] = None
        self._result_panel: Optional[ResultPanel] = None
        self._search_results: List[SearchResult] = []
        self._page_label: Optional[QLabel] = None
        self._scale_label: Optional[QLabel] = None
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
        self._connect_signals()
        return w
    
    def _create_left_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._keyword_panel = KeywordManager(self._config)
        layout.addWidget(self._keyword_panel)

        file_group = self._create_file_group()
        layout.addWidget(file_group)

        return panel
    
    def _create_file_group(self) -> QWidget:
        from PySide6.QtWidgets import QGroupBox, QVBoxLayout
        
        group = QGroupBox("📂 PDF文件")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 10, 12, 8)
        layout.setSpacing(6)

        self._file_label = QLabel("未选择文件")
        self._file_label.setObjectName("subtitle")
        self._file_label.setWordWrap(True)
        layout.addWidget(self._file_label)

        browse_btn = QPushButton("📂 选择PDF")
        browse_btn.setObjectName("primary")
        browse_btn.setFixedHeight(30)
        browse_btn.clicked.connect(self._browse_pdf)
        layout.addWidget(browse_btn)

        return group
    
    def _create_middle_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        toolbar = self._create_toolbar()
        layout.addLayout(toolbar)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self._pdf_canvas = PdfCanvas()
        scroll_area.setWidget(self._pdf_canvas)
        layout.addWidget(scroll_area, 1)

        return panel
    
    def _create_toolbar(self) -> QHBoxLayout:
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(12, 8, 12, 8)
        toolbar.setSpacing(6)
        
        btn_style = """
            QPushButton {
                background-color: #374151;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4b5563;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #1f2937;
                color: #ffffff;
            }
            QPushButton:disabled {
                background-color: #6b7280;
                color: #9ca3af;
            }
        """
        
        prev_btn = QPushButton("◀")
        prev_btn.setMinimumSize(48, 28)
        prev_btn.setMaximumSize(48, 28)
        prev_btn.setStyleSheet(btn_style)
        prev_btn.clicked.connect(self._prev_page)
        toolbar.addWidget(prev_btn)
        
        self._page_label = QLabel("0 / 0")
        self._page_label.setObjectName("subtitle")
        toolbar.addWidget(self._page_label)
        
        next_btn = QPushButton("▶")
        next_btn.setMinimumSize(48, 28)
        next_btn.setMaximumSize(48, 28)
        next_btn.setStyleSheet(btn_style)
        next_btn.clicked.connect(self._next_page)
        toolbar.addWidget(next_btn)
        
        toolbar.addStretch()
        
        zoom_out_btn = QPushButton("-")
        zoom_out_btn.setMinimumSize(40, 28)
        zoom_out_btn.setMaximumSize(40, 28)
        zoom_out_btn.setStyleSheet(btn_style)
        zoom_out_btn.clicked.connect(self._zoom_out)
        toolbar.addWidget(zoom_out_btn)
        
        self._scale_label = QLabel("100%")
        self._scale_label.setFixedWidth(50)
        self._scale_label.setAlignment(Qt.AlignCenter)
        toolbar.addWidget(self._scale_label)
        
        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setMinimumSize(40, 28)
        zoom_in_btn.setMaximumSize(40, 28)
        zoom_in_btn.setStyleSheet(btn_style)
        zoom_in_btn.clicked.connect(self._zoom_in)
        toolbar.addWidget(zoom_in_btn)
        
        reset_btn = QPushButton("重置")
        reset_btn.setMinimumSize(64, 28)
        reset_btn.setMaximumSize(64, 28)
        reset_btn.setStyleSheet(btn_style)
        reset_btn.clicked.connect(self._reset_zoom)
        toolbar.addWidget(reset_btn)
        
        return toolbar
    
    def _create_right_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._result_panel = ResultPanel()
        layout.addWidget(self._result_panel)

        return panel
    
    def _connect_signals(self) -> None:
        if self._pdf_canvas:
            self._pdf_canvas.page_changed.connect(self._update_page_label)
        
        if self._keyword_panel:
            self._keyword_panel.search_requested.connect(self._run_search)
        
        if self._result_panel:
            self._result_panel.result_clicked.connect(self._on_result_click)
    
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
                    self._keyword_panel.set_status(f"已加载 PDF，共 {self._pdf_canvas.get_page_count()} 页")
                else:
                    self._keyword_panel.set_status(f"❌ {msg}")
    
    def _run_search(self, keywords: List[str], context_length: int) -> None:
        if not self._pdf_canvas or not self._pdf_canvas.get_page_count():
            self._keyword_panel.set_status("⚠️ 请先加载PDF")
            return
        
        if not keywords:
            self._keyword_panel.set_status("⚠️ 请先添加关键词")
            return
        
        self._search_results = []
        if self._result_panel:
            self._result_panel.clear_results()
        
        if self._pdf_canvas:
            self._pdf_canvas.clear_highlights()
        
        doc = self._pdf_canvas._pdf_doc
        highlights_by_page = {}
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            
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
        
        if self._result_panel:
            self._result_panel.add_results(self._search_results)
        
        self._keyword_panel.set_status(f"✅ 搜索完成，找到 {len(self._search_results)} 个匹配")
    
    def _extract_context(self, page: fitz.Page, rect: fitz.Rect, context_length: int):
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
    
    def _on_result_click(self, result: SearchResult) -> None:
        if self._pdf_canvas:
            self._pdf_canvas.scroll_to_highlight(result.page_num, result.rect)
            self._pdf_canvas.set_active_highlight(result.page_num, result.rect)
    
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