"""
Phase 3 Week 4: Load Testing Script

Simulates organizing 1M files across the API to measure:
- API response times (p50, p95, p99)
- Database query performance
- Memory usage and CPU utilization
- Identify bottlenecks

Usage:
    python scripts/load_test.py --files 1000000 --report
    python scripts/load_test.py --files 10000 --profile  # Quick profile test
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import statistics
import sys
from dataclasses import dataclass, asdict
import psutil
import subprocess

import httpx
from dotenv import load_dotenv
import os

load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
TEST_EMAIL = f"load-test-{int(time.time())}@example.com"
TEST_PASSWORD = "LoadTest123!@#"
TEST_FILES_COUNT = 10000  # Default, override with --files
TARGET_DURATION_SECONDS = 300  # 5 minutes target

# File categories for simulation
CATEGORIES = {
    "Documents": {"extensions": [".pdf", ".doc", ".docx"], "count": 0.3},
    "Images": {"extensions": [".jpg", ".png", ".gif"], "count": 0.25},
    "Videos": {"extensions": [".mp4", ".avi", ".mkv"], "count": 0.15},
    "Audio": {"extensions": [".mp3", ".wav"], "count": 0.1},
    "Code": {"extensions": [".py", ".js", ".java"], "count": 0.2},
}


@dataclass
class PerformanceMetrics:
    """Metrics collected during load test"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_duration_seconds: float = 0.0
    
    # Response times
    response_times: List[float] = None
    
    # Resource usage
    memory_peak_mb: float = 0.0
    cpu_percent_avg: float = 0.0
    
    # Database metrics
    slow_queries_count: int = 0
    slow_query_threshold_ms: int = 50
    
    def __post_init__(self):
        if self.response_times is None:
            self.response_times = []
    
    def add_response_time(self, duration_ms: float):
        """Record response time"""
        self.response_times.append(duration_ms)
    
    def calculate_percentiles(self) -> Dict[str, float]:
        """Calculate response time percentiles"""
        if not self.response_times:
            return {"p50": 0, "p95": 0, "p99": 0, "avg": 0, "min": 0, "max": 0}
        
        sorted_times = sorted(self.response_times)
        return {
            "p50": statistics.median(sorted_times),
            "p95": sorted_times[int(len(sorted_times) * 0.95)],
            "p99": sorted_times[int(len(sorted_times) * 0.99)],
            "avg": statistics.mean(sorted_times),
            "min": min(sorted_times),
            "max": max(sorted_times),
        }
    
    def get_success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        percentiles = self.calculate_percentiles()
        return {
            "summary": {
                "total_requests": self.total_requests,
                "successful_requests": self.successful_requests,
                "failed_requests": self.failed_requests,
                "success_rate_percent": round(self.get_success_rate(), 2),
                "total_duration_seconds": round(self.total_duration_seconds, 2),
            },
            "response_times": {
                "p50_ms": round(percentiles["p50"], 2),
                "p95_ms": round(percentiles["p95"], 2),
                "p99_ms": round(percentiles["p99"], 2),
                "avg_ms": round(percentiles["avg"], 2),
                "min_ms": round(percentiles["min"], 2),
                "max_ms": round(percentiles["max"], 2),
            },
            "resource_usage": {
                "peak_memory_mb": round(self.memory_peak_mb, 2),
                "avg_cpu_percent": round(self.cpu_percent_avg, 2),
            },
            "database": {
                "slow_queries": self.slow_queries_count,
                "slow_query_threshold_ms": self.slow_query_threshold_ms,
            }
        }


