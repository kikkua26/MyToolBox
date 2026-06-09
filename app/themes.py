"""主题系统：设计令牌 + 样式表生成器。

每个主题定义一组设计令牌（design tokens），样式表从令牌派生，不硬编码颜色。

支持的主题：
  - midnight   深蓝夜空（默认）
  - dracula    紫暗吸血鬼
  - nord       北极冷调
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict

from PySide6.QtCore import QObject, Signal


# ──────────────────────────────────────────────────────────
# 设计令牌
# ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ThemeTokens:
    """一组完整的设计令牌。"""

    # ── 基础层级 ──
    bg_window: str          # 最底层：窗口背景
    bg_surface: str         # 中间层：侧边栏、面板
    bg_elevated: str        # 上层：输入框、卡片
    bg_hover: str           # 悬停态
    bg_selected: str        # 选中态
    bg_pressed: str         # 按下态

    # ── 边框 ──
    border_subtle: str      # 默认边框
    border_focus: str       # 聚焦边框

    # ── 文字 ──
    text_primary: str       # 标题、正文
    text_secondary: str     # 副标题、标签
    text_tertiary: str      # 提示文字、占位符
    text_disabled: str      # 禁用态
    text_on_accent: str     # 强调色上的文字（通常白色）

    # ── 强调色 ──
    accent: str             # 主强调色
    accent_hover: str       # 强调色悬停
    accent_pressed: str     # 强调色按下

    # ── 语义色 ──
    success: str
    error: str
    warning: str

    # ── 特殊 ──
    code_bg: str            # 代码/终端背景
    code_text: str          # 代码文字
    scrollbar: str          # 滚动条
    progress_chunk: str     # 进度条填充

    # ── 元数据 ──
    name: str = ""
    label: str = ""


# ──────────────────────────────────────────────────────────
# 主题定义
# ──────────────────────────────────────────────────────────

MIDNIGHT = ThemeTokens(
    name="midnight",
    label="🌙 午夜蓝",
    bg_window="#0d1017",
    bg_surface="#141821",
    bg_elevated="#1a1f2e",
    bg_hover="#1f2639",
    bg_selected="#252d42",
    bg_pressed="#1a1f2e",
    border_subtle="#242c3d",
    border_focus="#3b82f6",
    text_primary="#e2e8f0",
    text_secondary="#94a3b8",
    text_tertiary="#64748b",
    text_disabled="#475569",
    text_on_accent="#ffffff",
    accent="#3b82f6",
    accent_hover="#60a5fa",
    accent_pressed="#2563eb",
    success="#22c55e",
    error="#ef4444",
    warning="#f59e0b",
    code_bg="#0f1419",
    code_text="#c9d1d9",
    scrollbar="#2a3348",
    progress_chunk="#3b82f6",
)

DRACULA = ThemeTokens(
    name="dracula",
    label="🧛 德古拉",
    bg_window="#1a1024",
    bg_surface="#221633",
    bg_elevated="#2a1e3d",
    bg_hover="#342750",
    bg_selected="#3d2f5c",
    bg_pressed="#2a1e3d",
    border_subtle="#3a2d54",
    border_focus="#bd93f9",
    text_primary="#f8f8f2",
    text_secondary="#bfb8d0",
    text_tertiary="#88799e",
    text_disabled="#5c4f73",
    text_on_accent="#1a1024",
    accent="#bd93f9",
    accent_hover="#d4b0ff",
    accent_pressed="#9b6ff7",
    success="#50fa7b",
    error="#ff5555",
    warning="#f1fa8c",
    code_bg="#15101e",
    code_text="#f8f8f2",
    scrollbar="#3a2d54",
    progress_chunk="#bd93f9",
)

NORD = ThemeTokens(
    name="nord",
    label="❄️ 北境",
    bg_window="#2e3440",
    bg_surface="#3b4252",
    bg_elevated="#434c5e",
    bg_hover="#4c566a",
    bg_selected="#4c566a",
    bg_pressed="#434c5e",
    border_subtle="#4c566a",
    border_focus="#88c0d0",
    text_primary="#eceff4",
    text_secondary="#d8dee9",
    text_tertiary="#a3b1c4",
    text_disabled="#6b7d95",
    text_on_accent="#2e3440",
    accent="#88c0d0",
    accent_hover="#8fbcbb",
    accent_pressed="#81a1c1",
    success="#a3be8c",
    error="#bf616a",
    warning="#ebcb8b",
    code_bg="#272c36",
    code_text="#d8dee9",
    scrollbar="#4c566a",
    progress_chunk="#88c0d0",
)

THEMES: Dict[str, ThemeTokens] = {
    t.name: t for t in [MIDNIGHT, DRACULA, NORD]
}

DEFAULT_THEME = "midnight"


# ──────────────────────────────────────────────────────────
# 样式表生成器
# ──────────────────────────────────────────────────────────

def build_stylesheet(t: ThemeTokens) -> str:
    """从设计令牌生成完整 QSS。"""

    return f"""
