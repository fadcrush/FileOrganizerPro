# FileOrganizer Pro 2.0 - AI Coding Agent Instructions

**Project:** FileOrganizer Pro 2.0 - Professional File Organization & Duplicate Management System  
**Version:** 2.0.0  
**Owner:** JSMS Academy (David)  
**Purpose:** Build productivity software funding free STEM education for underserved communities

## Architecture Overview

### Core Service Layers

FileOrganizer Pro uses a **layered architecture** with clear separation of concerns:

1. **GUI Layer** (`src/gui/`) - PyQt/Tkinter based desktop interface
   - `main_window.py` - Primary UI with file browser, category selector, operation controls
   - `settings_dialog.py` - User preferences (operation mode, organization style, icons)
   - `progress_window.py` - Real-time scanning/organization feedback
   - `reports_viewer.py` - Detailed results of operations
   - `about_dialog.py` - App metadata and documentation links

2. **Business Logic Layer** (`src/`) - Core operations
   - `file_categorizer.py` - Maps files to categories (11 defaults: Documents, Images, Videos, Audio, Code, Archives, etc.)
   - `duplicate_detector.py` - MD5 hash-based duplicate identification
   - `config_manager.py` - Persistent user settings management
   - `report_generator.py` - HTML/TXT operation reports
   - `icon_manager.py` - Windows folder icon application

3. **Core Processing Layer** (`src/core/`) - Infrastructure
   - `organizer.py` - Orchestrates full file organization workflow
   - `processor.py` - Individual file processing (move/copy/categorize)
   - `scanner.py` - Recursive directory scanning with progress tracking
   - `backup_manager.py` - Pre-operation backup system
   - `logger.py` - Structured logging to `data/logs/`

4. **Utility Layer** (`src/utils/`) - Shared functions
   - `file_utils.py` - File I/O, permissions, metadata
   - `hash_utils.py` - MD5 duplicate detection
   - `path_utils.py` - Cross-platform path handling
   - `size_utils.py` - File size calculations
   - `date_utils.py` - Timestamp parsing for year-based organization

### Data Flow Pattern

```
User GUI Input
    ↓
ConfigManager (validate preferences)
    ↓
Scanner (recursively find files) → Logger (activity tracking)
    ↓
FileCategorizer (apply rules) + DuplicateDetector (identify duplicates)
    ↓
BackupManager (create snapshot if enabled)
    ↓
Processor (execute move/copy operations)
    ↓
ReportGenerator (create HTML/TXT results)
    ↓
IconManager (apply folder icons on Windows)
    ↓
ProgressWindow (update UI) → ReportsViewer (display final results)
```

## Key Features & Implementation Patterns

### Operation Modes (Default: Move)
- **Move:** Files relocated; source deleted after verification
- **Copy:** Files duplicated; source preserved
- Config flag: `preferences.operation_mode` in `default_config.json`

### Organization Modes
- **Category Only:** `Documents/`, `Images/`, etc.
- **Category + Year:** `Documents/2025/`, `Images/2024/` (uses `date_utils.py`)
- Default mode: `category_year` (from `default_config.json`)

### Duplicate Handling Strategy
1. First file encountered = "original" (kept in destination)
2. Subsequent duplicates = marked with `[DUPLICATE]` prefix or moved to `Duplicates/` folder
3. Config flag: `skip_duplicates` (when True, leaves identified duplicates in place)

### Dry Run Feature
- Simulates operations without modifying filesystem
- `preferences.dry_run = true` runs complete analysis, skips Processor step
- Essential for user confidence before large operations

### Configuration System
- **Location:** `config/default_config.json`
- **User Overrides:** Stored in `AppData/FileOrganizerPro/` (Windows) via `ConfigManager`
- **Profile Templates:** `config/templates/{business,developer,photographer}_profile.json`
- **Mappings:** `config/category_mappings.json`, `config/icon_mappings.json`

## Development Workflows & Commands

### Running the Application
```bash
python src/file_organizer_pro.py  # Launch GUI
```
Or Windows: `launch.bat`

### Testing
```bash
python scripts/run_tests.py  # Run full test suite
pytest tests/unit/ -v        # Unit tests only
pytest tests/integration/ -v # Integration tests only
```

### Code Quality
```bash
black src/                    # Format code
flake8 src/                   # Lint (max line 100 chars, ignore E501)
mypy src/                     # Type checking
pylint src/                   # Additional linting
```

### Building Installer
```bash
python scripts/build_installer.py  # Creates .exe via PyInstaller
```

### Project Dependencies
- **Pillow 9.0+** - Icon/image handling
- **PyQt5/Tkinter** - GUI framework (implicit in stdlib or distribution)
- **Dev Only:** pytest, black, flake8, mypy, pylint, sphinx, pyinstaller

