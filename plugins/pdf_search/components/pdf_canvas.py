"""PDF画布组件：负责PDF渲染、缩放、拖动和高亮显示。"""

from __future__ import annotations

import fitz
from typing import Optional, List, Dict

from PySide6.QtCore import Qt, QPoint, Signal, QSize
from PySide6.QtGui import QPixmap, QPainter, QColor, QBrush, QPen
from PySide6.QtWidgets import QWidget


class PdfCanvas(QWidget):
    page_changed = Signal(int)
    
    def __init__(self) -> None:
        super().__init__()
        self._pdf_doc: Optional[fitz.Document] = None
        self._current_page = 0
        self._pixmap: Optional[QPixmap] = None
        self._search_highlights: Dict[int, List[fitz.Rect]] = {}
        self._active_highlight: Optional[fitz.Rect] = None
        self._active_page: int = -1
        self._scale = 1.0
        self._offset = QPoint(0, 0)
        self._is_dragging = False
        self._drag_start = QPoint(0, 0)
        self._base_matrix = fitz.Matrix(2.0, 2.0)
        self.setMinimumSize(400, 500)
        self.setMouseTracking(True)
    
    def load_pdf(self, filepath: str) -> tuple[bool, str]:
        try:
            self._pdf_doc = fitz.open(filepath)
            self._current_page = 0
            self._search_highlights = {}
            self._scale = 1.0
            self._offset = QPoint(0, 0)
            self.render_page()
            return True, ""
        except fitz.FileDataError as e:
            return False, f"PDF文件格式错误或已损坏: {str(e)}"
        except FileNotFoundError:
            return False, "文件不存在，请检查路径"
        except Exception as e:
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
        
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self._delayed_center)
        
        self.update()
        self.page_changed.emit(self._current_page + 1)
    
    def _delayed_center(self) -> None:
        self.center_content()
        self.update()
    
    def center_content(self) -> None:
        if not self._pixmap:
            return
        
        container_width = self.width()
        container_height = self.height()
        pix_width = self._pixmap.width()
        pix_height = self._pixmap.height()
        
        if pix_width == 0 or pix_height == 0:
            return
        
        scale_x = container_width / pix_width
        scale_y = container_height / pix_height
        fit_scale = min(scale_x, scale_y)
        final_scale = fit_scale * self._scale
        
        scaled_width = pix_width * final_scale
        scaled_height = pix_height * final_scale
        
        offset_x = (container_width - scaled_width) / 2
        offset_y = (container_height - scaled_height) / 2
        
        self._offset = QPoint(int(offset_x), int(offset_y))
    
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
        self._active_highlight = None
        self._active_page = -1
        self.update()
    
    def set_active_highlight(self, page_num: int, rect: fitz.Rect) -> None:
        self._active_highlight = rect
        self._active_page = page_num
        self.update()
    
    def scroll_to_highlight(self, page_num: int, rect: fitz.Rect) -> None:
        self.set_page(page_num)
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
        self.center_content()
        self.update()
    
    def sizeHint(self) -> QSize:
        if self._pixmap:
            return QSize(self._pixmap.width(), self._pixmap.height())
        return super().sizeHint()
    
    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        bg_color = self.palette().window().color()
        
        if not self._pixmap:
            painter.fillRect(self.rect(), bg_color)
            painter.setPen(self.palette().windowText().color())
            painter.drawText(self.rect(), Qt.AlignCenter, "请选择PDF文件")
            return
        
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
        
        painter.fillRect(0, 0, container_width, container_height, bg_color)
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
                
                is_active = (self._active_page == self._current_page and 
                           self._active_highlight is not None and 
                           abs(r.x0 - self._active_highlight.x0) < 1 and
                           abs(r.y0 - self._active_highlight.y0) < 1)
                
                if is_active:
                    painter.fillRect(x0, y0, x1 - x0, y1 - y0, 
                                   QBrush(QColor(255, 100, 100, 150)))
                    painter.setPen(QPen(QColor(255, 0, 0, 255), max(2, int(final_scale * 1.5))))
                else:
                    painter.fillRect(x0, y0, x1 - x0, y1 - y0, 
                                   QBrush(QColor(255, 255, 0, 120)))
                    painter.setPen(QPen(QColor(255, 100, 100, 200), max(1, int(final_scale))))
                
                painter.drawRect(x0, y0, x1 - x0, y1 - y0)