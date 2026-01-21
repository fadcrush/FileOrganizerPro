"""
FileOrganizer Pro 4.0 - Main Entry Point

Launches the application with the new modular architecture.
Maintains backward compatibility with existing code during transition.
"""

import sys
from pathlib import Path

# Add package to path if running from development directory
PACKAGE_DIR = Path(__file__).parent
if PACKAGE_DIR not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

import tkinter as tk

# Try to use new modular structure, fall back to old if not available
try:
    from fileorganizer_pro.ui import FileOrganizerApp
    print("✓ Using new modular architecture (v4.0-alpha)")
    USE_NEW_STRUCTURE = True
except ImportError:
    print("⚠ New structure not fully initialized, using legacy code")
    from file_organizer_pro_v3_1 import FileOrganizerProV31 as LegacyApp
    USE_NEW_STRUCTURE = False


def main():
    """Main application entry point."""
    root = tk.Tk()

    try:
        if USE_NEW_STRUCTURE:
            app = FileOrganizerApp(root)
        else:
            app = LegacyApp(root)

        root.mainloop()

    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
