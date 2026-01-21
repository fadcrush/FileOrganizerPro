from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

@dataclass(frozen=True)
class FileItem:
    path: Path
    size: int
    created_at: datetime
    modified_at: datetime
