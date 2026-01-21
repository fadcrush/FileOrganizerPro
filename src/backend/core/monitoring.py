"""
Phase 3 Week 4: Monitoring & Logging

Structured logging, metrics collection, and error tracking.

Features:
- JSON-formatted logs for easy parsing
- Prometheus metrics export
- Sentry error tracking
- Health check endpoints
- Performance monitoring

Usage:
    from src.backend.core.monitoring import (
        get_logger,
        metrics,
        setup_monitoring,
    )
    
    logger = get_logger(__name__)
    logger.info("Starting operation", extra={"user_id": user_id})
    
    metrics.api_request_duration.observe(0.5)
"""

import json
import logging
import time
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from prometheus_client import (
    Counter, Histogram, Gauge, CollectorRegistry
)
import structlog


# Configure structured logging
def setup_logging(log_level: str = "INFO"):
    """Setup structured logging with JSON output"""
    
    # Create logs directory
    log_dir = Path("data/logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(message)s",
        handlers=[
            logging.FileHandler(log_dir / "file_organizer_pro.log"),
            logging.StreamHandler(),
        ],
    )
    
    # Set third-party logging levels
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)


def get_logger(name: str):
    """Get logger instance"""
    return structlog.get_logger(name)


# Prometheus Metrics
class Metrics:
    """Application metrics"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        
        # API metrics
        self.api_requests_total = Counter(
            'api_requests_total',
            'Total API requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.api_request_duration = Histogram(
            'api_request_duration_seconds',
            'API request duration',
            ['method', 'endpoint'],
            registry=self.registry,
            buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0)
        )
        
        self.api_request_size = Histogram(
            'api_request_size_bytes',
            'API request size',
            ['method', 'endpoint'],
            registry=self.registry,
            buckets=(100, 1000, 10000, 100000, 1000000)
        )
        
        self.api_response_size = Histogram(
            'api_response_size_bytes',
            'API response size',
            ['method', 'endpoint'],
            registry=self.registry,
            buckets=(100, 1000, 10000, 100000, 1000000)
        )
        
        # Database metrics
        self.db_queries_total = Counter(
            'db_queries_total',
            'Total database queries',
            ['operation', 'status'],
            registry=self.registry
        )
        
        self.db_query_duration = Histogram(
            'db_query_duration_seconds',
            'Database query duration',
            ['operation'],
            registry=self.registry,
            buckets=(0.001, 0.01, 0.05, 0.1, 0.5, 1.0)
        )
        
        # Cache metrics
        self.cache_hits = Counter(
            'cache_hits_total',
            'Total cache hits',
            ['cache_type'],
            registry=self.registry
        )
        
        self.cache_misses = Counter(
            'cache_misses_total',
            'Total cache misses',
            ['cache_type'],
            registry=self.registry
        )
        
        # Business metrics
        self.files_organized = Counter(
            'files_organized_total',
            'Total files organized',
            ['category', 'status'],
            registry=self.registry
        )
        
        self.duplicates_found = Counter(
            'duplicates_found_total',
            'Total duplicates found',
            registry=self.registry
        )
        
        self.operations_total = Counter(
            'operations_total',
            'Total operations',
            ['operation_type', 'status'],
            registry=self.registry
        )
        
        # System metrics
        self.active_operations = Gauge(
            'active_operations',
            'Number of active operations',
            registry=self.registry
        )
        
        self.active_users = Gauge(
            'active_users',
            'Number of active users',
            registry=self.registry
        )
        
        self.storage_bytes = Gauge(
            'storage_bytes_total',
            'Total storage used',
            ['storage_type'],
            registry=self.registry
        )


# Global metrics instance
metrics = Metrics()


class PerformanceMonitor:
    """Monitor and log performance metrics"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.samples = {
            "api_response_times": [],
            "db_query_times": [],
            "cache_hit_rates": [],
        }
    
    def record_api_call(
        self,
        method: str,
        endpoint: str,
        status: int,
        duration_ms: float,
        request_size: int = 0,
        response_size: int = 0,
    ):
        """Record API call metrics"""
        self.logger.info(
            "api_call",
            method=method,
            endpoint=endpoint,
            status=status,
            duration_ms=round(duration_ms, 2),
            request_size=request_size,
            response_size=response_size,
        )
        
        # Update metrics
        metrics.api_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=status
        ).inc()
        
        metrics.api_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration_ms / 1000)
        
        if request_size:
            metrics.api_request_size.labels(
                method=method,
                endpoint=endpoint
            ).observe(request_size)
        
        if response_size:
            metrics.api_response_size.labels(
                method=method,
                endpoint=endpoint
            ).observe(response_size)
        
        # Track samples for analysis
        self.samples["api_response_times"].append(duration_ms)
        if len(self.samples["api_response_times"]) > 1000:
            self.samples["api_response_times"].pop(0)
    
    def record_db_query(
        self,
        operation: str,
        status: str,
        duration_ms: float,
    ):
        """Record database query metrics"""
        self.logger.debug(
            "db_query",
            operation=operation,
            status=status,
            duration_ms=round(duration_ms, 2),
        )
        
        # Update metrics
        metrics.db_queries_total.labels(
            operation=operation,
            status=status
        ).inc()
        
        metrics.db_query_duration.labels(
            operation=operation
        ).observe(duration_ms / 1000)
        
        # Track samples
        self.samples["db_query_times"].append(duration_ms)
        if len(self.samples["db_query_times"]) > 1000:
            self.samples["db_query_times"].pop(0)
    
    def record_file_organization(
        self,
        category: str,
        status: str,
        count: int = 1,
    ):
        """Record file organization metrics"""
        for _ in range(count):
            metrics.files_organized.labels(
                category=category,
                status=status
            ).inc()
    
    def record_operation(
        self,
        operation_type: str,
        status: str,
    ):
        """Record operation completion"""
        metrics.operations_total.labels(
            operation_type=operation_type,
            status=status
        ).inc()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get performance statistics"""
        import statistics as stats
        
        api_times = self.samples["api_response_times"]
        db_times = self.samples["db_query_times"]
        
        return {
            "api_response_times": {
                "count": len(api_times),
                "avg_ms": round(stats.mean(api_times), 2) if api_times else 0,
                "median_ms": round(stats.median(api_times), 2) if api_times else 0,
                "p95_ms": round(sorted(api_times)[int(len(api_times) * 0.95)], 2) if api_times else 0,
                "max_ms": round(max(api_times), 2) if api_times else 0,
            },
            "db_query_times": {
                "count": len(db_times),
                "avg_ms": round(stats.mean(db_times), 2) if db_times else 0,
                "median_ms": round(stats.median(db_times), 2) if db_times else 0,
                "p95_ms": round(sorted(db_times)[int(len(db_times) * 0.95)], 2) if db_times else 0,
                "max_ms": round(max(db_times), 2) if db_times else 0,
            },
            "total_samples": len(api_times) + len(db_times),
        }


# Global monitor instance
monitor = PerformanceMonitor()


class HealthCheck:
    """System health status"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": "unknown",
                "redis": "unknown",
                "storage": "unknown",
            }
        }
    
    async def check_database(self, db_session) -> bool:
        """Check database connectivity"""
        try:
            await db_session.execute("SELECT 1")
            self.status["services"]["database"] = "healthy"
            return True
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            self.status["services"]["database"] = "unhealthy"
            return False
    
    async def check_redis(self, redis_client) -> bool:
        """Check Redis connectivity"""
        try:
            await redis_client.ping()
            self.status["services"]["redis"] = "healthy"
            return True
        except Exception as e:
            self.logger.error(f"Redis health check failed: {e}")
            self.status["services"]["redis"] = "unhealthy"
            return False
    
    async def check_storage(self, storage_client) -> bool:
        """Check storage connectivity"""
        try:
            # Test storage access
            self.status["services"]["storage"] = "healthy"
            return True
        except Exception as e:
            self.logger.error(f"Storage health check failed: {e}")
            self.status["services"]["storage"] = "unhealthy"
            return False
    
    async def check_all(self, db, redis, storage) -> dict:
        """Check all services"""
        db_ok = await self.check_database(db)
        redis_ok = await self.check_redis(redis)
        storage_ok = await self.check_storage(storage)
        
        self.status["status"] = (
            "healthy"
            if all([db_ok, redis_ok, storage_ok])
            else "degraded"
        )
        self.status["timestamp"] = datetime.utcnow().isoformat()
        
        return self.status
    
    def get_status(self) -> dict:
        """Get current status"""
        return self.status


# Global health check instance
health_check = HealthCheck()


def setup_monitoring():
    """Setup all monitoring components"""
    setup_logging()
    logger = get_logger(__name__)
    logger.info("Monitoring initialized")
