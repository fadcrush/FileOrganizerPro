import os
from pathlib import Path

# Root folder for your new architecture
ROOT = Path("fileorganizer_pro")

# Folder layout definition
LAYOUT = [
    "app",
    "domain",
    "services",
    "infrastructure/fs",
    "infrastructure/db",
    "infrastructure/system",
    "infrastructure/hashing",
    "infrastructure/imaging",
    "infrastructure/networking",
    "plugins/rules",
    "plugins/duplicate_strategies",
    "plugins/exporters",
    "presentation/cli",
    "presentation/gui/qt/dialogs",
    "presentation/gui/qt/widgets",
    "presentation/gui/qt/view_models",
    "tests/unit",
    "tests/integration",
    "tests/e2e",
]

# Basic placeholder Python modules for each layer
PLACEHOLDERS = {
    "app/application.py": 
        "class Application:\n    def __init__(self):\n        pass\n",

    "app/startup.py":
        "def start():\n    print('Starting FileOrganizer Pro...')\n",

    "domain/file_item.py":
        "from dataclasses import dataclass\nfrom pathlib import Path\nfrom datetime import datetime\n\n"
        "@dataclass(frozen=True)\n"
        "class FileItem:\n"
        "    path: Path\n"
        "    size: int\n"
        "    created_at: datetime\n"
        "    modified_at: datetime\n",

    "domain/duplicate_group.py":
        "from dataclasses import dataclass\nfrom .file_item import FileItem\n\n"
        "@dataclass(frozen=True)\n"
        "class DuplicateGroup:\n"
        "    files: list[FileItem]\n",

    "domain/rule.py":
        "from abc import ABC, abstractmethod\n"
        "from pathlib import Path\n"
        "from .file_item import FileItem\n\n"
        "class Rule(ABC):\n"
        "    @abstractmethod\n"
        "    def apply(self, file: FileItem) -> Path | None:\n"
        "        pass\n",

    "services/scan_service.py":
        "from pathlib import Path\n\n"
        "class ScanService:\n"
        "    def scan(self, root: Path):\n"
        "        pass\n",

    "services/organize_service.py":
        "class OrganizeService:\n"
        "    def organize(self, files, rules):\n"
        "        pass\n",

    "services/duplicate_service.py":
        "class DuplicateService:\n"
        "    def find_duplicates(self, scan_result):\n"
        "        pass\n",

    "plugins/base.py":
        "from abc import ABC, abstractmethod\n\n"
        "class Plugin(ABC):\n"
        "    name: str\n"
        "    version: str\n\n"
        "    @abstractmethod\n"
        "    def register(self, app):\n"
        "        pass\n",

    "infrastructure/fs/filesystem.py":
        "from pathlib import Path\n\n"
        "class FileSystem:\n"
        "    def read(self, path: Path) -> bytes:\n"
        "        pass\n"
        "    def write(self, path: Path, data: bytes):\n"
        "        pass\n"
        "    def move(self, src: Path, dst: Path):\n"
        "        pass\n",

    "infrastructure/fs/path_validator.py":
        "from pathlib import Path\n\n"
        "class PathValidator:\n"
        "    def ensure_inside_root(self, path: Path, root: Path):\n"
        "        pass\n",

    "presentation/cli/main.py":
        "def main():\n"
        "    print('CLI interface coming soon...')\n",

    "presentation/gui/qt/main_window.py":
        "class MainWindow:\n"
        "    def __init__(self):\n"
        "        pass\n",
}

def create_structure():
    print(f"Creating architecture under: {ROOT.resolve()}")
    ROOT.mkdir(exist_ok=True)

    for folder in LAYOUT:
        path = ROOT / folder
        path.mkdir(parents=True, exist_ok=True)

        # ensure __init__.py for package behavior
        init_file = path / "__init__.py"
        if not init_file.exists():
            init_file.write_text("")

    # create placeholder modules
    for rel_path, content in PLACEHOLDERS.items():
        file_path = ROOT / rel_path
        if not file_path.parent.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
        if not file_path.exists():
            file_path.write_text(content)

    print("Done! Folder structure + placeholders created successfully.")

if __name__ == "__main__":
    create_structure()
