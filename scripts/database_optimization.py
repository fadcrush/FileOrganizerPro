"""
Phase 3 Week 4: Database Optimization

Migration script to add indexes for performance optimization.
Also includes analysis tools for identifying slow queries.

Usage:
    # Run migration (adds indexes)
    alembic upgrade head
    
    # Or run directly:
    python scripts/database_optimization.py --optimize
    
    # Analyze slow queries:
    python scripts/database_optimization.py --analyze
"""

from sqlalchemy import text, create_engine, inspect
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import time
from typing import List, Dict

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/file_organizer"
)


class DatabaseOptimizer:
    """Database optimization and analysis"""
    
    def __init__(self, database_url: str = DATABASE_URL):
        self.engine = create_engine(database_url, echo=False)
        self.inspector = inspect(self.engine)
    
    def get_existing_indexes(self) -> Dict[str, List[str]]:
        """Get all existing indexes by table"""
        indexes = {}
        for table_name in self.inspector.get_table_names():
            indexes[table_name] = [
                idx["name"] for idx in self.inspector.get_indexes(table_name)
            ]
        return indexes
    
    def create_indexes(self) -> List[str]:
        """Create recommended indexes"""
        indexes_to_create = [
            # Operations table
            ("idx_operations_user_id", "operations", ["user_id"]),
            ("idx_operations_created_at", "operations", ["created_at"]),
            ("idx_operations_status", "operations", ["status"]),
            ("idx_operations_user_created", "operations", ["user_id", "created_at"]),
            
            # FileRecord table
            ("idx_file_record_operation_id", "file_record", ["operation_id"]),
            ("idx_file_record_status", "file_record", ["status"]),
            ("idx_file_record_category", "file_record", ["category"]),
            ("idx_file_record_hash", "file_record", ["file_hash"]),
            ("idx_file_record_op_status", "file_record", ["operation_id", "status"]),
            ("idx_file_record_op_hash", "file_record", ["operation_id", "file_hash"]),
            ("idx_file_record_path", "file_record", ["new_path"]),
            
            # APIKey table
            ("idx_api_key_user_id", "api_key", ["user_id"]),
            ("idx_api_key_token_hash", "api_key", ["token_hash"]),
            
            # User table
            ("idx_user_email", "user", ["email"]),
        ]
        
        created = []
        with self.engine.connect() as conn:
            for idx_name, table_name, columns in indexes_to_create:
                try:
                    column_str = ", ".join(columns)
                    query = f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name} ({column_str})"
                    conn.execute(text(query))
                    conn.commit()
                    created.append(f"✅ {idx_name}")
                    print(f"✅ Created index: {idx_name}")
                except Exception as e:
                    print(f"⚠️  Could not create {idx_name}: {e}")
        
        return created
    
    def analyze_query_performance(self, query: str) -> Dict:
        """Analyze query performance with EXPLAIN"""
        with self.engine.connect() as conn:
            try:
                explain_query = f"EXPLAIN ANALYZE {query}"
                result = conn.execute(text(explain_query))
                plan = result.fetchall()
                
                # Parse plan to extract key metrics
                plan_text = "\n".join([row[0] for row in plan])
                
                metrics = {
                    "query": query,
                    "execution_plan": plan_text,
                    "uses_index": "Index" in plan_text,
                    "full_scan": "Seq Scan" in plan_text,
                }
                
                return metrics
            except Exception as e:
                return {"error": str(e)}
    
    def get_slow_queries_report(self) -> List[Dict]:
        """Get report of potentially slow queries"""
        queries = [
            {
                "name": "List operations for user",
                "query": """
                    SELECT * FROM operations 
                    WHERE user_id = '123e4567-e89b-12d3-a456-426614174000'
                    ORDER BY created_at DESC 
                    LIMIT 10
                """
            },
            {
                "name": "Find duplicates in operation",
                "query": """
                    SELECT file_hash, COUNT(*) as count 
                    FROM file_record 
                    WHERE operation_id = '123e4567-e89b-12d3-a456-426614174000'
                    GROUP BY file_hash 
                    HAVING COUNT(*) > 1
                """
            },
            {
                "name": "Search files by path",
                "query": """
                    SELECT * FROM file_record 
                    WHERE operation_id = '123e4567-e89b-12d3-a456-426614174000'
                    AND new_path ILIKE '%documents%'
                    LIMIT 100
                """
            },
            {
                "name": "Get files by category",
                "query": """
                    SELECT * FROM file_record 
                    WHERE operation_id = '123e4567-e89b-12d3-a456-426614174000'
                    AND category = 'Documents'
                    ORDER BY created_at DESC
                """
            },
            {
                "name": "Files with status filter",
                "query": """
                    SELECT * FROM file_record 
                    WHERE operation_id = '123e4567-e89b-12d3-a456-426614174000'
                    AND status = 'completed'
                    LIMIT 100
                """
            }
        ]
        
        results = []
        for query_info in queries:
            analysis = self.analyze_query_performance(query_info["query"])
            results.append({
                **query_info,
                **analysis
            })
        
        return results
    
    def get_table_stats(self) -> Dict:
        """Get table statistics"""
        stats = {}
        with self.engine.connect() as conn:
            for table_name in self.inspector.get_table_names():
                try:
                    result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                    count = result.scalar()
                    
                    # Get size
                    size_result = conn.execute(
                        text(f"SELECT pg_total_relation_size('{table_name}') as size")
                    )
                    size = size_result.scalar()
                    
                    stats[table_name] = {
                        "row_count": count,
                        "size_bytes": size,
                        "size_mb": round(size / (1024 * 1024), 2),
                    }
                except:
                    pass
        
        return stats
    
    def optimize_database(self) -> Dict:
        """Run all optimizations"""
        print("\n🗄️  Phase 3 Week 4: Database Optimization")
        print("=" * 80)
        
        results = {
            "timestamp": time.time(),
            "optimizations": []
        }
        
        # Create indexes
        print("\n📊 Creating indexes...")
        created = self.create_indexes()
        results["optimizations"].extend(created)
        
        # Get table stats
        print("\n📈 Table statistics:")
        stats = self.get_table_stats()
        for table, info in stats.items():
            print(f"  {table}: {info['row_count']} rows, {info['size_mb']}MB")
        results["table_stats"] = stats
        
        # Analyze slow queries
        print("\n⚡ Analyzing query performance...")
        slow_queries = self.get_slow_queries_report()
        for query_info in slow_queries:
            status = "🟢 Uses Index" if query_info.get("uses_index") else "🔴 Full Scan"
            print(f"  {query_info['name']}: {status}")
        results["query_analysis"] = slow_queries
        
        return results
    
    def print_optimization_report(self, results: Dict):
        """Print optimization report"""
        print("\n✅ OPTIMIZATION REPORT")
        print("=" * 80)
        
        print("\n📊 Indexes Created:")
        for opt in results.get("optimizations", []):
            print(f"  {opt}")
        
        print("\n📈 Table Statistics:")
        for table, stats in results.get("table_stats", {}).items():
            print(f"  {table}:")
            print(f"    Rows: {stats['row_count']}")
            print(f"    Size: {stats['size_mb']}MB")
        
        print("\n⚡ Query Performance Analysis:")
        for query in results.get("query_analysis", []):
            print(f"  {query['name']}:")
            if "error" in query:
                print(f"    ⚠️  Error: {query['error']}")
            else:
                print(f"    Uses Index: {query.get('uses_index', False)}")
                print(f"    Full Scan: {query.get('full_scan', False)}")


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Database optimization")
    parser.add_argument("--optimize", action="store_true", help="Run optimizations")
    parser.add_argument("--analyze", action="store_true", help="Analyze queries")
    parser.add_argument("--stats", action="store_true", help="Show table statistics")
    
    args = parser.parse_args()
    
    optimizer = DatabaseOptimizer()
    
    if args.optimize or (not args.analyze and not args.stats):
        results = optimizer.optimize_database()
        optimizer.print_optimization_report(results)
    
    if args.analyze:
        print("\n⚡ Query Performance Analysis")
        print("=" * 80)
        queries = optimizer.get_slow_queries_report()
        for query in queries:
            print(f"\n{query['name']}:")
            print(query.get("execution_plan", "N/A"))
    
    if args.stats:
        print("\n📈 Table Statistics")
        print("=" * 80)
        stats = optimizer.get_table_stats()
        for table, info in stats.items():
            print(f"{table}: {info['row_count']} rows, {info['size_mb']}MB")


if __name__ == "__main__":
    main()
