"""插件管理器：扫描、加载、注册插件，支持分类。"""

from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from app.base_plugin import BasePlugin
from app.event_bus import EventBus
from app.utils.logger import get_logger

logger = get_logger("PluginManager")

_PLUGINS_DIR = Path(__file__).resolve().parent.parent / "plugins"


class PluginManager:
    """管理所有插件的生命周期与服务注册。"""

    def __init__(self) -> None:
        self._plugins: Dict[str, BasePlugin] = {}
        self._meta: Dict[str, dict] = {}           # plugin_id → plugin.json
        self._services: Dict[Type, Any] = {}
        self.event_bus = EventBus()

    # ── 插件加载 ──────────────────────────────────────────

    def load_all(self) -> None:
        if not _PLUGINS_DIR.is_dir():
            logger.warning("插件目录不存在: %s", _PLUGINS_DIR)
            return

        for sub in sorted(_PLUGINS_DIR.iterdir()):
            if not sub.is_dir() or sub.name.startswith("_"):
                continue
            meta_path = sub / "plugin.json"
            if not meta_path.exists():
                continue
            self._load_plugin(sub, meta_path)

        logger.info("插件加载完成，共 %d 个: %s", len(self._plugins), list(self._plugins.keys()))

    def _load_plugin(self, folder: Path, meta_path: Path) -> None:
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            entry: str = meta["entry_point"]
            module_path, class_name = entry.rsplit(":", 1)

            plugins_dir_str = str(_PLUGINS_DIR)
            if plugins_dir_str not in sys.path:
                sys.path.insert(0, plugins_dir_str)

            module = importlib.import_module(module_path)
            cls: Type[BasePlugin] = getattr(module, class_name)

            instance = cls()
            instance.manager = self  # type: ignore[assignment]
            instance.event_bus = self.event_bus  # type: ignore[assignment]

            self._plugins[instance.plugin_id] = instance
            self._meta[instance.plugin_id] = meta
            logger.info("已加载插件: %s (%s) [%s]", instance.plugin_name, instance.plugin_id, meta.get("category", "未分类"))
        except Exception:
            logger.exception("加载插件失败: %s", folder.name)

    # ── 插件查询 ──────────────────────────────────────────

    def get_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        return self._plugins.get(plugin_id)

    def list_plugins(self) -> List[BasePlugin]:
        return list(self._plugins.values())

    def get_meta(self, plugin_id: str) -> dict:
        return self._meta.get(plugin_id, {})

    def list_categories(self) -> Dict[str, List[BasePlugin]]:
        """返回 {category_name: [plugin, ...]} 的有序字典。"""
        from collections import OrderedDict
        result: Dict[str, List[BasePlugin]] = OrderedDict()
        for pid, plugin in self._plugins.items():
            cat = self._meta.get(pid, {}).get("category", "未分类")
            result.setdefault(cat, []).append(plugin)
        return result

    # ── 服务注册 / 查找 ──────────────────────────────────

    def register_service(self, interface: Type, provider: Any) -> None:
        self._services[interface] = provider
        logger.info("服务已注册: %s -> %s", interface.__name__, type(provider).__name__)

    def get_service(self, interface: Type) -> Any:
        return self._services.get(interface)
