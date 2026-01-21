"""
License Activation Dialog for FileOrganizer Pro

Handles license key entry and trial information.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional


class ActivationDialog(tk.Toplevel):
    """
    License activation dialog

    Features:
    - License key entry
    - Trial status display
    - Purchase link
    - Activation validation
    """

    def __init__(
        self,
        parent,
        license_manager,
        theme_engine=None,
        on_activate: Optional[Callable] = None
    ):
        """
        Initialize activation dialog

        Args:
            parent: Parent window
            license_manager: LicenseManager instance
            theme_engine: NeonThemeEngine instance
            on_activate: Callback when activated successfully
        """
        super().__init__(parent)

        self.license_manager = license_manager
        self.theme_engine = theme_engine
        self.on_activate = on_activate

        self.title("Activate FileOrganizer Pro")
        self.geometry("500x400")
        self.resizable(False, False)

        # Center on parent
        self.transient(parent)
        self.grab_set()

        # Get license status
        self.status = license_manager.get_status()

        self._setup_ui()

        # Apply theme if available
        if theme_engine:
            theme_engine.apply_theme(self)

    def _setup_ui(self):
        """Setup dialog UI"""
        # Main container
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        title_label = ttk.Label(
            header_frame,
            text="⚡ FileOrganizer Pro",
            font=('Segoe UI', 24, 'bold'),
            style='Neon.TLabel'
        )
        title_label.pack()

        version_label = ttk.Label(
            header_frame,
            text="Version 4.0 - Sci-Fi Edition",
            font=('Segoe UI', 10),
            style='NeonDim.TLabel'
        )
        version_label.pack()

        # Status section
        status_frame = ttk.LabelFrame(
            main_frame,
            text="License Status",
            padding=15,
            style='Neon.TLabelframe'
        )
        status_frame.pack(fill=tk.X, pady=(0, 20))

        if self.status['activated']:
            # Already activated
            status_icon = ttk.Label(
                status_frame,
                text="✓",
                font=('Segoe UI', 32),
                foreground='#00FF41',
                style='Neon.TLabel'
            )
            status_icon.pack()

            status_text = ttk.Label(
                status_frame,
                text="Software Activated",
                font=('Segoe UI', 14, 'bold'),
                style='Neon.TLabel'
            )
            status_text.pack(pady=(10, 5))

            key_text = ttk.Label(
                status_frame,
                text=f"License: {self.status['license_key'][:10]}...",
                font=('Segoe UI', 10),
                style='NeonDim.TLabel'
            )
            key_text.pack()

        elif self.status['trial_active']:
            # Trial active
            status_icon = ttk.Label(
                status_frame,
                text="⏱",
                font=('Segoe UI', 32),
                style='Neon.TLabel'
            )
            status_icon.pack()

            status_text = ttk.Label(
                status_frame,
                text=f"Trial Active: {self.status['trial_days_remaining']} Days Remaining",
                font=('Segoe UI', 14, 'bold'),
                style='Neon.TLabel'
            )
            status_text.pack(pady=(10, 5))

            trial_info = ttk.Label(
                status_frame,
                text="Enter a license key to unlock full version",
                font=('Segoe UI', 10),
                style='NeonDim.TLabel'
            )
            trial_info.pack()

        else:
            # Trial expired
            status_icon = ttk.Label(
                status_frame,
                text="⚠",
                font=('Segoe UI', 32),
                foreground='#FF8C00',
                style='Neon.TLabel'
            )
            status_icon.pack()

            status_text = ttk.Label(
                status_frame,
                text="Trial Expired",
                font=('Segoe UI', 14, 'bold'),
                foreground='#FF8C00',
                style='Neon.TLabel'
            )
            status_text.pack(pady=(10, 5))

            expired_info = ttk.Label(
                status_frame,
                text="Purchase a license to continue using FileOrganizer Pro",
                font=('Segoe UI', 10),
                style='NeonDim.TLabel'
            )
            expired_info.pack()

        # License key entry (if not activated)
        if not self.status['activated']:
            entry_frame = ttk.LabelFrame(
                main_frame,
                text="Enter License Key",
                padding=15,
                style='Neon.TLabelframe'
            )
            entry_frame.pack(fill=tk.X, pady=(0, 20))

            self.key_var = tk.StringVar()
            key_entry = ttk.Entry(
                entry_frame,
                textvariable=self.key_var,
                font=('Consolas', 12),
                width=30,
                style='Neon.TEntry'
            )
            key_entry.pack(fill=tk.X, pady=(0, 10))

            format_label = ttk.Label(
                entry_frame,
                text="Format: XXXX-XXXX-XXXX-XXXX",
                font=('Segoe UI', 9),
                style='NeonDim.TLabel'
            )
            format_label.pack()

            # Activate button
            activate_btn = ttk.Button(
                entry_frame,
                text="🔓 Activate",
                command=self._activate,
                style='NeonPrimary.TButton'
            )
            activate_btn.pack(fill=tk.X, pady=(10, 0))

        # Purchase section (if not activated)
        if not self.status['activated']:
            purchase_frame = ttk.Frame(main_frame)
            purchase_frame.pack(fill=tk.X, pady=(0, 10))

            purchase_label = ttk.Label(
                purchase_frame,
                text="Don't have a license?",
                font=('Segoe UI', 10),
                style='NeonDim.TLabel'
            )
            purchase_label.pack()

            purchase_btn = ttk.Button(
                purchase_frame,
                text="💳 Purchase License ($49)",
                command=self._open_purchase_link,
                style='NeonSecondary.TButton'
            )
            purchase_btn.pack(fill=tk.X, pady=(5, 0))

        # Bottom buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)

        if self.status['trial_active'] or self.status['activated']:
            continue_btn = ttk.Button(
                button_frame,
                text="Continue",
                command=self.destroy,
                style='Neon.TButton'
            )
            continue_btn.pack(side=tk.RIGHT)

        close_btn = ttk.Button(
            button_frame,
            text="Close" if (self.status['trial_active'] or self.status['activated']) else "Exit",
            command=self._close,
            style='Neon.TButton'
        )
        close_btn.pack(side=tk.RIGHT, padx=(0, 10))

    def _activate(self):
        """Activate with entered license key"""
        license_key = self.key_var.get().strip().upper()

        if not license_key:
            messagebox.showwarning(
                "No License Key",
                "Please enter a license key.",
                parent=self
            )
            return

        # Validate format
        if len(license_key) != 19 or license_key.count('-') != 3:
            messagebox.showerror(
                "Invalid Format",
                "License key must be in format: XXXX-XXXX-XXXX-XXXX",
                parent=self
            )
            return

        # Attempt activation
        if self.license_manager.activate(license_key):
            messagebox.showinfo(
                "Activation Successful",
                "FileOrganizer Pro has been activated!\n\nThank you for your purchase.",
                parent=self
            )

            # Callback
            if self.on_activate:
                self.on_activate()

            # Close dialog
            self.destroy()

        else:
            messagebox.showerror(
                "Activation Failed",
                "Invalid license key. Please check and try again.\n\n"
                "If you continue to have problems, contact support.",
                parent=self
            )

    def _open_purchase_link(self):
        """Open purchase link in browser"""
        import webbrowser

        # Replace with your actual purchase URL
        purchase_url = "https://gumroad.com/fileorganizerpro"  # Example

        webbrowser.open(purchase_url)

        messagebox.showinfo(
            "Purchase",
            "Opening purchase page in your browser.\n\n"
            "After purchasing, you'll receive a license key via email.",
            parent=self
        )

    def _close(self):
        """Close dialog"""
        if not self.status['can_use']:
            # Trial expired and not activated - exit app
            if messagebox.askyesno(
                "Exit Application",
                "Trial has expired. Purchase a license to continue.\n\nExit application?",
                parent=self
            ):
                self.master.quit()
        else:
            self.destroy()


# Example integration in main app
if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()

    from src.license_manager import LicenseManager

    license_mgr = LicenseManager()

    # Show activation dialog
    ActivationDialog(root, license_mgr)

    root.mainloop()
