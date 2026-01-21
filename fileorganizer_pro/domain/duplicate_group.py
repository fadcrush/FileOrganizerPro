from dataclasses import dataclass
from .file_item import FileItem

@dataclass(frozen=True)
class DuplicateGroup:
    files: list[FileItem]
