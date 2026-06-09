"""批量重命名逻辑：负责文件加载、筛选和重命名操作。"""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

from app.utils.logger import get_logger

logger = get_logger("BatchRenameLogic")


class BatchRenameLogic:
    """批量重命名业务逻辑类，无UI依赖。"""
    
    def __init__(self):
        self._files: List[Path] = []
    
    def load_directory(self, directory: Path) -> Tuple[int, str]:
        """加载目录中的所有文件"""
        try:
            self._files = sorted(
                [p for p in directory.rglob("*") if p.is_file()],
                key=lambda p: p.name,
            )
            return len(self._files), f"已加载目录: {directory}"
        except Exception as e:
            logger.exception("加载目录失败")
            return 0, f"加载失败: {str(e)}"
    
    def load_files(self, files: List[Path]) -> Tuple[int, str]:
        """加载指定文件列表"""
        self._files = sorted(files, key=lambda p: p.name)
        return len(self._files), "已加载文件"
    
    def filter_by_extension(self, ext: str) -> Tuple[int, str]:
        """按扩展名筛选文件"""
        before = len(self._files)
        self._files = [f for f in self._files if f.suffix.lower() == ext.lower()]
        return len(self._files), f"筛选 {ext}: {before} → {len(self._files)}"
    
    def preview_rename(self, src_ext: str, dst_ext: str) -> List[Tuple[int, str, str]]:
        """
        预览重命名结果
        
        Returns:
            列表，每个元素包含 (索引, 原文件名, 新文件名或"跳过")
        """
        results = []
        for i, f in enumerate(self._files):
            if f.suffix.lower() == src_ext.lower():
                new_name = f"{f.stem}{dst_ext}"
                results.append((i, f.name, new_name))
            else:
                results.append((i, f.name, "跳过"))
        return results
    
    def execute_rename(self, src_ext: str, dst_ext: str) -> Tuple[int, int, Path, List[str]]:
        """
        执行重命名操作
        
        Returns:
            (成功数, 失败数, 最后输出目录, 错误信息列表)
        """
        success = 0
        errors = 0
        last_dir = None
        error_messages = []
        
        matched = [(i, f) for i, f in enumerate(self._files) if f.suffix.lower() == src_ext.lower()]
        
        for idx, (row, f) in enumerate(matched):
            new_path = f.parent / (f.stem + dst_ext)
            try:
                if f == new_path:
                    success += 1
                    last_dir = f.parent
                    continue
                    
                if new_path.exists():
                    raise FileExistsError(f"目标文件已存在: {new_path.name}")
                
                f.rename(new_path)
                self._files[row] = new_path
                success += 1
                last_dir = new_path.parent
                
            except PermissionError:
                errors += 1
                msg = f"❌ {f.name}: 文件被占用，请关闭正在查看此文件的程序（如PDF阅读器、浏览器、资源管理器预览等）"
                error_messages.append(msg)
                logger.error(msg)
                
            except FileExistsError as e:
                errors += 1
                msg = f"❌ {f.name}: {str(e)}"
                error_messages.append(msg)
                logger.error(msg)
                
            except Exception as e:
                errors += 1
                msg = f"❌ {f.name}: 重命名失败 - {str(e)}"
                error_messages.append(msg)
                logger.exception("重命名失败: %s", f)
        
        return success, errors, last_dir, error_messages
    
    def get_files(self) -> List[Path]:
        """获取当前文件列表"""
        return self._files
    
    def clear_files(self) -> None:
        """清空文件列表"""
        self._files.clear()
    
    def get_file_count(self) -> int:
        """获取文件数量"""
        return len(self._files)