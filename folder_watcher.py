"""
Smart Folder Watching System for FileOrganizer Pro
Monitors folders and automatically organizes new files

Author: David - JSMS Academy
License: Proprietary
"""

import time
import threading
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Callable, Optional, List
from collections import defaultdict

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    print("⚠️  watchdog not installed. Folder watching disabled.")
    print("   Install with: pip install watchdog")


class WatchedFolder:
    """Represents a folder being watched"""

    def __init__(self, folder_id: str, path: Path, config: Dict):
        self.folder_id = folder_id
        self.path = Path(path)
        self.config = config  # Organization settings
        self.enabled = True
        self.created_at = datetime.now()
        self.files_processed = 0
        self.last_activity = None

    def to_dict(self) -> Dict:
        """Serialize to dictionary"""
        return {
            'folder_id': self.folder_id,
            'path': str(self.path),
            'config': self.config,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat(),
            'files_processed': self.files_processed,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'WatchedFolder':
        """Deserialize from dictionary"""
        folder = cls(
            data['folder_id'],
            data['path'],
            data['config']
        )
        folder.enabled = data.get('enabled', True)
        folder.files_processed = data.get('files_processed', 0)

        if data.get('created_at'):
            folder.created_at = datetime.fromisoformat(data['created_at'])
        if data.get('last_activity'):
            folder.last_activity = datetime.fromisoformat(data['last_activity'])

        return folder


class FileOrganizerEventHandler(FileSystemEventHandler):
    """Handles file system events for organization"""

    def __init__(self, watched_folder: WatchedFolder, callback: Callable):
        super().__init__()
        self.watched_folder = watched_folder
        self.callback = callback
        self.processing_files = set()  # Track files being processed
        self.debounce_time = 2  # Wait 2 seconds before processing
        self.pending_files = {}  # file_path: timestamp

    def on_created(self, event):
        """Handle file creation events"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Ignore hidden files and temp files
        if file_path.name.startswith('.') or file_path.name.startswith('~'):
            return

        # Add to pending with debounce
        self.pending_files[file_path] = time.time()

        # Schedule processing
        threading.Timer(self.debounce_time, self._process_pending_file, args=[file_path]).start()

    def on_modified(self, event):
        """Handle file modification events"""
        # For now, we only care about new files, not modifications
        pass

    def _process_pending_file(self, file_path: Path):
        """Process a pending file after debounce period"""
        # Check if file is still pending and enough time has passed
        if file_path not in self.pending_files:
            return

        pending_time = self.pending_files[file_path]
        if time.time() - pending_time < self.debounce_time:
            return

        # Remove from pending
        del self.pending_files[file_path]

        # Skip if already processing
        if file_path in self.processing_files:
            return

        # Verify file still exists and is stable (not being written)
        if not file_path.exists():
            return

        try:
            # Check if file is still being written (size changing)
            size1 = file_path.stat().st_size
            time.sleep(0.5)
            if not file_path.exists():
                return
            size2 = file_path.stat().st_size

            if size1 != size2:
                # File still being written, re-queue
                self.pending_files[file_path] = time.time()
                threading.Timer(self.debounce_time, self._process_pending_file, args=[file_path]).start()
                return

            # File is stable, process it
            self.processing_files.add(file_path)

            print(f"[Watcher] New file detected: {file_path.name}")

            # Call organization callback
            if self.callback:
                self.callback(file_path, self.watched_folder.config)

            self.watched_folder.files_processed += 1
            self.watched_folder.last_activity = datetime.now()

        except Exception as e:
            print(f"[Watcher] Error processing {file_path}: {e}")

        finally:
            # Remove from processing
            self.processing_files.discard(file_path)


class FolderWatcher:
    """
    Monitors folders and automatically organizes new files

    Features:
    - Real-time file detection
    - Debouncing (wait for file to finish writing)
    - Multiple folder watching
    - Configurable organization per folder
    - Statistics tracking
    """

    def __init__(self, config_file: Optional[Path] = None, callback: Optional[Callable] = None):
        if not WATCHDOG_AVAILABLE:
            raise ImportError("watchdog library required for folder watching")

        self.config_file = config_file or Path("./watched_folders.json")
        self.callback = callback
        self.watched_folders: Dict[str, WatchedFolder] = {}
        self.observers: Dict[str, Observer] = {}
        self.is_running = False

        # Load persisted folders
        self.load_folders()

    def add_folder(self, path: Path, config: Dict) -> str:
        """
        Add a folder to watch

        Args:
            path: Directory to watch
            config: Organization settings for this folder

        Returns:
            folder_id of added folder
        """
        folder_id = f"folder_{int(datetime.now().timestamp())}"

        watched_folder = WatchedFolder(folder_id, path, config)
        self.watched_folders[folder_id] = watched_folder

        # Start watching if watcher is running
        if self.is_running:
            self._start_watching_folder(watched_folder)

        self.save_folders()

        return folder_id

    def remove_folder(self, folder_id: str) -> bool:
        """Stop watching a folder and remove it"""
        if folder_id not in self.watched_folders:
            return False

        # Stop observer
        if folder_id in self.observers:
            self.observers[folder_id].stop()
            self.observers[folder_id].join(timeout=2)
            del self.observers[folder_id]

        # Remove folder
        del self.watched_folders[folder_id]
        self.save_folders()

        return True

    def enable_folder(self, folder_id: str):
        """Enable watching for a folder"""
        if folder_id in self.watched_folders:
            self.watched_folders[folder_id].enabled = True

            if self.is_running:
                self._start_watching_folder(self.watched_folders[folder_id])

            self.save_folders()

    def disable_folder(self, folder_id: str):
        """Disable watching for a folder"""
        if folder_id in self.watched_folders:
            self.watched_folders[folder_id].enabled = False

            if folder_id in self.observers:
                self.observers[folder_id].stop()
                self.observers[folder_id].join(timeout=2)
                del self.observers[folder_id]

            self.save_folders()

    def _start_watching_folder(self, watched_folder: WatchedFolder):
        """Internal: Start watching a specific folder"""
        if not watched_folder.enabled:
            return

        if not watched_folder.path.exists():
            print(f"[Watcher] Folder does not exist: {watched_folder.path}")
            return

        try:
            # Create event handler
            event_handler = FileOrganizerEventHandler(watched_folder, self.callback)

            # Create observer
            observer = Observer()
            observer.schedule(event_handler, str(watched_folder.path), recursive=False)
            observer.start()

            self.observers[watched_folder.folder_id] = observer

            print(f"[Watcher] Now watching: {watched_folder.path}")

        except Exception as e:
            print(f"[Watcher] Failed to watch {watched_folder.path}: {e}")

    def start(self):
        """Start watching all enabled folders"""
        if self.is_running:
            return

        self.is_running = True

        for watched_folder in self.watched_folders.values():
            if watched_folder.enabled:
                self._start_watching_folder(watched_folder)

        print(f"[Watcher] Started watching {len(self.observers)} folders")

    def stop(self):
        """Stop watching all folders"""
        self.is_running = False

        for observer in self.observers.values():
            observer.stop()

        for observer in self.observers.values():
            observer.join(timeout=2)

        self.observers.clear()

        print("[Watcher] Stopped")

    def get_all_folders(self) -> List[WatchedFolder]:
        """Get list of all watched folders"""
        return list(self.watched_folders.values())

    def get_folder_stats(self, folder_id: str) -> Optional[Dict]:
        """Get statistics for a watched folder"""
        if folder_id not in self.watched_folders:
            return None

        folder = self.watched_folders[folder_id]
        return {
            'folder_id': folder.folder_id,
            'path': str(folder.path),
            'enabled': folder.enabled,
            'files_processed': folder.files_processed,
            'last_activity': folder.last_activity.strftime('%Y-%m-%d %H:%M:%S') if folder.last_activity else 'None',
            'watching': folder.folder_id in self.observers
        }

    def get_summary(self) -> Dict:
        """Get overall watcher statistics"""
        return {
            'total_folders': len(self.watched_folders),
            'active_watchers': len(self.observers),
            'enabled_folders': sum(1 for f in self.watched_folders.values() if f.enabled),
            'total_files_processed': sum(f.files_processed for f in self.watched_folders.values()),
            'is_running': self.is_running
        }

    def save_folders(self):
        """Persist watched folders to disk"""
        try:
            data = {
                'version': '1.0',
                'saved_at': datetime.now().isoformat(),
                'folders': {fid: folder.to_dict() for fid, folder in self.watched_folders.items()}
            }

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Warning: Could not save watched folders: {e}")

    def load_folders(self):
        """Load persisted watched folders"""
        if not self.config_file.exists():
            return

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for folder_id, folder_data in data.get('folders', {}).items():
                folder = WatchedFolder.from_dict(folder_data)
                self.watched_folders[folder_id] = folder

            print(f"[Watcher] Loaded {len(self.watched_folders)} folders")

        except Exception as e:
            print(f"Warning: Could not load watched folders: {e}")


# Example usage
if __name__ == "__main__":
    if not WATCHDOG_AVAILABLE:
        print("Please install watchdog: pip install watchdog")
        exit(1)

    def mock_organize(file_path, config):
        """Mock organization function"""
        print(f"  Organizing: {file_path}")
        print(f"  Config: {config}")

    # Create watcher
    watcher = FolderWatcher(callback=mock_organize)

    # Add a folder to watch
    folder_id = watcher.add_folder(
        path=Path("./test_watch"),
        config={'mode': 'category', 'skip_duplicates': True}
    )

    print(f"Added watched folder: {folder_id}")

    # Start watching
    watcher.start()

    print("\n✨ Folder watcher is now active!")
    print("Try creating a file in the watched folder...")
    print("Press Ctrl+C to stop")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping watcher...")
        watcher.stop()
