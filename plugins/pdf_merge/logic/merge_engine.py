"""PDF合并逻辑：负责PDF文件合并操作。"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple, Optional

from app.utils.logger import get_logger

logger = get_logger("PdfMergeLogic")


class PdfMergeLogic:
    """PDF合并业务逻辑类，无UI依赖。"""
    
    def __init__(self):
        self._files: List[Path] = []
    
    def load_directory(self, directory: Path) -> Tuple[int, str]:
        """加载目录中的所有PDF文件"""
        try:
            self._files = sorted(directory.rglob("*.pdf"), key=lambda p: p.name)
            return len(self._files), f"已加载目录: {directory}"
        except Exception as e:
            logger.exception("加载目录失败")
            return 0, f"加载失败: {str(e)}"
    
    def load_files(self, files: List[Path]) -> Tuple[int, str]:
        """加载指定PDF文件列表"""
        self._files = files.copy()
        return len(self._files), "已加载文件"
    
    def set_files(self, files: List[Path]) -> None:
        """设置文件列表"""
        self._files = files.copy()
    
    def merge_pdfs(self, output_path: Path) -> Tuple[bool, str]:
        """
        合并PDF文件
        
        Returns:
            (成功标志, 结果消息)
        """
        if len(self._files) < 2:
            return False, "至少需要 2 个 PDF"
        
        try:
            from pypdf import PdfWriter
            
            writer = PdfWriter()
            for f in self._files:
                try:
                    writer.append(str(f))
                except Exception as e:
                    logger.exception("添加失败: %s", f)
                    return False, f"添加失败: {f.name}"

            output_path.parent.mkdir(parents=True, exist_ok=True)
            writer.write(str(output_path))
            writer.close()
            
            return True, f"合并成功: {output_path}"
        
        except ImportError:
            return False, "缺少 pypdf，请运行: pip install pypdf"
        except Exception as e:
            logger.exception("PDF 合并失败")
            return False, f"合并失败: {e}"
    
    def generate_default_output_name(self) -> Optional[str]:
        """生成默认输出文件名"""
        if not self._files:
            return None
        
        parent_dir = self._files[0].parent
        parent_name = parent_dir.name
        return f"00合并版-{parent_name}.pdf"
    
    def get_files(self) -> List[Path]:
        """获取当前文件列表"""
        return self._files
    
    def get_file_count(self) -> int:
        """获取文件数量"""
        return len(self._files)
    
    def clear_files(self) -> None:
        """清空文件列表"""
        self._files.clear()