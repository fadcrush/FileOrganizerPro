"""
Enhanced Settings Dialog - Comprehensive application settings
Includes theme switching, project exclusions, shortcuts, and preferences

Features:
- Dark/Light theme toggle with live preview
- Project folder exclusions management
- Keyboard shortcuts customization
- Default paths configuration
- Export/Import settings
- Recent folders quick access
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from pathlib import Path
from typing import Dict, List, Callable, Optional
import json
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))


class ThemeSwitcher(ttk.Frame):
    """
    Theme switcher widget with live preview
    """

    def __init__(self, parent, theme_engine, on_theme_change=None):
        super().__init__(parent)
        self.theme_engine = theme_engine
        self.on_theme_change = on_theme_change

        self._setup_ui()

    def _setup_ui(self):
        """Setup UI"""
        # Header
        header = ttk.Label(
            self,
            text="🎨 THEME SETTINGS",
            font=('Segoe UI', 12, 'bold')
        )
        header.pack(anchor='w', pady=(0, 10))

        # Theme selector
        selector_frame = ttk.Frame(self)
        selector_frame.pack(fill='x', pady=5)

        ttk.Label(selector_frame, text="Theme:").pack(side='left', padx=(0, 10))

        self.theme_var = tk.StringVar(value=self.theme_engine.theme_name)

        theme_options = ['neon_dark', 'neon_light'] + list(self.theme_engine.custom_themes.keys())

        theme_combo = ttk.Combobox(
            selector_frame,
            textvariable=self.theme_var,
            values=theme_options,
            state='readonly',
            width=20
        )
        theme_combo.pack(side='left')
        theme_combo.bind('<<ComboboxSelected>>', self._on_theme_change)

        # Quick toggle buttons
        toggle_frame = ttk.Frame(self)
        toggle_frame.pack(fill='x', pady=10)

        ttk.Button(
            toggle_frame,
            text="🌙 Dark Mode",
            command=lambda: self._set_theme('neon_dark'),
            width=15
        ).pack(side='left', padx=5)

        ttk.Button(
            toggle_frame,
            text="☀️ Light Mode",
            command=lambda: self._set_theme('neon_light'),
            width=15
        ).pack(side='left', padx=5)

        # Preview colors
        preview_frame = ttk.LabelFrame(self, text="Color Preview", padding=10)
        preview_frame.pack(fill='x', pady=10)

        self.preview_labels = {}
        colors_to_show = [
            ('Primary', 'cyan_primary'),
            ('Secondary', 'violet_primary'),
            ('Success', 'matrix_green'),
            ('Background', 'void_black'),
        ]

        for i, (name, color_key) in enumerate(colors_to_show):
            color_frame = ttk.Frame(preview_frame)
            color_frame.grid(row=i//2, column=i%2, padx=5, pady=5, sticky='ew')

            label = ttk.Label(color_frame, text=f"{name}:", width=12)
            label.pack(side='left')

            color_display = tk.Label(
                color_frame,
                text="      ",
                width=6,
                relief='solid',
                borderwidth=1
            )
            color_display.pack(side='left', padx=(5, 0))

            self.preview_labels[color_key] = color_display

        preview_frame.columnconfigure(0, weight=1)
        preview_frame.columnconfigure(1, weight=1)

        self._update_preview()

    def _set_theme(self, theme_name):
        """Set theme"""
        self.theme_var.set(theme_name)
        self._on_theme_change()

    def _on_theme_change(self, event=None):
        """Handle theme change"""
        theme_name = self.theme_var.get()

        if self.on_theme_change:
            self.on_theme_change(theme_name)

        self._update_preview()

    def _update_preview(self):
        """Update color preview"""
        theme = self.theme_engine._load_theme(self.theme_var.get())

        for color_key, label in self.preview_labels.items():
            color = theme.get(color_key, '#FFFFFF')
            label.config(bg=color)


class ProjectExclusionsManager(ttk.Frame):
    """
    Project folder exclusions manager
    Prevents organizing important project folders
    """

    def __init__(self, parent, exclusions_dict=None):
        super().__init__(parent)
        self.exclusions = exclusions_dict or {}

        self._setup_ui()

    def _setup_ui(self):
        """Setup UI"""
        # Header
        header = ttk.Label(
            self,
            text="📁 PROJECT EXCLUSIONS",
            font=('Segoe UI', 12, 'bold')
        )
        header.pack(anchor='w', pady=(0, 10))

        info = ttk.Label(
            self,
            text="Protect project folders from being organized.\nExcluded folders will be skipped during organization.",
            foreground='gray'
        )
        info.pack(anchor='w', pady=(0, 10))

        # List frame
        list_frame = ttk.Frame(self)
        list_frame.pack(fill='both', expand=True)

        # Treeview with checkboxes
        columns = ('Folder', 'Type')
        self.tree = ttk.Treeview(
            list_frame,
            columns=columns,
            show='tree headings',
            selectmode='extended'
        )

        self.tree.heading('#0', text='✓')
        self.tree.heading('Folder', text='Folder/Pattern')
        self.tree.heading('Type', text='Type')

        self.tree.column('#0', width=30, stretch=False)
        self.tree.column('Folder', width=300)
        self.tree.column('Type', width=100)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Populate list
        self._populate_tree()

        # Bind click to toggle
        self.tree.bind('<Button-1>', self._on_click)

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill='x', pady=(10, 0))

        ttk.Button(
            btn_frame,
            text="➕ Add Folder",
            command=self._add_folder,
            width=15
        ).pack(side='left', padx=2)

        ttk.Button(
            btn_frame,
            text="➕ Add Pattern",
            command=self._add_pattern,
            width=15
        ).pack(side='left', padx=2)

        ttk.Button(
            btn_frame,
            text="🗑 Remove Selected",
            command=self._remove_selected,
            width=18
        ).pack(side='left', padx=2)

        ttk.Button(
            btn_frame,
            text="🔄 Reset to Defaults",
            command=self._reset_defaults,
            width=18
        ).pack(side='left', padx=2)

        # Common project types
        presets_frame = ttk.LabelFrame(self, text="Quick Add Presets", padding=10)
        presets_frame.pack(fill='x', pady=(10, 0))

        presets = [
            ("Node.js", "node_modules"),
            ("Python", "__pycache__"),
            ("Git", ".git"),
            ("VS Code", ".vscode"),
            ("Build", "build"),
            ("Dist", "dist"),
            ("JetBrains", ".idea"),
            ("Virtual Env", "venv"),
            ("Test Cache", ".pytest_cache"),
        ]

        for i, (name, pattern) in enumerate(presets):
            ttk.Button(
                presets_frame,
                text=name,
                command=lambda p=pattern: self._quick_add(p),
                width=12
            ).grid(row=i//3, column=i%3, padx=3, pady=3)

    def _populate_tree(self):
        """Populate tree with exclusions"""
        self.tree.delete(*self.tree.get_children())

        for folder, enabled in sorted(self.exclusions.items()):
            check = '✓' if enabled else '☐'
            item_type = 'Pattern' if self._is_pattern(folder) else 'Folder'

            self.tree.insert(
                '',
                'end',
                text=check,
                values=(folder, item_type),
                tags=(folder, 'enabled' if enabled else 'disabled')
            )

    def _is_pattern(self, path_str):
        """Check if string is a pattern (not absolute path)"""
        return not Path(path_str).is_absolute()

    def _on_click(self, event):
        """Handle click to toggle checkbox"""
        region = self.tree.identify_region(event.x, event.y)
        if region == 'tree':
            item = self.tree.identify_row(event.y)
            if item:
                tags = self.tree.item(item, 'tags')
                folder = tags[0] if tags else None

                if folder in self.exclusions:
                    # Toggle enabled/disabled
                    self.exclusions[folder] = not self.exclusions[folder]
                    self._populate_tree()

    def _add_folder(self):
        """Add folder path"""
        folder = filedialog.askdirectory(title="Select Project Folder to Exclude")
        if folder:
            if folder not in self.exclusions:
                self.exclusions[folder] = True
                self._populate_tree()
                messagebox.showinfo("Added", f"Added: {folder}")
            else:
                messagebox.showwarning("Exists", "This folder is already in the exclusion list")

    def _add_pattern(self):
        """Add exclusion pattern"""
        pattern = simpledialog.askstring(
            "Add Pattern",
            "Enter folder name or pattern to exclude:\n(e.g., 'node_modules', '.git', 'build')"
        )
        if pattern:
            pattern = pattern.strip()
            if pattern and pattern not in self.exclusions:
                self.exclusions[pattern] = True
                self._populate_tree()
                messagebox.showinfo("Added", f"Added pattern: {pattern}")

    def _remove_selected(self):
        """Remove selected exclusions"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select exclusions to remove")
            return

        if messagebox.askyesno("Confirm", f"Remove {len(selected)} exclusion(s)?"):
            for item in selected:
                tags = self.tree.item(item, 'tags')
                folder = tags[0] if tags else None
                if folder in self.exclusions:
                    del self.exclusions[folder]

            self._populate_tree()

    def _reset_defaults(self):
        """Reset to default exclusions"""
        if messagebox.askyesno("Reset", "Reset to default exclusions?"):
            self.exclusions.clear()
            defaults = [
                'node_modules', '.git', '.vscode', '.idea', '__pycache__',
                'venv', 'env', '.env', 'build', 'dist', '.pytest_cache',
                '.mypy_cache', 'Organized', 'Duplicates_RecycleBin',
                '.next', '.nuxt', 'target', 'obj', 'bin'
            ]
            for pattern in defaults:
                self.exclusions[pattern] = True

            self._populate_tree()

    def _quick_add(self, pattern):
        """Quick add preset pattern"""
        if pattern not in self.exclusions:
            self.exclusions[pattern] = True
            self._populate_tree()

    def get_exclusions(self):
        """Get exclusions dictionary"""
        return self.exclusions.copy()


