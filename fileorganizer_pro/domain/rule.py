from abc import ABC, abstractmethod
from pathlib import Path
from .file_item import FileItem

class Rule(ABC):
    @abstractmethod
    def apply(self, file: FileItem) -> Path | None:
        pass