/* ============================================================
   主题: {t.label}
   自动生成 — 不要手动编辑，修改 ThemeTokens 即可
   ============================================================ */

/* ── 全局 ────────────────────────────────────────────────── */

QMainWindow {{
    background: {t.bg_window};
}}

QWidget {{
    color: {t.text_primary};
}}

QSplitter::handle {{
    background: {t.border_subtle};
}}
QSplitter::handle:horizontal {{
    width: 1px;
}}
QSplitter::handle:vertical {{
    height: 1px;
}}

/* ── 侧边栏 ────────────────────────────────────────────── */

QTreeWidget {{
    background: {t.bg_surface};
    border: none;
    outline: none;
    font-size: 13px;
    padding: 4px 0;
}}
QTreeWidget::item {{
    padding: 7px 10px;
    border-radius: 6px;
    margin: 1px 6px;
    color: {t.text_secondary};
}}
QTreeWidget::item:hover {{
    background: {t.bg_hover};
    color: {t.text_primary};
}}
QTreeWidget::item:selected {{
    background: {t.bg_selected};
    color: {t.text_primary};
}}

/* ── 标签层级 ────────────────────────────────────────────── */

QLabel {{
    color: {t.text_primary};
    background: transparent;
}}
QLabel#title {{
    font-size: 20px;
    font-weight: bold;
    color: {t.text_primary};
    background: transparent;
}}
QLabel#subtitle {{
    font-size: 13px;
    color: {t.text_tertiary};
    background: transparent;
}}
QLabel#sectionTitle {{
    font-size: 14px;
    font-weight: bold;
    color: {t.text_secondary};
    padding: 4px 0;
    background: transparent;
}}

/* ── 按钮 ────────────────────────────────────────────────── */

QPushButton {{
    background: {t.bg_elevated};
    color: {t.text_secondary};
    border: 1px solid {t.border_subtle};
    border-radius: 6px;
    padding: 7px 16px;
    font-size: 13px;
}}
QPushButton:hover {{
    background: {t.bg_hover};
    border-color: {t.border_focus};
    color: {t.text_primary};
}}
QPushButton:pressed {{
    background: {t.bg_pressed};
}}
QPushButton:disabled {{
    color: {t.text_disabled};
    border-color: {t.border_subtle};
}}

/*  主按钮 */
QPushButton#primary {{
    background: {t.accent};
    color: {t.text_on_accent};
    border: none;
    font-weight: bold;
}}
QPushButton#primary:hover {{
    background: {t.accent_hover};
}}
QPushButton#primary:pressed {{
    background: {t.accent_pressed};
}}

/*  危险按钮 */
QPushButton#danger {{
    background: {t.error};
    color: #ffffff;
    border: none;
}}
QPushButton#danger:hover {{
    background: {t.error};
    opacity: 0.85;
}}

/* ── 输入控件 ────────────────────────────────────────────── */

QLineEdit, QTextEdit, QSpinBox, QComboBox {{
    background: {t.bg_elevated};
    color: {t.text_primary};
    border: 1px solid {t.border_subtle};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
    selection-background-color: {t.accent};
    selection-color: {t.text_on_accent};
}}
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border-color: {t.border_focus};
}}
QLineEdit:disabled, QTextEdit:disabled {{
    color: {t.text_disabled};
    background: {t.bg_surface};
}}

