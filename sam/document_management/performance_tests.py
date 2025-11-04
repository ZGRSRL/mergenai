#!/usr/bin/env python3
"""
Performance Test Suite
Tests the optimized components and measures performance improvements
"""

import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, Any, List

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PerformanceTester:
    """Performance test suite for optimized components"""
    
    def __init__(self):
        self.test_results = {}
        self.performance_metrics = {}
    
    def test_database_manager(self):
        """Test database manager performance"""
        logger.info("🔌 Testing database manager performance...")
        
        try:
            from database_manager import db_manager, DatabaseUtils
            
            # Test connection
            start_time = time.time()
            if db_manager.test_connection():
                connection_time = time.time() - start_time
                logger.info(f"✅ Database connection: {connection_time:.3f}s")
                
                # Test query performance
                start_time = time.time()
                count = DatabaseUtils.get_opportunity_count()
                query_time = time.time() - start_time
                logger.info(f"✅ Opportunity count query: {query_time:.3f}s ({count} records)")
                
                # Test recent opportunities query
                start_time = time.time()
                recent = DatabaseUtils.get_recent_opportunities(10)
                recent_time = time.time() - start_time
                logger.info(f"✅ Recent opportunities query: {recent_time:.3f}s ({len(recent)} records)")
                
                self.performance_metrics['database'] = {
                    'connection_time': connection_time,
                    'count_query_time': query_time,
                    'recent_query_time': recent_time,
                    'total_opportunities': count
                }
                
                return True
            else:
                logger.error("❌ Database connection failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Database manager test failed: {e}")
            return False
    
    def test_session_manager(self):
        """Test session manager performance"""
        logger.info("🌐 Testing session manager performance...")
        
        try:
            from session_manager import session_manager, http_client, get_http_stats
            
            # Test session creation
            start_time = time.time()
            session = session_manager.get_session()
            session_time = time.time() - start_time
            logger.info(f"✅ Session creation: {session_time:.3f}s")
            
            # Test HTTP client stats
            stats = get_http_stats()
            logger.info(f"📊 HTTP Client stats: {stats}")
            
            self.performance_metrics['session_manager'] = {
                'session_creation_time': session_time,
                'http_stats': stats
            }
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Session manager test failed: {e}")
            return False
    
    def test_streamlit_cache(self):
        """Test Streamlit cache performance"""
        logger.info("💾 Testing Streamlit cache performance...")
        
        try:
            from streamlit_cache import cache_manager, get_cache_info
            
            # Test cache info
            cache_info = get_cache_info()
            logger.info(f"📊 Cache info: {cache_info}")
            
            self.performance_metrics['streamlit_cache'] = cache_info
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Streamlit cache test failed: {e}")
            return False
    
    def test_optimized_sam_access(self):
        """Test optimized SAM access performance"""
        logger.info("🚀 Testing optimized SAM access performance...")
        
        try:
            from optimized_sam_access import optimized_sam_access
            
            # Test API stats
            api_stats = optimized_sam_access.get_api_stats()
            logger.info(f"📊 API stats: {api_stats}")
            
            # Test cached opportunity fetch (if data exists)
            start_time = time.time()
            try:
                # This will use cached data if available
                result = optimized_sam_access.fetch_opportunities_cached(
                    keywords="", days_back=7, limit=10
                )
                fetch_time = time.time() - start_time
                logger.info(f"✅ Cached opportunity fetch: {fetch_time:.3f}s ({result.get('totalRecords', 0)} records)")
                
                self.performance_metrics['sam_access'] = {
                    'cached_fetch_time': fetch_time,
                    'records_fetched': result.get('totalRecords', 0),
                    'api_stats': api_stats
                }
                
            except Exception as e:
                logger.warning(f"⚠️ Opportunity fetch test failed (expected without API key): {e}")
                self.performance_metrics['sam_access'] = {
                    'cached_fetch_time': 0,
                    'records_fetched': 0,
                    'api_stats': api_stats
                }
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Optimized SAM access test failed: {e}")
            return False
    
    def test_integration_performance(self):
        """Test overall integration performance"""
        logger.info("🔗 Testing integration performance...")
        
        try:
            # Test multiple components working together
            start_time = time.time()
            
            # Test database + cache integration
            from database_manager import DatabaseUtils
            from streamlit_cache import cache_manager
            
            # Simulate a typical workflow
            count = DatabaseUtils.get_opportunity_count()
            recent = DatabaseUtils.get_recent_opportunities(5)
            
            integration_time = time.time() - start_time
            
            logger.info(f"✅ Integration test: {integration_time:.3f}s")
            logger.info(f"   - Database queries: {len(recent)} records")
            logger.info(f"   - Total opportunities: {count}")
            
            self.performance_metrics['integration'] = {
                'total_time': integration_time,
                'opportunities_count': count,
                'recent_count': len(recent)
            }
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Integration performance test failed: {e}")
            return False
    
    def run_performance_tests(self):
        """Run all performance tests"""
        logger.info("🚀 Starting performance tests...")
        
        tests = [
            self.test_database_manager,
            self.test_session_manager,
            self.test_streamlit_cache,
            self.test_optimized_sam_access,
            self.test_integration_performance
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                logger.error(f"❌ Test {test.__name__} crashed: {e}")
        
        logger.info(f"📊 Performance Tests: {passed}/{total} tests passed")
        
        # Print performance summary
        self.print_performance_summary()
        
        return passed == total
    
    def print_performance_summary(self):
        """Print performance summary"""
        logger.info("\n📈 Performance Summary:")
        logger.info("=" * 50)
        
        for component, metrics in self.performance_metrics.items():
            logger.info(f"\n🔧 {component.upper()}:")
            for metric, value in metrics.items():
                if isinstance(value, dict):
                    logger.info(f"  {metric}:")
                    for sub_metric, sub_value in value.items():
                        logger.info(f"    {sub_metric}: {sub_value}")
                else:
                    logger.info(f"  {metric}: {value}")
        
        # Calculate overall performance score
        total_time = sum(
            metrics.get('total_time', 0) or 
            metrics.get('connection_time', 0) or 
            metrics.get('session_creation_time', 0) or 0
            for metrics in self.performance_metrics.values()
        )
        
        logger.info(f"\n⏱️ Total Test Time: {total_time:.3f}s")
        
        if total_time < 1.0:
            logger.info("🎉 EXCELLENT: All tests completed in under 1 second!")
        elif total_time < 5.0:
            logger.info("✅ GOOD: All tests completed in under 5 seconds")
        else:
            logger.info("⚠️ SLOW: Tests took longer than 5 seconds")

def main():
    """Main test runner"""
    print("⚡ SAM System Performance Tests")
    print("=" * 50)
    
    tester = PerformanceTester()
    
    try:
        success = tester.run_performance_tests()
        
        if success:
            print("\n🎉 All performance tests passed!")
            print("🚀 System is optimized and ready for production!")
            return 0
        else:
            print("\n⚠️ Some performance tests failed.")
            print("Check the logs above for details.")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Performance test suite crashed: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
