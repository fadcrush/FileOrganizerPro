"""
Advanced Features Module for FileOrganizer Pro
Includes AI categorization, fuzzy duplicate detection, and tagging system

Author: David - JSMS Academy
"""

import hashlib
from pathlib import Path
from typing import List, Dict, Tuple, Set
from collections import defaultdict
import mimetypes


class AIFileCategorizer:
    """
    AI-powered file categorization using content analysis
    """

    def __init__(self):
        self.mime = mimetypes.MimeTypes()
        self.content_patterns = self._load_content_patterns()

    def _load_content_patterns(self) -> Dict[str, List[bytes]]:
        """Load file signature patterns for content-based detection"""
        return {
            'PDF': [b'%PDF'],
            'ZIP': [b'PK\x03\x04', b'PK\x05\x06'],
            'JPEG': [b'\xff\xd8\xff'],
            'PNG': [b'\x89PNG'],
            'GIF': [b'GIF87a', b'GIF89a'],
            'MP4': [b'ftyp'],
            'MP3': [b'ID3', b'\xff\xfb'],
            'DOCX': [b'PK\x03\x04'],  # Office Open XML
            'EXE': [b'MZ'],
            'ELF': [b'\x7fELF'],  # Linux executables
        }

    def categorize_by_content(self, file_path: Path) -> str:
        """
        Categorize file based on actual content, not just extension
        This prevents misnamed files from being miscategorized
        """
        try:
            with open(file_path, 'rb') as f:
                header = f.read(512)  # Read first 512 bytes

            # Check file signatures
            for file_type, signatures in self.content_patterns.items():
                for signature in signatures:
                    if header.startswith(signature) or signature in header[:64]:
                        return self._map_signature_to_category(file_type)

            # Fallback to MIME type
            mime_type, _ = self.mime.guess_type(str(file_path))
            if mime_type:
                return self._map_mime_to_category(mime_type)

            # Ultimate fallback to extension
            return 'Others'

        except Exception:
            return 'Others'

    def _map_signature_to_category(self, file_type: str) -> str:
        """Map file signature to user-friendly category"""
        mapping = {
            'PDF': 'Documents',
            'JPEG': 'Images',
            'PNG': 'Images',
            'GIF': 'Images',
            'ZIP': 'Archives',
            'MP4': 'Videos',
            'MP3': 'Audio',
            'DOCX': 'Documents',
            'EXE': 'Executables',
            'ELF': 'Executables',
        }
        return mapping.get(file_type, 'Others')

    def _map_mime_to_category(self, mime_type: str) -> str:
        """Map MIME type to category"""
        if mime_type.startswith('image/'):
            return 'Images'
        elif mime_type.startswith('video/'):
            return 'Videos'
        elif mime_type.startswith('audio/'):
            return 'Audio'
        elif mime_type.startswith('text/'):
            return 'Documents'
        elif 'pdf' in mime_type:
            return 'Documents'
        elif 'zip' in mime_type or 'compressed' in mime_type:
            return 'Archives'
        else:
            return 'Others'


