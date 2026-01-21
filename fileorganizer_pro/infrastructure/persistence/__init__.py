"""Persistence layer - Repository pattern for data storage."""

from abc import ABC, abstractmethod
from typing import List, Optional

from ...domain import FileItem, DuplicateGroup


class Repository(ABC):
    """Abstract base class for repository implementations."""

    @abstractmethod
    def save(self, entity: object) -> None:
        """Save entity to persistence."""
        pass

    @abstractmethod
    def load(self, entity_id: str) -> Optional[object]:
        """Load entity from persistence."""
        pass

    @abstractmethod
    def delete(self, entity_id: str) -> None:
        """Delete entity from persistence."""
        pass


class FileRepository(Repository):
    """Repository for FileItem entities.

    Tracks file history, organization records, and metadata.
    """

    pass


class DuplicateRepository(Repository):
    """Repository for DuplicateGroup entities.

    Stores duplicate detection results and recycle bin history.
    """

    pass
