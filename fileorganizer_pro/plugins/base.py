from abc import ABC, abstractmethod

class Plugin(ABC):
    name: str
    version: str

    @abstractmethod
    def register(self, app):
        pass
