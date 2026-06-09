"""PDF搜索插件的UI组件模块。"""

from .pdf_canvas import PdfCanvas
from .keyword_panel import KeywordPanel
from .result_panel import ResultPanel, SearchResult

__all__ = ["PdfCanvas", "KeywordPanel", "ResultPanel", "SearchResult"]