/*  下拉框 */
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}
QComboBox QAbstractItemView {{
    background: {t.bg_elevated};
    color: {t.text_primary};
    border: 1px solid {t.border_subtle};
    selection-background-color: {t.bg_selected};
    selection-color: {t.text_primary};
    border-radius: 4px;
}}

/* ── 列表 ────────────────────────────────────────────────── */

QListWidget {{
    background: {t.bg_elevated};
    color: {t.text_primary};
    border: 1px solid {t.border_subtle};
    border-radius: 6px;
    outline: none;
}}
QListWidget::item {{
    padding: 5px 8px;
    border-radius: 4px;
}}
QListWidget::item:selected {{
    background: {t.bg_selected};
    color: {t.text_primary};
}}
QListWidget::item:hover {{
    background: {t.bg_hover};
}}

/* ── 表格 ────────────────────────────────────────────────── */

QTableWidget {{
    background: {t.bg_elevated};
    color: {t.text_primary};
    border: 1px solid {t.border_subtle};
    border-radius: 6px;
    gridline-color: {t.border_subtle};
    outline: none;
}}
QTableWidget::item {{
    padding: 4px 8px;
}}
QTableWidget::item:selected {{
    background: {t.bg_selected};
    color: {t.text_primary};
}}
QHeaderView::section {{
    background: {t.bg_surface};
    color: {t.text_secondary};
    border: none;
    border-bottom: 1px solid {t.border_subtle};
    padding: 6px 8px;
    font-size: 12px;
    font-weight: bold;
}}

/* ── 分组框 ────────────────────────────────────────────────── */

QGroupBox {{
    border: 1px solid {t.border_subtle};
    border-radius: 8px;
    margin-top: 14px;
    padding: 16px 12px 12px 12px;
    font-weight: bold;
    color: {t.text_secondary};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {t.text_secondary};
}}

/* ── 复选框 / 单选框 ────────────────────────────────────── */

QCheckBox, QRadioButton {{
    color: {t.text_primary};
    spacing: 6px;
}}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid {t.border_subtle};
    background: {t.bg_elevated};
}}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background: {t.accent};
    border-color: {t.accent};
}}
QRadioButton::indicator {{
    border-radius: 9px;
}}
QRadioButton::indicator:checked {{
    background: {t.accent};
    border-color: {t.accent};
}}

/* ── 进度条 ────────────────────────────────────────────── */

QProgressBar {{
    background: {t.bg_surface};
    border: none;
    border-radius: 3px;
    text-align: center;
    color: {t.text_secondary};
    font-size: 12px;
    max-height: 6px;
}}
QProgressBar::chunk {{
    background: {t.progress_chunk};
    border-radius: 3px;
}}

/* ── 滚动条 ────────────────────────────────────────────── */

QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {t.scrollbar};
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    background: transparent;
    height: 6px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {t.scrollbar};
    border-radius: 3px;
    min-width: 30px;
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* ── 工具提示 ────────────────────────────────────────────── */

QToolTip {{
    background: {t.bg_elevated};
    color: {t.text_primary};
    border: 1px solid {t.border_subtle};
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
}}
"""


# ──────────────────────────────────────────────────────────
# 主题管理器（全局单例）
# ──────────────────────────────────────────────────────────

class ThemeManager(QObject):
    """管理当前主题，提供切换和查询接口。"""

    theme_changed = Signal(str)  # theme_name

    def __init__(self, initial: str = DEFAULT_THEME) -> None:
        super().__init__()
        self._current_name = initial if initial in THEMES else DEFAULT_THEME

    @property
    def current(self) -> ThemeTokens:
        return THEMES[self._current_name]

    @property
    def current_name(self) -> str:
        return self._current_name

    def set_theme(self, name: str) -> None:
        if name not in THEMES:
            return
        if name == self._current_name:
            return
        self._current_name = name
        self.theme_changed.emit(name)

    def stylesheet(self) -> str:
        return build_stylesheet(self.current)

    @staticmethod
    def available_themes() -> list[tuple[str, str]]:
        """返回 [(name, label), ...]。"""
        return [(t.name, t.label) for t in THEMES.values()]
