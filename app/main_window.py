"""主窗口：左侧分类树 + 右侧操作栏/工作区 + 主题切换。"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QSplitter,
    QStackedWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.base_plugin import BasePlugin
from app.plugin_manager import PluginManager
from app.themes import ThemeManager
from app.utils.logger import get_logger

logger = get_logger("MainWindow")

# ── 分类 / 插件图标映射 ──────────────────────────────────

CATEGORY_ICONS: dict[str, str] = {
    "文档工具": "📄",
    "图片工具": "🖼️",
    "网络工具": "🌐",
    "系统工具": "⚙️",
    "示例工具": "🧪",
}

PLUGIN_ICONS: dict[str, str] = {
    "batch_rename": "✏️",
    "pdf_merge": "📑",
    "hello_world": "👋",
    "demo_service": "🔧",
}


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("工具集")
        self.resize(1100, 700)

        # 主题管理器
        self.theme_mgr = ThemeManager()
        self.theme_mgr.theme_changed.connect(self._apply_theme)
        self._apply_theme(self.theme_mgr.current_name)

        self.pm = PluginManager()
        self.pm.load_all()

        self._plugin_index_map: list[tuple[str, BasePlugin]] = []
        self._built_widgets: set[str] = set()  # 已构建的 plugin_id

        self._init_ui()
        self._populate_sidebar()

    # ── 主题 ─────────────────────────────────────────────

    def _apply_theme(self, _name: str) -> None:
        self.setStyleSheet(self.theme_mgr.stylesheet())

    # ── UI 构建 ──────────────────────────────────────────

    def _init_ui(self) -> None:
        # ── 左侧边栏 ──
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 0)
        sb_layout.setSpacing(0)

        # Logo
        logo = QWidget()
        logo_lay = QVBoxLayout(logo)
        logo_lay.setContentsMargins(16, 18, 16, 14)

        lbl_icon = QLabel("🧰")
        lbl_icon.setStyleSheet("font-size: 32px; background: transparent;")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_lay.addWidget(lbl_icon)

        lbl_name = QLabel("工具集")
        lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_name.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {self.theme_mgr.current.text_primary}; background: transparent;")
        logo_lay.addWidget(lbl_name)

        lbl_ver = QLabel("v1.0")
        lbl_ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_ver.setStyleSheet(f"font-size: 11px; color: {self.theme_mgr.current.text_tertiary}; background: transparent;")
        logo_lay.addWidget(lbl_ver)

        sb_layout.addWidget(logo)

        # 分隔线
        sep = QWidget()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {self.theme_mgr.current.border_subtle};")
        sb_layout.addWidget(sep)

        # 分类树
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setIndentation(16)
        self.tree.currentItemChanged.connect(self._on_tree_item_changed)
        sb_layout.addWidget(self.tree, 1)

        # 主题切换
        theme_row = QWidget()
        theme_lay = QHBoxLayout(theme_row)
        theme_lay.setContentsMargins(12, 8, 12, 10)
        theme_lay.setSpacing(6)

        lbl_theme = QLabel("🎨")
        lbl_theme.setStyleSheet("font-size: 14px; background: transparent;")
        theme_lay.addWidget(lbl_theme)

        self._theme_combo = QComboBox()
        for name, label in ThemeManager.available_themes():
            self._theme_combo.addItem(label, name)
        # 默认选中
        idx = next(
            (i for i, (n, _) in enumerate(ThemeManager.available_themes()) if n == self.theme_mgr.current_name),
            0,
        )
        self._theme_combo.setCurrentIndex(idx)
        self._theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        theme_lay.addWidget(self._theme_combo, 1)

        sb_layout.addWidget(theme_row)

        # ── 右侧内容区 ──
        self.control_stack = QStackedWidget()
        self.workspace_stack = QStackedWidget()

        # 欢迎页（index 0）
        self.workspace_stack.addWidget(self._build_welcome())

        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.addWidget(self.control_stack)
        right_splitter.addWidget(self.workspace_stack)
        right_splitter.setStretchFactor(0, 0)
        right_splitter.setStretchFactor(1, 1)
        right_splitter.setSizes([0, 1])

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.addWidget(sidebar)
        main_splitter.addWidget(right_splitter)
        main_splitter.setStretchFactor(0, 0)
        main_splitter.setStretchFactor(1, 1)

        self.setCentralWidget(main_splitter)

    def _build_welcome(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t = self.theme_mgr.current

        icon = QLabel("🧰")
        icon.setStyleSheet("font-size: 56px; background: transparent;")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(icon)

        title = QLabel("欢迎使用工具集")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        hint = QLabel("从左侧选择一个工具开始使用")
        hint.setObjectName("subtitle")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(hint)

        return w

    # ── 侧边栏填充 ──────────────────────────────────────

    def _populate_sidebar(self) -> None:
        categories = self.pm.list_categories()
        first_item = None

        for cat_name, plugins in categories.items():
            icon = CATEGORY_ICONS.get(cat_name, "📁")
            cat_item = QTreeWidgetItem(self.tree, [f"  {icon}  {cat_name}"])
            cat_item.setFlags(cat_item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
            cat_item.setExpanded(True)

            font = cat_item.font(0)
            font.setPointSize(11)
            font.setBold(True)
            cat_item.setFont(0, font)
            cat_item.setForeground(0, QColor(self.theme_mgr.current.text_tertiary))

            for plugin in plugins:
                picon = PLUGIN_ICONS.get(plugin.plugin_id, "🔹")
                child = QTreeWidgetItem(cat_item, [f"  {picon}  {plugin.plugin_name}"])
                child.setData(0, Qt.ItemDataRole.UserRole, plugin.plugin_id)
                self._plugin_index_map.append((plugin.plugin_id, plugin))
                if first_item is None:
                    first_item = child

        if first_item:
            self.tree.setCurrentItem(first_item)

    # ── 主题切换 ─────────────────────────────────────────

    def _on_theme_changed(self, index: int) -> None:
        name = self._theme_combo.itemData(index)
        if name:
            self.theme_mgr.set_theme(name)

    # ── 插件切换 ─────────────────────────────────────────

    def _on_tree_item_changed(self, current: QTreeWidgetItem, _prev: QTreeWidgetItem) -> None:
        if current is None:
            return
        plugin_id = current.data(0, Qt.ItemDataRole.UserRole)
        if plugin_id is None:
            return

        plugin = self.pm.get_plugin(plugin_id)
        if plugin is None:
            return

        # 通知旧插件 deactivate
        old_ws_idx = self.workspace_stack.currentIndex()
        if old_ws_idx > 0:
            old_pid, old_plugin = self._plugin_index_map[old_ws_idx - 1]
            try:
                old_plugin.on_deactivate()
            except Exception:
                logger.exception("on_deactivate 失败")

        # 查找 map 索引
        map_idx = -1
        for i, (pid, _) in enumerate(self._plugin_index_map):
            if pid == plugin_id:
                map_idx = i
                break
        if map_idx == -1:
            return

        needed = map_idx + 2  # index 0 = 欢迎页

        # 确保 stacked widget 够用
        while self.control_stack.count() < needed:
            self.control_stack.addWidget(QWidget())
        while self.workspace_stack.count() < needed:
            self.workspace_stack.addWidget(QWidget())

        # 首次构建
        if plugin_id not in self._built_widgets:
            self._built_widgets.add(plugin_id)

            try:
                ctrl = plugin.get_control_widget()
            except Exception:
                logger.exception("get_control_widget 失败: %s", plugin_id)
                ctrl = None
            try:
                ws = plugin.get_widget()
            except Exception:
                logger.exception("get_widget 失败: %s", plugin_id)
                ws = QWidget()

            # 替换占位
            old_ctrl = self.control_stack.widget(map_idx + 1)
            self.control_stack.removeWidget(old_ctrl)
            old_ctrl.deleteLater()
            self.control_stack.insertWidget(map_idx + 1, ctrl if ctrl else QWidget())

            old_ws = self.workspace_stack.widget(map_idx + 1)
            self.workspace_stack.removeWidget(old_ws)
            old_ws.deleteLater()
            self.workspace_stack.insertWidget(map_idx + 1, ws)

        self.control_stack.setCurrentIndex(map_idx + 1)
        self.workspace_stack.setCurrentIndex(map_idx + 1)

        try:
            plugin.on_activate()
        except Exception:
            logger.exception("on_activate 失败")

        logger.info("已切换到插件: %s", plugin.plugin_name)
