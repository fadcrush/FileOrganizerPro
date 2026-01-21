"""
FileOrganizer Pro 3.0 - Modern UI Edition
Professional File Organization with Futuristic Interface

Author: David - JSMS Academy
License: Proprietary
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import sys

# Import the core functionality from the fixed version
from file_organizer_pro import FileOrganizerPro as FileOrganizerProCore


class ModernTheme:
    """Modern glassmorphism theme with cyberpunk aesthetics"""

    # Dark Theme Colors (Cyberpunk)
    DARK = {
        'bg_primary': '#0a0e27',      # Deep space background
        'bg_secondary': '#1a1f3a',    # Dark navy surface
        'bg_tertiary': '#252a48',     # Elevated surface
        'accent_cyan': '#00f7ff',     # Neon cyan
        'accent_magenta': '#ff00ff',  # Neon magenta
        'accent_green': '#00ff41',    # Matrix green
        'text_primary': '#ffffff',    # White text
        'text_secondary': '#a0aec0',  # Gray text
        'success': '#10b981',         # Success green
        'warning': '#f59e0b',         # Warning amber
        'error': '#ef4444',           # Error red
        'glass_overlay': '#ffffff0d', # 5% white for glass effect
        'border': '#ffffff1a',        # 10% white for borders
    }

    # Light Theme Colors (Minimal Modern)
    LIGHT = {
        'bg_primary': '#f8fafc',      # Light background
        'bg_secondary': '#ffffff',    # White surface
        'bg_tertiary': '#f1f5f9',     # Elevated surface
        'accent_cyan': '#0ea5e9',     # Sky blue
        'accent_magenta': '#a855f7',  # Purple
        'accent_green': '#22c55e',    # Green
        'text_primary': '#0f172a',    # Dark text
        'text_secondary': '#64748b',  # Gray text
        'success': '#10b981',         # Success green
        'warning': '#f59e0b',         # Warning amber
        'error': '#ef4444',           # Error red
        'glass_overlay': '#0000000d', # 5% black for glass effect
        'border': '#e2e8f0',          # Light border
    }

    @classmethod
    def get_theme(cls, dark_mode=True):
        """Get theme colors"""
        return cls.DARK if dark_mode else cls.LIGHT


class FileOrganizerProModern(FileOrganizerProCore):
    """Modern UI version with glassmorphism and futuristic design"""

    VERSION = "3.0.0-MODERN"

    def __init__(self, root):
        self.dark_mode = tk.BooleanVar(value=True)
        self.theme = ModernTheme.get_theme(True)

        # Initialize parent (this will call setup_ui)
        super().__init__(root)

        # Override window settings for modern look
        self.root.title(f"FileOrganizer Pro {self.VERSION}")
        self.root.geometry("1400x900")

        # Apply modern theme
        self.apply_modern_theme()

        # Add theme toggle
        self.add_theme_toggle()

    def apply_modern_theme(self):
        """Apply modern glassmorphism theme"""
        style = ttk.Style()

        # Configure root window
        self.root.configure(bg=self.theme['bg_primary'])

        # Modern button styles
        style.configure(
            'Modern.TButton',
            background=self.theme['accent_cyan'],
            foreground=self.theme['text_primary'],
            borderwidth=0,
            focuscolor='none',
            padding=(20, 10),
            font=('Segoe UI', 10, 'bold')
        )

        style.map('Modern.TButton',
            background=[('active', self.theme['accent_magenta'])],
            foreground=[('active', self.theme['text_primary'])]
        )

        # Accent button style
        style.configure(
            'Accent.TButton',
            background=self.theme['accent_green'],
            foreground=self.theme['bg_primary'],
            borderwidth=0,
            padding=(25, 12),
            font=('Segoe UI', 11, 'bold')
        )

        # Frame styles
        style.configure(
            'Glass.TFrame',
            background=self.theme['bg_secondary'],
            relief='flat'
        )

        style.configure(
            'Card.TLabelframe',
            background=self.theme['bg_secondary'],
            foreground=self.theme['text_primary'],
            borderwidth=1,
            relief='solid'
        )

        style.configure(
            'Card.TLabelframe.Label',
            background=self.theme['bg_secondary'],
            foreground=self.theme['accent_cyan'],
            font=('Segoe UI', 11, 'bold')
        )

        # Label styles
        style.configure(
            'Title.TLabel',
            background=self.theme['bg_primary'],
            foreground=self.theme['text_primary'],
            font=('Segoe UI', 24, 'bold')
        )

        style.configure(
            'Subtitle.TLabel',
            background=self.theme['bg_primary'],
            foreground=self.theme['text_secondary'],
            font=('Segoe UI', 11)
        )

        style.configure(
            'Modern.TLabel',
            background=self.theme['bg_secondary'],
            foreground=self.theme['text_primary'],
            font=('Segoe UI', 10)
        )

        # Checkbutton style
        style.configure(
            'Modern.TCheckbutton',
            background=self.theme['bg_secondary'],
            foreground=self.theme['text_primary'],
            font=('Segoe UI', 10)
        )

        # Radiobutton style
        style.configure(
            'Modern.TRadiobutton',
            background=self.theme['bg_secondary'],
            foreground=self.theme['text_primary'],
            font=('Segoe UI', 10)
        )

        # Progress bar with neon glow effect
        style.configure(
            'Neon.Horizontal.TProgressbar',
            background=self.theme['accent_cyan'],
            troughcolor=self.theme['bg_tertiary'],
            borderwidth=0,
            thickness=8
        )

    def setup_ui(self):
        """Override setup_ui with modern design"""
        # Main container with padding
        main_container = tk.Frame(self.root, bg=self.theme['bg_primary'], padx=20, pady=20)
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Header with gradient effect (simulated)
        self.create_modern_header(main_container)

        # Configuration panel with glass effect
        config_frame = tk.LabelFrame(
            main_container,
            text="  ⚙️  Configuration  ",
            bg=self.theme['bg_secondary'],
            fg=self.theme['accent_cyan'],
            font=('Segoe UI', 12, 'bold'),
            padx=15,
            pady=15,
            relief='flat',
            borderwidth=2,
            highlightbackground=self.theme['border'],
            highlightthickness=1
        )
        config_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=15)
        self.create_modern_config_panel(config_frame)

        # Options panel
        options_frame = tk.LabelFrame(
            main_container,
            text="  🎯  Options  ",
            bg=self.theme['bg_secondary'],
            fg=self.theme['accent_magenta'],
            font=('Segoe UI', 12, 'bold'),
            padx=15,
            pady=15,
            relief='flat',
            borderwidth=2,
            highlightbackground=self.theme['border'],
            highlightthickness=1
        )
        options_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=15)
        self.create_modern_options_panel(options_frame)

        # Action buttons with neon glow
        button_frame = tk.Frame(main_container, bg=self.theme['bg_primary'])
        button_frame.grid(row=3, column=0, pady=20)
        self.create_modern_action_buttons(button_frame)

        # Progress section with modern design
        progress_frame = tk.LabelFrame(
            main_container,
            text="  📊  Progress & Logs  ",
            bg=self.theme['bg_secondary'],
            fg=self.theme['accent_green'],
            font=('Segoe UI', 12, 'bold'),
            padx=15,
            pady=15,
            relief='flat',
            borderwidth=2,
            highlightbackground=self.theme['border'],
            highlightthickness=1
        )
        progress_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=15)
        main_container.rowconfigure(4, weight=1)
        self.create_modern_progress_section(progress_frame)

        # Status bar with gradient
        self.create_modern_status_bar(main_container)

    def create_modern_header(self, parent):
        """Create modern header with gradient effect"""
        header = tk.Frame(parent, bg=self.theme['bg_primary'], pady=10)
        header.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 20))

        # Title with icon
        title_label = tk.Label(
            header,
            text=f"🚀 FileOrganizer Pro {self.VERSION}",
            bg=self.theme['bg_primary'],
            fg=self.theme['text_primary'],
            font=('Segoe UI', 28, 'bold')
        )
        title_label.grid(row=0, column=0, sticky=tk.W)

        # Subtitle with accent color
        subtitle_label = tk.Label(
            header,
            text="Professional File Organization & Duplicate Management System",
            bg=self.theme['bg_primary'],
            fg=self.theme['accent_cyan'],
            font=('Segoe UI', 12)
        )
        subtitle_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))

    def create_modern_config_panel(self, parent):
        """Create modern configuration panel"""
        parent.configure(bg=self.theme['bg_secondary'])

        # Source directory with modern styling
        tk.Label(
            parent,
            text="Source Directory:",
            bg=self.theme['bg_secondary'],
            fg=self.theme['text_primary'],
            font=('Segoe UI', 10, 'bold')
        ).grid(row=0, column=0, sticky=tk.W, pady=10)

        # Custom entry with modern look
        source_frame = tk.Frame(parent, bg=self.theme['bg_tertiary'], relief='flat')
        source_frame.grid(row=0, column=1, padx=10, pady=10, sticky=(tk.W, tk.E))
        parent.columnconfigure(1, weight=1)

        source_entry = tk.Entry(
            source_frame,
            textvariable=self.source_path,
            bg=self.theme['bg_tertiary'],
            fg=self.theme['text_primary'],
            font=('Segoe UI', 10),
            relief='flat',
            insertbackground=self.theme['accent_cyan'],
            borderwidth=2,
            highlightthickness=2,
            highlightbackground=self.theme['border'],
            highlightcolor=self.theme['accent_cyan']
        )
        source_entry.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        browse_btn = tk.Button(
            parent,
            text="📁 Browse",
            command=self.browse_source,
            bg=self.theme['accent_cyan'],
            fg=self.theme['bg_primary'],
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            padx=20,
            pady=8,
            cursor='hand2',
            activebackground=self.theme['accent_magenta'],
            activeforeground=self.theme['text_primary']
        )
        browse_btn.grid(row=0, column=2, padx=10, pady=10)

        # Organization mode with modern radio buttons
        tk.Label(
            parent,
            text="Organization Mode:",
            bg=self.theme['bg_secondary'],
            fg=self.theme['text_primary'],
            font=('Segoe UI', 10, 'bold')
        ).grid(row=1, column=0, sticky=tk.W, pady=10)

        mode_frame = tk.Frame(parent, bg=self.theme['bg_secondary'])
        mode_frame.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=10)

        modes = [
            ("📁 Category Only", "category"),
            ("📅 Year Only", "year"),
            ("📁📅 Category → Year", "category_year")
        ]

        for i, (text, value) in enumerate(modes):
            tk.Radiobutton(
                mode_frame,
                text=text,
                variable=self.organization_mode,
                value=value,
                bg=self.theme['bg_secondary'],
                fg=self.theme['text_primary'],
                selectcolor=self.theme['bg_tertiary'],
                activebackground=self.theme['bg_secondary'],
                activeforeground=self.theme['accent_cyan'],
                font=('Segoe UI', 10),
                cursor='hand2'
            ).grid(row=0, column=i, padx=10)

        # Operation mode
        tk.Label(
            parent,
            text="Operation:",
            bg=self.theme['bg_secondary'],
            fg=self.theme['text_primary'],
            font=('Segoe UI', 10, 'bold')
        ).grid(row=2, column=0, sticky=tk.W, pady=10)

        op_frame = tk.Frame(parent, bg=self.theme['bg_secondary'])
        op_frame.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=10)

        operations = [
            ("🚚 Move Files (Remove from source)", "move"),
            ("📋 Copy Files (Keep source intact)", "copy")
        ]

        for i, (text, value) in enumerate(operations):
            tk.Radiobutton(
                op_frame,
                text=text,
                variable=self.operation_mode,
                value=value,
                bg=self.theme['bg_secondary'],
                fg=self.theme['text_primary'],
                selectcolor=self.theme['bg_tertiary'],
                activebackground=self.theme['bg_secondary'],
                activeforeground=self.theme['accent_magenta'],
                font=('Segoe UI', 10),
                cursor='hand2'
            ).grid(row=0, column=i, padx=10)

    def create_modern_options_panel(self, parent):
        """Create modern options panel"""
        parent.configure(bg=self.theme['bg_secondary'])

        options_left = tk.Frame(parent, bg=self.theme['bg_secondary'])
        options_left.grid(row=0, column=0, sticky=(tk.W, tk.N), padx=20)

        options_right = tk.Frame(parent, bg=self.theme['bg_secondary'])
        options_right.grid(row=0, column=1, sticky=(tk.W, tk.N), padx=20)

        # Left column options
        left_options = [
            ("✅ Skip Duplicates (MD5)", self.skip_duplicates),
            ("💾 Create Backup Before Processing", self.create_backup),
            ("🔍 DRY RUN (Preview Only)", self.dry_run)
        ]

        for i, (text, var) in enumerate(left_options):
            tk.Checkbutton(
                options_left,
                text=text,
                variable=var,
                bg=self.theme['bg_secondary'],
                fg=self.theme['text_primary'],
                selectcolor=self.theme['bg_tertiary'],
                activebackground=self.theme['bg_secondary'],
                activeforeground=self.theme['accent_green'],
                font=('Segoe UI', 10),
                cursor='hand2'
            ).grid(row=i, column=0, sticky=tk.W, pady=5)

        # Right column options
        tk.Checkbutton(
            options_right,
            text="🎨 Apply Custom Folder Icons",
            variable=self.apply_folder_icons,
            bg=self.theme['bg_secondary'],
            fg=self.theme['text_primary'],
            selectcolor=self.theme['bg_tertiary'],
            activebackground=self.theme['bg_secondary'],
            activeforeground=self.theme['accent_magenta'],
            font=('Segoe UI', 10),
            cursor='hand2'
        ).grid(row=0, column=0, sticky=tk.W, pady=5)

    def create_modern_action_buttons(self, parent):
        """Create modern action buttons with neon effect"""
        buttons = [
            ("▶️ Start Organization", self.start_organization, self.theme['accent_green'], 'start_btn'),
            ("⏹️ Stop", self.stop_organization, self.theme['error'], 'stop_btn'),
            ("🚫 Manage Exclusions", self.manage_exclusions, self.theme['accent_cyan'], None),
            ("♻️ Review Duplicates", self.review_duplicates, self.theme['accent_magenta'], None),
            ("⚙️ Settings", self.open_settings, self.theme['text_secondary'], None)
        ]

        for i, (text, command, color, attr) in enumerate(buttons):
            btn = tk.Button(
                parent,
                text=text,
                command=command,
                bg=color,
                fg=self.theme['text_primary'],
                font=('Segoe UI', 11, 'bold'),
                relief='flat',
                padx=20,
                pady=12,
                cursor='hand2',
                activebackground=self.theme['accent_cyan'],
                activeforeground=self.theme['bg_primary'],
                borderwidth=0
            )
            btn.grid(row=0, column=i, padx=5)

            if attr:
                setattr(self, attr, btn)
                if attr == 'stop_btn':
                    btn.config(state=tk.DISABLED)

    def create_modern_progress_section(self, parent):
        """Create modern progress section"""
        parent.configure(bg=self.theme['bg_secondary'])

        # Progress bar with neon glow
        self.progress_var = tk.DoubleVar()

        progress_container = tk.Frame(parent, bg=self.theme['bg_tertiary'], relief='flat')
        progress_container.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=10)
        parent.columnconfigure(0, weight=1)

        self.progress_bar = ttk.Progressbar(
            progress_container,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            style='Neon.Horizontal.TProgressbar'
        )
        self.progress_bar.pack(fill=tk.BOTH, padx=2, pady=2)

        # Progress label
        self.progress_label = tk.Label(
            parent,
            text="Ready to organize your files",
            bg=self.theme['bg_secondary'],
            fg=self.theme['accent_cyan'],
            font=('Segoe UI', 10, 'bold')
        )
        self.progress_label.grid(row=1, column=0, sticky=tk.W, pady=5)

        # Log output with dark theme
        log_frame = tk.Frame(parent, bg=self.theme['bg_tertiary'], relief='flat')
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        parent.rowconfigure(2, weight=1)

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            wrap=tk.WORD,
            bg=self.theme['bg_primary'],
            fg=self.theme['text_primary'],
            insertbackground=self.theme['accent_cyan'],
            font=('Consolas', 9),
            relief='flat',
            padx=10,
            pady=10,
            borderwidth=0
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)

        # Configure log text colors
        self.log_text.tag_config('INFO', foreground=self.theme['accent_cyan'])
        self.log_text.tag_config('SUCCESS', foreground=self.theme['success'])
        self.log_text.tag_config('WARNING', foreground=self.theme['warning'])
        self.log_text.tag_config('ERROR', foreground=self.theme['error'])

    def create_modern_status_bar(self, parent):
        """Create modern status bar"""
        status_frame = tk.Frame(
            parent,
            bg=self.theme['bg_secondary'],
            relief='flat',
            height=40
        )
        status_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(10, 0))

        self.status_label = tk.Label(
            status_frame,
            text="🟢 Ready",
            bg=self.theme['bg_secondary'],
            fg=self.theme['success'],
            font=('Segoe UI', 10, 'bold'),
            anchor=tk.W
        )
        self.status_label.pack(side=tk.LEFT, padx=10, pady=10)

        # Version label on right
        version_label = tk.Label(
            status_frame,
            text=f"v{self.VERSION}",
            bg=self.theme['bg_secondary'],
            fg=self.theme['text_secondary'],
            font=('Segoe UI', 9)
        )
        version_label.pack(side=tk.RIGHT, padx=10, pady=10)

    def add_theme_toggle(self):
        """Add theme toggle button"""
        # This would be added to the header or toolbar
        pass

    def toggle_theme(self):
        """Toggle between dark and light theme"""
        self.dark_mode.set(not self.dark_mode.get())
        self.theme = ModernTheme.get_theme(self.dark_mode.get())

        # Recreate UI with new theme
        for widget in self.root.winfo_children():
            widget.destroy()
        self.setup_ui()


def main():
    """Main entry point for modern UI"""
    root = tk.Tk()

    # Remove default window border for modern look (optional)
    # root.overrideredirect(True)  # Uncomment for frameless window

    app = FileOrganizerProModern(root)
    root.mainloop()


if __name__ == "__main__":
    main()
