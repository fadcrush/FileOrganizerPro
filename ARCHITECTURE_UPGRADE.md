# FileOrganizer Pro - Modular Architecture Upgrade

**Version:** 2.0 (Proposed)  
**Target Release:** v4.0  
**Timeline:** 4-6 weeks  

---

## 🎯 Vision

Transform FileOrganizer Pro from a **monolithic Tkinter GUI app** into a **modular, layered system** that:
- ✅ Separates concerns (domain, services, infrastructure, UI, plugins)
- ✅ Enables testing without GUI dependencies
- ✅ Supports reuse in CLI, API, plugins, and cloud contexts
- ✅ Prepares for SaaS evolution and multi-tenant architecture
- ✅ Remains backward-compatible with existing features

---

## 🏗️ Proposed Modular Architecture

### High-Level Layers

```
┌──────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                    │
├──────────────────────────────────────────────────────────────┤
│  UI / API / CLI                                              │
│  - fileorganizer_pro/ui/        (Tkinter GUI)               │
│  - fileorganizer_pro/api/        (FastAPI - future)         │
│  - fileorganizer_pro/cli/        (Click CLI - future)       │
└──────────────────────────────────────────────────────────────┘
                              ▲
                              │ uses
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                        │
├──────────────────────────────────────────────────────────────┤
│  Services / Use Cases                                        │
│  - fileorganizer_pro/services/                               │
│    - organization_service.py    (orchestrate operations)    │
│    - scanning_service.py        (find & index files)        │
│    - categorization_service.py  (apply rules/categories)    │
│    - duplicate_service.py       (detect duplicates)         │
│    - rules_service.py           (manage rules & filters)    │
│    - export_service.py          (reports, Excel, etc.)      │
│    - backup_service.py          (pre-operation backup)      │
└──────────────────────────────────────────────────────────────┘
                              ▲
                              │ uses
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                        DOMAIN LAYER                           │
├──────────────────────────────────────────────────────────────┤
│  Core Entities & Value Objects                              │
│  - fileorganizer_pro/domain/                                 │
│    - entities/                  (FileItem, FolderItem, etc.) │
│    - value_objects/             (Category, Hash, Path, etc.) │
│    - events/                    (FileScanned, Organized, etc)│
│    - exceptions/                (Custom exceptions)          │
└──────────────────────────────────────────────────────────────┘
                              ▲
                              │ uses
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                    INFRASTRUCTURE LAYER                       │
├──────────────────────────────────────────────────────────────┤
│  External Systems & Adapters                                │
│  - fileorganizer_pro/infrastructure/                         │
│    - filesystem/                (File I/O, path handling)   │
│    - persistence/               (Database, JSON, etc.)       │
│    - config/                    (Configuration management)   │
│    - logging/                   (Structured logging)         │
│    - os_integration/            (Windows icons, etc.)        │
└──────────────────────────────────────────────────────────────┘
                              ▲
                              │ uses
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                       PLUGIN LAYER                            │
├──────────────────────────────────────────────────────────────┤
│  Extensibility Points                                        │
│  - fileorganizer_pro/plugins/                                │
│    - plugin_base.py             (Plugin interface)           │
│    - hooks.py                   (Hook registry)              │
│    - examples/                  (Sample plugins)             │
└──────────────────────────────────────────────────────────────┘
```

---

## 📁 Detailed Package Structure

### New Folder Layout

