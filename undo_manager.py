"""
Undo/Redo Manager for FileOrganizer Pro
Tracks all file operations and enables safe reversal

Author: David - JSMS Academy
License: Proprietary
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from collections import deque


class UndoOperation:
    """Represents a single undoable operation"""

    def __init__(self, operation_type: str, source: Path, destination: Path,
                 metadata: Optional[Dict] = None):
        self.operation_type = operation_type  # 'move', 'copy', 'delete'
        self.source = Path(source)
        self.destination = Path(destination)
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        self.id = f"{operation_type}_{self.timestamp.timestamp()}"

    def to_dict(self) -> Dict:
        """Serialize to dictionary"""
        return {
            'id': self.id,
            'type': self.operation_type,
            'source': str(self.source),
            'destination': str(self.destination),
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'UndoOperation':
        """Deserialize from dictionary"""
        op = cls(
            data['type'],
            data['source'],
            data['destination'],
            data.get('metadata', {})
        )
        op.id = data['id']
        op.timestamp = datetime.fromisoformat(data['timestamp'])
        return op


class UndoManager:
    """
    Manages undo/redo operations for file organization

    Features:
    - Track all file operations
    - Undo individual operations or entire jobs
    - Persist history across sessions
    - Verify files before undo
    - Report what will be undone
    """

    def __init__(self, history_file: Optional[Path] = None, max_history: int = 1000):
        self.history_file = history_file or Path("./undo_history.json")
        self.max_history = max_history

        # In-memory operation stacks
        self.undo_stack = deque(maxlen=max_history)
        self.redo_stack = deque(maxlen=max_history)

        # Current job operations (cleared after each job)
        self.current_job_operations = []
        self.current_job_id = None

        # Load persisted history
        self.load_history()

    def start_job(self, job_id: str):
        """Start tracking a new organization job"""
        self.current_job_id = job_id
        self.current_job_operations = []

    def record_operation(self, operation_type: str, source: Path, destination: Path,
                        metadata: Optional[Dict] = None):
        """
        Record a file operation for undo

        Args:
            operation_type: 'move', 'copy', or 'delete'
            source: Original file location
            destination: New file location
            metadata: Additional info (size, hash, category, etc.)
        """
        operation = UndoOperation(operation_type, source, destination, metadata)

        # Add to current job
        self.current_job_operations.append(operation)

        # Add to undo stack
        self.undo_stack.append(operation)

        # Clear redo stack (new operation invalidates redo)
        self.redo_stack.clear()

    def end_job(self, save_to_disk: bool = True):
        """Complete current job and optionally save to disk"""
        if save_to_disk:
            self.save_history()

        self.current_job_id = None
        self.current_job_operations = []

    def undo_last_operation(self) -> bool:
        """
        Undo the most recent operation

        Returns:
            True if successful, False otherwise
        """
        if not self.undo_stack:
            return False

        operation = self.undo_stack.pop()

        try:
            success = self._reverse_operation(operation)

            if success:
                # Move to redo stack
                self.redo_stack.append(operation)
                self.save_history()
                return True
            else:
                # Put back if failed
                self.undo_stack.append(operation)
                return False

        except Exception as e:
            # Restore to undo stack on error
            self.undo_stack.append(operation)
            raise Exception(f"Undo failed: {e}")

    def undo_last_job(self) -> Dict:
        """
        Undo entire last organization job

        Returns:
            Statistics about the undo operation
        """
        if not self.undo_stack:
            return {'success': False, 'message': 'No operations to undo'}

        # Find operations from the most recent job
        job_operations = []
        temp_stack = []

        # Get most recent job ID
        if self.undo_stack:
            last_job_time = self.undo_stack[-1].timestamp

            # Collect all operations from same time period (within 1 minute)
            while self.undo_stack:
                op = self.undo_stack.pop()
                time_diff = (last_job_time - op.timestamp).total_seconds()

                if time_diff <= 60:  # Same job if within 1 minute
                    job_operations.append(op)
                else:
                    # Different job, put back
                    temp_stack.append(op)
                    break

            # Restore non-job operations
            while temp_stack:
                self.undo_stack.append(temp_stack.pop())

        if not job_operations:
            return {'success': False, 'message': 'No job operations found'}

        # Reverse operations in reverse order (LIFO)
        stats = {
            'total': len(job_operations),
            'successful': 0,
            'failed': 0,
            'errors': []
        }

        for operation in job_operations:
            try:
                if self._reverse_operation(operation):
                    stats['successful'] += 1
                    self.redo_stack.append(operation)
                else:
                    stats['failed'] += 1
                    self.undo_stack.append(operation)  # Put back if failed
            except Exception as e:
                stats['failed'] += 1
                stats['errors'].append(str(e))
                self.undo_stack.append(operation)

        self.save_history()

        return {
            'success': stats['failed'] == 0,
            'stats': stats,
            'message': f"Undone {stats['successful']}/{stats['total']} operations"
        }

    def redo_last_operation(self) -> bool:
        """Redo the most recently undone operation"""
        if not self.redo_stack:
            return False

        operation = self.redo_stack.pop()

        try:
            success = self._apply_operation(operation)

            if success:
                self.undo_stack.append(operation)
                self.save_history()
                return True
            else:
                self.redo_stack.append(operation)
                return False

        except Exception as e:
            self.redo_stack.append(operation)
            raise Exception(f"Redo failed: {e}")

    def _reverse_operation(self, operation: UndoOperation) -> bool:
        """
        Reverse a file operation

        Returns:
            True if successful, False otherwise
        """
        try:
            if operation.operation_type == 'move':
                # Move file back to original location
                if operation.destination.exists():
                    # Ensure source directory exists
                    operation.source.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(operation.destination), str(operation.source))
                    return True
                else:
                    return False

            elif operation.operation_type == 'copy':
                # Delete the copied file
                if operation.destination.exists():
                    operation.destination.unlink()
                    return True
                else:
                    return False

            elif operation.operation_type == 'delete':
                # Restore from backup if available
                backup_path = operation.metadata.get('backup_path')
                if backup_path and Path(backup_path).exists():
                    operation.destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup_path, operation.destination)
                    return True
                else:
                    return False

            return False

        except Exception as e:
            raise Exception(f"Failed to reverse {operation.operation_type}: {e}")

    def _apply_operation(self, operation: UndoOperation) -> bool:
        """Re-apply an undone operation (for redo)"""
        try:
            if operation.operation_type == 'move':
                if operation.source.exists():
                    operation.destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(operation.source), str(operation.destination))
                    return True

            elif operation.operation_type == 'copy':
                if operation.source.exists():
                    operation.destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(str(operation.source), str(operation.destination))
                    return True

            return False

        except Exception:
            return False

    def preview_undo(self, count: int = 1) -> List[Dict]:
        """
        Preview what will be undone without actually undoing

        Args:
            count: Number of operations to preview

        Returns:
            List of operation details
        """
        preview = []

        for i in range(min(count, len(self.undo_stack))):
            op = list(self.undo_stack)[-(i+1)]
            preview.append({
                'type': op.operation_type,
                'source': str(op.source),
                'destination': str(op.destination),
                'timestamp': op.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'exists': op.destination.exists()
            })

        return preview

    def get_history_summary(self) -> Dict:
        """Get summary of undo/redo history"""
        return {
            'undo_available': len(self.undo_stack),
            'redo_available': len(self.redo_stack),
            'total_operations': len(self.undo_stack) + len(self.redo_stack),
            'current_job_operations': len(self.current_job_operations)
        }

    def save_history(self):
        """Persist undo history to disk"""
        try:
            data = {
                'version': '1.0',
                'saved_at': datetime.now().isoformat(),
                'undo_stack': [op.to_dict() for op in self.undo_stack],
                'redo_stack': [op.to_dict() for op in self.redo_stack]
            }

            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            print(f"Warning: Could not save undo history: {e}")

    def load_history(self):
        """Load persisted undo history"""
        if not self.history_file.exists():
            return

        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Restore undo stack
            self.undo_stack.clear()
            for op_data in data.get('undo_stack', []):
                self.undo_stack.append(UndoOperation.from_dict(op_data))

            # Restore redo stack
            self.redo_stack.clear()
            for op_data in data.get('redo_stack', []):
                self.redo_stack.append(UndoOperation.from_dict(op_data))

        except Exception as e:
            print(f"Warning: Could not load undo history: {e}")

    def clear_history(self):
        """Clear all undo/redo history"""
        self.undo_stack.clear()
        self.redo_stack.clear()
        self.current_job_operations.clear()

        if self.history_file.exists():
            self.history_file.unlink()


# Example usage
if __name__ == "__main__":
    # Demo the undo manager
    undo_mgr = UndoManager()

    print("Undo Manager - Demo")
    print("=" * 50)

    # Simulate some operations
    undo_mgr.start_job("test_job_1")
    undo_mgr.record_operation('move', Path("file1.txt"), Path("organized/file1.txt"))
    undo_mgr.record_operation('move', Path("file2.txt"), Path("organized/file2.txt"))
    undo_mgr.end_job()

    # Check history
    summary = undo_mgr.get_history_summary()
    print(f"\nHistory: {summary}")

    # Preview undo
    preview = undo_mgr.preview_undo(2)
    print(f"\nPreview undo: {len(preview)} operations")
    for op in preview:
        print(f"  - {op['type']}: {op['destination']}")

    print("\n✅ Undo Manager ready!")
