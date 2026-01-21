"""
Search Workspace - Advanced file search interface
Multi-keyword semantic search with visual results grid

Features:
- Real-time search with autocomplete
- Advanced filter panel
- Thumbnail grid view
- Bulk actions on search results
- Search history
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from search_engine import SemanticSearchEngine, SearchFilter, SearchPresets, SearchResult


class SearchWorkspace(ttk.Frame):
    """
    Complete search workspace with filters and results

    Layout:
    ┌────────────────────────────────────┐
    │  Search Bar + Autocomplete         │
    ├────────────────────────────────────┤
    │  Filters (Type, Size, Date, Tags)  │
    ├────────────────────────────────────┤
    │  Results Grid (Thumbnails)         │
    │                                    │
    ├────────────────────────────────────┤
    │  Actions Toolbar                   │
    └────────────────────────────────────┘
    """

    def __init__(self, parent, theme_engine=None, tag_system=None):
        """
        Initialize search workspace

        Args:
            parent: Parent widget
            theme_engine: NeonThemeEngine instance
            tag_system: FileTaggingSystem instance
        """
        super().__init__(parent)

        self.theme_engine = theme_engine
        self.tag_system = tag_system
        self.search_engine = SemanticSearchEngine(tag_system=tag_system)
        self.current_results: List[SearchResult] = []
        self.selected_files: List[Path] = []

        # Configure style
        if theme_engine:
            self.configure(style='Glass.TFrame')

        self._setup_ui()
        self._bind_events()

    def _setup_ui(self):
        """Setup UI components"""

        # Main container
        container = ttk.Frame(self, style='Glass.TFrame' if self.theme_engine else 'TFrame')
        container.pack(fill='both', expand=True, padx=10, pady=10)

        # Header
        self._create_header(container)

        # Search bar
        self._create_search_bar(container)

        # Filters panel
        self._create_filters_panel(container)

        # Results area
        self._create_results_area(container)

        # Actions toolbar
        self._create_actions_toolbar(container)

        # Status bar
        self._create_status_bar(container)

    def _create_header(self, parent):
        """Create header with title"""
        header_frame = ttk.Frame(parent, style='Glass.TFrame' if self.theme_engine else 'TFrame')
        header_frame.pack(fill='x', pady=(0, 10))

        title = ttk.Label(
            header_frame,
            text="🔍 SEARCH INTERFACE",
            style='Header.TLabel' if self.theme_engine else 'TLabel',
            font=('Segoe UI', 16, 'bold')
        )
        title.pack(side='left')

        subtitle = ttk.Label(
            header_frame,
            text="Semantic multi-keyword search with advanced filters",
            style='Dim.TLabel' if self.theme_engine else 'TLabel'
        )
        subtitle.pack(side='left', padx=(10, 0))

    def _create_search_bar(self, parent):
        """Create search input with autocomplete"""
        search_frame = ttk.Frame(parent, style='Glass.TFrame' if self.theme_engine else 'TFrame')
        search_frame.pack(fill='x', pady=(0, 10))

        # Search icon
        icon_label = ttk.Label(search_frame, text="🔍", font=('Segoe UI', 14))
        icon_label.pack(side='left', padx=(0, 5))

        # Search entry
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=('Segoe UI', 12),
            style='Neon.TEntry' if self.theme_engine else 'TEntry'
        )
        self.search_entry.pack(side='left', fill='x', expand=True, ipady=8)

        # Search button
        search_btn = ttk.Button(
            search_frame,
            text="SEARCH",
            command=self._perform_search,
            style='Neon.TButton' if self.theme_engine else 'TButton'
        )
        search_btn.pack(side='left', padx=(5, 0))

        # Match all checkbox
        self.match_all_var = tk.BooleanVar(value=False)
        match_all_cb = ttk.Checkbutton(
            search_frame,
            text="Match ALL keywords",
            variable=self.match_all_var,
            style='Neon.TCheckbutton' if self.theme_engine else 'TCheckbutton'
        )
        match_all_cb.pack(side='left', padx=(10, 0))

    def _create_filters_panel(self, parent):
        """Create advanced filters panel"""
        filters_frame = ttk.LabelFrame(
            parent,
            text="FILTERS",
            style='Neon.TLabelframe' if self.theme_engine else 'TLabelframe',
            padding=10
        )
        filters_frame.pack(fill='x', pady=(0, 10))

        # Row 1: File types
        type_frame = ttk.Frame(filters_frame)
        type_frame.pack(fill='x', pady=5)

        ttk.Label(type_frame, text="Type:").pack(side='left', padx=(0, 5))

        self.type_vars = {}
        types = ['Images', 'Videos', 'Documents', 'Audio', 'Archives', 'Code']
        for file_type in types:
            var = tk.BooleanVar(value=False)
            self.type_vars[file_type] = var
            cb = ttk.Checkbutton(
                type_frame,
                text=file_type,
                variable=var,
                style='Neon.TCheckbutton' if self.theme_engine else 'TCheckbutton'
            )
            cb.pack(side='left', padx=5)

        # Row 2: Size range
        size_frame = ttk.Frame(filters_frame)
        size_frame.pack(fill='x', pady=5)

        ttk.Label(size_frame, text="Size:").pack(side='left', padx=(0, 5))

        self.size_min_var = tk.StringVar(value="0")
        self.size_max_var = tk.StringVar(value="")

        ttk.Label(size_frame, text="Min (MB):").pack(side='left', padx=(10, 2))
        size_min_entry = ttk.Entry(size_frame, textvariable=self.size_min_var, width=10)
        size_min_entry.pack(side='left')

        ttk.Label(size_frame, text="Max (MB):").pack(side='left', padx=(10, 2))
        size_max_entry = ttk.Entry(size_frame, textvariable=self.size_max_var, width=10)
        size_max_entry.pack(side='left')

        # Row 3: Date range
        date_frame = ttk.Frame(filters_frame)
        date_frame.pack(fill='x', pady=5)

        ttk.Label(date_frame, text="Date:").pack(side='left', padx=(0, 5))

        self.date_preset_var = tk.StringVar(value="All time")
        date_presets = ['All time', 'Today', 'Last 7 days', 'Last 30 days', 'Last year', 'Custom']
        date_combo = ttk.Combobox(
            date_frame,
            textvariable=self.date_preset_var,
            values=date_presets,
            state='readonly',
            width=15
        )
        date_combo.pack(side='left', padx=(10, 0))

        # Row 4: Actions
        action_frame = ttk.Frame(filters_frame)
        action_frame.pack(fill='x', pady=(10, 0))

        ttk.Button(
            action_frame,
            text="Apply Filters",
            command=self._perform_search,
            style='Neon.TButton' if self.theme_engine else 'TButton'
        ).pack(side='left', padx=(0, 5))

        ttk.Button(
            action_frame,
            text="Clear Filters",
            command=self._clear_filters,
            style='Ghost.TButton' if self.theme_engine else 'TButton'
        ).pack(side='left')

    def _create_results_area(self, parent):
        """Create results display area"""
        results_frame = ttk.LabelFrame(
            parent,
            text="RESULTS",
            style='Neon.TLabelframe' if self.theme_engine else 'TLabelframe',
            padding=10
        )
        results_frame.pack(fill='both', expand=True, pady=(0, 10))

        # View mode selector
        view_frame = ttk.Frame(results_frame)
        view_frame.pack(fill='x', pady=(0, 5))

        ttk.Label(view_frame, text="View:").pack(side='left', padx=(0, 5))

        self.view_mode_var = tk.StringVar(value="List")
        ttk.Radiobutton(
            view_frame,
            text="List",
            variable=self.view_mode_var,
            value="List",
            style='Neon.TRadiobutton' if self.theme_engine else 'TRadiobutton',
            command=self._switch_view_mode
        ).pack(side='left', padx=5)

        ttk.Radiobutton(
            view_frame,
            text="Grid",
            variable=self.view_mode_var,
            value="Grid",
            style='Neon.TRadiobutton' if self.theme_engine else 'TRadiobutton',
            command=self._switch_view_mode
        ).pack(side='left', padx=5)

        # Results container (will hold list or grid)
        self.results_container = ttk.Frame(results_frame)
        self.results_container.pack(fill='both', expand=True)

        # Create list view (default)
        self._create_list_view()

    def _create_list_view(self):
        """Create list view for results"""
        # Clear container
        for widget in self.results_container.winfo_children():
            widget.destroy()

        # Create treeview
        columns = ('Name', 'Size', 'Modified', 'Path', 'Score')
        self.results_tree = ttk.Treeview(
            self.results_container,
            columns=columns,
            show='headings',
            style='Neon.Treeview' if self.theme_engine else 'Treeview',
            selectmode='extended'
        )

        # Configure columns
        self.results_tree.heading('Name', text='Name')
        self.results_tree.heading('Size', text='Size')
        self.results_tree.heading('Modified', text='Modified')
        self.results_tree.heading('Path', text='Path')
        self.results_tree.heading('Score', text='Relevance')

        self.results_tree.column('Name', width=200)
        self.results_tree.column('Size', width=100)
        self.results_tree.column('Modified', width=150)
        self.results_tree.column('Path', width=300)
        self.results_tree.column('Score', width=80)

        # Scrollbar
        scrollbar = ttk.Scrollbar(
            self.results_container,
            orient='vertical',
            command=self.results_tree.yview,
            style='Neon.Vertical.TScrollbar' if self.theme_engine else 'Vertical.TScrollbar'
        )
        self.results_tree.configure(yscrollcommand=scrollbar.set)

        self.results_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

    def _create_grid_view(self):
        """Create grid view for results"""
        # Clear container
        for widget in self.results_container.winfo_children():
            widget.destroy()

        # Create canvas with scrollbar
        canvas = tk.Canvas(self.results_container, bg='#1A1F3A' if self.theme_engine else 'white')
        scrollbar = ttk.Scrollbar(
            self.results_container,
            orient='vertical',
            command=canvas.yview
        )
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.grid_frame = scrollable_frame

    def _create_actions_toolbar(self, parent):
        """Create actions toolbar for selected files"""
        toolbar_frame = ttk.Frame(parent, style='Glass.TFrame' if self.theme_engine else 'TFrame')
        toolbar_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(toolbar_frame, text="ACTIONS:").pack(side='left', padx=(0, 10))

        ttk.Button(
            toolbar_frame,
            text="📋 Export Results",
            command=self._export_results,
            style='Ghost.TButton' if self.theme_engine else 'TButton'
        ).pack(side='left', padx=2)

        ttk.Button(
            toolbar_frame,
            text="🏷 Tag Selected",
            command=self._tag_selected,
            style='Ghost.TButton' if self.theme_engine else 'TButton'
        ).pack(side='left', padx=2)

        ttk.Button(
            toolbar_frame,
            text="📁 Move to...",
            command=self._move_selected,
            style='Ghost.TButton' if self.theme_engine else 'TButton'
        ).pack(side='left', padx=2)

        ttk.Button(
            toolbar_frame,
            text="🗑 Delete",
            command=self._delete_selected,
            style='Danger.TButton' if self.theme_engine else 'TButton'
        ).pack(side='left', padx=2)

    def _create_status_bar(self, parent):
        """Create status bar"""
        self.status_label = ttk.Label(
            parent,
            text="Ready to search",
            style='Dim.TLabel' if self.theme_engine else 'TLabel'
        )
        self.status_label.pack(fill='x')

    def _bind_events(self):
        """Bind keyboard events"""
        self.search_entry.bind('<Return>', lambda e: self._perform_search())
        self.search_entry.bind('<KeyRelease>', self._on_search_change)

    def _on_search_change(self, event):
        """Handle search input change for autocomplete"""
        # Could show suggestions here
        pass

    def _perform_search(self):
        """Perform search with current query and filters"""
        query = self.search_var.get().strip()

        # Build filters
        filters = self._build_filters()

        if not query and not filters.has_filters():
            self.status_label.config(text="Please enter a search query or select filters")
            return

        # Update status
        self.status_label.config(text="Searching...")
        self.update_idletasks()

        # Perform search
        try:
            match_all = self.match_all_var.get()
            results = self.search_engine.search(query, filters, match_all)
            self.current_results = results

            # Display results
            self._display_results(results)

            # Update status
            self.status_label.config(
                text=f"Found {len(results)} file(s) matching '{query}'" if query else f"Found {len(results)} file(s)"
            )

        except Exception as e:
            messagebox.showerror("Search Error", f"Error performing search: {e}")
            self.status_label.config(text="Search error")

    def _build_filters(self) -> SearchFilter:
        """Build SearchFilter from UI inputs"""
        filters = SearchFilter()

        # File types
        filters.file_types = [t for t, var in self.type_vars.items() if var.get()]

        # Size range
        try:
            size_min = float(self.size_min_var.get() or 0)
            filters.size_min = int(size_min * 1024 * 1024)  # MB to bytes
        except:
            filters.size_min = None

        try:
            size_max_str = self.size_max_var.get()
            if size_max_str:
                size_max = float(size_max_str)
                filters.size_max = int(size_max * 1024 * 1024)
        except:
            filters.size_max = None

        # Date range
        date_preset = self.date_preset_var.get()
        if date_preset == 'Today':
            filters.date_min = datetime.now().replace(hour=0, minute=0, second=0)
        elif date_preset == 'Last 7 days':
            filters.date_min = datetime.now() - timedelta(days=7)
        elif date_preset == 'Last 30 days':
            filters.date_min = datetime.now() - timedelta(days=30)
        elif date_preset == 'Last year':
            filters.date_min = datetime.now() - timedelta(days=365)

        return filters

    def _display_results(self, results: List[SearchResult]):
        """Display search results in current view mode"""
        if self.view_mode_var.get() == "List":
            self._display_results_list(results)
        else:
            self._display_results_grid(results)

    def _display_results_list(self, results: List[SearchResult]):
        """Display results in list view"""
        # Clear existing
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        # Add results
        for result in results:
            name = result.file_path.name
            size = f"{result.metadata.get('size', 0) / (1024*1024):.2f} MB"
            modified = result.metadata.get('modified', datetime.now()).strftime('%Y-%m-%d %H:%M')
            path = str(result.file_path.parent)
            score = f"{result.score:.2f}"

            self.results_tree.insert('', 'end', values=(name, size, modified, path, score))

    def _display_results_grid(self, results: List[SearchResult]):
        """Display results in grid view"""
        # Create grid if not exists
        if not hasattr(self, 'grid_frame'):
            self._create_grid_view()

        # Clear grid
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        # Add result cards (3 per row)
        row = 0
        col = 0
        for result in results:
            card = self._create_result_card(result)
            card.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')

            col += 1
            if col >= 3:
                col = 0
                row += 1

    def _create_result_card(self, result: SearchResult):
        """Create a result card for grid view"""
        card = ttk.Frame(self.grid_frame, style='GlassElevated.TFrame' if self.theme_engine else 'TFrame', padding=10)

        # File icon (placeholder)
        icon_label = ttk.Label(card, text="📄", font=('Segoe UI', 24))
        icon_label.pack()

        # File name
        name_label = ttk.Label(card, text=result.file_path.name, wraplength=150)
        name_label.pack()

        # Size
        size_mb = result.metadata.get('size', 0) / (1024*1024)
        size_label = ttk.Label(
            card,
            text=f"{size_mb:.2f} MB",
            style='Dim.TLabel' if self.theme_engine else 'TLabel'
        )
        size_label.pack()

        return card

    def _switch_view_mode(self):
        """Switch between list and grid view"""
        if self.view_mode_var.get() == "List":
            self._create_list_view()
        else:
            self._create_grid_view()

        # Refresh results
        if self.current_results:
            self._display_results(self.current_results)

    def _clear_filters(self):
        """Clear all filters"""
        for var in self.type_vars.values():
            var.set(False)
        self.size_min_var.set("0")
        self.size_max_var.set("")
        self.date_preset_var.set("All time")

    def _export_results(self):
        """Export search results to file"""
        messagebox.showinfo("Export", "Export functionality will be implemented")

    def _tag_selected(self):
        """Tag selected files"""
        messagebox.showinfo("Tag", "Tag functionality will be implemented")

    def _move_selected(self):
        """Move selected files"""
        messagebox.showinfo("Move", "Move functionality will be implemented")

    def _delete_selected(self):
        """Delete selected files"""
        if messagebox.askyesno("Confirm Delete", "Delete selected files?"):
            messagebox.showinfo("Delete", "Delete functionality will be implemented")

    def update_file_index(self, file_paths: List[Path]):
        """Update search engine file index"""
        self.search_engine.update_index(file_paths)


# Demo/Test
if __name__ == '__main__':
    from theme_engine import NeonThemeEngine

    root = tk.Tk()
    root.title("Search Workspace Test")
    root.geometry("1200x800")

    # Apply theme
    theme = NeonThemeEngine('neon_dark')
    theme.apply_theme(root)

    # Create workspace
    workspace = SearchWorkspace(root, theme_engine=theme)
    workspace.pack(fill='both', expand=True)

    # Add sample files to index
    sample_files = [
        Path('E:/Photos/vacation_beach_2024.jpg'),
        Path('E:/Photos/family_dinner.png'),
        Path('E:/Downloads/video_tutorial.mp4'),
        Path('E:/Documents/report_2024.pdf'),
    ]
    workspace.update_file_index(sample_files)

    root.mainloop()