```
fileorganizer_pro/
│
├── __init__.py                          # Package root
├── __version__.py                       # Version constant
├── __main__.py                          # CLI entry point
│
├── domain/                              # DOMAIN LAYER
│   ├── __init__.py
│   ├── entities/
│   │   ├── __init__.py
│   │   ├── file_item.py                 # FileItem (core entity)
│   │   ├── folder_item.py               # FolderItem (container)
│   │   ├── scan_result.py               # ScanResult (from scanner)
│   │   ├── organization_task.py         # OrganizationTask (input)
│   │   ├── operation_result.py          # OperationResult (output)
│   │   └── duplicate_group.py           # DuplicateGroup (detection result)
│   │
│   ├── value_objects/
│   │   ├── __init__.py
│   │   ├── file_path.py                 # Path (safe, normalized)
│   │   ├── file_hash.py                 # FileHash (MD5, SHA256, etc.)
│   │   ├── category.py                  # Category (enum-like)
│   │   ├── file_size.py                 # FileSize (bytes with formatting)
│   │   ├── timestamp.py                 # Timestamp (with timezone)
│   │   └── operation_mode.py            # OperationMode (move/copy enum)
│   │
│   ├── events/
│   │   ├── __init__.py
│   │   ├── domain_event.py              # Base event class
│   │   ├── file_scanned.py              # FileScannedEvent
│   │   ├── file_organized.py            # FileOrganizedEvent
│   │   ├── duplicate_detected.py        # DuplicateDetectedEvent
│   │   └── operation_completed.py       # OperationCompletedEvent
│   │
│   └── exceptions/
│       ├── __init__.py
│       ├── domain_exception.py          # Base exception
│       ├── invalid_path.py              # Invalid path error
│       ├── category_not_found.py        # Unknown category
│       ├── operation_failed.py          # Operation failure
│       └── duplicate_error.py           # Duplicate detection error
│
├── services/                            # APPLICATION LAYER
│   ├── __init__.py
│   ├── scanning_service.py              # Scan files & build index
│   ├── categorization_service.py        # Apply categorization rules
│   ├── duplicate_service.py             # Detect & manage duplicates
│   ├── organization_service.py          # Orchestrate organization
│   ├── rules_service.py                 # Manage rules & filters
│   ├── export_service.py                # Generate reports/exports
│   ├── backup_service.py                # Pre-operation backup
│   ├── statistics_service.py            # Compute statistics
│   └── __init__.py
│
├── infrastructure/                      # INFRASTRUCTURE LAYER
│   ├── __init__.py
│   │
│   ├── filesystem/
│   │   ├── __init__.py
│   │   ├── path_validator.py            # Path safety & normalization
│   │   ├── file_reader.py               # Safe file I/O
│   │   ├── file_writer.py               # Safe write operations
│   │   ├── directory_scanner.py         # Walk directories safely
│   │   └── hash_calculator.py           # Compute file hashes
│   │
│   ├── persistence/
│   │   ├── __init__.py
│   │   ├── repository.py                # Base repository pattern
│   │   ├── file_repository.py           # FileItem persistence
│   │   ├── duplicate_repository.py      # Duplicate metadata
│   │   ├── rule_repository.py           # Rule storage
│   │   ├── sqlite_impl.py               # SQLite backend
│   │   └── json_impl.py                 # JSON fallback
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── config_manager.py            # Config loading/saving
│   │   ├── schema.py                    # Config schema & validation
│   │   ├── defaults.py                  # Default configuration
│   │   └── loaders.py                   # JSON, YAML, ENV loaders
│   │
│   ├── logging/
│   │   ├── __init__.py
│   │   ├── logger.py                    # Structured logging
│   │   ├── handlers.py                  # File, console handlers
│   │   └── formatters.py                # Custom formatters
│   │
│   └── os_integration/
│       ├── __init__.py
│       ├── folder_icons.py              # Windows folder icons
│       ├── explorer_integration.py      # Open in Explorer, etc.
│       └── platform_detection.py        # Cross-platform helpers
│
├── ui/                                  # PRESENTATION LAYER (Desktop)
│   ├── __init__.py
│   ├── app.py                           # Main window (refactored)
│   │
│   ├── components/                      # Reusable UI components
│   │   ├── __init__.py
│   │   ├── file_browser.py              # Folder tree + file list
│   │   ├── progress_widget.py           # Progress bar & status
│   │   ├── duplicate_viewer.py          # Duplicate review UI
│   │   ├── settings_panel.py            # Settings/preferences
│   │   └── results_panel.py             # Results & reports
│   │
│   ├── themes/                          # UI themes
│   │   ├── __init__.py
│   │   ├── dark_neon.py                 # Current cyberpunk theme
│   │   ├── light_minimal.py             # Light theme
│   │   └── theme_manager.py             # Theme switching
│   │
│   ├── dialogs/                         # Modal dialogs
│   │   ├── __init__.py
│   │   ├── exclusions_dialog.py         # Manage exclusions
│   │   ├── duplicates_dialog.py         # Review duplicates
│   │   └── settings_dialog.py           # Settings dialog
│   │
│   └── presenters/                      # View models (testable)
│       ├── __init__.py
│       ├── file_presenter.py            # Format files for UI
│       ├── stats_presenter.py           # Format stats for display
│       └── report_presenter.py          # Format reports
│
├── plugins/                             # PLUGIN LAYER
│   ├── __init__.py
│   ├── plugin_base.py                   # Abstract plugin class
│   ├── hook_registry.py                 # Hook system
│   │
│   ├── examples/
│   │   ├── custom_categorizer.py        # Example: custom rule plugin
│   │   ├── email_notifier.py            # Example: notify on complete
│   │   └── cloud_uploader.py            # Example: upload to cloud
│   │
│   └── builtins/
│       ├── __init__.py
│       ├── ai_categorizer.py            # Built-in AI categorization
│       ├── fuzzy_duplicate_finder.py    # Built-in fuzzy duplicates
│       └── tagging_system.py            # Built-in tagging
│
├── api/                                 # PRESENTATION LAYER (Web - Future)
│   ├── __init__.py
│   └── (scaffolding for v3.2)
│
├── cli/                                 # PRESENTATION LAYER (CLI - Future)
│   ├── __init__.py
│   └── (scaffolding for v3.2)
│
├── tests/                               # TEST SUITE
│   ├── __init__.py
│   ├── conftest.py                      # Pytest configuration
│   │
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── domain/
│   │   │   ├── test_entities.py
│   │   │   ├── test_value_objects.py
│   │   │   └── test_exceptions.py
│   │   │
│   │   ├── services/
│   │   │   ├── test_scanning_service.py
│   │   │   ├── test_categorization_service.py
│   │   │   ├── test_duplicate_service.py
│   │   │   └── test_organization_service.py
│   │   │
│   │   └── infrastructure/
│   │       ├── test_path_validator.py
│   │       ├── test_hash_calculator.py
│   │       └── test_config_manager.py
│   │
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_end_to_end_organize.py
│   │   ├── test_duplicate_workflow.py
│   │   └── test_report_generation.py
│   │
│   └── fixtures/
│       ├── __init__.py
│       ├── sample_files.py              # Create test files
│       ├── temp_directories.py          # Temporary test dirs
│       └── mock_services.py             # Mock service implementations
│
├── config/                              # CONFIGURATION FILES
│   ├── default_config.json              # Default settings
│   ├── categories.json                  # Category definitions
│   ├── icon_mappings.json               # Icon mappings
│   └── profiles.json                    # Preset profiles
│
├── resources/                           # STATIC RESOURCES
│   ├── localization/                    # i18n strings
│   │   ├── en_US.json
│   │   ├── es_ES.json
│   │   └── de_DE.json
│   │
│   ├── templates/                       # Report templates
│   │   ├── organization_report.html
│   │   └── duplicate_report.html
│   │
│   └── icons/                           # Application icons
│       ├── app.ico
│       └── categories/
│
├── scripts/                             # UTILITY SCRIPTS
│   ├── build_installer.py               # PyInstaller wrapper
│   ├── run_tests.py                     # Test runner
│   ├── lint_and_format.py               # Code quality
│   └── generate_docs.py                 # Sphinx wrapper
│
├── docs/                                # DOCUMENTATION
│   ├── architecture.md
│   ├── plugin_development.md
│   ├── api_reference.md
│   ├── user_guide.md
│   └── contributing.md
│
├── launch.py                            # Desktop app launcher (root)
├── cli.py                               # CLI launcher (future)
├── pyproject.toml                       # Modern Python packaging
├── requirements.txt                     # Production dependencies
├── requirements-dev.txt                 # Development dependencies
├── pytest.ini                           # Pytest config
├── .pre-commit-config.yaml              # Pre-commit hooks
│
└── .github/
    └── workflows/
        ├── ci.yml                       # GitHub Actions CI
        └── codeql.yml                   # Security scanning
```

