#!/usr/bin/env python3
"""
Hotel Intelligence Integration Test Suite
ZgrProp ↔ ZgrSam entegrasyonunu test eder
"""

import sys
import time
import json
from datetime import datetime
from typing import Dict, Any, Tuple
from hotel_intelligence_bridge import (
    check_zgrprop_connectivity,
    quick_hotel_analysis,
    hybrid_search_hotel_intelligence,
    get_enhanced_sow_workflow
)


class Colors:
    """Terminal renkleri"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'
    EMOJI_PASS = '✅'
    EMOJI_FAIL = '❌'
    EMOJI_WARN = '⚠️'


def print_header(title: str):
    """Test başlığı yazdır"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.END}\n")


def print_test_result(test_name: str, passed: bool, duration: float, details: str = ""):
    """Test sonucunu yazdır"""
    emoji = Colors.EMOJI_PASS if passed else Colors.EMOJI_FAIL
    color = Colors.GREEN if passed else Colors.RED
    status = "PASSED" if passed else "FAILED"
    
    print(f"{emoji} {test_name}: {color}{status}{Colors.END} ({duration:.2f}s)")
    if details:
        print(f"   {details}")


def test_zgrprop_connectivity() -> Tuple[bool, float, str]:
    """Test 1: ZgrProp Connectivity"""
    start_time = time.time()
    
    try:
        result = check_zgrprop_connectivity()
        duration = time.time() - start_time
        
        if result.get("connected"):
            return True, duration, "Connected to ZgrProp RAG API"
        else:
            return False, duration, f"Connection failed: {result.get('message', 'Unknown error')}"
    
    except Exception as e:
        duration = time.time() - start_time
        return False, duration, f"Exception: {str(e)}"


def test_health_endpoint() -> Tuple[bool, float, str]:
    """Test 2: Health Endpoint"""
    start_time = time.time()
    
    try:
        result = check_zgrprop_connectivity()
        duration = time.time() - start_time
        
        if result.get("connected") and "response" in result:
            return True, duration, "Health endpoint responding"
        else:
            return False, duration, "Health endpoint not responding"
    
    except Exception as e:
        duration = time.time() - start_time
        return False, duration, f"Exception: {str(e)}"


def test_hybrid_search() -> Tuple[bool, float, str]:
    """Test 3: Hybrid Search"""
    start_time = time.time()
    
    try:
        result = hybrid_search_hotel_intelligence(
            query="conference room military base",
            alpha=0.6,
            topk=5
        )
        duration = time.time() - start_time
        
        if result.get("status") == "success" or "results" in result:
            results_count = len(result.get("results", []))
            return True, duration, f"Found {results_count} results"
        else:
            return False, duration, f"Search failed: {result.get('message', 'Unknown error')}"
    
    except Exception as e:
        duration = time.time() - start_time
        return False, duration, f"Exception: {str(e)}"


def test_proposal_generation() -> Tuple[bool, float, str]:
    """Test 4: Proposal Generation"""
    start_time = time.time()
    
    try:
        result = quick_hotel_analysis(
            notice_id="086008536ec84226ad9de043dc738d06",
            query="conference room military base requirements",
            agency="Department of Defense",
            topk=12
        )
        duration = time.time() - start_time
        
        if result.get("status") == "success":
            proposal = result.get("proposal_draft", "")
            sources = result.get("source_count", 0)
            return True, duration, f"Generated {len(proposal)} chars, {sources} sources"
        else:
            return False, duration, f"Generation failed: {result.get('message', 'Unknown error')}"
    
    except Exception as e:
        duration = time.time() - start_time
        return False, duration, f"Exception: {str(e)}"


def test_hotel_intelligence_bridge() -> Tuple[bool, float, str]:
    """Test 5: Hotel Intelligence Bridge"""
    start_time = time.time()
    
    try:
        result = quick_hotel_analysis(
            notice_id="086008536ec84226ad9de043dc738d06",
            query="military base accommodations hotel services",
            agency="Department of Defense",
            topk=15
        )
        duration = time.time() - start_time
        
        if result.get("status") == "success":
            sources = result.get("source_count", 0)
            return True, duration, f"Bridge working, {sources} sources"
        else:
            return False, duration, f"Bridge failed: {result.get('message', 'Unknown error')}"
    
    except Exception as e:
        duration = time.time() - start_time
        return False, duration, f"Exception: {str(e)}"


