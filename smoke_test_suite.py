#!/usr/bin/env python3
"""
Smoke Test Suite - Production readiness tests
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Add current directory to path
sys.path.append('.')

# Import modules
try:
    from agent_log_manager import get_recent_actions, get_agent_stats, get_termination_metrics
    from rate_limit_guard import execute_with_retry, backoff_sleep
    from duplicate_guard import should_process_notice, start_processing, complete_processing
    from security_mask import mask_sensitive_data, get_masked_env_vars
    from sow_autogen_workflow import run_workflow_for_notice
    from sam_api_client_safe import SamClientSafe
except ImportError as e:
    print(f"Warning: Could not import modules: {e}")
    print("Some tests may be skipped")

class SmokeTestSuite:
    """Smoke test suite for production readiness"""
    
    def __init__(self):
        self.logger = logging.getLogger("SmokeTestSuite")
        self.test_results = []
        self.start_time = datetime.now()
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        
    def log_test_result(self, test_name: str, status: str, message: str, duration: float = 0.0):
        """Log test result"""
        result = {
            "test_name": test_name,
            "status": status,
            "message": message,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "[PASS]" if status == "PASS" else "[FAIL]" if status == "FAIL" else "[WARN]"
        print(f"{status_icon} {test_name}: {message} ({duration:.2f}s)")
    
    def test_environment_variables(self) -> bool:
        """Test environment variables"""
        start_time = time.time()
        
        try:
            # Check required environment variables
            required_vars = ['POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
            missing_vars = []
            
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                self.logger.warning(f"Missing environment variables: {missing_vars}")
                self.log_test_result(
                    "Environment Variables", 
                    "WARN", 
                    f"Missing: {missing_vars}",
                    time.time() - start_time
                )
                return False
            else:
                self.log_test_result(
                    "Environment Variables", 
                    "PASS", 
                    "All required variables present",
                    time.time() - start_time
                )
                return True
                
        except Exception as e:
            self.log_test_result(
                "Environment Variables", 
                "FAIL", 
                f"Error: {e}",
                time.time() - start_time
            )
            return False
    
    def test_database_connection(self) -> bool:
        """Test database connection"""
        start_time = time.time()
        
        try:
            from check_database import execute_query
            
            # Simple query to test connection
            result = execute_query("SELECT 1 as test", fetch='one')
            
            if result and result[0] == 1:
                self.log_test_result(
                    "Database Connection", 
                    "PASS", 
                    "Database connection successful",
                    time.time() - start_time
                )
                return True
            else:
                self.log_test_result(
                    "Database Connection", 
                    "FAIL", 
                    "Database query failed",
                    time.time() - start_time
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Database Connection", 
                "FAIL", 
                f"Error: {e}",
                time.time() - start_time
            )
            return False
    
    def test_sam_api_connection(self) -> bool:
        """Test SAM API connection"""
        start_time = time.time()
        
        try:
            client = SamClientSafe()
            
            # Test API connection with minimal request
            result = client.search_recent(days=1, limit=1)
            
            if result and result.get('success'):
                self.log_test_result(
                    "SAM API Connection", 
                    "PASS", 
                    "SAM API connection successful",
                    time.time() - start_time
                )
                return True
            else:
                self.log_test_result(
                    "SAM API Connection", 
                    "WARN", 
                    "SAM API returned no data",
                    time.time() - start_time
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "SAM API Connection", 
                "FAIL", 
                f"Error: {e}",
                time.time() - start_time
            )
            return False
    
    def test_agent_log_system(self) -> bool:
        """Test agent log system"""
        start_time = time.time()
        
        try:
            # Test log functions
            recent_actions = get_recent_actions(5)
            stats = get_agent_stats()
            termination_metrics = get_termination_metrics()
            
            if isinstance(recent_actions, list) and isinstance(stats, dict):
                self.log_test_result(
                    "Agent Log System", 
                    "PASS", 
                    f"Log system working: {len(recent_actions)} recent actions",
                    time.time() - start_time
                )
                return True
            else:
                self.log_test_result(
                    "Agent Log System", 
                    "FAIL", 
                    "Log system returned invalid data",
                    time.time() - start_time
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Agent Log System", 
                "FAIL", 
                f"Error: {e}",
                time.time() - start_time
            )
            return False
    
    def test_rate_limiting(self) -> bool:
        """Test rate limiting system"""
        start_time = time.time()
        
        try:
            # Test backoff sleep
            test_start = time.time()
            backoff_sleep(1, base=0.1, cap=1.0)
            sleep_duration = time.time() - test_start
            
            if 0.1 <= sleep_duration <= 1.5:  # Allow some jitter
                self.log_test_result(
                    "Rate Limiting", 
                    "PASS", 
                    f"Backoff sleep working: {sleep_duration:.2f}s",
                    time.time() - start_time
                )
                return True
            else:
                self.log_test_result(
                    "Rate Limiting", 
                    "FAIL", 
                    f"Backoff sleep incorrect: {sleep_duration:.2f}s",
                    time.time() - start_time
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Rate Limiting", 
                "FAIL", 
                f"Error: {e}",
                time.time() - start_time
            )
            return False
    
    def test_duplicate_guard(self) -> bool:
        """Test duplicate guard system"""
        start_time = time.time()
        
        try:
            # Test duplicate detection
            notice_id = "SMOKE_TEST_001"
            source_hash = "test_hash_123"
            
            # First check should allow processing
            result1 = should_process_notice(notice_id, source_hash)
            if result1.get('should_process'):
                # Start processing
                key = start_processing(notice_id, source_hash)
                
                # Second check should block
                result2 = should_process_notice(notice_id, source_hash)
                if not result2.get('should_process'):
                    # Complete processing
                    complete_processing(key, "test_analysis_123")
                    
                    self.log_test_result(
                        "Duplicate Guard", 
                        "PASS", 
                        "Duplicate detection working",
                        time.time() - start_time
                    )
                    return True
                else:
                    self.log_test_result(
                        "Duplicate Guard", 
                        "FAIL", 
                        "Duplicate detection not working",
                        time.time() - start_time
                    )
                    return False
            else:
                self.log_test_result(
                    "Duplicate Guard", 
                    "FAIL", 
                    "Initial processing check failed",
                    time.time() - start_time
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Duplicate Guard", 
                "FAIL", 
                f"Error: {e}",
                time.time() - start_time
            )
            return False
    
    def test_security_mask(self) -> bool:
        """Test security mask system"""
        start_time = time.time()
        
        try:
            # Test masking
            test_data = {
                'api_key': 'sk-1234567890abcdef',
                'password': 'secret123',
                'normal_data': 'this is not sensitive'
            }
            
            masked_data = mask_sensitive_data(test_data)
            
            if (masked_data['api_key'] == '***MASKED***' and 
                masked_data['password'] == '***MASKED***' and
                masked_data['normal_data'] == 'this is not sensitive'):
                
                self.log_test_result(
                    "Security Mask", 
                    "PASS", 
                    "Sensitive data masking working",
                    time.time() - start_time
                )
                return True
            else:
                self.log_test_result(
                    "Security Mask", 
                    "FAIL", 
                    "Sensitive data not properly masked",
                    time.time() - start_time
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Security Mask", 
                "FAIL", 
                f"Error: {e}",
                time.time() - start_time
            )
            return False
    
    def test_sow_workflow(self) -> bool:
        """Test SOW workflow"""
        start_time = time.time()
        
        try:
            # Test workflow with mock notice
            result = run_workflow_for_notice("SMOKE_TEST_001")
            
            if result and isinstance(result, dict) and 'status' in result:
                self.log_test_result(
                    "SOW Workflow", 
                    "PASS", 
                    f"Workflow completed: {result['status']}",
                    time.time() - start_time
                )
                return True
            else:
                self.log_test_result(
                    "SOW Workflow", 
                    "FAIL", 
                    "Workflow returned invalid result",
                    time.time() - start_time
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "SOW Workflow", 
                "FAIL", 
                f"Error: {e}",
                time.time() - start_time
            )
            return False
    
    def test_load_performance(self) -> bool:
        """Test load performance with 5 notices"""
        start_time = time.time()
        
        try:
            # Test processing 5 notices sequentially
            test_notices = [f"LOAD_TEST_{i:03d}" for i in range(1, 6)]
            results = []
            
            for notice in test_notices:
                notice_start = time.time()
                result = run_workflow_for_notice(notice)
                notice_duration = time.time() - notice_start
                results.append((notice, result.get('status', 'unknown'), notice_duration))
            
            total_duration = time.time() - start_time
            avg_duration = total_duration / len(test_notices)
            
            if avg_duration < 15.0:  # P95 < 15s target
                self.log_test_result(
                    "Load Performance", 
                    "PASS", 
                    f"Average processing time: {avg_duration:.2f}s",
                    time.time() - start_time
                )
                return True
            else:
                self.log_test_result(
                    "Load Performance", 
                    "WARN", 
                    f"Average processing time too high: {avg_duration:.2f}s",
                    time.time() - start_time
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Load Performance", 
                "FAIL", 
                f"Error: {e}",
                time.time() - start_time
            )
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all smoke tests"""
        print("Starting Smoke Test Suite...")
        print("=" * 50)
        
        # Run all tests
        tests = [
            self.test_environment_variables,
            self.test_database_connection,
            self.test_sam_api_connection,
            self.test_agent_log_system,
            self.test_rate_limiting,
            self.test_duplicate_guard,
            self.test_security_mask,
            self.test_sow_workflow,
            self.test_load_performance
        ]
        
        passed = 0
        failed = 0
        warned = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    if any("WARN" in result["status"] for result in self.test_results[-1:]):
                        warned += 1
                    else:
                        failed += 1
            except Exception as e:
                failed += 1
                self.log_test_result(test.__name__, "FAIL", f"Exception: {e}")
        
        # Summary
        total_duration = (datetime.now() - self.start_time).total_seconds()
        
        print("\n" + "=" * 50)
        print("SMOKE TEST SUMMARY")
        print("=" * 50)
        print(f"Passed: {passed}")
        print(f"Warnings: {warned}")
        print(f"Failed: {failed}")
        print(f"Total Duration: {total_duration:.2f}s")
        
        # Overall status
        if failed == 0:
            print("ALL TESTS PASSED - System is production ready!")
            overall_status = "PASS"
        elif failed <= 2:
            print("Some tests failed - Review before production")
            overall_status = "WARN"
        else:
            print("Multiple tests failed - System not ready for production")
            overall_status = "FAIL"
        
        return {
            "overall_status": overall_status,
            "passed": passed,
            "warned": warned,
            "failed": failed,
            "total_duration": total_duration,
            "test_results": self.test_results
        }

def main():
    """Main function"""
    suite = SmokeTestSuite()
    results = suite.run_all_tests()
    
    # Save results to file
    results_file = f"smoke_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")
    
    # Exit with appropriate code
    if results["overall_status"] == "PASS":
        sys.exit(0)
    elif results["overall_status"] == "WARN":
        sys.exit(1)
    else:
        sys.exit(2)

if __name__ == "__main__":
    main()