---

## 🔀 Dependency Graph

### Import Rules (Strict Layering)

```
Presentation Layer (UI/CLI/API)
  ↓ can import
Services Layer
  ↓ can import
Domain Layer
  ↓ can import
Infrastructure Layer (adapters only)

✗ FORBIDDEN:
- Domain ← Services (no upward dependencies)
- Services ← Presentation (no upward dependencies)
- Infrastructure ← anything except Domain
```

### Example: File Scanning

```
presentation/ui/file_browser.py
  │
  ├─ imports: services/scanning_service.py
  │            services/statistics_service.py
  │
  └─ ScanningService
      │
      ├─ imports: domain/entities/file_item.py
      │            domain/entities/scan_result.py
      │
      ├─ imports: infrastructure/filesystem/directory_scanner.py
      │            infrastructure/filesystem/hash_calculator.py
      │            infrastructure/logging/logger.py
      │
      └─ Logic: 
          - Calls filesystem.directory_scanner.walk()  ◄─ Infrastructure
          - Creates domain.FileItem objects            ◄─ Domain
          - Returns domain.ScanResult                  ◄─ Domain
```

### Another Example: Duplicate Detection

```
presentation/dialogs/duplicates_dialog.py
  │
  ├─ imports: services/duplicate_service.py
  │
  └─ DuplicateService
      │
      ├─ imports: domain/entities/duplicate_group.py
      │            domain/value_objects/file_hash.py
      │
      ├─ imports: infrastructure/persistence/duplicate_repository.py
      │            infrastructure/filesystem/hash_calculator.py
      │
      └─ Logic:
          - Calls hash_calculator.compute()           ◄─ Infrastructure
          - Creates DuplicateGroup entities           ◄─ Domain
          - Persists via repository                   ◄─ Infrastructure
```

