#!/usr/bin/env python3
"""
Test SAM Opportunity Analyzer Agent with real data
"""

from autogen_analysis_center import analyze_opportunity_comprehensive, get_analysis_statistics

def test_real_opportunity():
    """Test with real opportunity data"""
    print("🧪 Testing SAM Opportunity Analyzer Agent with Real Data")
    print("=" * 60)
    
    # Test with real opportunity ID
    opportunity_id = "DEMO-001"
    print(f"📋 Testing opportunity: {opportunity_id}")
    
    # Run analysis
    result = analyze_opportunity_comprehensive(opportunity_id)
    
    # Display results
    print(f"\n📊 Analysis Results:")
    print(f"   Status: {result.get('status', 'unknown')}")
    print(f"   Confidence Score: {result.get('confidence_score', 0.0):.2f}")
    print(f"   Risk Level: {result.get('risk_level', 'unknown')}")
    print(f"   Priority Score: {result.get('priority_score', 0)}")
    
    recommendations = result.get('recommendations', [])
    if recommendations:
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    
    # Test statistics
    print(f"\n📈 System Statistics:")
    stats = get_analysis_statistics()
    analyzer_stats = stats.get('analyzer_agent', {})
    print(f"   Total Opportunities: {analyzer_stats.get('total_opportunities', 0)}")
    print(f"   Recent Opportunities: {analyzer_stats.get('recent_opportunities_count', 0)}")
    print(f"   Cache Size: {analyzer_stats.get('cache_size', 0)}")
    print(f"   Analyzer Status: {analyzer_stats.get('analyzer_status', 'unknown')}")
    
    print(f"\n✅ Test completed successfully!")

if __name__ == "__main__":
    test_real_opportunity()
