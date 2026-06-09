"""PDF搜索逻辑：负责关键词搜索和上下文提取。"""

from __future__ import annotations

import fitz
from typing import List, Tuple, Dict, Optional
from pathlib import Path

from app.utils.logger import get_logger

logger = get_logger("PdfSearchLogic")


class PdfSearchLogic:
    """PDF搜索业务逻辑类，无UI依赖。"""
    
    def __init__(self):
        self._doc: Optional[fitz.Document] = None
    
    def load_pdf(self, filepath: str) -> tuple[bool, str]:
        """加载PDF文档"""
        try:
            self._doc = fitz.open(filepath)
            return True, f"已加载，共 {len(self._doc)} 页"
        except fitz.FileDataError as e:
            logger.exception("加载PDF失败")
            return False, f"PDF文件格式错误或已损坏: {str(e)}"
        except FileNotFoundError:
            logger.exception("文件未找到")
            return False, "文件不存在，请检查路径"
        except Exception as e:
            logger.exception("加载PDF失败")
            return False, f"加载失败: {str(e)}"
    
    def search_keywords(self, keywords: List[str], context_length: int = 8) -> Tuple[List[dict], Dict[int, List[fitz.Rect]]]:
        """
        在PDF中搜索多个关键词
        
        Returns:
            - 搜索结果列表，每个结果包含 page_num, text, rect, keyword, context_before, context_after
            - 按页码分组的高亮矩形字典
        """
        if not self._doc:
            return [], {}
        
        results = []
        highlights_by_page: Dict[int, List[fitz.Rect]] = {}
        
        for page_num in range(len(self._doc)):
            page = self._doc[page_num]
            
            for keyword in keywords:
                rects = page.search_for(keyword)
                for rect in rects:
                    context_before, context_after = self._extract_context(page, rect, context_length)
                    
                    result = {
                        'page_num': page_num,
                        'text': keyword,
                        'rect': rect,
                        'keyword': keyword,
                        'context_before': context_before,
                        'context_after': context_after
                    }
                    results.append(result)
                    
                    if page_num not in highlights_by_page:
                        highlights_by_page[page_num] = []
                    highlights_by_page[page_num].append(rect)
        
        logger.info(f"搜索完成，找到 {len(results)} 个匹配")
        return results, highlights_by_page
    
    def _extract_context(self, page: fitz.Page, rect: fitz.Rect, context_length: int) -> Tuple[str, str]:
        """
        从页面中提取关键词的前后上下文
        
        Args:
            page: PDF页面对象
            rect: 关键词所在的矩形区域
            context_length: 前后文的字数
        
        Returns:
            (context_before, context_after): 关键词前后的文本
        """
        try:
            words = page.get_text("words")
            if not words:
                return "", ""
            
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
    
    def get_page_count(self) -> int:
        """获取总页数"""
        return len(self._doc) if self._doc else 0
    
    def close(self) -> None:
        """关闭文档"""
        if self._doc:
            self._doc.close()
            self._doc = None