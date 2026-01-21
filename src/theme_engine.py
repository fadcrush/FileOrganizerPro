"""
Neon Theme Engine for FileOrganizer Pro
Tron/Ghost in the Shell Inspired Sci-Fi UI System

Provides centralized theme management with glassmorphism and neon aesthetics
"""

import tkinter as tk
from tkinter import ttk
import json
from pathlib import Path
from typing import Dict, Any


class NeonThemeEngine:
    """
    Centralized theme engine with sci-fi neon palette
    Supports glassmorphism, neon glows, and cyberpunk aesthetics
    """

    # Core Neon Palette
    NEON_DARK_THEME = {
        # Primary Accents
        'cyan_primary': '#00F7FF',
        'violet_primary': '#B83FFF',
        'blue_electric': '#0066FF',

        # Status Colors
        'matrix_green': '#00FF41',
        'warning_orange': '#FF8C00',
        'danger_red': '#FF0055',

        # Backgrounds (Glass Layers)
        'void_black': '#0A0E27',
        'surface_dark': '#1A1F3A',
        'surface_mid': '#252B48',
        'surface_light': '#2D3454',

        # Text
        'text_white': '#FFFFFF',
        'text_cyan': '#A0E7FF',
        'text_dim': '#7A85A8',
        'text_disabled': '#4A5574',

        # Glows (RGBA for transparency)
        'glow_cyan': 'rgba(0, 247, 255, 0.5)',
        'glow_violet': 'rgba(184, 63, 255, 0.5)',
        'glow_green': 'rgba(0, 255, 65, 0.5)',

        # Gradients
        'gradient_primary': ['#00F7FF', '#0066FF'],
        'gradient_danger': ['#FF0055', '#B83FFF'],
        'gradient_success': ['#00FF41', '#00F7FF'],
    }

    # Light Neon Theme (enhanced)
    NEON_LIGHT_THEME = {
        # Primary Accents
        'cyan_primary': '#0099DD',
        'violet_primary': '#9933FF',
        'blue_electric': '#0066CC',

        # Status Colors
        'matrix_green': '#00AA33',
        'warning_orange': '#FF9900',
        'danger_red': '#DD0044',

        # Backgrounds (Light Layers)
        'void_black': '#F8F9FA',
        'surface_dark': '#FFFFFF',
        'surface_mid': '#F0F2F5',
        'surface_light': '#E4E6EB',

        # Text
        'text_white': '#1A1F3A',
        'text_cyan': '#0066CC',
        'text_dim': '#65676B',
        'text_disabled': '#A8ABAF',

        # Glows (RGBA for transparency)
        'glow_cyan': 'rgba(0, 153, 221, 0.3)',
        'glow_violet': 'rgba(153, 51, 255, 0.3)',
        'glow_green': 'rgba(0, 170, 51, 0.3)',

        # Gradients
        'gradient_primary': ['#0099DD', '#0066CC'],
        'gradient_danger': ['#DD0044', '#9933FF'],
        'gradient_success': ['#00AA33', '#0099DD'],
    }

    def __init__(self, theme_name: str = 'neon_dark'):
        """
        Initialize theme engine

        Args:
            theme_name: 'neon_dark' or 'neon_light'
        """
        self.theme_name = theme_name
        self.current_theme = self._load_theme(theme_name)
        self.custom_themes = {}
        self._load_custom_themes()

    def _load_theme(self, theme_name: str) -> Dict[str, Any]:
        """Load theme by name"""
        if theme_name == 'neon_dark':
            return self.NEON_DARK_THEME.copy()
        elif theme_name == 'neon_light':
            return self.NEON_LIGHT_THEME.copy()
        elif theme_name in self.custom_themes:
            return self.custom_themes[theme_name]
        else:
            return self.NEON_DARK_THEME.copy()

    def _load_custom_themes(self):
        """Load custom themes from assets/themes/"""
        themes_dir = Path(__file__).parent.parent / 'assets' / 'themes'
        if not themes_dir.exists():
            return

        for theme_file in themes_dir.glob('*.json'):
            try:
                with open(theme_file, 'r') as f:
                    theme_data = json.load(f)
                    if 'colors' in theme_data:
                        self.custom_themes[theme_file.stem] = theme_data['colors']
            except Exception:
                pass

    def apply_theme(self, root: tk.Tk):
        """
        Apply neon theme to tkinter application

        Args:
            root: Main Tk window
        """
        style = ttk.Style(root)

        # Try to use a modern base theme
        try:
            style.theme_use('clam')
        except:
            pass

        theme = self.current_theme

        # Configure root window
        root.configure(bg=theme['void_black'])

        # ===================
        # FRAMES
        # ===================

        # Glass Frame (Primary)
        style.configure(
            'Glass.TFrame',
            background=theme['surface_dark'],
            borderwidth=1,
            relief='flat'
        )

        # Elevated Glass Frame
        style.configure(
            'GlassElevated.TFrame',
            background=theme['surface_mid'],
            borderwidth=1,
            relief='flat'
        )

        # ===================
        # LABELS
        # ===================

        style.configure(
            'TLabel',
            background=theme['surface_dark'],
            foreground=theme['text_white'],
            font=('Segoe UI', 10)
        )

        style.configure(
            'Header.TLabel',
            background=theme['surface_dark'],
            foreground=theme['cyan_primary'],
            font=('Segoe UI', 16, 'bold')
        )

        style.configure(
            'Subheader.TLabel',
            background=theme['surface_dark'],
            foreground=theme['text_cyan'],
            font=('Segoe UI', 12)
        )

        style.configure(
            'Dim.TLabel',
            background=theme['surface_dark'],
            foreground=theme['text_dim'],
            font=('Segoe UI', 9)
        )

        # ===================
        # BUTTONS
        # ===================

        # Primary Neon Button
        style.configure(
            'Neon.TButton',
            background=theme['cyan_primary'],
            foreground='white',
            borderwidth=0,
            padding=(20, 10),
            font=('Segoe UI', 10, 'bold')
        )

        style.map(
            'Neon.TButton',
            background=[
                ('active', theme['blue_electric']),
                ('pressed', theme['violet_primary'])
            ],
            relief=[('pressed', 'flat'), ('!pressed', 'flat')]
        )

        # Danger Button
        style.configure(
            'Danger.TButton',
            background=theme['danger_red'],
            foreground='white',
            borderwidth=0,
            padding=(20, 10),
            font=('Segoe UI', 10, 'bold')
        )

        # Success Button
        style.configure(
            'Success.TButton',
            background=theme['matrix_green'],
            foreground=theme['void_black'],
            borderwidth=0,
            padding=(20, 10),
            font=('Segoe UI', 10, 'bold')
        )

        # Ghost Button (Outline)
        style.configure(
            'Ghost.TButton',
            background=theme['surface_dark'],
            foreground=theme['cyan_primary'],
            borderwidth=1,
            padding=(20, 10),
            font=('Segoe UI', 10)
        )

        # ===================
        # ENTRIES
        # ===================

        style.configure(
            'Neon.TEntry',
            fieldbackground=theme['surface_mid'],
            foreground=theme['text_white'],
            borderwidth=1,
            insertcolor=theme['cyan_primary'],
            padding=10
        )

        # ===================
        # CHECKBUTTONS
        # ===================

        style.configure(
            'Neon.TCheckbutton',
            background=theme['surface_dark'],
            foreground=theme['text_white'],
            font=('Segoe UI', 10),
            indicatorbackground=theme['surface_mid'],
            indicatorforeground=theme['cyan_primary']
        )

        # ===================
        # RADIOBUTTONS
        # ===================

        style.configure(
            'Neon.TRadiobutton',
            background=theme['surface_dark'],
            foreground=theme['text_white'],
            font=('Segoe UI', 10),
            indicatorbackground=theme['surface_mid'],
            indicatorforeground=theme['cyan_primary']
        )

        # ===================
        # LABELFRAMES
        # ===================

        style.configure(
            'Neon.TLabelframe',
            background=theme['surface_dark'],
            foreground=theme['cyan_primary'],
            borderwidth=1,
            relief='flat'
        )

        style.configure(
            'Neon.TLabelframe.Label',
            background=theme['surface_dark'],
            foreground=theme['cyan_primary'],
            font=('Segoe UI', 11, 'bold')
        )

        # ===================
        # PROGRESSBAR
        # ===================

        style.configure(
            'Neon.Horizontal.TProgressbar',
            background=theme['cyan_primary'],
            troughcolor=theme['surface_mid'],
            borderwidth=0,
            thickness=8
        )

        # ===================
        # NOTEBOOK (Tabs)
        # ===================

        style.configure(
            'Neon.TNotebook',
            background=theme['surface_dark'],
            borderwidth=0
        )

        style.configure(
            'Neon.TNotebook.Tab',
            background=theme['surface_mid'],
            foreground=theme['text_dim'],
            padding=(20, 10),
            borderwidth=0,
            font=('Segoe UI', 10)
        )

        style.map(
            'Neon.TNotebook.Tab',
            background=[('selected', theme['surface_dark'])],
            foreground=[('selected', theme['cyan_primary'])],
            expand=[('selected', [1, 1, 1, 0])]
        )

        # ===================
        # TREEVIEW
        # ===================

        style.configure(
            'Neon.Treeview',
            background=theme['surface_mid'],
            foreground=theme['text_white'],
            fieldbackground=theme['surface_mid'],
            borderwidth=0,
            font=('Segoe UI', 9)
        )

        style.configure(
            'Neon.Treeview.Heading',
            background=theme['surface_dark'],
            foreground=theme['cyan_primary'],
            borderwidth=0,
            font=('Segoe UI', 10, 'bold')
        )

        style.map(
            'Neon.Treeview',
            background=[('selected', theme['violet_primary'])],
            foreground=[('selected', 'white')]
        )

        # ===================
        # SCROLLBAR
        # ===================

        style.configure(
            'Neon.Vertical.TScrollbar',
            background=theme['surface_mid'],
            troughcolor=theme['surface_dark'],
            borderwidth=0,
            arrowcolor=theme['cyan_primary']
        )

        style.configure(
            'Neon.Horizontal.TScrollbar',
            background=theme['surface_mid'],
            troughcolor=theme['surface_dark'],
            borderwidth=0,
            arrowcolor=theme['cyan_primary']
        )

    def get_color(self, color_name: str) -> str:
        """Get color value by name"""
        return self.current_theme.get(color_name, '#FFFFFF')

    def create_gradient_label(self, parent, text, colors=None):
        """
        Create label with gradient text effect (simulated with color)
        Note: True gradients require custom drawing in tkinter
        """
        if colors is None:
            colors = self.current_theme['gradient_primary']

        label = ttk.Label(
            parent,
            text=text,
            style='Header.TLabel'
        )
        return label

    def save_custom_theme(self, theme_name: str, colors: Dict[str, str]):
        """Save custom theme to file"""
        themes_dir = Path(__file__).parent.parent / 'assets' / 'themes'
        themes_dir.mkdir(parents=True, exist_ok=True)

        theme_file = themes_dir / f'{theme_name}.json'
        theme_data = {
            'name': theme_name,
            'colors': colors,
            'version': '1.0'
        }

        with open(theme_file, 'w') as f:
            json.dump(theme_data, f, indent=2)

        self.custom_themes[theme_name] = colors

    def switch_theme(self, root: tk.Tk, theme_name: str):
        """Switch to different theme"""
        self.theme_name = theme_name
        self.current_theme = self._load_theme(theme_name)
        self.apply_theme(root)


