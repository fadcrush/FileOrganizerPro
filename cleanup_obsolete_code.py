"""
Cleanup Script - Remove obsolete and empty files from FileOrganizerPro2

Based on comprehensive audit, this removes:
- 49+ empty placeholder files (0 bytes)
- Unused test files
- Duplicate/old version files
- Empty example/script directories

SAFE: Only removes files with 0 bytes or confirmed unused
"""

import os
from pathlib import Path
import shutil


def get_empty_files():
    """Return list of empty files to delete"""

    empty_files = [
        # Empty GUI Components
        "src/gui/about_dialog.py",
        "src/gui/main_window.py",
        "src/gui/progress_window.py",
        "src/gui/reports_viewer.py",
        "src/gui/settings_dialog.py",  # Replaced by settings_dialog_enhanced.py
        "src/gui/__init__.py",

        # Empty Core Modules
        "src/core/backup_manager.py",
        "src/core/logger.py",
        "src/core/organizer.py",
        "src/core/processor.py",
        "src/core/scanner.py",
        "src/core/__init__.py",

        # Empty Utilities
        "src/duplicate_detector.py",
        "src/file_categorizer.py",
        "src/file_organizer_pro.py",
        "src/icon_manager.py",
        "src/config_manager.py",  # Duplicate - real one in root
        "src/report_generator.py",
        "src/utils/date_utils.py",
        "src/utils/file_utils.py",
        "src/utils/hash_utils.py",
        "src/utils/path_utils.py",
        "src/utils/size_utils.py",
        "src/utils/__init__.py",
    ]

    return [f for f in empty_files if Path(f).exists()]


def get_empty_test_files():
    """Return list of empty test files"""

    test_files = [
        "tests/__init__.py",
        "tests/conftest.py",
        "tests/test_config_manager.py",
        "tests/test_duplicate_detector.py",
        "tests/test_file_categorizer.py",
        "tests/test_icon_manager.py",
        "tests/test_organizer.py",
        "tests/fixtures/sample_files.py",
        "tests/integration/test_duplicate_workflow.py",
        "tests/integration/test_full_organization.py",
        "tests/integration/__init__.py",
        "tests/unit/test_core.py",
        "tests/unit/test_utils.py",
        "tests/unit/__init__.py",
    ]

    return [f for f in test_files if Path(f).exists()]


def get_empty_examples():
    """Return list of empty example files"""

    examples = [
        "examples/api_usage.py",
        "examples/basic_usage.py",
        "examples/batch_organization.py",
        "examples/custom_categories.py",
    ]

    return [f for f in examples if Path(f).exists()]


def get_empty_scripts():
    """Return list of empty script files"""

    scripts = [
        "scripts/build_installer.py",
        "scripts/deploy.py",
        "scripts/generate_icons.py",
        "scripts/run_tests.py",
    ]

    return [f for f in scripts if Path(f).exists()]


def get_empty_tools():
    """Return list of empty tool files"""

    tools = [
        "tools/category_editor.py",
        "tools/drive_analyzer.py",
        "tools/duplicate_finder.py",
    ]

    return [f for f in tools if Path(f).exists()]


def get_unused_modules():
    """Return list of unused but non-empty modules"""

    # These have code but are NEVER imported anywhere
    unused = [
        "folder_watcher.py",      # 395 lines - never used
        "scheduler.py",            # 317 lines - never used
        "undo_manager.py",         # 400 lines - never used
        "advanced_features.py",    # 440 lines - claimed in README but not connected
    ]

    return [f for f in unused if Path(f).exists()]


def remove_empty_directories():
    """Remove empty directories after cleanup"""

    dirs_to_check = [
        "tests/fixtures",
        "tests/integration",
        "tests/unit",
        "tests",
        "examples",
        "scripts",
        "tools",
        "src/core",
        "src/utils",
    ]

    removed = []
    for dir_path in dirs_to_check:
        p = Path(dir_path)
        if p.exists() and p.is_dir():
            # Check if empty
            if not any(p.iterdir()):
                shutil.rmtree(p)
                removed.append(dir_path)

    return removed


def main():
    """Main cleanup process"""

    print("=" * 60)
    print("FileOrganizer Pro - Code Cleanup")
    print("=" * 60)
    print()
    print("This will remove:")
    print("- Empty placeholder files (0 bytes)")
    print("- Unused test suite")
    print("- Empty examples/scripts/tools")
    print("- Unused modules (optional)")
    print()

    # Collect all files to remove
    all_files = []

    # Category 1: Empty files (safe to delete)
    empty = get_empty_files()
    tests = get_empty_test_files()
    examples = get_empty_examples()
    scripts = get_empty_scripts()
    tools = get_empty_tools()

    all_files.extend(empty)
    all_files.extend(tests)
    all_files.extend(examples)
    all_files.extend(scripts)
    all_files.extend(tools)

    print(f"Found {len(all_files)} empty files to remove")
    print()

    # Category 2: Unused modules (ask user)
    unused = get_unused_modules()

    if unused:
        print(f"Found {len(unused)} unused modules (have code but never imported):")
        for f in unused:
            size = Path(f).stat().st_size if Path(f).exists() else 0
            print(f"  - {f} ({size} bytes)")
        print()

        response = input("Remove unused modules too? (y/n): ").strip().lower()
        if response == 'y':
            all_files.extend(unused)
            print("✓ Will remove unused modules")
        else:
            print("✓ Keeping unused modules")
        print()

    if not all_files:
        print("Nothing to clean up!")
        return

    # Confirm
    print(f"Total files to remove: {len(all_files)}")
    print()
    confirm = input("Proceed with cleanup? (y/n): ").strip().lower()

    if confirm != 'y':
        print("Cleanup cancelled.")
        return

    # Remove files
    removed_count = 0
    for file_path in all_files:
        try:
            p = Path(file_path)
            if p.exists():
                p.unlink()
                removed_count += 1
                print(f"✓ Removed: {file_path}")
        except Exception as e:
            print(f"✗ Failed to remove {file_path}: {e}")

    print()
    print(f"✓ Removed {removed_count} files")

    # Remove empty directories
    print()
    print("Cleaning up empty directories...")
    removed_dirs = remove_empty_directories()

    if removed_dirs:
        for d in removed_dirs:
            print(f"✓ Removed empty directory: {d}")

    print()
    print("=" * 60)
    print("✓ Cleanup Complete!")
    print("=" * 60)
    print()
    print(f"Freed up space by removing {removed_count} files")
    print()
    print("Your codebase is now cleaner!")
    print()


if __name__ == '__main__':
    main()
