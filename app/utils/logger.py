"""统一日志模块：同时输出到控制台和文件。"""

import logging
import os
from pathlib import Path

_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
_LOG_DIR.mkdir(exist_ok=True)

_initialized = False


def _setup_root() -> None:
    global _initialized
    if _initialized:
        return
    _initialized = True

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    root.addHandler(ch)

    # 文件
    fh = logging.FileHandler(_LOG_DIR / "app.log", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    root.addHandler(fh)


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的 logger，首次调用时初始化根日志。"""
    _setup_root()
    return logging.getLogger(name)
