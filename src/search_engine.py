"""
Semantic Search Engine for FileOrganizer Pro
Multi-keyword search with advanced filters

Features:
- Multi-keyword semantic matching
- Type, size, date, tag filters
- Fuzzy filename matching
- Content-based search (via tags/metadata)
- Search history and suggestions
"""

from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
import re
from collections import defaultdict
import json


class SearchFilter:
    """Container for search filters"""

    def __init__(self):
        self.file_types: List[str] = []  # ['Images', 'Videos', ...]
        self.size_min: Optional[int] = None  # bytes
        self.size_max: Optional[int] = None  # bytes
        self.date_min: Optional[datetime] = None
        self.date_max: Optional[datetime] = None
        self.tags: List[str] = []
        self.extensions: List[str] = []  # ['.jpg', '.png', ...]

    def has_filters(self) -> bool:
        """Check if any filters are active"""
        return bool(
            self.file_types or
            self.size_min or self.size_max or
            self.date_min or self.date_max or
            self.tags or
            self.extensions
        )


class SearchResult:
    """Container for a single search result"""

    def __init__(self, file_path: Path, score: float, matches: List[str]):
        self.file_path = file_path
        self.score = score  # Relevance score (0.0 to 1.0)
        self.matches = matches  # List of matching keywords
        self.metadata = {}

    def __repr__(self):
        return f"SearchResult({self.file_path.name}, score={self.score:.2f})"


