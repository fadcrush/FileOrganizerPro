"""Plugin system - Extensible plugin architecture."""

from abc import ABC, abstractmethod


class PluginBase(ABC):
    """Abstract base class for all plugins."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Plugin name."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Plugin version."""
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Initialize plugin."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up plugin resources."""
        pass


class HookRegistry:
    """Registry for plugin hooks."""

    def __init__(self):
        self.hooks: dict = {}

    def register(self, hook_name: str, callback) -> None:
        """Register a hook callback.

        Args:
            hook_name: Name of the hook
            callback: Callable to execute
        """
        if hook_name not in self.hooks:
            self.hooks[hook_name] = []
        self.hooks[hook_name].append(callback)

    def fire(self, hook_name: str, **kwargs) -> None:
        """Fire a hook.

        Args:
            hook_name: Name of the hook
            **kwargs: Arguments to pass to callbacks
        """
        if hook_name in self.hooks:
            for callback in self.hooks[hook_name]:
                callback(**kwargs)
