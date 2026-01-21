from pathlib import Path

class FileSystem:
    def read(self, path: Path) -> bytes:
        pass
    def write(self, path: Path, data: bytes):
        pass
    def move(self, src: Path, dst: Path):
        pass
