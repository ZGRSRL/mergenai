#!/usr/bin/env python3
"""
UI Validation Test Script
Test the improved agent system
"""

from agent_log_manager import get_recent_actions, get_agent_stats, get_notice_processing_log
from sow_autogen_workflow import run_workflow_for_notice
import json

def test_ui_validation():
    """Test UI validation checklist"""
    print("=== UI VALIDATION TEST ===")
    print()
    
    # Test 1: Recent Actions
    print("1. Recent Actions Test:")
    recent_actions = get_recent_actions(5)
    print(f"   Found {len(recent_actions)} recent actions")
    for i, action in enumerate(recent_actions, 1):
        print(f"   {i}. {action['timestamp']} - {action['agent_name']} - {action['action']} - {action['status']}")
    print()
    
    # Test 2: Agent Stats
    print("2. Agent Statistics Test:")
    stats = get_agent_stats()
    print(f"   Total Actions: {stats['total_actions']}")
    print(f"   Success Rate: {stats['success_rate']}%")
    print(f"   Avg Processing Time: {stats['avg_processing_time']}s")
    print(f"   Error Count: {stats['error_count']}")
    print()
    
    # Test 3: Notice Processing Log
    print("3. Notice Processing Log Test:")
    notice_log = get_notice_processing_log("TEST001")
    print(f"   Found {len(notice_log)} actions for TEST001")
    for action in notice_log:
        print(f"   - {action['agent_name']}: {action['action']} ({action['status']})")
    print()
    
    # Test 4: SOW Workflow Test
    print("4. SOW Workflow Test:")
    try:
        result = run_workflow_for_notice("70LART26QPFB00001")
        print(f"   Status: {result['status']}")
        print(f"   Analysis ID: {result['analysis_id']}")
        print(f"   Files Processed: {result['files_processed']}")
        print(f"   Files Found: {result['files_found']}")
        print(f"   Errors: {len(result['errors'])}")
        if result['errors']:
            for error in result['errors']:
                print(f"     - {error}")
    except Exception as e:
        print(f"   Error: {e}")
    print()
    
    # Test 5: Agent Performance by Type
    print("5. Agent Performance by Type:")
    agents = ["DocumentProcessor", "SOWParser", "Validator", "DBWriter"]
    for agent in agents:
        agent_stats = get_agent_stats(agent_name=agent)
        if agent_stats['total_actions'] > 0:
            print(f"   {agent}: {agent_stats['success_rate']}% success, {agent_stats['avg_processing_time']}s avg")
        else:
            print(f"   {agent}: No actions recorded")
    print()
    
    print("=== UI VALIDATION TEST COMPLETED ===")

if __name__ == "__main__":
    test_ui_validation()

