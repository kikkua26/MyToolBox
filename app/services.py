"""预定义服务接口（抽象基类）。插件可实现并在 manager 中注册。"""

from abc import ABC, abstractmethod


class ITextFormatter(ABC):
    """文本格式化服务接口。"""

    @abstractmethod
    def format_text(self, text: str) -> str:
        ...


class IImageProcessor(ABC):
    """图片处理服务接口。"""

    @abstractmethod
    def process_image(self, path: str) -> str:
        ...