---

## 🔧 Core Service Interfaces (Contracts)

### ScanningService

```python
from typing import List, Optional
from domain.entities import FileItem, ScanResult

class ScanningService:
    """Recursively scan directory & build file index"""
    
    def scan(
        self, 
        root_path: str,
        excluded_patterns: Optional[List[str]] = None,
        max_depth: Optional[int] = None
    ) -> ScanResult:
        """
        Scan directory tree.
        
        Args:
            root_path: Directory to scan
            excluded_patterns: Folders/patterns to skip
            max_depth: Maximum recursion depth (safety)
        
        Returns:
            ScanResult with file list and metadata
        """
        pass
```

### CategorizationService

```python
from domain.entities import FileItem
from domain.value_objects import Category

class CategorizationService:
    """Apply categorization rules to files"""
    
    def categorize(self, file_item: FileItem) -> Category:
        """
        Determine category for a file.
        
        Strategy (priority):
        1. Custom rule (if user-configured)
        2. AI categorization (if enabled)
        3. Extension-based lookup
        4. Content-based (magic bytes)
        5. Fallback to 'Others'
        """
        pass
```

### OrganizationService

```python
from domain.entities import OrganizationTask, OperationResult

class OrganizationService:
    """Orchestrate the entire organization workflow"""
    
    def organize(self, task: OrganizationTask) -> OperationResult:
        """
        Execute organization operation.
        
        Workflow:
        1. Validate task
        2. Create backup (if enabled)
        3. Scan source directory
        4. Categorize each file
        5. Detect duplicates
        6. Move/copy files
        7. Generate reports
        8. Fire completion event
        """
        pass
```

---

## 📋 Migration Plan (From Monolith to Modular)

### Step-by-Step Refactoring (Keep App Runnable)

#### Phase 1: Scaffolding (Week 1)
- [ ] Create new `fileorganizer_pro/` package structure
- [ ] Create empty modules with docstrings & imports
- [ ] Keep old `file_organizer_pro.py` for backward compatibility
- [ ] Add `launch.py` that imports from new structure
- [ ] All tests still pass (none exist yet!)