class RecentFoldersManager(ttk.Frame):
    """
    Recent folders quick access manager
    """

    def __init__(self, parent, recent_folders=None):
        super().__init__(parent)
        self.recent_folders = recent_folders or []

        self._setup_ui()

    def _setup_ui(self):
        """Setup UI"""
        # Header
        header = ttk.Label(
            self,
            text="📂 RECENT FOLDERS",
            font=('Segoe UI', 12, 'bold')
        )
        header.pack(anchor='w', pady=(0, 10))

        info = ttk.Label(
            self,
            text="Quick access to recently organized folders",
            foreground='gray'
        )
        info.pack(anchor='w', pady=(0, 10))

        # List
        list_frame = ttk.Frame(self)
        list_frame.pack(fill='both', expand=True)

        self.listbox = tk.Listbox(
            list_frame,
            font=('Consolas', 9),
            selectmode=tk.SINGLE
        )
        self.listbox.pack(side='left', fill='both', expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')

        self._populate_list()

        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill='x', pady=(10, 0))

        ttk.Button(
            btn_frame,
            text="📂 Open in Explorer",
            command=self._open_folder,
            width=18
        ).pack(side='left', padx=2)

        ttk.Button(
            btn_frame,
            text="🗑 Remove Selected",
            command=self._remove_selected,
            width=18
        ).pack(side='left', padx=2)

        ttk.Button(
            btn_frame,
            text="🗑 Clear All",
            command=self._clear_all,
            width=15
        ).pack(side='left', padx=2)

    def _populate_list(self):
        """Populate recent folders list"""
        self.listbox.delete(0, tk.END)
        for folder in self.recent_folders:
            self.listbox.insert(tk.END, folder)

    def _open_folder(self):
        """Open selected folder in file explorer"""
        selection = self.listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a folder")
            return

        folder = self.listbox.get(selection[0])
        if Path(folder).exists():
            import subprocess
            import platform

            system = platform.system()
            try:
                if system == "Windows":
                    subprocess.Popen(f'explorer "{folder}"')
                elif system == "Darwin":
                    subprocess.Popen(['open', folder])
                else:
                    subprocess.Popen(['xdg-open', folder])
            except Exception as e:
                messagebox.showerror("Error", f"Could not open folder: {e}")
        else:
            messagebox.showwarning("Not Found", "Folder no longer exists")

    def _remove_selected(self):
        """Remove selected folder from history"""
        selection = self.listbox.curselection()
        if selection:
            self.recent_folders.pop(selection[0])
            self._populate_list()

    def _clear_all(self):
        """Clear all recent folders"""
        if messagebox.askyesno("Clear All", "Clear all recent folders?"):
            self.recent_folders.clear()
            self._populate_list()

    def get_recent_folders(self):
        """Get recent folders list"""
        return self.recent_folders.copy()


