"""Cloud storage abstraction layer for multi-platform file access."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, BinaryIO
from dataclasses import dataclass
import os


@dataclass
class StorageFile:
    """Represents a file in storage."""
    
    path: str  # Relative path in storage
    size_bytes: int
    modified_at: float  # Unix timestamp
    is_dir: bool = False


class StorageProvider(ABC):
    """Abstract base class for storage providers."""
    
    @abstractmethod
    async def exists(self, path: str) -> bool:
        """Check if file/directory exists."""
        pass
    
    @abstractmethod
    async def list_files(self, path: str, recursive: bool = True) -> List[StorageFile]:
        """List files in directory."""
        pass
    
    @abstractmethod
    async def read_file(self, path: str) -> bytes:
        """Read file contents."""
        pass
    
    @abstractmethod
    async def write_file(self, path: str, content: bytes) -> None:
        """Write file contents."""
        pass
    
    @abstractmethod
    async def move_file(self, source: str, destination: str) -> None:
        """Move file to new location."""
        pass
    
    @abstractmethod
    async def delete_file(self, path: str) -> None:
        """Delete file."""
        pass
    
    @abstractmethod
    async def get_file_hash(self, path: str, algorithm: str = "sha256") -> str:
        """Get file hash."""
        pass


class LocalStorageProvider(StorageProvider):
    """Local filesystem storage provider."""
    
    def __init__(self, base_path: str = None):
        """Initialize with base directory."""
        self.base_path = Path(base_path or os.getcwd())
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _resolve_path(self, path: str) -> Path:
        """Resolve path relative to base."""
        full_path = (self.base_path / path).resolve()
        
        # Prevent directory traversal attacks
        if not str(full_path).startswith(str(self.base_path)):
            raise ValueError(f"Path {path} escapes base directory")
        
        return full_path
    
    async def exists(self, path: str) -> bool:
        """Check if file exists."""
        return self._resolve_path(path).exists()
    
    async def list_files(self, path: str, recursive: bool = True) -> List[StorageFile]:
        """List files in directory."""
        base = self._resolve_path(path)
        
        if not base.exists():
            return []
        
        files = []
        pattern = "**/*" if recursive else "*"
        
        for file_path in base.glob(pattern):
            if file_path.is_file():
                stat = file_path.stat()
                rel_path = str(file_path.relative_to(self.base_path))
                
                files.append(StorageFile(
                    path=rel_path,
                    size_bytes=stat.st_size,
                    modified_at=stat.st_mtime,
                    is_dir=False,
                ))
        
        return files
    
    async def read_file(self, path: str) -> bytes:
        """Read file contents."""
        return self._resolve_path(path).read_bytes()
    
    async def write_file(self, path: str, content: bytes) -> None:
        """Write file contents."""
        file_path = self._resolve_path(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)
    
    async def move_file(self, source: str, destination: str) -> None:
        """Move file to new location."""
        source_path = self._resolve_path(source)
        dest_path = self._resolve_path(destination)
        
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.rename(dest_path)
    
    async def delete_file(self, path: str) -> None:
        """Delete file."""
        self._resolve_path(path).unlink(missing_ok=True)
    
    async def get_file_hash(self, path: str, algorithm: str = "sha256") -> str:
        """Get file hash."""
        import hashlib
        
        file_path = self._resolve_path(path)
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()


class S3StorageProvider(StorageProvider):
    """AWS S3 storage provider."""
    
    def __init__(self, bucket: str, region: str = "us-east-1", prefix: str = ""):
        """Initialize S3 provider.
        
        Args:
            bucket: S3 bucket name
            region: AWS region
            prefix: Prefix for all paths in bucket
        """
        self.bucket = bucket
        self.region = region
        self.prefix = prefix.rstrip("/")
        
        # boto3 imported lazily to avoid dependency if not using S3
        try:
            import boto3
            self.s3_client = boto3.client("s3", region_name=region)
        except ImportError:
            raise ImportError("boto3 required for S3StorageProvider. Install with: pip install boto3")
    
    def _make_key(self, path: str) -> str:
        """Create S3 key from path."""
        if self.prefix:
            return f"{self.prefix}/{path.lstrip('/')}"
        return path.lstrip("/")
    
    async def exists(self, path: str) -> bool:
        """Check if object exists in S3."""
        key = self._make_key(path)
        
        try:
            self.s3_client.head_object(Bucket=self.bucket, Key=key)
            return True
        except self.s3_client.exceptions.NoSuchKey:
            return False
    
    async def list_files(self, path: str, recursive: bool = True) -> List[StorageFile]:
        """List objects in S3."""
        prefix = self._make_key(path.rstrip("/") + "/")
        delimiter = None if recursive else "/"
        
        files = []
        paginator = self.s3_client.get_paginator("list_objects_v2")
        
        for page in paginator.paginate(
            Bucket=self.bucket,
            Prefix=prefix,
            Delimiter=delimiter
        ):
            for obj in page.get("Contents", []):
                # Skip directory markers
                if obj["Key"].endswith("/"):
                    continue
                
                files.append(StorageFile(
                    path=obj["Key"].removeprefix(self.prefix + "/"),
                    size_bytes=obj["Size"],
                    modified_at=obj["LastModified"].timestamp(),
                ))
        
        return files
    
    async def read_file(self, path: str) -> bytes:
        """Read object from S3."""
        key = self._make_key(path)
        response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()
    
    async def write_file(self, path: str, content: bytes) -> None:
        """Write object to S3."""
        key = self._make_key(path)
        self.s3_client.put_object(Bucket=self.bucket, Key=key, Body=content)
    
    async def move_file(self, source: str, destination: str) -> None:
        """Move object in S3."""
        source_key = self._make_key(source)
        dest_key = self._make_key(destination)
        
        # Copy object
        self.s3_client.copy_object(
            Bucket=self.bucket,
            CopySource={"Bucket": self.bucket, "Key": source_key},
            Key=dest_key,
        )
        
        # Delete original
        self.s3_client.delete_object(Bucket=self.bucket, Key=source_key)
    
    async def delete_file(self, path: str) -> None:
        """Delete object from S3."""
        key = self._make_key(path)
        self.s3_client.delete_object(Bucket=self.bucket, Key=key)
    
    async def get_file_hash(self, path: str, algorithm: str = "sha256") -> str:
        """Get hash of S3 object (using ETag for efficiency)."""
        key = self._make_key(path)
        response = self.s3_client.head_object(Bucket=self.bucket, Key=key)
        
        # S3 ETag is MD5 for single-part uploads, use it as is
        return response["ETag"].strip('"')


def create_storage_provider(provider_type: str, **kwargs) -> StorageProvider:
    """Factory function to create storage provider.
    
    Args:
        provider_type: "local", "s3", or "r2"
        **kwargs: Provider-specific configuration
        
    Returns:
        StorageProvider instance
    """
    if provider_type == "local":
        return LocalStorageProvider(kwargs.get("base_path"))
    elif provider_type == "s3":
        return S3StorageProvider(
            bucket=kwargs["bucket"],
            region=kwargs.get("region", "us-east-1"),
            prefix=kwargs.get("prefix", ""),
        )
    elif provider_type == "r2":
        # Cloudflare R2 (S3-compatible)
        return S3StorageProvider(
            bucket=kwargs["bucket"],
            region=kwargs.get("region", "auto"),
            prefix=kwargs.get("prefix", ""),
        )
    else:
        raise ValueError(f"Unknown storage provider: {provider_type}")