#### Phase 2: Domain Extraction (Week 1)
- [ ] Create domain entities (`FileItem`, `FolderItem`, `ScanResult`, etc.)
- [ ] Create value objects (`FileHash`, `FilePath`, `Category`, etc.)
- [ ] Create custom exceptions
- [ ] Define domain events (for future event sourcing)
- [ ] Unit tests for domain entities

#### Phase 3: Infrastructure Layer (Week 2)
- [ ] Extract filesystem operations to `infrastructure/filesystem/`
  - `PathValidator` (normalize, safety checks)
  - `DirectoryScanner` (walk, skip folders)
  - `HashCalculator` (MD5, SHA256)
  - `FileReader` & `FileWriter` (safe I/O)
- [ ] Create persistence layer (`infrastructure/persistence/`)
  - `Repository` base class
  - SQLite implementation for file history
  - JSON fallback for small datasets
- [ ] Move config management to `infrastructure/config/`
- [ ] Set up structured logging
- [ ] Unit tests for infrastructure

#### Phase 4: Services Layer (Week 2-3)
- [ ] `ScanningService` (orchestrate file discovery)
- [ ] `CategorizationService` (apply rules)
- [ ] `DuplicateService` (MD5-based detection + future fuzzy)
- [ ] `OrganizationService` (main workflow)
- [ ] `ExportService` (reports, Excel, JSON)
- [ ] `BackupService` (pre-operation snapshots)
- [ ] `RulesService` (manage categorization rules)
- [ ] Integration tests for service workflows

#### Phase 5: UI Refactoring (Week 3-4)
- [ ] Extract `MainWindow` from monolith → `ui/app.py`
- [ ] Extract dialogs to `ui/dialogs/`
- [ ] Create reusable components (`ui/components/`)
- [ ] Remove business logic from UI (use services instead)
- [ ] Add presenters/view models for testability
- [ ] Keep `file_organizer_pro.py` runnable during migration

#### Phase 6: Plugins Layer (Week 4)
- [ ] Create plugin interface & hook registry
- [ ] Extract AI categorizer → plugin example
- [ ] Extract tagging system → plugin example
- [ ] Document plugin development guide

#### Phase 7: Testing & CI/CD (Week 4+)
- [ ] Implement unit test suite (80%+ domain coverage)
- [ ] Implement integration tests (end-to-end workflows)
- [ ] Set up GitHub Actions CI
- [ ] Add code coverage reporting
- [ ] Set up pre-commit hooks

#### Phase 8: Clean-up (Week 5)
- [ ] Remove old `file_organizer_pro.py` (when new structure is stable)
- [ ] Consolidate duplicate code
- [ ] Final type hints pass
- [ ] Documentation generation (Sphinx)

### Migration Checkpoints (Sanity Checks)

```
After Phase 1 (Scaffolding):
✓ New package exists
✓ Old app still runs
✓ No circular imports

After Phase 2 (Domain):
✓ Domain entities have tests
✓ Can create FileItem(path, category, hash)
✓ Value objects immutable & testable

After Phase 3 (Infrastructure):
✓ Path validation rejects escape attempts
✓ Hash calculator matches MD5 expectations
✓ Repository can save/load duplicates

After Phase 4 (Services):
✓ Can call organize(task) end-to-end
✓ Results match old behavior
✓ Integration tests pass

After Phase 5 (UI Refactor):
✓ UI calls services instead of doing logic inline
✓ Old and new UI produce identical results
✓ No business logic in UI code

After Phase 6 (Plugins):
✓ Plugin loads & executes
✓ Hook system works
✓ Can create custom plugin

After Phase 7 (Tests):
✓ 80%+ coverage on domain + services
✓ CI runs on every commit
✓ No regressions vs. old code

After Phase 8 (Cleanup):
✓ Old monolith removed
✓ New structure is sole implementation
✓ All tests pass
✓ Documentation complete
```

---