def test_enhanced_sow_workflow() -> Tuple[bool, float, str]:
    """Test 6: Enhanced SOW Workflow"""
    start_time = time.time()
    
    try:
        result = get_enhanced_sow_workflow(
            notice_id="086008536ec84226ad9de043dc738d06",
            query="military base hotel requirements and compliance",
            agency="Department of Defense"
        )
        duration = time.time() - start_time
        
        if result.get("status") == "success" and result.get("workflow_completed"):
            confidence = result.get("confidence", 0.0)
            return True, duration, f"Workflow completed, confidence: {confidence:.2f}"
        else:
            return False, duration, f"Workflow failed: {result.get('message', 'Unknown error')}"
    
    except Exception as e:
        duration = time.time() - start_time
        return False, duration, f"Exception: {str(e)}"


def test_end_to_end_integration() -> Tuple[bool, float, str]:
    """Test 7: End-to-End Integration"""
    start_time = time.time()
    
    try:
        # Tam entegrasyon testi
        result = quick_hotel_analysis(
            notice_id="086008536ec84226ad9de043dc738d06",
            query="conference room military base requirements",
            agency="Department of Defense",
            topk=15
        )
        duration = time.time() - start_time
        
        if result.get("status") == "success":
            proposal = result.get("proposal_draft", "")
            sources = result.get("source_count", 0)
            
            # Kalite değerlendirmesi (basit)
            quality_score = min(5, (sources / 3) + min(1, len(proposal) / 500))
            
            return True, duration, (
                f"Quality: {quality_score:.0f}/5, "
                f"Sources: {sources}, "
                f"Length: {len(proposal)}"
            )
        else:
            return False, duration, f"Integration failed: {result.get('message', 'Unknown error')}"
    
    except Exception as e:
        duration = time.time() - start_time
        return False, duration, f"Exception: {str(e)}"


def run_test_suite() -> Dict[str, Any]:
    """Tüm testleri çalıştır ve sonuçları topla"""
    
    print_header("🧪 Hotel Intelligence Integration Test Suite")
    
    tests = [
        ("ZgrProp Connectivity", test_zgrprop_connectivity),
        ("Health Endpoint", test_health_endpoint),
        ("Hybrid Search", test_hybrid_search),
        ("Proposal Generation", test_proposal_generation),
        ("Hotel Intelligence Bridge", test_hotel_intelligence_bridge),
        ("Enhanced SOW Workflow", test_enhanced_sow_workflow),
        ("End-to-End Integration", test_end_to_end_integration),
    ]
    
    results = []
    total_start = time.time()
    
    for test_name, test_func in tests:
        passed, duration, details = test_func()
        results.append({
            "name": test_name,
            "passed": passed,
            "duration": duration,
            "details": details
        })
        print_test_result(test_name, passed, duration, details)
    
    total_duration = time.time() - total_start
    
    # Özet
    passed_count = sum(1 for r in results if r["passed"])
    total_count = len(results)
    success_rate = (passed_count / total_count * 100) if total_count > 0 else 0
    
    print_header("📈 TEST RESULTS SUMMARY")
    print(f"Total Tests: {total_count}")
    print(f"{Colors.GREEN}{Colors.EMOJI_PASS} Passed: {passed_count}{Colors.END}")
    print(f"{Colors.RED}{Colors.EMOJI_FAIL} Failed: {total_count - passed_count}{Colors.END}")
    print(f"{Colors.YELLOW}{Colors.EMOJI_WARN} Warnings: 0{Colors.END}")
    print(f"\n{Colors.BOLD}🏆 Success Rate: {success_rate:.1f}%{Colors.END}")
    
    if success_rate == 100.0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 INTEGRATION TEST SUITE: PASSED{Colors.END}")
        print(f"{Colors.GREEN}{Colors.BOLD}🎉 ZgrProp ↔ ZgrSam Hotel Intelligence Entegrasyonu Test Edildi!{Colors.END}")
    
    return {
        "timestamp": datetime.now().isoformat(),
        "total_tests": total_count,
        "passed": passed_count,
        "failed": total_count - passed_count,
        "success_rate": success_rate,
        "total_duration": total_duration,
        "results": results
    }


if __name__ == "__main__":
    try:
        results = run_test_suite()
        
        # JSON olarak kaydet
        output_file = f"hotel_intelligence_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📊 Test sonuçları kaydedildi: {output_file}")
        
        # Exit code
        sys.exit(0 if results["success_rate"] == 100.0 else 1)
    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test durduruldu (Ctrl+C){Colors.END}")
        sys.exit(130)
    
    except Exception as e:
        print(f"\n{Colors.RED}{Colors.EMOJI_FAIL} Test suite hatası: {str(e)}{Colors.END}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