class SemanticSearchEngine:
    """
    Advanced search engine with semantic matching and filters

    Features:
    - Multi-keyword search (AND/OR logic)
    - Fuzzy filename matching
    - Extension filtering
    - Size/date range filtering
    - Tag-based filtering
    - Search result ranking
    """

    def __init__(self, file_index: Optional[List[Path]] = None,
                 tag_system=None):
        """
        Initialize search engine

        Args:
            file_index: List of file paths to search
            tag_system: FileTaggingSystem instance for tag search
        """
        self.file_index = file_index or []
        self.tag_system = tag_system
        self.search_history = []
        self.max_history = 50

        # File type mappings (from main app)
        self.file_types = {
            'Images': {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp',
                      '.svg', '.ico', '.heic', '.raw', '.cr2', '.nef', '.psd'},
            'Videos': {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
                      '.m4v', '.mpg', '.mpeg', '.3gp'},
            'Documents': {'.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.md'},
            'Spreadsheets': {'.xls', '.xlsx', '.csv', '.ods'},
            'Presentations': {'.ppt', '.pptx', '.odp', '.key'},
            'Audio': {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'},
            'Archives': {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.iso'},
            'Code': {'.py', '.js', '.java', '.cpp', '.c', '.h', '.cs', '.php',
                    '.html', '.css', '.json', '.xml', '.sql', '.sh'},
            'Executables': {'.exe', '.msi', '.app', '.deb', '.rpm', '.apk'},
            'Fonts': {'.ttf', '.otf', '.woff', '.woff2'},
        }

    def update_index(self, file_paths: List[Path]):
        """Update file index"""
        self.file_index = file_paths

    def search(self, query: str, filters: Optional[SearchFilter] = None,
               match_all_keywords: bool = False) -> List[SearchResult]:
        """
        Search files with multi-keyword and filters

        Args:
            query: Search query (e.g., "vacation photos 2024")
            filters: SearchFilter instance
            match_all_keywords: If True, all keywords must match (AND logic)

        Returns:
            List of SearchResult objects, sorted by relevance
        """
        if not query.strip() and not (filters and filters.has_filters()):
            return []

        # Parse query into keywords
        keywords = self._parse_query(query)

        results = []

        for file_path in self.file_index:
            # Calculate relevance score
            score, matches = self._calculate_relevance(file_path, keywords, match_all_keywords)

            # Apply filters
            if filters and not self._passes_filters(file_path, filters):
                continue

            if score > 0:
                result = SearchResult(file_path, score, matches)
                self._enrich_metadata(result)
                results.append(result)

        # Sort by score (descending)
        results.sort(key=lambda r: r.score, reverse=True)

        # Add to search history
        self._add_to_history(query, filters, len(results))

        return results

    def _parse_query(self, query: str) -> List[str]:
        """
        Parse query into keywords

        Handles:
        - Quoted phrases: "vacation photos" becomes single keyword
        - Special chars removal
        - Lowercase conversion
        """
        keywords = []

        # Extract quoted phrases
        quoted_pattern = r'"([^"]+)"'
        quoted_matches = re.findall(quoted_pattern, query)
        for match in quoted_matches:
            keywords.append(match.lower())
            query = query.replace(f'"{match}"', '')

        # Split remaining into words
        words = query.lower().split()
        keywords.extend([w.strip() for w in words if w.strip()])

        return keywords

    def _calculate_relevance(self, file_path: Path, keywords: List[str],
                            match_all: bool) -> Tuple[float, List[str]]:
        """
        Calculate relevance score for a file

        Scoring factors:
        - Filename exact match: +0.5
        - Filename partial match: +0.3
        - Extension match: +0.2
        - Parent folder match: +0.1
        - Tag match: +0.4

        Args:
            file_path: File to score
            keywords: List of keywords
            match_all: If True, all keywords must match

        Returns:
            (score, matched_keywords)
        """
        score = 0.0
        matches = []

        filename = file_path.stem.lower()
        extension = file_path.suffix.lower()
        parent = file_path.parent.name.lower()

        # Get tags if available
        tags = []
        if self.tag_system:
            try:
                tags = self.tag_system.get_tags(file_path)
                tags = [t.lower() for t in tags]
            except:
                pass

        search_text = f"{filename} {extension} {parent} {' '.join(tags)}"

        keyword_scores = {}

        for keyword in keywords:
            keyword_score = 0.0

            # Exact filename match
            if keyword == filename:
                keyword_score += 0.5
                matches.append(keyword)

            # Partial filename match
            elif keyword in filename:
                keyword_score += 0.3
                matches.append(keyword)

            # Extension match
            elif keyword in extension:
                keyword_score += 0.2
                matches.append(keyword)

            # Parent folder match
            elif keyword in parent:
                keyword_score += 0.1
                matches.append(keyword)

            # Tag match
            elif keyword in tags:
                keyword_score += 0.4
                matches.append(keyword)

            # Fuzzy match in search text
            elif keyword in search_text:
                keyword_score += 0.15
                matches.append(keyword)

            keyword_scores[keyword] = keyword_score

        # Calculate total score
        if match_all:
            # All keywords must match
            if len(keyword_scores) == len(keywords):
                score = sum(keyword_scores.values()) / len(keywords)
            else:
                score = 0.0
        else:
            # Any keyword match
            if keyword_scores:
                score = sum(keyword_scores.values()) / len(keywords)

        return score, list(set(matches))

    def _passes_filters(self, file_path: Path, filters: SearchFilter) -> bool:
        """Check if file passes all filters"""

        # File type filter
        if filters.file_types:
            extension = file_path.suffix.lower()
            type_match = False
            for file_type in filters.file_types:
                if file_type in self.file_types:
                    if extension in self.file_types[file_type]:
                        type_match = True
                        break
            if not type_match:
                return False

        # Extension filter
        if filters.extensions:
            if file_path.suffix.lower() not in [e.lower() for e in filters.extensions]:
                return False

        # Size filter
        if filters.size_min or filters.size_max:
            try:
                size = file_path.stat().st_size
                if filters.size_min and size < filters.size_min:
                    return False
                if filters.size_max and size > filters.size_max:
                    return False
            except:
                return False

        # Date filter
        if filters.date_min or filters.date_max:
            try:
                mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                if filters.date_min and mod_time < filters.date_min:
                    return False
                if filters.date_max and mod_time > filters.date_max:
                    return False
            except:
                return False

        # Tag filter
        if filters.tags and self.tag_system:
            try:
                file_tags = self.tag_system.get_tags(file_path)
                file_tags_lower = [t.lower() for t in file_tags]
                for required_tag in filters.tags:
                    if required_tag.lower() not in file_tags_lower:
                        return False
            except:
                return False

        return True

    def _enrich_metadata(self, result: SearchResult):
        """Add metadata to search result"""
        try:
            stat = result.file_path.stat()
            result.metadata = {
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime),
                'extension': result.file_path.suffix,
                'parent': result.file_path.parent.name,
            }

            # Add tags if available
            if self.tag_system:
                try:
                    result.metadata['tags'] = self.tag_system.get_tags(result.file_path)
                except:
                    result.metadata['tags'] = []

        except Exception:
            pass

    def _add_to_history(self, query: str, filters: Optional[SearchFilter], result_count: int):
        """Add search to history"""
        entry = {
            'query': query,
            'timestamp': datetime.now(),
            'result_count': result_count,
            'had_filters': filters.has_filters() if filters else False
        }

        self.search_history.insert(0, entry)
        self.search_history = self.search_history[:self.max_history]

    def get_search_suggestions(self, partial_query: str, limit: int = 10) -> List[str]:
        """
        Get search suggestions based on history

        Args:
            partial_query: Partial query string
            limit: Max suggestions

        Returns:
            List of suggested queries
        """
        if not partial_query:
            # Return recent searches
            return [h['query'] for h in self.search_history[:limit] if h['query']]

        partial_lower = partial_query.lower()
        suggestions = []

        # Find matching history entries
        for entry in self.search_history:
            query = entry['query']
            if query and partial_lower in query.lower():
                if query not in suggestions:
                    suggestions.append(query)
                if len(suggestions) >= limit:
                    break

        return suggestions

    def save_search_history(self, file_path: Path):
        """Save search history to file"""
        try:
            history_data = []
            for entry in self.search_history:
                history_data.append({
                    'query': entry['query'],
                    'timestamp': entry['timestamp'].isoformat(),
                    'result_count': entry['result_count'],
                    'had_filters': entry['had_filters']
                })

            with open(file_path, 'w') as f:
                json.dump(history_data, f, indent=2)

        except Exception as e:
            print(f"Error saving search history: {e}")

    def load_search_history(self, file_path: Path):
        """Load search history from file"""
        try:
            if not file_path.exists():
                return

            with open(file_path, 'r') as f:
                history_data = json.load(f)

            self.search_history = []
            for entry in history_data:
                self.search_history.append({
                    'query': entry['query'],
                    'timestamp': datetime.fromisoformat(entry['timestamp']),
                    'result_count': entry['result_count'],
                    'had_filters': entry['had_filters']
                })

        except Exception as e:
            print(f"Error loading search history: {e}")


# Predefined filter presets
class SearchPresets:
    """Common search filter presets"""

    @staticmethod
    def recent_files(days: int = 7) -> SearchFilter:
        """Files modified in last N days"""
        f = SearchFilter()
        f.date_min = datetime.now() - timedelta(days=days)
        return f

    @staticmethod
    def large_files(min_mb: int = 100) -> SearchFilter:
        """Files larger than N MB"""
        f = SearchFilter()
        f.size_min = min_mb * 1024 * 1024
        return f

    @staticmethod
    def images_only() -> SearchFilter:
        """Images only"""
        f = SearchFilter()
        f.file_types = ['Images']
        return f

    @staticmethod
    def videos_only() -> SearchFilter:
        """Videos only"""
        f = SearchFilter()
        f.file_types = ['Videos']
        return f

    @staticmethod
    def documents_only() -> SearchFilter:
        """Documents only"""
        f = SearchFilter()
        f.file_types = ['Documents', 'Spreadsheets', 'Presentations']
        return f


# Demo/Test
if __name__ == '__main__':
    # Create sample file index
    sample_files = [
        Path('E:/Photos/vacation_beach_2024.jpg'),
        Path('E:/Photos/family_dinner.png'),
        Path('E:/Downloads/video_tutorial.mp4'),
        Path('E:/Documents/report_2024.pdf'),
        Path('E:/Documents/invoice.xlsx'),
    ]

    # Initialize search engine
    engine = SemanticSearchEngine(sample_files)

    # Test 1: Simple keyword search
    print("=" * 60)
    print("Test 1: Search for 'vacation'")
    print("=" * 60)
    results = engine.search("vacation")
    for r in results:
        print(f"  {r.file_path.name} (score: {r.score:.2f}, matches: {r.matches})")

    # Test 2: Multi-keyword search
    print("\n" + "=" * 60)
    print("Test 2: Search for '2024 photos'")
    print("=" * 60)
    results = engine.search("2024 photos")
    for r in results:
        print(f"  {r.file_path.name} (score: {r.score:.2f}, matches: {r.matches})")

    # Test 3: Filtered search
    print("\n" + "=" * 60)
    print("Test 3: Search for images only")
    print("=" * 60)
    filter_images = SearchFilter()
    filter_images.file_types = ['Images']
    results = engine.search("", filters=filter_images)
    for r in results:
        print(f"  {r.file_path.name}")

    # Test 4: Search suggestions
    print("\n" + "=" * 60)
    print("Test 4: Search suggestions for 'vac'")
    print("=" * 60)
    suggestions = engine.get_search_suggestions("vac")
    for s in suggestions:
        print(f"  {s}")
