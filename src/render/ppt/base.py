"""
PPT 构建器基类与注册机制
"""
from abc import ABC, abstractmethod


class PPTBuilder(ABC):
    """PPT 构建器抽象基类"""

    @abstractmethod
    def build(self, output_path: str) -> None:
        """构建 PPT"""
        pass


class BuilderRegistry:
    """构建器注册表"""

    __builders: dict[str, type[PPTBuilder]] = {}

    @classmethod
    def register(cls, name: str):
        """注册构建器"""

        def decorator(builder_cls: type[PPTBuilder]) -> type[PPTBuilder]:
            cls.__builders[name] = builder_cls
            return builder_cls

        return decorator

    @classmethod
    def get(cls, name: str) -> type[PPTBuilder]:
        """获取构建器类"""
        if name not in cls.__builders:
            raise ValueError(f"Unknown builder: {name}. Available: {list(cls.__builders.keys())}")
        return cls.__builders[name]

    @classmethod
    def list(cls) -> list[str]:
        """列出所有可用构建器"""
        return list(cls.__builders.keys())