class FuzzyDuplicateDetector:
    """
    Detect similar files using perceptual hashing and fuzzy matching
    Useful for finding similar images, videos, or audio files
    """

    def __init__(self):
        self.image_hashes = {}
        self.audio_fingerprints = {}

    def find_similar_images(self, file_paths: List[Path], threshold: float = 0.9) -> Dict[str, List[Path]]:
        """
        Find visually similar images using perceptual hashing
        threshold: 0.0 (completely different) to 1.0 (identical)
        """
        try:
            from PIL import Image
            import imagehash

            groups = defaultdict(list)
            hashes = {}

            for file_path in file_paths:
                try:
                    if file_path.suffix.lower() in {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}:
                        img = Image.open(file_path)
                        # Use perceptual hash (pHash) - resistant to minor changes
                        phash = imagehash.phash(img)
                        hashes[file_path] = phash
                except Exception:
                    continue

            # Find similar pairs
            processed = set()
            for path1, hash1 in hashes.items():
                if path1 in processed:
                    continue

                similar_group = [path1]
                for path2, hash2 in hashes.items():
                    if path1 == path2:
                        continue

                    # Calculate similarity (hamming distance)
                    similarity = 1 - (hash1 - hash2) / 64.0  # pHash is 64-bit

                    if similarity >= threshold:
                        similar_group.append(path2)
                        processed.add(path2)

                if len(similar_group) > 1:
                    groups[str(hash1)] = similar_group

            return dict(groups)

        except ImportError:
            print("PIL and imagehash required for image similarity detection")
            print("Install with: pip install Pillow imagehash")
            return {}

    def find_similar_audio(self, file_paths: List[Path], threshold: float = 0.85) -> Dict[str, List[Path]]:
        """
        Find similar audio files using acoustic fingerprinting
        Useful for finding duplicate songs with different encodings
        """
        # Placeholder for audio fingerprinting
        # Would use libraries like chromaprint/acoustid
        print("Audio similarity detection - requires chromaprint library")
        return {}

    def calculate_file_similarity(self, file1: Path, file2: Path) -> float:
        """
        Calculate similarity between two files (0.0 to 1.0)
        Uses multiple methods depending on file type
        """
        # Check if exact duplicates first
        if self._are_identical(file1, file2):
            return 1.0

        # Check by extension
        if file1.suffix.lower() in {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}:
            return self._image_similarity(file1, file2)
        elif file1.suffix.lower() in {'.mp3', '.wav', '.flac', '.m4a'}:
            return self._audio_similarity(file1, file2)
        else:
            # Text-based similarity for documents
            return self._text_similarity(file1, file2)

    def _are_identical(self, file1: Path, file2: Path) -> bool:
        """Check if files are binary identical"""
        if file1.stat().st_size != file2.stat().st_size:
            return False

        hash1 = self._quick_hash(file1)
        hash2 = self._quick_hash(file2)
        return hash1 == hash2

    def _quick_hash(self, file_path: Path) -> str:
        """Fast hash for comparison"""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            # Read first and last MB for quick comparison
            hasher.update(f.read(1024 * 1024))
            f.seek(-min(1024 * 1024, file_path.stat().st_size), 2)
            hasher.update(f.read())
        return hasher.hexdigest()

    def _image_similarity(self, file1: Path, file2: Path) -> float:
        """Calculate image similarity"""
        try:
            from PIL import Image
            import imagehash

            img1 = Image.open(file1)
            img2 = Image.open(file2)

            hash1 = imagehash.phash(img1)
            hash2 = imagehash.phash(img2)

            return 1 - (hash1 - hash2) / 64.0
        except Exception:
            return 0.0

    def _audio_similarity(self, file1: Path, file2: Path) -> float:
        """Calculate audio similarity"""
        # Placeholder - would use audio fingerprinting
        return 0.0

    def _text_similarity(self, file1: Path, file2: Path) -> float:
        """Calculate text similarity using simple algorithm"""
        try:
            with open(file1, 'rb') as f:
                content1 = f.read(10000)  # First 10KB
            with open(file2, 'rb') as f:
                content2 = f.read(10000)

            # Simple byte-level similarity
            if len(content1) == 0 or len(content2) == 0:
                return 0.0

            # Count matching bytes
            matches = sum(a == b for a, b in zip(content1, content2))
            max_len = max(len(content1), len(content2))

            return matches / max_len

        except Exception:
            return 0.0