## 🔄 Backward Compatibility Strategy

### Keep v3.1 Runnable During Migration

1. **New Structure in `/fileorganizer_pro/` (parallel package)**
   - Old code untouched in `file_organizer_pro.py` (root)
   - New code in `fileorganizer_pro/` package

2. **Adapter Layer (bridge during transition)**
   ```python
   # file_organizer_pro.py (updated)
   
   # Detect if new structure is available
   try:
       from fileorganizer_pro.services import OrganizationService
       USE_NEW_STRUCTURE = True
   except ImportError:
       USE_NEW_STRUCTURE = False
   
   class FileOrganizerPro:  # Old class, updated
       def process_files(self):
           if USE_NEW_STRUCTURE:
               # Use new service layer
               service = OrganizationService()
               result = service.organize(task)
           else:
               # Fall back to old inline logic
               self._process_files_legacy()
   ```

3. **Gradual Deprecation Path**
   - v3.2: New structure available, old code still works
   - v4.0: New structure is default, old code optional flag
   - v5.0: Old code removed

---

## 💡 Example: Refactoring File Scanning

### Before (Monolithic)
```python
# file_organizer_pro.py (line ~500-520)

def process_files(self):
    all_files = []
    for root, dirs, files in os.walk(source):  # Direct os.walk
        if str(output_base) in root:
            continue
        if self.is_excluded_folder(root):  # Inline exclusion check
            dirs[:] = []
            continue
        for file in files:
            all_files.append(Path(root) / file)  # Raw Path objects
    
    total_files = len(all_files)
    self.log(f"Found {total_files} files")  # Direct logging
```

### After (Modular)
```python
# ui/app.py (new)

class FileOrganizerWindow(tk.Tk):
    def __init__(self):
        self.scanning_service = ScanningService()
        self.organization_service = OrganizationService()
        self.logger = get_logger(__name__)
    
    def start_organization(self):
        try:
            # Create domain task
            task = OrganizationTask(
                source_path=self.source_path.get(),
                operation_mode=self.operation_mode.get(),
                exclusions=self.excluded_folders
            )
            
            # Call service (business logic separated)
            result = self.organization_service.organize(task)
            
            # Update UI
            self.display_results(result)
        
        except DomainException as e:
            self.show_error(str(e))
            self.logger.error(f"Organization failed: {e}")
```

```python
# services/scanning_service.py (new)

from infrastructure.filesystem import DirectoryScanner
from domain.entities import ScanResult, FileItem

class ScanningService:
    def __init__(self):
        self.scanner = DirectoryScanner()
        self.logger = get_logger(__name__)
    
    def scan(self, root_path: str, exclusions: List[str]) -> ScanResult:
        files = []
        for path in self.scanner.walk(root_path, exclusions):
            if path.is_file():
                files.append(FileItem(
                    path=path,
                    size=path.stat().st_size,
                    modified=path.stat().st_mtime
                ))
        
        self.logger.info(f"Scanned {len(files)} files")
        return ScanResult(files=files, total_count=len(files))
```

```python
# infrastructure/filesystem/directory_scanner.py (new)

from domain.value_objects import FilePath

class DirectoryScanner:
    def walk(self, root: str, exclusions: List[str]):
        root = FilePath.normalize(root)  # Safety: normalize path
        
        for root_dir, dirs, files in os.walk(root):
            # Filter excluded directories
            dirs[:] = [d for d in dirs if d not in exclusions]
            
            for file in files:
                yield root_dir / file
```

---

## 🧪 Testing Strategy (New)

### Unit Tests by Layer