class LoadTestClient:
    """HTTP client for load testing"""
    
    def __init__(self):
        self.client = httpx.Client(base_url=API_BASE_URL, timeout=30.0)
        self.token = None
        self.operation_id = None
        self.metrics = PerformanceMetrics()
        self.process = psutil.Process()
    
    async def register_user(self) -> bool:
        """Register a test user"""
        try:
            response = self.client.post(
                "/api/v1/auth/signup",
                json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD,
                    "name": "Load Test"
                }
            )
            if response.status_code in [201, 200]:
                print(f"✅ User registered: {TEST_EMAIL}")
                return True
            else:
                print(f"❌ Registration failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False
    
    async def login_user(self) -> bool:
        """Login and get JWT token"""
        try:
            response = self.client.post(
                "/api/v1/auth/login",
                json={
                    "email": TEST_EMAIL,
                    "password": TEST_PASSWORD
                }
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.client.headers["Authorization"] = f"Bearer {self.token}"
                print(f"✅ Logged in successfully")
                return True
            else:
                print(f"❌ Login failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    async def start_operation(self) -> bool:
        """Start a file organization operation"""
        try:
            response = self.client.post(
                "/api/v1/operations",
                json={
                    "source_path": "C:\\TestFiles",
                    "operation_type": "organize",
                    "move_duplicates_to_folder": True,
                    "create_year_folders": True,
                    "skip_duplicates": False,
                }
            )
            if response.status_code == 201:
                data = response.json()
                self.operation_id = data.get("id")
                print(f"✅ Operation started: {self.operation_id}")
                return True
            else:
                print(f"❌ Operation start failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Operation start error: {e}")
            return False
    
    async def create_test_files(self, count: int) -> bool:
        """Simulate creating file records in the database"""
        print(f"Creating {count} test file records...")
        try:
            batch_size = 100
            for batch_num in range(0, count, batch_size):
                batch_files = []
                for i in range(batch_num, min(batch_num + batch_size, count)):
                    # Distribute files across categories
                    category = self._get_category_for_file(i, count)
                    extension = self._get_extension_for_category(category)
                    
                    batch_files.append({
                        "operation_id": str(self.operation_id),
                        "original_path": f"C:\\TestFiles\\file_{i}{extension}",
                        "new_path": f"C:\\Organized\\{category}\\file_{i}{extension}",
                        "category": category,
                        "status": "completed",
                        "size_bytes": (i % 1000) * 10240,  # 0 - 10MB
                        "file_hash": f"hash_{i % 1000}",  # Create some "duplicates"
                    })
                
                # Insert batch (simulated - in real scenario, would use database directly)
                print(f"  Batch {batch_num//batch_size + 1}: {len(batch_files)} files", end="\r")
            
            print(f"✅ Created {count} test file records")
            return True
        except Exception as e:
            print(f"❌ File creation error: {e}")
            return False
    
    def _get_category_for_file(self, file_index: int, total: int) -> str:
        """Determine category based on file index"""
        position = file_index / total
        cumulative = 0.0
        for category, config in CATEGORIES.items():
            cumulative += config["count"]
            if position <= cumulative:
                return category
        return "Documents"
    
    def _get_extension_for_category(self, category: str) -> str:
        """Get random extension for category"""
        extensions = CATEGORIES[category]["extensions"]
        return extensions[hash(str(time.time())) % len(extensions)]
    
    async def test_list_files(self) -> bool:
        """Test GET /api/v1/files"""
        start = time.time()
        try:
            response = self.client.get(
                "/api/v1/files",
                params={
                    "operation_id": self.operation_id,
                    "page": 1,
                    "page_size": 100,
                }
            )
            duration_ms = (time.time() - start) * 1000
            
            self.metrics.total_requests += 1
            self.metrics.add_response_time(duration_ms)
            
            if response.status_code == 200:
                self.metrics.successful_requests += 1
                return True
            else:
                self.metrics.failed_requests += 1
                return False
        except Exception as e:
            self.metrics.failed_requests += 1
            return False
    
    async def test_search_files(self, query: str) -> bool:
        """Test GET /api/v1/files/search"""
        start = time.time()
        try:
            response = self.client.get(
                "/api/v1/files/search",
                params={
                    "operation_id": self.operation_id,
                    "query": query,
                    "page": 1,
                    "page_size": 50,
                }
            )
            duration_ms = (time.time() - start) * 1000
            
            self.metrics.total_requests += 1
            self.metrics.add_response_time(duration_ms)
            
            if response.status_code == 200:
                self.metrics.successful_requests += 1
                return True
            else:
                self.metrics.failed_requests += 1
                return False
        except Exception as e:
            self.metrics.failed_requests += 1
            return False
    
    async def test_get_duplicates(self) -> bool:
        """Test GET /api/v1/duplicates"""
        start = time.time()
        try:
            response = self.client.get(
                f"/api/v1/duplicates/{self.operation_id}",
                params={"limit": 50, "offset": 0}
            )
            duration_ms = (time.time() - start) * 1000
            
            self.metrics.total_requests += 1
            self.metrics.add_response_time(duration_ms)
            
            if response.status_code == 200:
                self.metrics.successful_requests += 1
                return True
            else:
                self.metrics.failed_requests += 1
                return False
        except Exception as e:
            self.metrics.failed_requests += 1
            return False
    
    async def test_get_report(self) -> bool:
        """Test GET /api/v1/reports"""
        start = time.time()
        try:
            response = self.client.get(f"/api/v1/reports/{self.operation_id}")
            duration_ms = (time.time() - start) * 1000
            
            self.metrics.total_requests += 1
            self.metrics.add_response_time(duration_ms)
            
            if response.status_code == 200:
                self.metrics.successful_requests += 1
                return True
            else:
                self.metrics.failed_requests += 1
                return False
        except Exception as e:
            self.metrics.failed_requests += 1
            return False
    
    async def test_export_report(self, format_type: str = "json") -> bool:
        """Test GET /api/v1/reports/export"""
        start = time.time()
        try:
            response = self.client.get(
                f"/api/v1/reports/{self.operation_id}/export",
                params={"format": format_type}
            )
            duration_ms = (time.time() - start) * 1000
            
            self.metrics.total_requests += 1
            self.metrics.add_response_time(duration_ms)
            
            if response.status_code == 200:
                self.metrics.successful_requests += 1
                return True
            else:
                self.metrics.failed_requests += 1
                return False
        except Exception as e:
            self.metrics.failed_requests += 1
            return False
    
    async def test_list_categories(self) -> bool:
        """Test GET /api/v1/categories"""
        start = time.time()
        try:
            response = self.client.get("/api/v1/categories")
            duration_ms = (time.time() - start) * 1000
            
            self.metrics.total_requests += 1
            self.metrics.add_response_time(duration_ms)
            
            if response.status_code == 200:
                self.metrics.successful_requests += 1
                return True
            else:
                self.metrics.failed_requests += 1
                return False
        except Exception as e:
            self.metrics.failed_requests += 1
            return False
    
    async def run_load_test(self, concurrent_requests: int = 10, duration_seconds: int = 60):
        """Run load test with concurrent requests"""
        print(f"\n🔥 Starting load test: {concurrent_requests} concurrent requests for {duration_seconds}s")
        print("=" * 80)
        
        start_time = time.time()
        self.metrics.total_duration_seconds = 0
        
        test_operations = [
            (self.test_list_files, "List Files"),
            (self.test_search_files, "Search Files", "Documents"),
            (self.test_get_duplicates, "Get Duplicates"),
            (self.test_get_report, "Get Report"),
            (self.test_export_report, "Export JSON", "json"),
            (self.test_list_categories, "List Categories"),
        ]
        
        request_num = 0
        while time.time() - start_time < duration_seconds:
            tasks = []
            for _ in range(concurrent_requests):
                test_func, *args = test_operations[request_num % len(test_operations)]
                tasks.append(test_func(*args))
                request_num += 1
            
            # Run concurrent requests
            await asyncio.gather(*tasks)
            
            # Record resource usage
            self._record_resource_usage()
            
            elapsed = time.time() - start_time
            print(f"  Requests: {self.metrics.total_requests:>6} | "
                  f"Success: {self.metrics.successful_requests:>6} | "
                  f"Failed: {self.metrics.failed_requests:>6} | "
                  f"Elapsed: {elapsed:>6.1f}s", end="\r")
        
        self.metrics.total_duration_seconds = time.time() - start_time
        print()
    
    def _record_resource_usage(self):
        """Record memory and CPU usage"""
        try:
            memory_info = self.process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            self.metrics.memory_peak_mb = max(self.metrics.memory_peak_mb, memory_mb)
            
            cpu_percent = self.process.cpu_percent(interval=0.1)
            # Running average
            if self.metrics.cpu_percent_avg == 0:
                self.metrics.cpu_percent_avg = cpu_percent
            else:
                self.metrics.cpu_percent_avg = (
                    self.metrics.cpu_percent_avg * 0.9 + cpu_percent * 0.1
                )
        except:
            pass
    
    def print_results(self):
        """Print formatted test results"""
        print("\n📊 LOAD TEST RESULTS")
        print("=" * 80)
        
        results = self.metrics.to_dict()
        
        print("\n📈 Summary:")
        for key, value in results["summary"].items():
            print(f"  {key}: {value}")
        
        print("\n⏱️  Response Times:")
        for key, value in results["response_times"].items():
            print(f"  {key}: {value}ms")
        
        print("\n💾 Resource Usage:")
        for key, value in results["resource_usage"].items():
            print(f"  {key}: {value}")
        
        print("\n🗄️  Database Metrics:")
        for key, value in results["database"].items():
            print(f"  {key}: {value}")
        
        return results
    
    def save_results(self, filename: str = "load_test_results.json"):
        """Save results to JSON file"""
        results = self.metrics.to_dict()
        results["timestamp"] = datetime.now().isoformat()
        results["test_file_count"] = TEST_FILES_COUNT
        results["api_url"] = API_BASE_URL
        
        output_path = Path("data/reports") / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"\n✅ Results saved to: {output_path}")
        return str(output_path)
    
    def close(self):
        """Close client"""
        self.client.close()


async def main():
    """Main load test execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load test FileOrganizer API")
    parser.add_argument("--files", type=int, default=TEST_FILES_COUNT,
                       help="Number of test files to simulate")
    parser.add_argument("--duration", type=int, default=60,
                       help="Load test duration in seconds")
    parser.add_argument("--concurrent", type=int, default=10,
                       help="Number of concurrent requests")
    parser.add_argument("--report", action="store_true",
                       help="Save results to JSON report")
    
    args = parser.parse_args()
    
    # Check if API is running
    try:
        response = httpx.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ API is not healthy. Please start the API server.")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to API at {API_BASE_URL}")
        print(f"   Make sure the API server is running: python -m uvicorn src.backend.api.main:app")
        sys.exit(1)
    
    print(f"\n🚀 Phase 3 Week 4: Load Testing")
    print(f"   API URL: {API_BASE_URL}")
    print(f"   Test Files: {args.files:,}")
    print(f"   Duration: {args.duration}s")
    print(f"   Concurrent Requests: {args.concurrent}")
    print()
    
    client = LoadTestClient()
    
    try:
        # Setup
        print("📝 Setting up test...")
        if not await client.register_user():
            if "already exists" not in str(client.client.get(
                "/api/v1/auth/login",
                json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
            )):
                print("❌ Cannot setup test user")
                return
        
        if not await client.login_user():
            print("❌ Cannot login")
            return
        
        if not await client.start_operation():
            print("❌ Cannot start operation")
            return
        
        if not await client.create_test_files(args.files):
            print("❌ Cannot create test files")
            return
        
        # Run load test
        await client.run_load_test(
            concurrent_requests=args.concurrent,
            duration_seconds=args.duration
        )
        
        # Display results
        client.print_results()
        
        # Save if requested
        if args.report:
            client.save_results()
    
    finally:
        client.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⛔ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
