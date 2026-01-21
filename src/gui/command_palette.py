"""
Command Palette - Keyboard-driven command launcher
Inspired by VSCode/Sublime Text command palette

Provides fuzzy search for all app commands with Ctrl+K shortcut
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Dict, List, Optional
import difflib


class CommandPalette(tk.Toplevel):
    """
    Fuzzy-searchable command palette for power users

    Features:
    - Fuzzy search across all commands
    - Keyboard navigation (↑↓ arrows, Enter)
    - Global hotkey (Ctrl+K)
    - Recent commands history
    - Category-based organization
    """

    def __init__(self, parent, commands: Dict[str, dict], theme_engine=None):
        """
        Initialize command palette

        Args:
            parent: Parent window
            commands: Dict of {command_id: {'label': str, 'action': Callable, 'category': str}}
            theme_engine: Theme engine instance
        """
        super().__init__(parent)

        self.parent = parent
        self.commands = commands
        self.filtered_commands = list(commands.items())
        self.selected_index = 0
        self.theme_engine = theme_engine
        self.recent_commands = []

        # Window configuration
        self.title("Command Palette")
        self.geometry("700x500")
        self.resizable(False, False)

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self._center_window()

        # Setup UI
        self._setup_ui()

        # Bind events
        self._bind_events()

        # Focus search input
        self.search_input.focus_set()

    def _center_window(self):
        """Center window on parent"""
        self.update_idletasks()

        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        window_width = 700
        window_height = 500

        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2

        self.geometry(f'{window_width}x{window_height}+{x}+{y}')

    def _setup_ui(self):
        """Setup UI components"""

        # Apply theme if available
        if self.theme_engine:
            bg_color = self.theme_engine.get_color('surface_dark')
            fg_color = self.theme_engine.get_color('text_white')
            accent_color = self.theme_engine.get_color('cyan_primary')
            self.configure(bg=bg_color)
        else:
            bg_color = '#1A1F3A'
            fg_color = '#FFFFFF'
            accent_color = '#00F7FF'

        # Main container
        container = tk.Frame(self, bg=bg_color)
        container.pack(fill='both', expand=True, padx=2, pady=2)

        # Header
        header_frame = tk.Frame(container, bg=bg_color)
        header_frame.pack(fill='x', padx=10, pady=10)

        header_label = tk.Label(
            header_frame,
            text="⚡ COMMAND PALETTE",
            font=('Segoe UI', 14, 'bold'),
            bg=bg_color,
            fg=accent_color
        )
        header_label.pack(side='left')

        hint_label = tk.Label(
            header_frame,
            text="Type to search • ↑↓ Navigate • Enter Execute • Esc Close",
            font=('Segoe UI', 8),
            bg=bg_color,
            fg=self.theme_engine.get_color('text_dim') if self.theme_engine else '#7A85A8'
        )
        hint_label.pack(side='right')

        # Search input
        search_frame = tk.Frame(container, bg=bg_color)
        search_frame.pack(fill='x', padx=10, pady=(0, 10))

        search_icon = tk.Label(
            search_frame,
            text="🔍",
            font=('Segoe UI', 12),
            bg=bg_color,
            fg=fg_color
        )
        search_icon.pack(side='left', padx=(0, 5))

        self.search_input = tk.Entry(
            search_frame,
            font=('Segoe UI', 12),
            bg=self.theme_engine.get_color('surface_mid') if self.theme_engine else '#252B48',
            fg=fg_color,
            insertbackground=accent_color,
            relief='flat',
            borderwidth=0
        )
        self.search_input.pack(side='left', fill='x', expand=True, ipady=8)

        # Results listbox
        results_frame = tk.Frame(container, bg=bg_color)
        results_frame.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # Scrollbar
        scrollbar = tk.Scrollbar(results_frame)
        scrollbar.pack(side='right', fill='y')

        self.results_listbox = tk.Listbox(
            results_frame,
            font=('Segoe UI', 10),
            bg=self.theme_engine.get_color('surface_mid') if self.theme_engine else '#252B48',
            fg=fg_color,
            selectbackground=self.theme_engine.get_color('violet_primary') if self.theme_engine else '#B83FFF',
            selectforeground='white',
            activestyle='none',
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            yscrollcommand=scrollbar.set
        )
        self.results_listbox.pack(side='left', fill='both', expand=True)
        scrollbar.config(command=self.results_listbox.yview)

        # Footer with command count
        footer_frame = tk.Frame(container, bg=bg_color)
        footer_frame.pack(fill='x', padx=10, pady=(0, 10))

        self.footer_label = tk.Label(
            footer_frame,
            text=f"{len(self.commands)} commands available",
            font=('Segoe UI', 9),
            bg=bg_color,
            fg=self.theme_engine.get_color('text_dim') if self.theme_engine else '#7A85A8'
        )
        self.footer_label.pack(side='left')

        # Populate initial results
        self._update_results()

    def _bind_events(self):
        """Bind keyboard events"""
        self.search_input.bind('<KeyRelease>', self._on_search_change)
        self.search_input.bind('<Down>', self._on_arrow_down)
        self.search_input.bind('<Up>', self._on_arrow_up)
        self.search_input.bind('<Return>', self._on_execute)
        self.bind('<Escape>', lambda e: self.destroy())
        self.results_listbox.bind('<Return>', self._on_execute)
        self.results_listbox.bind('<Double-Button-1>', self._on_execute)

    def _on_search_change(self, event):
        """Handle search input change"""
        query = self.search_input.get().strip().lower()

        if not query:
            # Show all commands
            self.filtered_commands = list(self.commands.items())
        else:
            # Fuzzy search
            self.filtered_commands = self._fuzzy_search(query)

        self.selected_index = 0
        self._update_results()

    def _fuzzy_search(self, query: str) -> List[tuple]:
        """
        Fuzzy search commands

        Uses difflib for fuzzy matching
        Searches in command label and category
        """
        results = []

        for cmd_id, cmd_data in self.commands.items():
            label = cmd_data['label'].lower()
            category = cmd_data.get('category', '').lower()
            search_text = f"{label} {category}"

            # Calculate similarity ratio
            ratio = difflib.SequenceMatcher(None, query, search_text).ratio()

            # Also check if query is substring
            if query in search_text:
                ratio = max(ratio, 0.8)

            if ratio > 0.3:  # Threshold
                results.append((cmd_id, cmd_data, ratio))

        # Sort by relevance
        results.sort(key=lambda x: x[2], reverse=True)

        return [(cmd_id, cmd_data) for cmd_id, cmd_data, _ in results]

    def _update_results(self):
        """Update results listbox"""
        self.results_listbox.delete(0, tk.END)

        for cmd_id, cmd_data in self.filtered_commands:
            label = cmd_data['label']
            category = cmd_data.get('category', 'General')
            display_text = f"{label}  ({category})"
            self.results_listbox.insert(tk.END, display_text)

        # Update selection
        if self.filtered_commands:
            self.results_listbox.selection_set(self.selected_index)
            self.results_listbox.see(self.selected_index)

        # Update footer
        self.footer_label.config(text=f"{len(self.filtered_commands)} commands found")

    def _on_arrow_down(self, event):
        """Handle down arrow"""
        if self.filtered_commands:
            self.selected_index = min(self.selected_index + 1, len(self.filtered_commands) - 1)
            self.results_listbox.selection_clear(0, tk.END)
            self.results_listbox.selection_set(self.selected_index)
            self.results_listbox.see(self.selected_index)
        return 'break'

    def _on_arrow_up(self, event):
        """Handle up arrow"""
        if self.filtered_commands:
            self.selected_index = max(self.selected_index - 1, 0)
            self.results_listbox.selection_clear(0, tk.END)
            self.results_listbox.selection_set(self.selected_index)
            self.results_listbox.see(self.selected_index)
        return 'break'

    def _on_execute(self, event=None):
        """Execute selected command"""
        if not self.filtered_commands:
            return

        selection = self.results_listbox.curselection()
        if selection:
            index = selection[0]
        else:
            index = self.selected_index

        if index < len(self.filtered_commands):
            cmd_id, cmd_data = self.filtered_commands[index]
            action = cmd_data.get('action')

            if action and callable(action):
                # Add to recent commands
                if cmd_id not in self.recent_commands:
                    self.recent_commands.insert(0, cmd_id)
                    self.recent_commands = self.recent_commands[:10]  # Keep last 10

                # Close palette
                self.destroy()

                # Execute action
                try:
                    action()
                except Exception as e:
                    print(f"Error executing command {cmd_id}: {e}")

    @staticmethod
    def show_palette(parent, commands: Dict[str, dict], theme_engine=None):
        """
        Static method to show command palette

        Args:
            parent: Parent window
            commands: Command dictionary
            theme_engine: Theme engine instance

        Returns:
            CommandPalette instance
        """
        palette = CommandPalette(parent, commands, theme_engine)
        return palette


# Global keyboard shortcut handler
class GlobalCommandPaletteHandler:
    """
    Handler for global command palette shortcut
    Binds Ctrl+K to show command palette
    """

    def __init__(self, root, command_registry, theme_engine=None):
        """
        Initialize global handler

        Args:
            root: Root window
            command_registry: CommandRegistry instance
            theme_engine: Theme engine instance
        """
        self.root = root
        self.command_registry = command_registry
        self.theme_engine = theme_engine
        self.palette = None

        # Bind global shortcut
        self.root.bind('<Control-k>', self._show_palette)
        self.root.bind('<Control-K>', self._show_palette)

    def _show_palette(self, event=None):
        """Show command palette"""
        if self.palette and self.palette.winfo_exists():
            self.palette.focus_set()
        else:
            commands = self.command_registry.get_all_commands()
            self.palette = CommandPalette.show_palette(
                self.root,
                commands,
                self.theme_engine
            )


class CommandRegistry:
    """
    Central registry for all application commands
    """

    def __init__(self):
        self.commands = {}
        self.categories = set()

    def register(self, cmd_id: str, label: str, action: Callable,
                 category: str = 'General', shortcut: Optional[str] = None):
        """
        Register a command

        Args:
            cmd_id: Unique command identifier
            label: Display label (e.g., "🔍 Search Files")
            action: Callable to execute
            category: Command category
            shortcut: Optional keyboard shortcut display
        """
        self.commands[cmd_id] = {
            'label': label,
            'action': action,
            'category': category,
            'shortcut': shortcut
        }
        self.categories.add(category)

    def unregister(self, cmd_id: str):
        """Unregister a command"""
        if cmd_id in self.commands:
            del self.commands[cmd_id]

    def get_all_commands(self) -> Dict[str, dict]:
        """Get all registered commands"""
        return self.commands.copy()

    def get_commands_by_category(self, category: str) -> Dict[str, dict]:
        """Get commands in a specific category"""
        return {
            cmd_id: cmd_data
            for cmd_id, cmd_data in self.commands.items()
            if cmd_data['category'] == category
        }


# Demo/Test
if __name__ == '__main__':
    root = tk.Tk()
    root.title("Command Palette Test")
    root.geometry("800x600")
    root.configure(bg='#0A0E27')

    # Create command registry
    registry = CommandRegistry()

    # Register sample commands
    registry.register(
        'search',
        '🔍 Search Files',
        lambda: print('Search executed'),
        'Navigation',
        'Ctrl+F'
    )

    registry.register(
        'organize',
        '🎯 Organize Now',
        lambda: print('Organize executed'),
        'Actions',
        'Ctrl+O'
    )

    registry.register(
        'duplicates',
        '🔁 Find Duplicates',
        lambda: print('Duplicates executed'),
        'Analysis',
        'Ctrl+D'
    )

    registry.register(
        'tag',
        '🏷 Tag Selected Files',
        lambda: print('Tag executed'),
        'Organization',
        'Ctrl+T'
    )

    registry.register(
        'settings',
        '⚙ Open Settings',
        lambda: print('Settings executed'),
        'General',
        'Ctrl+,'
    )

    # Create theme engine
    from theme_engine import NeonThemeEngine
    theme = NeonThemeEngine('neon_dark')
    theme.apply_theme(root)

    # Setup global handler
    handler = GlobalCommandPaletteHandler(root, registry, theme)

    # Instructions
    label = tk.Label(
        root,
        text="Press Ctrl+K to open Command Palette",
        font=('Segoe UI', 16),
        bg='#0A0E27',
        fg='#00F7FF'
    )
    label.pack(expand=True)

    root.mainloop()
