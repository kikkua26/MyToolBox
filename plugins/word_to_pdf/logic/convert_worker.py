"""Word转PDF逻辑：负责执行Word文档到PDF的批量转换。"""

from __future__ import annotations

from pathlib import Path
from typing import List

from PySide6.QtCore import QObject, Signal

from app.utils.logger import get_logger

logger = get_logger("WordToPdfLogic")


class ConvertWorker(QObject):
    """转换工作器：在后台线程中执行Word转PDF"""
    
    progress_updated = Signal(int, str)
    finished = Signal(int, int, Path)
    error = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self._files: List[Path] = []
        self._output_dir: Path = Path(".")
        self._running = True

    def set_task(self, files: List[Path], output_dir: Path) -> None:
        self._files = files
        self._output_dir = output_dir
        self._running = True

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        success_count = 0
        fail_count = 0

        try:
            from docx2pdf import convert

            for idx, f in enumerate(self._files):
                if not self._running:
                    break

                try:
                    output_path = self._output_dir / f.with_suffix(".pdf").name
                    self.progress_updated.emit(idx, f"转换中: {f.name}")
                    convert(str(f), str(output_path))
                    success_count += 1
                    logger.info("转换成功: %s -> %s", f.name, output_path)
                except Exception as e:
                    fail_count += 1
                    logger.exception("转换失败: %s", f.name)

            self.progress_updated.emit(len(self._files), "转换完成")
            self.finished.emit(success_count, fail_count, self._output_dir)

        except ImportError:
            self.error.emit("❌ 缺少 docx2pdf，请运行: pip install docx2pdf")
        except Exception as e:
            self.error.emit(f"❌ 转换失败: {e}")
            logger.exception("Word 转 PDF 失败")