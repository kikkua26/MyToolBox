"""插件基类：所有插件必须继承此类并实现抽象方法。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from PySide6.QtWidgets import QWidget

if TYPE_CHECKING:
    from app.event_bus import EventBus
    from app.plugin_manager import PluginManager


class BasePlugin(ABC):
    """插件基类。"""

    plugin_id: str = ""
    plugin_name: str = ""

    # 由框架在加载后注入
    manager: PluginManager  # type: ignore[assignment]
    event_bus: EventBus  # type: ignore[assignment]

    @abstractmethod
    def get_widget(self) -> QWidget:
        """返回插件主工作区组件（显示在右侧下方）。"""
        ...

    @abstractmethod
    def get_control_widget(self) -> Optional[QWidget]:
        """返回操作栏组件（显示在右侧上方），可返回 None。"""
        ...

    def on_activate(self) -> None:
        """插件被切换到时调用，子类可覆盖。"""

    def on_deactivate(self) -> None:
        """插件被切换走时调用，子类可覆盖。"""