## Code Conventions & Patterns

### File Structure Rules
- **Never** modify files in `data/` (logs, backups, cache) - managed by app
- **Config files** are JSON; load via `ConfigManager`, not direct JSON reads
- **Icons** stored in `assets/icons/categories/` named by category (e.g., `code.ico`)

### Naming Conventions
- Classes: `PascalCase` (e.g., `FileCategorizer`, `DuplicateDetector`)
- Functions: `snake_case` (e.g., `categorize_file()`, `compute_file_hash()`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_CATEGORIES`, `HASH_ALGORITHM`)
- Private methods: `_leading_underscore` (e.g., `_validate_path()`)

### Error Handling Pattern
```python
try:
    # File I/O or categorization logic
except FileNotFoundError as e:
    logger.error(f"File not found: {path}", exc_info=True)
    # Log and allow workflow to continue with next file
except PermissionError as e:
    logger.warning(f"Permission denied: {path}", exc_info=True)
    # Skip this file, log in report
```
**Key:** Errors are **logged but non-fatal**—one file failure shouldn't stop the entire operation.

### Logging Pattern
```python
from src.core.logger import get_logger
logger = get_logger(__name__)

logger.info(f"Processing: {file_path}")
logger.warning(f"Duplicate detected: {filename}")
logger.error(f"Failed to move: {path}", exc_info=True)
```
Logs written to `data/logs/file_organizer_pro.log` with timestamp, level, and context.

### Testing Pattern
```python
# tests/unit/test_file_categorizer.py
import pytest
from src.file_categorizer import FileCategorizer

def test_categorize_document():
    categorizer = FileCategorizer()
    assert categorizer.categorize("report.pdf") == "Documents"
    assert categorizer.categorize("script.py") == "Code"

@pytest.fixture
def sample_files(tmp_path):
    # Create temp files; cleanup auto-managed
    (tmp_path / "test.txt").touch()
    return tmp_path
```
Use pytest fixtures for file setup; `conftest.py` has shared fixtures.

## Critical Integration Points

### GUI → Core Communication
- `main_window.py` instantiates `Organizer` and `Processor`
- Calls `organizer.scan()` → `processor.execute()` based on user selections
- Progress updates via callback: `progress_window.update_progress(current, total)`

### Configuration Loading
```python
config = ConfigManager.load()
operation_mode = config['preferences']['operation_mode']  # 'move' or 'copy'
organization_mode = config['preferences']['organization_mode']  # 'category_year'
```

### Report Generation
After operations complete:
```python
report = ReportGenerator.generate(
    moved_files=processor.moved_count,
    duplicates_found=detector.duplicates,
    skipped_files=processor.failed,
    operation_type="move"
)
reports_viewer.display(report)  # Show HTML report in UI
```

### Localization Points
- UI strings sourced from `resources/localization/en_US.json`
- When adding UI text, add key to localization files
- Default fallback: English if translation missing

## Known Limitations & Future Considerations

- **Windows-only folder icons** (`icon_manager.py` uses Windows API)
- **MD5 hashing** for duplicates (fast but not cryptographic; sufficient for local deduplication)
- **Pillow 9.0+** required for advanced image icon generation
- **GUI framework** TBD in implementation (PyQt5/PySide6 recommended for modern desktop features)
- Future: Web interface planned (Flask scaffolding commented in requirements)

## Repository Structure Essentials

| Directory | Purpose |
|-----------|---------|
| `src/` | All source code (main entry point: `file_organizer_pro.py`) |
| `src/core/` | Orchestration, scanning, backup, logging infrastructure |
| `src/gui/` | PyQt/Tkinter UI components |
| `src/utils/` | Reusable utilities (hashing, path handling, etc.) |
| `config/` | Default JSON configs and profile templates |
| `tests/` | pytest test suite (unit/, integration/, fixtures/) |
| `docs/` | Markdown documentation and tutorials |
| `assets/` | Icons and themes |
| `data/` | Runtime artifacts (logs, backups, reports, cache) |
| `resources/` | Templates (HTML reports) and localization JSON |
| `scripts/` | Build, test, and deployment automation |

## Checklist for New Features

When implementing new features, follow this order:
1. ✅ Add unit tests in `tests/unit/`
2. ✅ Implement core logic in `src/` or `src/core/`
3. ✅ Add integration tests in `tests/integration/` if involves multiple components
4. ✅ Update config defaults in `config/default_config.json` if user-configurable
5. ✅ Add GUI elements in `src/gui/main_window.py` or new dialog
6. ✅ Update localization in `resources/localization/en_US.json`
7. ✅ Add documentation in `docs/`
8. ✅ Update `CHANGELOG.md` with feature entry
9. ✅ Run full test suite and code quality checks before commit
