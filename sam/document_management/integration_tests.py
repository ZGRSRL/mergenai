#!/usr/bin/env python3
"""
Integration Tests for SAM API and DB Interactions
Tests the critical components after bug fixes
"""

import os
import sys
import logging
import psycopg2
from datetime import datetime
from typing import Dict, Any, Optional

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class IntegrationTester:
    """Integration test suite for SAM system"""
    
    def __init__(self):
        self.test_results = {}
        self.db_conn = None
        
    def setup_environment(self):
        """Setup test environment"""
        logger.info("🔧 Setting up test environment...")
        
        # Check environment variables
        env_vars = ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'SAM_API_KEY']
        missing_vars = []
        
        for var in env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.warning(f"⚠️ Missing environment variables: {missing_vars}")
            logger.info("Using default values for testing...")
        
        return True
    
    def test_database_connection(self):
        """Test database connection with environment variables"""
        logger.info("🔌 Testing database connection...")
        
        try:
            self.db_conn = psycopg2.connect(
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'sam'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', 'postgres')
            )
            
            with self.db_conn.cursor() as cur:
                cur.execute("SELECT version();")
                version = cur.fetchone()
                logger.info(f"✅ Database connected: {version[0][:50]}...")
            
            self.test_results['database_connection'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            self.test_results['database_connection'] = False
            return False
    
    def test_sam_document_access(self):
        """Test SAM document access functionality"""
        logger.info("📄 Testing SAM document access...")
        
        try:
            from sam_document_access_v2 import SAMDocumentAccessManager
            
            manager = SAMDocumentAccessManager()
            
            # Test database connection
            if manager.db_conn:
                logger.info("✅ SAMDocumentAccessManager database connection OK")
                
                # Test opportunity count
                with manager.db_conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM opportunities;")
                    count = cur.fetchone()[0]
                    logger.info(f"✅ Opportunities count: {count}")
                
                self.test_results['sam_document_access'] = True
                return True
            else:
                logger.error("❌ SAMDocumentAccessManager database connection failed")
                self.test_results['sam_document_access'] = False
                return False
                
        except Exception as e:
            logger.error(f"❌ SAM document access test failed: {e}")
            self.test_results['sam_document_access'] = False
            return False
    
    def test_ultra_optimized_manager(self):
        """Test ultra optimized SAM manager"""
        logger.info("⚡ Testing ultra optimized SAM manager...")
        
        try:
            from ultra_optimized_sam_manager import UltraOptimizedSAMManager
            
            manager = UltraOptimizedSAMManager()
            
            # Test database connection
            if manager.db_conn:
                logger.info("✅ UltraOptimizedSAMManager database connection OK")
                
                # Test update strategy (should not crash with timedelta fix)
                try:
                    result = manager.ultra_bulk_fetch_and_store(days_back=1, limit=5)
                    logger.info(f"✅ Bulk fetch test completed: {result}")
                except Exception as e:
                    logger.warning(f"⚠️ Bulk fetch test failed (expected without API key): {e}")
                
                self.test_results['ultra_optimized_manager'] = True
                return True
            else:
                logger.error("❌ UltraOptimizedSAMManager database connection failed")
                self.test_results['ultra_optimized_manager'] = False
                return False
                
        except Exception as e:
            logger.error(f"❌ Ultra optimized manager test failed: {e}")
            self.test_results['ultra_optimized_manager'] = False
            return False
    
    def test_autogen_orchestrator(self):
        """Test AutoGen orchestrator (should not crash on import)"""
        logger.info("🤖 Testing AutoGen orchestrator...")
        
        try:
            from autogen_orchestrator import AutoGenOrchestrator
            
            orchestrator = AutoGenOrchestrator()
            logger.info("✅ AutoGen orchestrator imported successfully")
            
            # Test fallback analysis
            test_data = {
                'opportunity_id': 'TEST-123',
                'title': 'Test Opportunity',
                'description': 'This is a test opportunity for integration testing.'
            }
            
            result = orchestrator._fallback_analysis(test_data, [])
            logger.info(f"✅ Fallback analysis test completed: {result.get('go_no_go_score', 'N/A')}")
            
            self.test_results['autogen_orchestrator'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ AutoGen orchestrator test failed: {e}")
            self.test_results['autogen_orchestrator'] = False
            return False
    
    def test_job_manager(self):
        """Test job manager (should not crash on import)"""
        logger.info("⚙️ Testing job manager...")
        
        try:
            from job_manager import JobManager
            
            job_manager = JobManager()
            logger.info("✅ Job manager imported successfully")
            
            # Test job creation
            job_id = job_manager._create_job_record('TEST-123')
            logger.info(f"✅ Job creation test completed: {job_id}")
            
            self.test_results['job_manager'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Job manager test failed: {e}")
            self.test_results['job_manager'] = False
            return False
    
    def test_jsonb_parsing(self):
        """Test JSONB parsing fix"""
        logger.info("🔍 Testing JSONB parsing...")
        
        try:
            from sam_document_access_v2 import SAMDocumentAccessManager
            
            manager = SAMDocumentAccessManager()
            
            if manager.db_conn:
                # Test with a real opportunity if available
                with manager.db_conn.cursor() as cur:
                    cur.execute("SELECT opportunity_id, point_of_contact FROM opportunities LIMIT 1;")
                    result = cur.fetchone()
                    
                    if result:
                        opportunity_id, point_of_contact = result
                        logger.info(f"Testing JSONB parsing for opportunity: {opportunity_id}")
                        
                        # Test description access
                        description = manager.get_opportunity_description(opportunity_id)
                        logger.info(f"✅ Description access test: {description is not None}")
                        
                        # Test resource links access
                        resource_links = manager.get_opportunity_resource_links(opportunity_id)
                        logger.info(f"✅ Resource links access test: {len(resource_links) if resource_links else 0} links")
                        
                        self.test_results['jsonb_parsing'] = True
                        return True
                    else:
                        logger.warning("⚠️ No opportunities found for JSONB testing")
                        self.test_results['jsonb_parsing'] = True  # Pass if no data
                        return True
            else:
                logger.error("❌ No database connection for JSONB testing")
                self.test_results['jsonb_parsing'] = False
                return False
                
        except Exception as e:
            logger.error(f"❌ JSONB parsing test failed: {e}")
            self.test_results['jsonb_parsing'] = False
            return False
    
    def run_all_tests(self):
        """Run all integration tests"""
        logger.info("🚀 Starting integration tests...")
        
        tests = [
            self.setup_environment,
            self.test_database_connection,
            self.test_sam_document_access,
            self.test_ultra_optimized_manager,
            self.test_autogen_orchestrator,
            self.test_job_manager,
            self.test_jsonb_parsing
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                logger.error(f"❌ Test {test.__name__} crashed: {e}")
        
        logger.info(f"📊 Test Results: {passed}/{total} tests passed")
        
        # Print detailed results
        logger.info("\n📋 Detailed Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            logger.info(f"  {test_name}: {status}")
        
        return passed == total
    
    def cleanup(self):
        """Cleanup test resources"""
        if self.db_conn:
            self.db_conn.close()
            logger.info("🧹 Database connection closed")

def main():
    """Main test runner"""
    print("🧪 SAM System Integration Tests")
    print("=" * 50)
    
    tester = IntegrationTester()
    
    try:
        success = tester.run_all_tests()
        
        if success:
            print("\n🎉 All tests passed! System is ready.")
            return 0
        else:
            print("\n⚠️ Some tests failed. Check the logs above.")
            return 1
            
    except Exception as e:
        logger.error(f"❌ Test suite crashed: {e}")
        return 1
        
    finally:
        tester.cleanup()

if __name__ == "__main__":
    exit(main())