class SettingsDialog(tk.Toplevel):
    """
    Comprehensive enhanced settings dialog

    Features:
    - Dark/Light theme toggle
    - Project exclusions
    - Recent folders
    - Keyboard shortcuts
    - Default paths
    - Export/Import config
    """

    def __init__(self, parent, theme_engine=None, app_config=None, on_apply=None):
        super().__init__(parent)

        self.parent = parent
        self.theme_engine = theme_engine
        self.app_config = app_config or {}
        self.on_apply = on_apply

        # Window setup
        self.title("⚙ Settings - FileOrganizer Pro")
        self.geometry("950x750")
        self.resizable(True, True)

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center on parent
        self._center_window()

        # Setup UI
        self._setup_ui()

    def _center_window(self):
        """Center on parent"""
        self.update_idletasks()

        try:
            parent_x = self.parent.winfo_x()
            parent_y = self.parent.winfo_y()
            parent_width = self.parent.winfo_width()
            parent_height = self.parent.winfo_height()

            x = parent_x + (parent_width - 950) // 2
            y = parent_y + (parent_height - 750) // 2

            self.geometry(f'950x750+{x}+{y}')
        except:
            pass  # If positioning fails, use default

    def _setup_ui(self):
        """Setup UI"""
        # Apply theme if available
        bg_color = self.theme_engine.get_color('surface_dark') if self.theme_engine else '#F5F5F5'
        self.configure(bg=bg_color)

        # Header
        header_frame = tk.Frame(self, bg=bg_color)
        header_frame.pack(fill='x', padx=20, pady=20)

        header = tk.Label(
            header_frame,
            text="⚙ SETTINGS",
            font=('Segoe UI', 18, 'bold'),
            bg=bg_color,
            fg=self.theme_engine.get_color('cyan_primary') if self.theme_engine else 'black'
        )
        header.pack(anchor='w')

        subtitle = tk.Label(
            header_frame,
            text="Customize your FileOrganizer Pro experience",
            font=('Segoe UI', 10),
            bg=bg_color,
            fg=self.theme_engine.get_color('text_dim') if self.theme_engine else 'gray'
        )
        subtitle.pack(anchor='w')

        # Notebook
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=(0, 20))

        # Theme tab
        theme_frame = ttk.Frame(self.notebook, padding=20)
        self.theme_switcher = ThemeSwitcher(
            theme_frame,
            self.theme_engine,
            self._on_theme_change
        )
        self.theme_switcher.pack(fill='both', expand=True)
        self.notebook.add(theme_frame, text="🎨 Theme")

        # Project Exclusions tab
        exclusions_frame = ttk.Frame(self.notebook, padding=20)
        self.exclusions_manager = ProjectExclusionsManager(
            exclusions_frame,
            self.app_config.get('excluded_folders', {})
        )
        self.exclusions_manager.pack(fill='both', expand=True)
        self.notebook.add(exclusions_frame, text="📁 Exclusions")

        # Recent Folders tab
        recent_frame = ttk.Frame(self.notebook, padding=20)
        self.recent_manager = RecentFoldersManager(
            recent_frame,
            self.app_config.get('recent_folders', [])
        )
        self.recent_manager.pack(fill='both', expand=True)
        self.notebook.add(recent_frame, text="📂 Recent")

        # Paths tab
        paths_frame = self._create_paths_tab()
        self.notebook.add(paths_frame, text="🗂️ Paths")

        # Advanced tab
        advanced_frame = self._create_advanced_tab()
        self.notebook.add(advanced_frame, text="🔧 Advanced")

        # Buttons
        self._create_buttons()

    def _create_paths_tab(self):
        """Create default paths tab"""
        frame = ttk.Frame(self.notebook, padding=20)

        header = ttk.Label(
            frame,
            text="🗂️ DEFAULT PATHS",
            font=('Segoe UI', 12, 'bold')
        )
        header.pack(anchor='w', pady=(0, 10))

        info = ttk.Label(
            frame,
            text="Set default locations for file organization",
            foreground='gray'
        )
        info.pack(anchor='w', pady=(0, 15))

        # Default source
        self._create_path_setting(frame, "Default Source Folder:", "default_source")

        # Default destination
        self._create_path_setting(frame, "Default Output Folder:", "default_output")

        # Backup location
        self._create_path_setting(frame, "Backup Location:", "backup_location")

        # Reports location
        self._create_path_setting(frame, "Reports Location:", "reports_location")

        return frame

    def _create_path_setting(self, parent, label_text, config_key):
        """Create a path setting row"""
        row = ttk.Frame(parent)
        row.pack(fill='x', pady=8)

        label = ttk.Label(row, text=label_text, width=25)
        label.pack(side='left')

        var = tk.StringVar(value=self.app_config.get(config_key, ''))
        entry = ttk.Entry(row, textvariable=var, width=50)
        entry.pack(side='left', fill='x', expand=True, padx=5)

        ttk.Button(
            row,
            text="Browse...",
            command=lambda: self._browse_folder(var),
            width=10
        ).pack(side='left')

        # Store reference
        setattr(self, f'{config_key}_var', var)

    def _browse_folder(self, var):
        """Browse for folder"""
        folder = filedialog.askdirectory()
        if folder:
            var.set(folder)

    def _create_advanced_tab(self):
        """Create advanced settings tab"""
        frame = ttk.Frame(self.notebook, padding=20)

        header = ttk.Label(
            frame,
            text="🔧 ADVANCED SETTINGS",
            font=('Segoe UI', 12, 'bold')
        )
        header.pack(anchor='w', pady=(0, 10))

        # Export/Import configuration
        export_frame = ttk.LabelFrame(frame, text="Configuration Management", padding=15)
        export_frame.pack(fill='x', pady=10)

        ttk.Button(
            export_frame,
            text="📤 Export All Settings",
            command=self._export_settings,
            width=22
        ).grid(row=0, column=0, padx=5, pady=5, sticky='w')

        ttk.Button(
            export_frame,
            text="📥 Import Settings",
            command=self._import_settings,
            width=22
        ).grid(row=0, column=1, padx=5, pady=5, sticky='w')

        # Reset all
        reset_frame = ttk.LabelFrame(frame, text="Reset Options", padding=15)
        reset_frame.pack(fill='x', pady=10)

        ttk.Label(
            reset_frame,
            text="⚠️ Warning: This will reset ALL settings to factory defaults",
            foreground='red'
        ).pack(anchor='w', pady=(0, 10))

        ttk.Button(
            reset_frame,
            text="🔄 Reset All Settings",
            command=self._reset_all,
            width=20
        ).pack(anchor='w')

        # App info
        info_frame = ttk.LabelFrame(frame, text="Application Info", padding=15)
        info_frame.pack(fill='x', pady=10)

        info_text = """
FileOrganizer Pro - Sci-Fi Edition
Version: 4.0.0
Theme Engine: Neon (Dark/Light)
Configuration Format: JSON

Settings are saved automatically when you click Apply or OK.
        """.strip()

        ttk.Label(
            info_frame,
            text=info_text,
            justify='left'
        ).pack(anchor='w')

        return frame

    def _create_buttons(self):
        """Create dialog buttons"""
        btn_frame = tk.Frame(self, bg=self.theme_engine.get_color('surface_dark') if self.theme_engine else '#F5F5F5')
        btn_frame.pack(fill='x', padx=20, pady=(0, 20))

        ttk.Button(
            btn_frame,
            text="OK",
            command=self._ok,
            width=12
        ).pack(side='right', padx=2)

        ttk.Button(
            btn_frame,
            text="Cancel",
            command=self.destroy,
            width=12
        ).pack(side='right', padx=2)

        ttk.Button(
            btn_frame,
            text="Apply",
            command=self._apply_settings,
            width=12
        ).pack(side='right', padx=2)

    def _on_theme_change(self, theme_name):
        """Handle theme change (store for Apply)"""
        self.app_config['theme'] = theme_name

    def _apply_settings(self):
        """Apply settings"""
        # Collect all settings
        self.app_config['theme'] = self.theme_switcher.theme_var.get()
        self.app_config['excluded_folders'] = self.exclusions_manager.get_exclusions()
        self.app_config['recent_folders'] = self.recent_manager.get_recent_folders()

        # Paths
        for key in ['default_source', 'default_output', 'backup_location', 'reports_location']:
            if hasattr(self, f'{key}_var'):
                self.app_config[key] = getattr(self, f'{key}_var').get()

        # Call callback
        if self.on_apply:
            self.on_apply(self.app_config)

        messagebox.showinfo(
            "Settings Applied",
            "Settings have been applied successfully!\n\n"
            "Some changes may require restarting the application."
        )

    def _ok(self):
        """Apply and close"""
        self._apply_settings()
        self.destroy()

    def _export_settings(self):
        """Export settings to JSON"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            initialfile="fileorganizer_settings.json"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(self.app_config, f, indent=2)
                messagebox.showinfo("Export Complete", f"Settings exported to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export settings:\n{e}")

    def _import_settings(self):
        """Import settings from JSON"""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    imported = json.load(f)

                if messagebox.askyesno(
                    "Import Settings",
                    "This will replace all current settings.\nContinue?"
                ):
                    self.app_config.update(imported)
                    messagebox.showinfo(
                        "Import Complete",
                        "Settings imported successfully!\n\nClick Apply to use them."
                    )

                    # Refresh UI
                    self.destroy()
                    SettingsDialog(self.parent, self.theme_engine, self.app_config, self.on_apply)

            except Exception as e:
                messagebox.showerror("Import Error", f"Failed to import settings:\n{e}")

    def _reset_all(self):
        """Reset all settings to defaults"""
        if messagebox.askyesno(
            "Reset All Settings",
            "This will reset ALL settings to factory defaults.\n\n"
            "This action cannot be undone!\n\nContinue?",
            icon='warning'
        ):
            self.app_config.clear()
            self.app_config['theme'] = 'neon_dark'
            self.app_config['excluded_folders'] = {
                'node_modules': True,
                '.git': True,
                '__pycache__': True,
            }
            self.app_config['recent_folders'] = []

            messagebox.showinfo("Reset Complete", "All settings have been reset to defaults.")

            # Refresh dialog
            self.destroy()
            SettingsDialog(self.parent, self.theme_engine, self.app_config, self.on_apply)


# Demo/Test
if __name__ == '__main__':
    from theme_engine import NeonThemeEngine

    root = tk.Tk()
    root.title("Settings Dialog Test")
    root.geometry("600x400")

    # Apply theme
    theme = NeonThemeEngine('neon_dark')
    theme.apply_theme(root)

    # Test config
    test_config = {
        'theme': 'neon_dark',
        'excluded_folders': {
            'node_modules': True,
            '.git': True,
            '__pycache__': True,
            'venv': True,
        },
        'recent_folders': [
            'E:/Downloads',
            'E:/Documents',
            'E:/Projects',
        ],
        'default_source': 'E:/Downloads',
        'default_output': 'E:/Organized',
    }

    def on_apply(config):
        print("=" * 60)
        print("Settings applied:")
        print("=" * 60)
        print(json.dumps(config, indent=2))
        print("=" * 60)

        # Apply theme change
        if 'theme' in config:
            theme.switch_theme(root, config['theme'])
            print(f"✓ Theme changed to: {config['theme']}")

    # Center frame
    center_frame = ttk.Frame(root, style='Glass.TFrame')
    center_frame.pack(expand=True)

    # Button to open settings
    ttk.Label(
        center_frame,
        text="Enhanced Settings Dialog Test",
        style='Header.TLabel',
        font=('Segoe UI', 16, 'bold')
    ).pack(pady=10)

    ttk.Button(
        center_frame,
        text="⚙ Open Settings",
        command=lambda: SettingsDialog(root, theme, test_config, on_apply),
        style='Neon.TButton'
    ).pack(pady=5)

    ttk.Label(
        center_frame,
        text="Try switching between Dark and Light themes!",
        style='Dim.TLabel'
    ).pack(pady=5)

    root.mainloop()