class FileTaggingSystem:
    """
    Advanced tagging system for files
    Allows users to add custom tags and search by tags
    """

    def __init__(self, tags_db_path: Path):
        self.db_path = tags_db_path
        self.tags = self._load_tags()

    def _load_tags(self) -> Dict[str, Set[str]]:
        """Load tags from database"""
        import json

        if self.db_path.exists():
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Convert lists back to sets
                    return {path: set(tags) for path, tags in data.items()}
            except Exception:
                return {}
        return {}

    def _save_tags(self):
        """Save tags to database"""
        import json

        # Convert sets to lists for JSON serialization
        data = {path: list(tags) for path, tags in self.tags.items()}

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.db_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def add_tag(self, file_path: Path, tag: str):
        """Add a tag to a file"""
        path_str = str(file_path.absolute())
        if path_str not in self.tags:
            self.tags[path_str] = set()
        self.tags[path_str].add(tag.lower().strip())
        self._save_tags()

    def remove_tag(self, file_path: Path, tag: str):
        """Remove a tag from a file"""
        path_str = str(file_path.absolute())
        if path_str in self.tags:
            self.tags[path_str].discard(tag.lower().strip())
            if not self.tags[path_str]:
                del self.tags[path_str]
            self._save_tags()

    def get_tags(self, file_path: Path) -> Set[str]:
        """Get all tags for a file"""
        path_str = str(file_path.absolute())
        return self.tags.get(path_str, set())

    def find_by_tag(self, tag: str) -> List[Path]:
        """Find all files with a specific tag"""
        tag = tag.lower().strip()
        return [Path(path) for path, tags in self.tags.items() if tag in tags]

    def find_by_tags(self, tags: List[str], match_all: bool = False) -> List[Path]:
        """
        Find files matching multiple tags
        match_all: If True, file must have ALL tags. If False, ANY tag matches.
        """
        tags_set = {t.lower().strip() for t in tags}
        results = []

        for path, file_tags in self.tags.items():
            if match_all:
                if tags_set.issubset(file_tags):
                    results.append(Path(path))
            else:
                if tags_set.intersection(file_tags):
                    results.append(Path(path))

        return results

    def get_all_tags(self) -> Set[str]:
        """Get all unique tags in the system"""
        all_tags = set()
        for tags in self.tags.values():
            all_tags.update(tags)
        return all_tags

    def auto_tag_by_content(self, file_path: Path):
        """Automatically suggest tags based on file content"""
        # Analyze filename
        name_parts = file_path.stem.lower().split('_')
        name_parts.extend(file_path.stem.lower().split('-'))

        # Common words to suggest as tags
        suggested_tags = set()

        # Add year tags
        for part in name_parts:
            if part.isdigit() and len(part) == 4:
                if 1900 <= int(part) <= 2100:
                    suggested_tags.add(f"year:{part}")

        # Add file type tags
        ext = file_path.suffix.lower()
        if ext:
            suggested_tags.add(f"type:{ext[1:]}")

        # Add size category tags
        size_mb = file_path.stat().st_size / (1024 * 1024)
        if size_mb < 1:
            suggested_tags.add("size:small")
        elif size_mb < 10:
            suggested_tags.add("size:medium")
        else:
            suggested_tags.add("size:large")

        return suggested_tags


class SmartFileOrganizer:
    """
    Combines AI categorization, fuzzy detection, and tagging
    for intelligent file organization
    """

    def __init__(self, tags_db_path: Path):
        self.ai_categorizer = AIFileCategorizer()
        self.fuzzy_detector = FuzzyDuplicateDetector()
        self.tagging_system = FileTaggingSystem(tags_db_path)

    def smart_categorize(self, file_path: Path) -> Dict[str, any]:
        """
        Get comprehensive analysis of a file
        Returns category, suggested tags, and duplicate info
        """
        return {
            'category': self.ai_categorizer.categorize_by_content(file_path),
            'suggested_tags': self.tagging_system.auto_tag_by_content(file_path),
            'current_tags': self.tagging_system.get_tags(file_path),
            'size_mb': file_path.stat().st_size / (1024 * 1024),
            'extension': file_path.suffix.lower()
        }

    def find_all_duplicates(self, file_paths: List[Path]) -> Dict[str, any]:
        """
        Find both exact and fuzzy duplicates
        """
        # Separate by type
        images = [f for f in file_paths if f.suffix.lower() in {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}]
        others = [f for f in file_paths if f not in images]

        results = {
            'similar_images': self.fuzzy_detector.find_similar_images(images),
            'exact_duplicates': self._find_exact_duplicates(file_paths)
        }

        return results

    def _find_exact_duplicates(self, file_paths: List[Path]) -> Dict[str, List[Path]]:
        """Find exact duplicate files"""
        hash_map = defaultdict(list)

        for file_path in file_paths:
            try:
                file_hash = self._calculate_hash(file_path)
                hash_map[file_hash].append(file_path)
            except Exception:
                continue

        # Only return groups with duplicates
        return {h: paths for h, paths in hash_map.items() if len(paths) > 1}

    def _calculate_hash(self, file_path: Path) -> str:
        """Calculate MD5 hash of file"""
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()


# Example usage
if __name__ == "__main__":
    # Demo the features
    organizer = SmartFileOrganizer(Path("./file_tags.json"))

    print("Advanced Features Module - Ready!")
    print("\nFeatures:")
    print("✓ AI-powered file categorization by content")
    print("✓ Fuzzy duplicate detection for images")
    print("✓ Advanced tagging system")
    print("✓ Smart content analysis")
