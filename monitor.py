#!/usr/bin/env python3
"""
Monitoring script for ABT AI Image Description production server
"""

import psutil
import asyncio
import asyncpg
import json
import time
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class ProductionMonitor:
    def __init__(self):
        self.db_config = {
            'host': os.getenv("POSTGRES_HOST"),
            'port': int(os.getenv("POSTGRES_PORT")),
            'user': os.getenv("POSTGRES_USER"),
            'password': os.getenv("POSTGRES_PASSWORD"),
            'database': os.getenv("POSTGRES_DB")
        }
    
    async def get_system_stats(self):
        """Get system statistics"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available': memory.available,
            'memory_total': memory.total,
            'disk_percent': disk.percent,
            'disk_free': disk.free,
            'disk_total': disk.total
        }
    
    async def get_database_stats(self):
        """Get database connection statistics"""
        try:
            pool = await asyncpg.create_pool(**self.db_config)
            async with pool.acquire() as conn:
                # Get active connections
                active_connections = await conn.fetchval(
                    "SELECT count(*) FROM pg_stat_activity WHERE state = 'active'"
                )
                
                # Get database size
                db_size = await conn.fetchval(
                    "SELECT pg_database_size(current_database())"
                )
                
                # Get table statistics
                table_stats = await conn.fetch("""
                    SELECT 
                        schemaname,
                        tablename,
                        attname,
                        n_distinct,
                        correlation
                    FROM pg_stats 
                    WHERE schemaname = 'public'
                    LIMIT 10
                """)
                
            await pool.close()
            
            return {
                'active_connections': active_connections,
                'database_size_bytes': db_size,
                'table_stats': [dict(row) for row in table_stats]
            }
        except Exception as e:
            return {'error': str(e)}
    
    async def get_application_stats(self):
        """Get application-specific statistics"""
        try:
            pool = await asyncpg.create_pool(**self.db_config)
            async with pool.acquire() as conn:
                # Total records
                total_records = await conn.fetchval(
                    "SELECT COUNT(*) FROM abt_image_to_products_1688"
                )
                
                # Records with labels
                labeled_records = await conn.fetchval(
                    "SELECT COUNT(*) FROM abt_image_to_products_1688 WHERE abt_label IS NOT NULL"
                )
                
                # Records with best_match
                matched_records = await conn.fetchval(
                    "SELECT COUNT(*) FROM abt_image_to_products_1688 WHERE best_match IS NOT NULL"
                )
                
                # Recent activity (last 24 hours)
                recent_activity = await conn.fetchval("""
                    SELECT COUNT(*) FROM abt_image_to_products_1688 
                    WHERE updated_at >= NOW() - INTERVAL '24 hours'
                """)
                
                # Average confidence score
                avg_confidence = await conn.fetchval("""
                    SELECT AVG(CAST(abt_label->>'chi_so_tin_cay' AS FLOAT))
                    FROM abt_image_to_products_1688 
                    WHERE abt_label IS NOT NULL 
                    AND abt_label->>'chi_so_tin_cay' IS NOT NULL
                """)
                
            await pool.close()
            
            return {
                'total_records': total_records,
                'labeled_records': labeled_records,
                'matched_records': matched_records,
                'recent_activity_24h': recent_activity,
                'avg_confidence_score': float(avg_confidence) if avg_confidence else 0.0,
                'labeling_progress': (labeled_records / total_records * 100) if total_records > 0 else 0.0,
                'matching_progress': (matched_records / total_records * 100) if total_records > 0 else 0.0
            }
        except Exception as e:
            return {'error': str(e)}
    
    async def get_process_stats(self):
        """Get process statistics"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                if 'python' in proc.info['name'].lower() or 'gunicorn' in proc.info['name'].lower():
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'cpu_percent': proc.info['cpu_percent'],
                        'memory_percent': proc.info['memory_percent']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return processes
    
    async def generate_report(self):
        """Generate comprehensive monitoring report"""
        system_stats = await self.get_system_stats()
        db_stats = await self.get_database_stats()
        app_stats = await self.get_application_stats()
        process_stats = await self.get_process_stats()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'system': system_stats,
            'database': db_stats,
            'application': app_stats,
            'processes': process_stats
        }
        
        return report
    
    async def save_report(self, report):
        """Save monitoring report to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"monitoring_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        print(f"Report saved to {filename}")
    
    async def print_summary(self, report):
        """Print monitoring summary"""
        print("\n" + "="*50)
        print("PRODUCTION MONITORING SUMMARY")
        print("="*50)
        
        # System stats
        sys = report['system']
        print(f"CPU Usage: {sys['cpu_percent']:.1f}%")
        print(f"Memory Usage: {sys['memory_percent']:.1f}% ({sys['memory_available']/1024/1024/1024:.1f}GB available)")
        print(f"Disk Usage: {sys['disk_percent']:.1f}% ({sys['disk_free']/1024/1024/1024:.1f}GB free)")
        
        # Database stats
        db = report['database']
        if 'error' not in db:
            print(f"Active DB Connections: {db['active_connections']}")
            print(f"Database Size: {db['database_size_bytes']/1024/1024:.1f}MB")
        
        # Application stats
        app = report['application']
        if 'error' not in app:
            print(f"Total Records: {app['total_records']:,}")
            print(f"Labeled Records: {app['labeled_records']:,} ({app['labeling_progress']:.1f}%)")
            print(f"Matched Records: {app['matched_records']:,} ({app['matching_progress']:.1f}%)")
            print(f"Recent Activity (24h): {app['recent_activity_24h']:,}")
            print(f"Average Confidence: {app['avg_confidence_score']:.3f}")
        
        # Process stats
        print(f"Python/Gunicorn Processes: {len(report['processes'])}")
        for proc in report['processes'][:3]:  # Show top 3
            print(f"  PID {proc['pid']}: {proc['name']} - CPU: {proc['cpu_percent']:.1f}%, Mem: {proc['memory_percent']:.1f}%")
        
        print("="*50)

async def main():
    """Main monitoring function"""
    monitor = ProductionMonitor()
    
    print("Starting production monitoring...")
    
    try:
        report = await monitor.generate_report()
        await monitor.print_summary(report)
        await monitor.save_report(report)
        
    except Exception as e:
        print(f"Monitoring error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 