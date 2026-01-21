"""Categorization Service - Rule-based file classification.

This service handles:
- Extension-based categorization
- Custom rule application
- Category mapping configuration
- Fallback to default category
"""

from pathlib import Path
from typing import Dict, List, Optional
import json

from ..domain.entities import FileItem
from ..domain.value_objects import Category
from ..domain.exceptions import CategoryNotFoundError
from ..infrastructure.logging import get_logger


logger = get_logger(__name__)

# Default file extension to category mappings
DEFAULT_CATEGORY_MAPPINGS = {
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".xlsx", ".xls", ".ppt", ".pptx"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".ico", ".webp"],
    "Videos": [".mp4", ".avi", ".mkv", ".mov", ".flv", ".wmv", ".m4v", ".webm"],
    "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a", ".aiff"],
    "Code": [".py", ".js", ".ts", ".java", ".cpp", ".c", ".h", ".go", ".rs", ".rb"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".iso"],
    "Executables": [".exe", ".msi", ".bat", ".sh", ".app", ".dmg", ".apk"],
    "Spreadsheets": [".csv", ".tsv"],
    "Presentations": [],
    "Source": [".sql", ".xml", ".html", ".css", ".json", ".yaml", ".yml"],
    "Other": [],
}


class CategorizationService:
    """Categorizes files based on configurable rules.
    
    Features:
    - Extension-based categorization (primary)
    - Custom rule support
    - Category mapping configuration
    - Fallback to default category
    - Case-insensitive matching
    """

    def __init__(
        self,
        category_mappings: Optional[Dict[str, List[str]]] = None,
        default_category: str = "Other",
    ):
        """Initialize CategorizationService.
        
        Args:
            category_mappings: Extension to category mappings
                              (uses defaults if not provided)
            default_category: Category to use if no rule matches
        """
        self.category_mappings = category_mappings or DEFAULT_CATEGORY_MAPPINGS
        self.default_category = default_category
        
        # Build reverse mapping (extension -> category) for O(1) lookup
        self._extension_map: Dict[str, str] = {}
        self._build_extension_map()

    def _build_extension_map(self) -> None:
        """Build extension -> category reverse mapping for fast lookup."""
        for category, extensions in self.category_mappings.items():
            for ext in extensions:
                self._extension_map[ext.lower()] = category

    def categorize(self, file_item: FileItem) -> Category:
        """Categorize a file based on configured rules.
        
        Args:
            file_item: FileItem to categorize
            
        Returns:
            Category for the file
            
        Raises:
            CategoryNotFoundError: If categorization fails completely
        """
        try:
            # Get file extension
            extension = Path(file_item.path.path).suffix.lower()
            
            # Check extension mapping
            if extension in self._extension_map:
                category_name = self._extension_map[extension]
                logger.debug(f"Categorized {file_item.name} as {category_name}")
                return Category(category_name)
            
            # Fallback to default category
            logger.debug(
                f"No rule matched for {file_item.name}, using default: {self.default_category}"
            )
            return Category(self.default_category)
            
        except Exception as e:
            logger.error(f"Categorization failed for {file_item.name}: {e}")
            raise CategoryNotFoundError(
                file_name=file_item.name,
                reason=f"Categorization failed: {str(e)}",
            )

    def categorize_batch(self, files: List[FileItem]) -> Dict[str, Category]:
        """Categorize multiple files efficiently.
        
        Args:
            files: List of FileItem objects to categorize
            
        Returns:
            Dictionary mapping file path to Category
        """
        results = {}
        errors = []
        
        for file_item in files:
            try:
                results[file_item.path.path] = self.categorize(file_item)
            except Exception as e:
                error_msg = f"Failed to categorize {file_item.name}: {e}"
                errors.append(error_msg)
                logger.warning(error_msg)
                # Use default category on error
                results[file_item.path.path] = Category(self.default_category)
        
        if errors:
            logger.warning(f"Categorization had {len(errors)} errors")
        
        return results

    def add_rule(self, category: str, extensions: List[str]) -> None:
        """Add custom categorization rule.
        
        Args:
            category: Category name
            extensions: List of extensions (e.g., ['.pdf', '.doc'])
        """
        # Normalize extensions
        normalized = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}'
                     for ext in extensions]
        
        # Add to mappings
        if category not in self.category_mappings:
            self.category_mappings[category] = []
        
        self.category_mappings[category].extend(normalized)
        
        # Update reverse mapping
        for ext in normalized:
            self._extension_map[ext] = category
        
        logger.info(f"Added rule: {category} -> {normalized}")

    def remove_rule(self, category: str, extensions: Optional[List[str]] = None) -> None:
        """Remove categorization rule.
        
        Args:
            category: Category name
            extensions: List of extensions to remove.
                       If None, removes entire category.
        """
        if category not in self.category_mappings:
            logger.warning(f"Category not found: {category}")
            return
        
        if extensions is None:
            # Remove entire category
            del self.category_mappings[category]
            # Clean up reverse mapping
            to_remove = [ext for ext, cat in self._extension_map.items()
                        if cat == category]
            for ext in to_remove:
                del self._extension_map[ext]
            logger.info(f"Removed category: {category}")
        else:
            # Remove specific extensions
            normalized = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}'
                         for ext in extensions]
            
            for ext in normalized:
                if ext in self.category_mappings[category]:
                    self.category_mappings[category].remove(ext)
                if ext in self._extension_map:
                    del self._extension_map[ext]
            
            logger.info(f"Removed extensions from {category}: {normalized}")

    def get_categories(self) -> List[str]:
        """Get list of all available categories.
        
        Returns:
            List of category names
        """
        return list(self.category_mappings.keys())

    def get_extensions_for_category(self, category: str) -> List[str]:
        """Get extensions associated with a category.
        
        Args:
            category: Category name
            
        Returns:
            List of extensions
            
        Raises:
            CategoryNotFoundError: If category doesn't exist
        """
        if category not in self.category_mappings:
            raise CategoryNotFoundError(
                file_name="",
                reason=f"Category not found: {category}",
            )
        return self.category_mappings[category]

    def load_from_config(self, config_path: str) -> None:
        """Load category mappings from JSON config file.
        
        Args:
            config_path: Path to JSON config file with format:
                        {"Documents": [".pdf", ".doc"], ...}
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                self.category_mappings = config
                self._build_extension_map()
            logger.info(f"Loaded category mappings from: {config_path}")
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            raise

    def save_to_config(self, config_path: str) -> None:
        """Save current category mappings to JSON config file.
        
        Args:
            config_path: Path to write JSON config file
        """
        try:
            with open(config_path, 'w') as f:
                json.dump(self.category_mappings, f, indent=2)
            logger.info(f"Saved category mappings to: {config_path}")
        except Exception as e:
            logger.error(f"Failed to save config to {config_path}: {e}")
            raise
