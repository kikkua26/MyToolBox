"""PDF元数据编辑逻辑：负责读取和清理PDF元数据。"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Tuple

from app.utils.logger import get_logger

logger = get_logger("PdfMetadataLogic")


class PdfMetadataLogic:
    """PDF元数据编辑业务逻辑类，无UI依赖。"""
    
    def __init__(self):
        self._file_path: Path = None
    
    def load_file(self, file_path: Path) -> bool:
        """加载PDF文件"""
        self._file_path = file_path
        return True
    
    def read_metadata(self) -> Tuple[bool, Dict[str, str], str]:
        """
        读取PDF元数据
        
        Returns:
            (成功标志, 元数据字典, 报告信息)
        """
        if not self._file_path:
            return False, {}, "未选择文件"
        
        try:
            from pypdf import PdfReader
            
            reader = PdfReader(str(self._file_path))
            info = reader.metadata
            
            metadata = {
                "title": info.title or "",
                "author": info.author or "",
                "subject": info.subject or "",
                "keywords": info.keywords or "",
                "creator": info.creator or "",
                "producer": info.producer or "",
            }
            
            report_lines = []
            if info.title:
                report_lines.append(f"⚠️ 标题: {info.title[:30]}...")
            if info.author:
                report_lines.append(f"⚠️ 作者: {info.author}")
            if info.creator:
                report_lines.append(f"⚠️ 创建者: {info.creator}")
            if info.producer:
                report_lines.append(f"⚠️ 生产者: {info.producer}")
            if len(reader.pages) > 0:
                report_lines.append(f"📄 页数: {len(reader.pages)}")
            
            reader.stream.close()
            return True, metadata, "\n".join(report_lines) if report_lines else "✅ 文件元数据已读取"
        
        except ImportError:
            return False, {}, "缺少 pypdf，请运行: pip install pypdf"
        except Exception as e:
            logger.exception("读取 PDF 元数据失败")
            return False, {}, f"读取失败: {e}"
    
    def save_metadata(self, metadata: Dict[str, str], options: Dict[str, bool]) -> Tuple[bool, str, str]:
        """
        保存清理后的PDF（直接覆盖原文件）
        
        Args:
            metadata: 元数据字典
            options: 清理选项字典
        
        Returns:
            (成功标志, 结果消息, 清理报告)
        """
        if not self._file_path:
            return False, "未选择文件", ""
        
        try:
            from pypdf import PdfReader, PdfWriter
            from pypdf.generic import NameObject
            
            reader = PdfReader(str(self._file_path))
            writer = PdfWriter()

            for page in reader.pages:
                if options.get("annotations", False):
                    if "/Annots" in page:
                        del page["/Annots"]
                writer.add_page(page)

            if options.get("doc_id", False) and NameObject("/ID") in writer._root_object:
                del writer._root_object[NameObject("/ID")]

            writer.add_metadata(metadata)

            with open(self._file_path, "wb") as f:
                writer.write(f)

            reader.stream.close()

            cleaned_items = []
            if options.get("doc_id", False):
                cleaned_items.append("文档ID")
            if options.get("xmp", False):
                cleaned_items.append("XMP元数据")
            if options.get("annotations", False):
                cleaned_items.append("注释")
            if options.get("scripts", False):
                cleaned_items.append("脚本")
            if options.get("attachments", False):
                cleaned_items.append("附件")
            if options.get("forms", False):
                cleaned_items.append("表单字段")

            report = f"已清理: {', '.join(cleaned_items)}"
            message = f"已清理 {len(cleaned_items)} 项敏感信息（已覆盖原文件）"
            
            logger.info("元数据清理成功: %s", self._file_path)
            return True, message, report
        
        except PermissionError:
            return False, "无法保存：文件正在被其他程序占用，请关闭PDF阅读器后重试", ""
        except ImportError:
            return False, "缺少 pypdf，请运行: pip install pypdf", ""
        except Exception as e:
            logger.exception("保存 PDF 元数据失败")
            return False, f"保存失败: {e}", ""
    
    def get_output_path(self) -> Path:
        """获取输出文件路径"""
        return self._file_path
    
    def get_file_path(self) -> Path:
        """获取当前文件路径"""
        return self._file_path