# Singleton instance
_theme_engine_instance = None


def get_theme_engine(theme_name: str = 'neon_dark') -> NeonThemeEngine:
    """Get or create theme engine singleton"""
    global _theme_engine_instance
    if _theme_engine_instance is None:
        _theme_engine_instance = NeonThemeEngine(theme_name)
    return _theme_engine_instance


# Web Dashboard Theme (Tailwind Config Export)
def generate_tailwind_theme() -> dict:
    """
    Generate Tailwind CSS theme configuration
    For use in web-dashboard/tailwind.config.js
    """
    theme = NeonThemeEngine.NEON_DARK_THEME

    return {
        'colors': {
            'neon': {
                'cyan': theme['cyan_primary'],
                'violet': theme['violet_primary'],
                'blue': theme['blue_electric'],
                'green': theme['matrix_green'],
                'orange': theme['warning_orange'],
                'red': theme['danger_red'],
            },
            'void': theme['void_black'],
            'surface': {
                'dark': theme['surface_dark'],
                'mid': theme['surface_mid'],
                'light': theme['surface_light'],
            },
            'text': {
                'primary': theme['text_white'],
                'cyan': theme['text_cyan'],
                'dim': theme['text_dim'],
                'disabled': theme['text_disabled'],
            }
        },
        'fontFamily': {
            'display': ['Orbitron', 'Rajdhani', 'Exo 2', 'sans-serif'],
            'body': ['Inter', 'Roboto', 'sans-serif'],
            'mono': ['Fira Code', 'JetBrains Mono', 'monospace'],
        },
        'boxShadow': {
            'neon-sm': f"0 0 10px {theme['glow_cyan']}",
            'neon-md': f"0 0 20px {theme['glow_cyan']}",
            'neon-lg': f"0 0 30px {theme['glow_cyan']}",
            'neon-violet': f"0 0 20px {theme['glow_violet']}",
            'neon-green': f"0 0 20px {theme['glow_green']}",
        }
    }


if __name__ == '__main__':
    # Test theme engine
    root = tk.Tk()
    root.title("Neon Theme Engine Test")
    root.geometry("800x600")

    engine = NeonThemeEngine('neon_dark')
    engine.apply_theme(root)

    # Test components
    frame = ttk.Frame(root, style='Glass.TFrame', padding=20)
    frame.pack(fill='both', expand=True, padx=20, pady=20)

    ttk.Label(frame, text="Neon Theme Engine", style='Header.TLabel').pack(pady=10)
    ttk.Label(frame, text="Tron / Ghost in the Shell Aesthetic", style='Subheader.TLabel').pack(pady=5)

    ttk.Button(frame, text="Primary Action", style='Neon.TButton').pack(pady=5)
    ttk.Button(frame, text="Danger Action", style='Danger.TButton').pack(pady=5)
    ttk.Button(frame, text="Success Action", style='Success.TButton').pack(pady=5)

    ttk.Checkbutton(frame, text="Enable AI Categorization", style='Neon.TCheckbutton').pack(pady=5)

    progress = ttk.Progressbar(frame, style='Neon.Horizontal.TProgressbar', length=400)
    progress['value'] = 65
    progress.pack(pady=10)

    root.mainloop()
