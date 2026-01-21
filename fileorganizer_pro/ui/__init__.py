"""UI layer - Tkinter desktop application interface.

This layer is kept thin - all business logic delegates to services.
The UI purely handles presentation and user interaction.
"""

import tkinter as tk
from tkinter import ttk

from ...services import FileOrganizer


class FileOrganizerApp:
    """Main application window.

    Refactored to separate presentation from business logic.
    All file operations delegate to FileOrganizer service.
    """

    def __init__(self, root: tk.Tk):
        """Initialize the application.

        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("FileOrganizer Pro 4.0")
        self.root.geometry("1200x800")

        # Initialize service layer
        self.organizer = FileOrganizer()

        # TODO: Build UI using components
        self.setup_ui()

    def setup_ui(self):
        """Build the UI."""
        # TODO: Create main window, panels, dialogs
        pass
