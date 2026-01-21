"""
FileOrganizer Pro 2.0
Professional File Organization and Duplicate Management System

Author: David - JSMS Academy
License: Proprietary
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import os
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import json
import threading
import queue

class FileOrganizerPro:
    """Main application class for FileOrganizer Pro 2.0"""
    
    VERSION = "2.0.0"
    
    def __init__(self, root):
        self.root = root
        self.root.title(f"FileOrganizer Pro {self.VERSION}")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 600)
        
        # Application state
        self.source_path = tk.StringVar()
        self.operation_mode = tk.StringVar(value="move")  # move or copy
        self.organization_mode = tk.StringVar(value="category")  # category, date, or category_date
        self.organize_by_year = tk.BooleanVar(value=True)
        self.skip_duplicates = tk.BooleanVar(value=True)
        self.create_backup = tk.BooleanVar(value=True)
        self.dry_run = tk.BooleanVar(value=True)
        self.apply_folder_icons = tk.BooleanVar(value=True)
        
        # Excluded folders - don't organize these
        self.excluded_folders = {}  # Changed to dict: {folder: enabled}
        self.load_default_exclusions()
        
        # Duplicates recycle bin settings
        self.duplicates_retention_days = tk.IntVar(value=30)  # Default 30 days
        self.auto_delete_duplicates = tk.BooleanVar(value=False)
        
        # Processing state
        self.is_processing = False
        self.processing_queue = queue.Queue()
        
        # File categories
        self.file_categories = {
            'Images': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', '.webp', 
                      '.svg', '.ico', '.heic', '.heif', '.raw', '.cr2', '.nef', '.arw', 
                      '.dng', '.orf', '.psd'},
            'Videos': {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm', '.m4v', 
                      '.mpg', '.mpeg', '.3gp', '.ogv'},
            'Documents': {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.tex', '.wpd', 
                         '.md', '.markdown'},
            'Spreadsheets': {'.xls', '.xlsx', '.csv', '.ods', '.xlsm', '.xlsb'},
            'Presentations': {'.ppt', '.pptx', '.odp', '.key'},
            'Audio': {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a', '.opus', 
                     '.aiff', '.ape'},
            'Archives': {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.iso', 
                        '.dmg', '.pkg'},
            'Code': {'.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.php', '.rb', 
                    '.go', '.rs', '.swift', '.kt', '.ts', '.html', '.css', '.scss', '.sql',
                    '.sh', '.bat', '.ps1', '.r', '.m', '.scala', '.lua'},
            'Executables': {'.exe', '.msi', '.app', '.deb', '.rpm', '.apk', '.dmg'},
            'Fonts': {'.ttf', '.otf', '.woff', '.woff2', '.eot'},
            'Others': set()  # Catch-all category
        }
        
        # Statistics
        self.stats = {
            'files_processed': 0,
            'files_moved': 0,
            'files_copied': 0,
            'duplicates_found': 0,
            'errors': 0,
            'space_saved': 0,
            'categories': defaultdict(int)
        }
        
        # Setup UI
        self.setup_ui()
        
    def load_default_exclusions(self):
        """Load default folder exclusions"""
        # Common folders to exclude from organization
        default_exclusions = [
            'node_modules',
            '.git',
            '.vscode',
            '.idea',
            '__pycache__',
            'venv',
            'env',
            '.env',
            'build',
            'dist',
            '.pytest_cache',
            '.mypy_cache',
            'Organized',  # Don't organize the output folder!
            'Duplicates_RecycleBin',  # Don't organize the recycle bin!
        ]
        # Set all as enabled by default
        for folder in default_exclusions:
            self.excluded_folders[folder] = True
        
    def is_excluded_folder(self, folder_path):
        """Check if folder should be excluded from organization"""
        folder_path = Path(folder_path)
        folder_name = folder_path.name.lower()
        
        # Check if folder name matches any enabled exclusion
        for excluded, enabled in self.excluded_folders.items():
            if not enabled:  # Skip disabled exclusions
                continue
            if excluded.lower() in str(folder_path).lower():
                return True
            if folder_name == excluded.lower():
                return True
        
        return False
        
    def setup_ui(self):
        """Create the user interface"""
        
        # Style configuration
        style = ttk.Style()
        style.theme_use('clam')
        
        # Main container
        main_container = ttk.Frame(self.root, padding="10")
        main_container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Header
        self.create_header(main_container)
        
        # Configuration panel
        config_frame = ttk.LabelFrame(main_container, text="Configuration", padding="10")
        config_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        self.create_config_panel(config_frame)
        
        # Options panel
        options_frame = ttk.LabelFrame(main_container, text="Options", padding="10")
        options_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        self.create_options_panel(options_frame)
        
        # Action buttons
        button_frame = ttk.Frame(main_container)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        self.create_action_buttons(button_frame)
        
        # Progress section
        progress_frame = ttk.LabelFrame(main_container, text="Progress", padding="10")
        progress_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        main_container.rowconfigure(4, weight=1)
        self.create_progress_section(progress_frame)
        
        # Status bar
        self.create_status_bar(main_container)
        
    def create_header(self, parent):
        """Create application header"""
        header = ttk.Frame(parent)
        header.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        title_label = ttk.Label(
            header, 
            text=f"FileOrganizer Pro {self.VERSION}",
            font=('Helvetica', 20, 'bold')
        )
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        subtitle_label = ttk.Label(
            header,
            text="Professional File Organization & Duplicate Management",
            font=('Helvetica', 10)
        )
        subtitle_label.grid(row=1, column=0, sticky=tk.W)
        
    def create_config_panel(self, parent):
        """Create configuration panel"""
        
        # Source directory
        ttk.Label(parent, text="Source Directory:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        source_entry = ttk.Entry(parent, textvariable=self.source_path, width=60)
        source_entry.grid(row=0, column=1, padx=5, pady=5, sticky=(tk.W, tk.E))
        
        browse_btn = ttk.Button(parent, text="Browse...", command=self.browse_source)
        browse_btn.grid(row=0, column=2, padx=5, pady=5)
        
        parent.columnconfigure(1, weight=1)
        
        # Organization mode
        ttk.Label(parent, text="Organization Mode:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        mode_frame = ttk.Frame(parent)
        mode_frame.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(
            mode_frame, 
            text="By Category Only", 
            variable=self.organization_mode, 
            value="category"
        ).grid(row=0, column=0, padx=5)
        
        ttk.Radiobutton(
            mode_frame, 
            text="By Year Only", 
            variable=self.organization_mode, 
            value="year"
        ).grid(row=0, column=1, padx=5)
        
        ttk.Radiobutton(
            mode_frame, 
            text="Category → Year", 
            variable=self.organization_mode, 
            value="category_year"
        ).grid(row=0, column=2, padx=5)
        
        # Operation mode
        ttk.Label(parent, text="Operation:").grid(row=2, column=0, sticky=tk.W, pady=5)
        
        op_frame = ttk.Frame(parent)
        op_frame.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=5)
        
        ttk.Radiobutton(
            op_frame, 
            text="Move Files (Remove from source)", 
            variable=self.operation_mode, 
            value="move"
        ).grid(row=0, column=0, padx=5)
        
        ttk.Radiobutton(
            op_frame, 
            text="Copy Files (Keep source intact)", 
            variable=self.operation_mode, 
            value="copy"
        ).grid(row=0, column=1, padx=5)
        
    def create_options_panel(self, parent):
        """Create options panel"""
        
        options_left = ttk.Frame(parent)
        options_left.grid(row=0, column=0, sticky=(tk.W, tk.N), padx=10)
        
        options_right = ttk.Frame(parent)
        options_right.grid(row=0, column=1, sticky=(tk.W, tk.N), padx=10)
        
        # Left column options
        ttk.Checkbutton(
            options_left,
            text="Skip Duplicates (MD5)",
            variable=self.skip_duplicates
        ).grid(row=0, column=0, sticky=tk.W, pady=3)
        
        ttk.Checkbutton(
            options_left,
            text="Create Backup Before Processing",
            variable=self.create_backup
        ).grid(row=1, column=0, sticky=tk.W, pady=3)
        
        ttk.Checkbutton(
            options_left,
            text="DRY RUN (Preview Only)",
            variable=self.dry_run
        ).grid(row=2, column=0, sticky=tk.W, pady=3)
        
        # Right column options
        ttk.Checkbutton(
            options_right,
            text="Apply Custom Folder Icons",
            variable=self.apply_folder_icons
        ).grid(row=0, column=0, sticky=tk.W, pady=3)
        
    def create_action_buttons(self, parent):
        """Create action buttons"""
        
        self.start_btn = ttk.Button(
            parent,
            text="Start Organization",
            command=self.start_organization,
            style='Accent.TButton',
            width=20
        )
        self.start_btn.grid(row=0, column=0, padx=5)
        
        self.stop_btn = ttk.Button(
            parent,
            text="Stop",
            command=self.stop_organization,
            state=tk.DISABLED,
            width=15
        )
        self.stop_btn.grid(row=0, column=1, padx=5)
        
        ttk.Button(
            parent,
            text="Manage Exclusions",
            command=self.manage_exclusions,
            width=18
        ).grid(row=0, column=2, padx=5)
        
        ttk.Button(
            parent,
            text="Review Duplicates",
            command=self.review_duplicates,
            width=18
        ).grid(row=0, column=3, padx=5)
        
        ttk.Button(
            parent,
            text="Settings",
            command=self.open_settings,
            width=15
        ).grid(row=0, column=4, padx=5)
        
    def create_progress_section(self, parent):
        """Create progress display section"""
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            parent,
            variable=self.progress_var,
            maximum=100,
            mode='determinate'
        )
        self.progress_bar.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        parent.columnconfigure(0, weight=1)
        
        # Progress label
        self.progress_label = ttk.Label(parent, text="Ready")
        self.progress_label.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        # Log output
        log_frame = ttk.Frame(parent)
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        parent.rowconfigure(2, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=15,
            wrap=tk.WORD,
            font=('Consolas', 9)
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
    def create_status_bar(self, parent):
        """Create status bar"""
        status_frame = ttk.Frame(parent, relief=tk.SUNKEN)
        status_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.grid(row=0, column=0, sticky=tk.W, padx=5)
        
    def browse_source(self):
        """Browse for source directory"""
        directory = filedialog.askdirectory(title="Select Source Directory")
        if directory:
            self.source_path.set(directory)
            self.log(f"Source directory selected: {directory}")
            
    def log(self, message, level="INFO"):
        """Add message to log (thread-safe)"""
        def _log():
            timestamp = datetime.now().strftime("%H:%M:%S")
            log_message = f"[{timestamp}] {level}: {message}\n"

            self.log_text.insert(tk.END, log_message)
            self.log_text.see(tk.END)
            self.log_text.update()

        # Execute in main thread if called from worker thread
        if threading.current_thread() != threading.main_thread():
            self.root.after(0, _log)
        else:
            _log()
        
    def update_status(self, message):
        """Update status bar (thread-safe)"""
        def _update():
            self.status_label.config(text=message)
            self.root.update()

        # Execute in main thread if called from worker thread
        if threading.current_thread() != threading.main_thread():
            self.root.after(0, _update)
        else:
            _update()

    def update_progress_label(self, message):
        """Update progress label (thread-safe)"""
        def _update():
            self.progress_label.config(text=message)

        # Execute in main thread if called from worker thread
        if threading.current_thread() != threading.main_thread():
            self.root.after(0, _update)
        else:
            _update()

    def start_organization(self):
        """Start the organization process"""
        
        # Validation
        if not self.source_path.get():
            messagebox.showerror("Error", "Please select a source directory")
            return
            
        if not os.path.exists(self.source_path.get()):
            messagebox.showerror("Error", "Source directory does not exist")
            return
        
        # Confirmation for non-dry-run
        if not self.dry_run.get():
            mode_text = "MOVE" if self.operation_mode.get() == "move" else "COPY"
            message = f"This will {mode_text} files from:\n{self.source_path.get()}\n\n"
            
            if self.operation_mode.get() == "move":
                message += "⚠️ WARNING: Files will be removed from their original locations!\n\n"
            
            message += "Are you sure you want to continue?"
            
            if not messagebox.askyesno("Confirm Operation", message):
                return
        
        # Disable controls
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.is_processing = True
        
        # Clear log and stats
        self.log_text.delete(1.0, tk.END)
        self.reset_stats()
        
        # Start processing in separate thread
        thread = threading.Thread(target=self.process_files, daemon=True)
        thread.start()
        
    def stop_organization(self):
        """Stop the organization process"""
        self.is_processing = False
        self.log("Stopping organization...", "WARNING")
        self.update_status("Stopping...")
        
    def process_files(self):
        """Main file processing logic"""
        try:
            source = Path(self.source_path.get())
            
            self.log("="*70)
            self.log(f"FileOrganizer Pro {self.VERSION} - Processing Started")
            self.log("="*70)
            self.log(f"Source: {source}")
            self.log(f"Mode: {self.operation_mode.get().upper()}")
            self.log(f"Organization: {self.organization_mode.get()}")
            self.log(f"Dry Run: {self.dry_run.get()}")
            self.log("="*70)
            
            # Create output folders
            output_base = source / "Organized"
            duplicates_folder = output_base / "Duplicates_RecycleBin"  # Changed to RecycleBin
            duplicates_metadata_file = duplicates_folder / "duplicates_metadata.json"
            
            if not self.dry_run.get():
                output_base.mkdir(exist_ok=True)
                duplicates_folder.mkdir(exist_ok=True)
            
            # Load existing duplicates metadata
            duplicates_metadata = {}
            if duplicates_metadata_file.exists():
                try:
                    with open(duplicates_metadata_file, 'r', encoding='utf-8') as f:
                        duplicates_metadata = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    self.log(f"Warning: Could not load duplicates metadata: {e}", "WARNING")
            
            # Phase 1: Scan all files
            self.log("\nPhase 1: Scanning files...")
            self.update_status("Scanning files...")
            
            all_files = []
            for root, dirs, files in os.walk(source):
                # Skip output folders
                if str(output_base) in root:
                    continue
                
                # Skip excluded folders
                if self.is_excluded_folder(root):
                    self.log(f"Skipping excluded folder: {root}", "INFO")
                    dirs[:] = []  # Don't descend into this folder
                    continue
                    
                for file in files:
                    all_files.append(Path(root) / file)
            
            total_files = len(all_files)
            self.log(f"Found {total_files} files to process")
            
            if total_files == 0:
                self.log("No files found to process", "WARNING")
                self.processing_complete()
                return
            
            # Phase 2: Process files
            self.log("\nPhase 2: Processing files...")
            self.update_status("Processing files...")
            
            hash_database = {}
            duplicate_groups = defaultdict(list)
            processed = 0
            
            for file_path in all_files:
                if not self.is_processing:
                    self.log("Processing stopped by user", "WARNING")
                    break
                
                processed += 1
                progress = (processed / total_files) * 100
                self.progress_var.set(progress)
                
                # Update progress every 10 files
                if processed % 10 == 0:
                    self.update_progress_label(
                        f"Processing: {processed}/{total_files} files "
                        f"({progress:.1f}%) - "
                        f"Moved: {self.stats['files_moved']}, "
                        f"Duplicates: {self.stats['duplicates_found']}"
                    )
                
                try:
                    self.process_single_file(
                        file_path, 
                        output_base,
                        duplicates_folder,
                        hash_database,
                        duplicate_groups
                    )
                except Exception as e:
                    self.stats['errors'] += 1
                    self.log(f"Error processing {file_path}: {e}", "ERROR")
            
            # Phase 3: Apply folder icons (if enabled)
            if self.apply_folder_icons.get() and not self.dry_run.get():
                self.log("\nPhase 3: Applying folder icons...")
                self.update_status("Applying folder icons...")
                self.apply_category_icons(output_base)
            
            # Phase 4: Generate reports
            self.log("\nPhase 4: Generating reports...")
            self.update_status("Generating reports...")
            self.generate_reports(output_base, hash_database, duplicate_groups)
            
            # Complete
            self.processing_complete()
            
        except Exception as e:
            self.log(f"Fatal error: {e}", "ERROR")
            messagebox.showerror("Error", f"An error occurred:\n{e}")
            self.processing_complete()
    
    def process_single_file(self, file_path, output_base, duplicates_folder, hash_database, duplicate_groups):
        """Process a single file"""
        
        self.stats['files_processed'] += 1
        
        # Get file category
        category = self.get_file_category(file_path)
        
        # Calculate MD5 if duplicate detection enabled
        if self.skip_duplicates.get():
            file_hash = self.calculate_md5(file_path)
            if file_hash is None:
                self.stats['errors'] += 1
                return
            
            # Check if duplicate
            if file_hash in hash_database:
                # This is a duplicate - move to recycle bin
                self.stats['duplicates_found'] += 1
                duplicate_groups[file_hash].append(str(file_path))
                
                destination = duplicates_folder / file_path.name
                destination = self.get_unique_filename(destination)
                
                if not self.dry_run.get():
                    self.move_or_copy_file(file_path, destination)
                    
                    # Save metadata with timestamp
                    metadata_file = duplicates_folder / "duplicates_metadata.json"
                    metadata = {}
                    if metadata_file.exists():
                        try:
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                metadata = json.load(f)
                        except (json.JSONDecodeError, IOError) as e:
                            self.log(f"Warning: Could not load metadata file: {e}", "WARNING")
                    
                    # Add entry for this duplicate
                    metadata[destination.name] = {
                        'timestamp': datetime.now().timestamp(),
                        'original_path': str(file_path),
                        'md5': file_hash,
                        'size': file_path.stat().st_size if file_path.exists() else 0,
                        'category': category
                    }
                    
                    # Save updated metadata
                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, indent=2)
                
                self.log(f"[DUPLICATE] {file_path.name} → Duplicates_RecycleBin/", "WARN")
                return
            
            # Record as original
            hash_database[file_hash] = {
                'path': str(file_path),
                'category': category,
                'size': file_path.stat().st_size
            }
        
        # Determine destination based on organization mode
        destination = self.get_destination_path(file_path, output_base, category)
        
        # Create destination folder
        if not self.dry_run.get():
            destination.parent.mkdir(parents=True, exist_ok=True)
        
        # Ensure unique filename
        destination = self.get_unique_filename(destination)
        
        # Move or copy file
        if not self.dry_run.get():
            self.move_or_copy_file(file_path, destination)
        
        self.stats['files_moved'] += 1
        self.stats['categories'][category] += 1
        
        # Log periodically
        if self.stats['files_processed'] % 50 == 0:
            self.log(f"Processed {self.stats['files_processed']} files...")
    
    def get_file_category(self, file_path):
        """Determine file category"""
        ext = file_path.suffix.lower()
        
        for category, extensions in self.file_categories.items():
            if ext in extensions:
                return category
        
        return 'Others'
    
    def get_destination_path(self, file_path, output_base, category):
        """Get destination path based on organization mode"""
        
        mode = self.organization_mode.get()
        
        if mode == "category":
            # Just category
            return output_base / category / file_path.name
            
        elif mode == "year":
            # Just year
            year = self.get_file_year(file_path)
            return output_base / year / file_path.name
            
        elif mode == "category_year":
            # Category then year
            year = self.get_file_year(file_path)
            return output_base / category / year / file_path.name
        
        return output_base / category / file_path.name
    
    def get_file_year(self, file_path):
        """Get year from file modification date"""
        try:
            mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            return str(mod_time.year)
        except:
            return "Unknown"
    
    def calculate_md5(self, file_path):
        """Calculate MD5 hash of file"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            self.log(f"Error calculating hash for {file_path}: {e}", "ERROR")
            return None
    
    def get_unique_filename(self, path):
        """Get unique filename if file exists"""
        if not path.exists():
            return path
        
        counter = 1
        while True:
            new_path = path.parent / f"{path.stem}_{counter}{path.suffix}"
            if not new_path.exists():
                return new_path
            counter += 1
    
    def move_or_copy_file(self, source, destination):
        """Move or copy file based on operation mode"""
        try:
            if self.operation_mode.get() == "move":
                shutil.move(str(source), str(destination))
            else:
                shutil.copy2(str(source), str(destination))
        except Exception as e:
            raise Exception(f"Failed to {self.operation_mode.get()} file: {e}")
    
    def apply_category_icons(self, output_base):
        """Apply custom icons to category folders"""
        # This would integrate with the icon system we discussed
        # For now, just log that it would happen
        self.log("Custom folder icons would be applied here")
        pass
    
    def generate_reports(self, output_base, hash_database, duplicate_groups):
        """Generate comprehensive reports"""
        
        if self.dry_run.get():
            self.log("\nDRY RUN - No reports generated")
            return
        
        # Summary report
        summary_path = output_base / "organization_summary.txt"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write("FILEORGANIZER PRO - ORGANIZATION SUMMARY\n")
            f.write("="*70 + "\n\n")
            f.write(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Source: {self.source_path.get()}\n")
            f.write(f"Operation: {self.operation_mode.get().upper()}\n")
            f.write(f"Organization Mode: {self.organization_mode.get()}\n\n")
            f.write("Results:\n")
            f.write(f"  Files Processed: {self.stats['files_processed']}\n")
            f.write(f"  Files Organized: {self.stats['files_moved']}\n")
            f.write(f"  Duplicates Found: {self.stats['duplicates_found']}\n")
            f.write(f"  Errors: {self.stats['errors']}\n\n")
            f.write("Category Breakdown:\n")
            for category, count in sorted(self.stats['categories'].items()):
                f.write(f"  {category}: {count} files\n")
        
        self.log(f"Summary report saved: {summary_path}")
        
        # Duplicate report
        if duplicate_groups:
            dup_report_path = output_base / "duplicate_report.txt"
            with open(dup_report_path, 'w', encoding='utf-8') as f:
                f.write("="*70 + "\n")
                f.write("DUPLICATE FILES REPORT\n")
                f.write("="*70 + "\n\n")
                f.write(f"Total Duplicates: {self.stats['duplicates_found']}\n")
                f.write(f"Duplicate Groups: {len(duplicate_groups)}\n")
                f.write(f"Location: Duplicates_RecycleBin/\n\n")
                
                if self.auto_delete_duplicates.get():
                    f.write(f"Auto-Delete: ENABLED\n")
                    f.write(f"Retention Period: {self.duplicates_retention_days.get()} days\n\n")
                else:
                    f.write(f"Auto-Delete: DISABLED\n")
                    f.write(f"Review duplicates using 'Review Duplicates' button\n\n")
                
                f.write("="*70 + "\n\n")
                
                for file_hash, dup_paths in duplicate_groups.items():
                    original = hash_database[file_hash]
                    f.write(f"Original: {original['path']}\n")
                    f.write(f"Category: {original['category']}\n")
                    f.write(f"Size: {original['size']:,} bytes\n")
                    f.write(f"MD5: {file_hash}\n")
                    f.write(f"Duplicates ({len(dup_paths)}):\n")
                    for dup in dup_paths:
                        f.write(f"  - {dup}\n")
                    f.write("\n" + "-"*70 + "\n\n")
            
            self.log(f"Duplicate report saved: {dup_report_path}")
    
    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            'files_processed': 0,
            'files_moved': 0,
            'files_copied': 0,
            'duplicates_found': 0,
            'errors': 0,
            'space_saved': 0,
            'categories': defaultdict(int)
        }
    
    def processing_complete(self):
        """Called when processing is complete"""
        self.is_processing = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.progress_var.set(100)
        
        self.log("\n" + "="*70)
        self.log("PROCESSING COMPLETE!")
        self.log("="*70)
        self.log(f"Files Processed: {self.stats['files_processed']}")
        self.log(f"Files Organized: {self.stats['files_moved']}")
        self.log(f"Duplicates Found: {self.stats['duplicates_found']}")
        self.log(f"Errors: {self.stats['errors']}")
        self.log("="*70)
        
        self.update_status("Complete!")
        
        if not self.dry_run.get():
            messagebox.showinfo(
                "Complete",
                f"Organization complete!\n\n"
                f"Files Organized: {self.stats['files_moved']}\n"
                f"Duplicates Found: {self.stats['duplicates_found']}\n"
                f"Errors: {self.stats['errors']}"
            )
    
    def view_reports(self):
        """Open reports viewer"""
        # Placeholder for reports viewer
        messagebox.showinfo("Reports", "Reports viewer coming soon!")
    
    def manage_exclusions(self):
        """Open exclusions management dialog with checkboxes"""
        
        # Create dialog window
        dialog = tk.Toplevel(self.root)
        dialog.title("Manage Excluded Folders")
        dialog.geometry("700x600")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header_frame = ttk.Frame(dialog, padding="10")
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)
        
        ttk.Label(
            header_frame,
            text="Excluded Folders",
            font=('Helvetica', 14, 'bold')
        ).grid(row=0, column=0, sticky=tk.W)
        
        ttk.Label(
            header_frame,
            text="Check folders to exclude from organization. Uncheck to include.",
            font=('Helvetica', 9)
        ).grid(row=1, column=0, sticky=tk.W)
        
        # Scrollable frame for checkboxes
        canvas_frame = ttk.Frame(dialog, padding="10")
        canvas_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)
        dialog.rowconfigure(1, weight=1)
        dialog.columnconfigure(0, weight=1)
        
        # Create canvas with scrollbar
        canvas = tk.Canvas(canvas_frame, bg='white', highlightthickness=1, highlightbackground='gray')
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        canvas_frame.rowconfigure(0, weight=1)
        canvas_frame.columnconfigure(0, weight=1)
        
        # Create checkboxes for each exclusion
        checkbox_vars = {}
        checkboxes = {}
        
        for i, (folder, enabled) in enumerate(sorted(self.excluded_folders.items())):
            var = tk.BooleanVar(value=enabled)
            checkbox_vars[folder] = var
            
            cb = ttk.Checkbutton(
                scrollable_frame,
                text=folder,
                variable=var,
                style='Custom.TCheckbutton'
            )
            cb.grid(row=i, column=0, sticky=tk.W, padx=20, pady=3)
            checkboxes[folder] = cb
        
        # Add/Remove buttons
        button_frame = ttk.Frame(dialog, padding="10")
        button_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        def add_exclusion():
            """Add new exclusion"""
            new_folder = tk.simpledialog.askstring(
                "Add Exclusion",
                "Enter folder name or path to exclude:\n(e.g., 'MyProject' or 'E:\\MyCode')",
                parent=dialog
            )
            
            if new_folder:
                new_folder = new_folder.strip()
                if new_folder and new_folder not in self.excluded_folders:
                    self.excluded_folders[new_folder] = True
                    
                    # Add checkbox dynamically
                    row = len(checkbox_vars)
                    var = tk.BooleanVar(value=True)
                    checkbox_vars[new_folder] = var
                    
                    cb = ttk.Checkbutton(
                        scrollable_frame,
                        text=new_folder,
                        variable=var
                    )
                    cb.grid(row=row, column=0, sticky=tk.W, padx=20, pady=3)
                    checkboxes[new_folder] = cb
                    
                    # Update canvas scroll region
                    scrollable_frame.update_idletasks()
                    canvas.configure(scrollregion=canvas.bbox("all"))
                    
                    self.log(f"Added exclusion: {new_folder}")
        
        def remove_selected():
            """Remove exclusions that are unchecked"""
            to_remove = []
            for folder, var in checkbox_vars.items():
                if not var.get():  # If unchecked, mark for removal
                    to_remove.append(folder)
            
            if not to_remove:
                messagebox.showinfo(
                    "No Selection", 
                    "Uncheck folders you want to remove, then click this button.",
                    parent=dialog
                )
                return
            
            if messagebox.askyesno(
                "Confirm Removal",
                f"Remove {len(to_remove)} unchecked exclusion(s)?",
                parent=dialog
            ):
                for folder in to_remove:
                    if folder in self.excluded_folders:
                        del self.excluded_folders[folder]
                    if folder in checkboxes:
                        checkboxes[folder].destroy()
                        del checkboxes[folder]
                        del checkbox_vars[folder]
                    self.log(f"Removed exclusion: {folder}")
        
        def select_all():
            """Check all exclusions"""
            for var in checkbox_vars.values():
                var.set(True)
        
        def deselect_all():
            """Uncheck all exclusions"""
            for var in checkbox_vars.values():
                var.set(False)
        
        def reset_defaults():
            """Reset to default exclusions"""
            if messagebox.askyesno(
                "Reset to Defaults",
                "This will reset exclusions to default list. Continue?",
                parent=dialog
            ):
                # Clear all checkboxes
                for cb in checkboxes.values():
                    cb.destroy()
                checkbox_vars.clear()
                checkboxes.clear()
                
                # Reload defaults
                self.excluded_folders.clear()
                self.load_default_exclusions()
                
                # Recreate checkboxes
                for i, (folder, enabled) in enumerate(sorted(self.excluded_folders.items())):
                    var = tk.BooleanVar(value=enabled)
                    checkbox_vars[folder] = var
                    
                    cb = ttk.Checkbutton(
                        scrollable_frame,
                        text=folder,
                        variable=var
                    )
                    cb.grid(row=i, column=0, sticky=tk.W, padx=20, pady=3)
                    checkboxes[folder] = cb
                
                # Update canvas
                scrollable_frame.update_idletasks()
                canvas.configure(scrollregion=canvas.bbox("all"))
                
                self.log("Reset exclusions to defaults")
        
        def save_and_close():
            """Save checkbox states and close"""
            # Update enabled/disabled states
            for folder, var in checkbox_vars.items():
                self.excluded_folders[folder] = var.get()
            
            enabled_count = sum(1 for enabled in self.excluded_folders.values() if enabled)
            self.log(f"Saved exclusions: {enabled_count} enabled, {len(self.excluded_folders) - enabled_count} disabled")
            dialog.destroy()
        
        # Button layout
        ttk.Button(
            button_frame,
            text="Add Exclusion",
            command=add_exclusion,
            width=15
        ).grid(row=0, column=0, padx=5)
        
        ttk.Button(
            button_frame,
            text="Remove Unchecked",
            command=remove_selected,
            width=18
        ).grid(row=0, column=1, padx=5)
        
        ttk.Button(
            button_frame,
            text="Check All",
            command=select_all,
            width=12
        ).grid(row=0, column=2, padx=5)
        
        ttk.Button(
            button_frame,
            text="Uncheck All",
            command=deselect_all,
            width=12
        ).grid(row=0, column=3, padx=5)
        
        ttk.Button(
            button_frame,
            text="Reset to Defaults",
            command=reset_defaults,
            width=15
        ).grid(row=0, column=4, padx=5)
        
        # Info section
        info_frame = ttk.LabelFrame(dialog, text="How It Works", padding="10")
        info_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)
        
        info_text = """✓ Checked folders = EXCLUDED (protected from organization)
✗ Unchecked folders = INCLUDED (will be organized)

Tip: Use "Add Exclusion" to protect your project folders like E:\\Development"""
        
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).grid(row=0, column=0, sticky=tk.W)
        
        # Close button
        close_frame = ttk.Frame(dialog, padding="10")
        close_frame.grid(row=4, column=0, sticky=(tk.E), padx=10, pady=10)
        
        ttk.Button(
            close_frame,
            text="Save & Close",
            command=save_and_close,
            width=15
        ).grid(row=0, column=0, padx=5)
        
        ttk.Button(
            close_frame,
            text="Cancel",
            command=dialog.destroy,
            width=15
        ).grid(row=0, column=1)
        
        # Center dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
    
    def review_duplicates(self):
        """Open duplicates review dialog"""
        
        # Get source path
        if not self.source_path.get():
            messagebox.showwarning(
                "No Source",
                "Please select a source directory first.",
                parent=self.root
            )
            return
        
        recycle_bin = Path(self.source_path.get()) / "Organized" / "Duplicates_RecycleBin"
        metadata_file = recycle_bin / "duplicates_metadata.json"
        
        if not recycle_bin.exists() or not any(recycle_bin.iterdir()):
            messagebox.showinfo(
                "No Duplicates",
                "No duplicates found in recycle bin.",
                parent=self.root
            )
            return
        
        # Load metadata
        duplicates_data = {}
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    duplicates_data = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                self.log(f"Warning: Could not load duplicates data: {e}", "WARNING")
        
        # Create dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Review Duplicates - Recycle Bin")
        dialog.geometry("900x700")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Header
        header_frame = ttk.Frame(dialog, padding="10")
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=10)
        
        ttk.Label(
            header_frame,
            text="Duplicates Recycle Bin",
            font=('Helvetica', 14, 'bold')
        ).grid(row=0, column=0, sticky=tk.W)
        
        # Count duplicates
        duplicate_files = list(recycle_bin.glob('*'))
        duplicate_files = [f for f in duplicate_files if f.is_file() and f.name != 'duplicates_metadata.json']
        
        info_text = f"Found {len(duplicate_files)} duplicate file(s) in recycle bin"
        ttk.Label(
            header_frame,
            text=info_text,
            font=('Helvetica', 10)
        ).grid(row=1, column=0, sticky=tk.W)
        
        # Settings frame
        settings_frame = ttk.LabelFrame(dialog, text="Auto-Delete Settings", padding="10")
        settings_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        ttk.Checkbutton(
            settings_frame,
            text="Enable auto-delete",
            variable=self.auto_delete_duplicates
        ).grid(row=0, column=0, sticky=tk.W, padx=5)
        
        ttk.Label(settings_frame, text="Delete after:").grid(row=0, column=1, sticky=tk.W, padx=(20, 5))
        
        retention_spinbox = ttk.Spinbox(
            settings_frame,
            from_=1,
            to=365,
            textvariable=self.duplicates_retention_days,
            width=10
        )
        retention_spinbox.grid(row=0, column=2, sticky=tk.W, padx=5)
        
        ttk.Label(settings_frame, text="days").grid(row=0, column=3, sticky=tk.W, padx=5)
        
        def clean_old_duplicates():
            """Delete duplicates older than retention period"""
            if not self.auto_delete_duplicates.get():
                messagebox.showinfo("Auto-Delete Disabled", "Please enable auto-delete first")
                return
            
            cutoff_days = self.duplicates_retention_days.get()
            cutoff_timestamp = datetime.now().timestamp() - (cutoff_days * 24 * 60 * 60)
            
            deleted_count = 0
            for file in duplicate_files:
                file_data = duplicates_data.get(file.name, {})
                moved_timestamp = file_data.get('timestamp', 0)
                
                if moved_timestamp < cutoff_timestamp:
                    try:
                        file.unlink()
                        deleted_count += 1
                        if file.name in duplicates_data:
                            del duplicates_data[file.name]
                    except Exception as e:
                        self.log(f"Error deleting {file}: {e}", "ERROR")
            
            # Save updated metadata
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(duplicates_data, f, indent=2)
            
            messagebox.showinfo(
                "Cleanup Complete",
                f"Deleted {deleted_count} duplicate(s) older than {cutoff_days} days"
            )
            dialog.destroy()
            self.review_duplicates()  # Refresh
        
        ttk.Button(
            settings_frame,
            text="Clean Old Duplicates Now",
            command=clean_old_duplicates
        ).grid(row=0, column=4, padx=20)
        
        # Listbox with scrollbar
        list_frame = ttk.Frame(dialog, padding="10")
        list_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)
        dialog.rowconfigure(2, weight=1)
        dialog.columnconfigure(0, weight=1)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            font=('Consolas', 9),
            selectmode=tk.EXTENDED,
            width=80
        )
        listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.rowconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        
        scrollbar.config(command=listbox.yview)
        
        # Populate listbox with file info
        for file in sorted(duplicate_files, key=lambda f: f.stat().st_mtime, reverse=True):
            file_data = duplicates_data.get(file.name, {})
            moved_time = file_data.get('timestamp', file.stat().st_mtime)
            moved_date = datetime.fromtimestamp(moved_time).strftime('%Y-%m-%d %H:%M')
            size = file.stat().st_size
            size_mb = size / (1024 * 1024)
            
            days_old = (datetime.now().timestamp() - moved_time) / (24 * 60 * 60)
            
            display_text = f"{file.name:50} | {moved_date} | {size_mb:8.2f} MB | {days_old:5.1f} days old"
            listbox.insert(tk.END, display_text)
        
        # Details frame
        details_frame = ttk.LabelFrame(dialog, text="Selected File Details", padding="10")
        details_frame.grid(row=2, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)
        dialog.columnconfigure(1, weight=0)
        
        details_text = scrolledtext.ScrolledText(
            details_frame,
            width=40,
            height=20,
            wrap=tk.WORD,
            font=('Consolas', 9)
        )
        details_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        details_frame.rowconfigure(0, weight=1)
        details_frame.columnconfigure(0, weight=1)
        
        def show_details(event=None):
            """Show details of selected file"""
            selection = listbox.curselection()
            if not selection:
                return
            
            index = selection[0]
            file = sorted(duplicate_files, key=lambda f: f.stat().st_mtime, reverse=True)[index]
            file_data = duplicates_data.get(file.name, {})
            
            details_text.delete(1.0, tk.END)
            details_text.insert(tk.END, f"File: {file.name}\n\n")
            details_text.insert(tk.END, f"Location:\n{file}\n\n")
            details_text.insert(tk.END, f"Size: {file.stat().st_size:,} bytes\n\n")
            
            moved_time = file_data.get('timestamp', file.stat().st_mtime)
            details_text.insert(tk.END, f"Moved to Recycle Bin:\n{datetime.fromtimestamp(moved_time).strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            if 'original_path' in file_data:
                details_text.insert(tk.END, f"Original Location:\n{file_data['original_path']}\n\n")
            
            if 'md5' in file_data:
                details_text.insert(tk.END, f"MD5 Hash:\n{file_data['md5']}\n\n")
            
            days_old = (datetime.now().timestamp() - moved_time) / (24 * 60 * 60)
            if self.auto_delete_duplicates.get():
                days_remaining = self.duplicates_retention_days.get() - days_old
                if days_remaining > 0:
                    details_text.insert(tk.END, f"Auto-delete in: {days_remaining:.1f} days\n")
                else:
                    details_text.insert(tk.END, f"Scheduled for deletion (overdue by {abs(days_remaining):.1f} days)\n")
        
        listbox.bind('<<ListboxSelect>>', show_details)
        
        # Action buttons
        button_frame = ttk.Frame(dialog, padding="10")
        button_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        def delete_selected():
            """Permanently delete selected duplicates"""
            selected = listbox.curselection()
            if not selected:
                messagebox.showwarning("No Selection", "Please select duplicates to delete")
                return
            
            if not messagebox.askyesno(
                "Confirm Deletion",
                f"Permanently delete {len(selected)} duplicate(s)?\nThis cannot be undone!",
                icon='warning'
            ):
                return
            
            sorted_files = sorted(duplicate_files, key=lambda f: f.stat().st_mtime, reverse=True)
            for index in reversed(selected):
                file = sorted_files[index]
                try:
                    file.unlink()
                    if file.name in duplicates_data:
                        del duplicates_data[file.name]
                    listbox.delete(index)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to delete {file.name}: {e}")
            
            # Save updated metadata
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(duplicates_data, f, indent=2)
            
            self.log(f"Deleted {len(selected)} duplicate(s)")
        
        def delete_all():
            """Delete all duplicates"""
            if not duplicate_files:
                return
            
            if not messagebox.askyesno(
                "Confirm Deletion",
                f"Permanently delete ALL {len(duplicate_files)} duplicate(s)?\nThis cannot be undone!",
                icon='warning'
            ):
                return
            
            count = 0
            for file in duplicate_files:
                try:
                    file.unlink()
                    count += 1
                except Exception as e:
                    self.log(f"Error deleting {file}: {e}", "ERROR")
            
            # Clear metadata
            metadata_file.unlink(missing_ok=True)
            
            messagebox.showinfo("Complete", f"Deleted {count} duplicate(s)")
            dialog.destroy()
        
        def open_folder():
            """Open recycle bin folder in file manager (cross-platform)"""
            import subprocess
            import platform

            system = platform.system()
            try:
                if system == "Windows":
                    subprocess.Popen(f'explorer "{recycle_bin}"')
                elif system == "Darwin":  # macOS
                    subprocess.Popen(['open', str(recycle_bin)])
                else:  # Linux and others
                    subprocess.Popen(['xdg-open', str(recycle_bin)])
            except Exception as e:
                messagebox.showerror("Error", f"Could not open folder: {e}")
        
        ttk.Button(
            button_frame,
            text="Delete Selected",
            command=delete_selected,
            width=18
        ).grid(row=0, column=0, padx=5)
        
        ttk.Button(
            button_frame,
            text="Delete All",
            command=delete_all,
            width=18
        ).grid(row=0, column=1, padx=5)
        
        ttk.Button(
            button_frame,
            text="Open Recycle Bin Folder",
            command=open_folder,
            width=22
        ).grid(row=0, column=2, padx=5)
        
        ttk.Button(
            button_frame,
            text="Close",
            command=dialog.destroy,
            width=15
        ).grid(row=0, column=3, padx=5)
        
        # Center dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
    
    def open_settings(self):
        """Open settings dialog"""
        # Placeholder for settings dialog
        messagebox.showinfo("Settings", "Settings dialog coming soon!")


def main():
    """Main entry point"""
    root = tk.Tk()
    app = FileOrganizerPro(root)
    root.mainloop()


if __name__ == "__main__":
    main()