"""全局事件总线：基于 Qt Signal 实现插件间通信。"""

from PySide6.QtCore import QObject, Signal


class EventBus(QObject):
    """全局事件总线，插件通过它发布/订阅事件。"""

    event_triggered = Signal(str, dict)  # 事件名, 参数字典

    def emit(self, event_name: str, data: dict | None = None) -> None:
        """触发一个事件。"""
        self.event_triggered.emit(event_name, data or {})