```python
# tests/unit/domain/test_entities.py

def test_file_item_creation():
    item = FileItem(
        path="/home/user/docs/report.pdf",
        category="Documents",
        size=1024
    )
    assert item.path == "/home/user/docs/report.pdf"
    assert item.category == "Documents"

# tests/unit/infrastructure/test_path_validator.py

def test_path_escape_prevented():
    with pytest.raises(InvalidPathError):
        FilePath.validate("../../etc/passwd", root="/home/user")
    
    # Relative paths normalized
    assert FilePath.normalize("./docs/./file.txt") == "docs/file.txt"

# tests/integration/test_end_to_end.py

def test_full_organization_workflow(tmp_path):
    # Create test files
    (tmp_path / "photo.jpg").touch()
    (tmp_path / "doc.pdf").touch()
    
    # Organize
    service = OrganizationService()
    result = service.organize(
        OrganizationTask(
            source_path=str(tmp_path),
            operation_mode='move'
        )
    )
    
    # Verify results
    assert result.success
    assert (tmp_path / "Organized" / "Images" / "photo.jpg").exists()
    assert (tmp_path / "Organized" / "Documents" / "doc.pdf").exists()
```

---

## 📊 Comparison: Old vs. New

| Aspect | Old (Monolithic) | New (Modular) |
|--------|------------------|---------------|
| **File Lines** | 1432 (one file) | 100-200 each (15+ files) |
| **Testability** | Hard (UI coupled) | Easy (no UI needed) |
| **Reusability** | None (GUI-only) | High (services + plugins) |
| **Type Safety** | 0% coverage | 100% target |
| **Error Handling** | Bare excepts | Specific exceptions |
| **Path Safety** | None | Validated & normalized |
| **Extensibility** | Must edit source | Plugin interface |
| **Cloud Ready** | No | Yes (services-based) |
| **Testing** | Manual only | Unit + integration + CI |
| **Maintenance** | Hard (monolith) | Easy (clear boundaries) |

---

## 📅 Timeline Estimate

| Phase | Duration | Owner | Status |
|-------|----------|-------|--------|
| Scaffolding | 1 week | Dev | Not Started |
| Domain | 1 week | Dev | Not Started |
| Infrastructure | 1 week | Dev | Not Started |
| Services | 1-2 weeks | Dev | Not Started |
| UI Refactor | 1-2 weeks | Dev | Not Started |
| Plugins | 3-5 days | Dev | Not Started |
| Testing | 1-2 weeks | QA | Not Started |
| Cleanup | 3-5 days | Dev | Not Started |
| **TOTAL** | **4-6 weeks** | | **Not Started** |

---

## 🎯 Success Criteria

- ✅ All existing features work identically to v3.1
- ✅ Zero breaking changes for users
- ✅ 80%+ test coverage (domain + services)
- ✅ All business logic separated from UI
- ✅ Type hints 100% complete
- ✅ Documentation complete (API, plugin guide)
- ✅ CI/CD pipeline running (GitHub Actions)
- ✅ Plugin example works end-to-end
- ✅ Performance equivalent or better than v3.1
- ✅ Code follows PEP 8 + security best practices

---

## 🚀 Future Capabilities (Enabled by Modular Architecture)

Once refactored, these become possible:

### 1. **CLI Tool**
```bash
fileorganizer --scan /path/to/files --organize --dry-run
fileorganizer --check-duplicates /path/to/files
```

### 2. **REST API**
```bash
POST /api/v1/organize
GET /api/v1/duplicates
GET /api/v1/reports/latest
```

### 3. **Plugin Extension**
```python
# Custom plugin: auto-tag by AI
class AITaggerPlugin(PluginBase):
    def on_file_categorized(self, file_item, category):
        tags = self.ai_model.predict_tags(file_item)
        self.emit_event('file_tagged', file_item=file_item, tags=tags)
```

### 4. **Cloud Sync** (SaaS v2)
```python
# Services work with remote storage
service = OrganizationService(
    storage=CloudStorage("s3://bucket"),
    db=PostgreSQL("cloud-db")
)
```

### 5. **Batch Processing**
```python
# Organize multiple directories in parallel
results = organize_batch(
    tasks=[
        OrganizationTask(path1),
        OrganizationTask(path2),
        OrganizationTask(path3),
    ],
    parallelism=4
)
```

---

**End of Architecture Upgrade Document**

*This architecture is designed to evolve FileOrganizer Pro into a production-grade, extensible, and cloud-ready platform while maintaining backward compatibility during the transition.*
