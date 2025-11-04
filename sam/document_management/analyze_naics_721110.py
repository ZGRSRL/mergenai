#!/usr/bin/env python3
"""
Analyze NAICS 721110 opportunities directly
"""

from autogen_analysis_center import analyze_opportunity_comprehensive, batch_analyze_opportunities

def analyze_naics_721110_opportunities():
    """Analyze all NAICS 721110 opportunities"""
    print("🏨 Analyzing NAICS 721110 (Hotels and Motels) Opportunities")
    print("=" * 70)
    
    # Known NAICS 721110 opportunity IDs from database
    opportunity_ids = ['DEMO-001', 'DEMO-002', 'DEMO-003', 'DEMO001']
    
    print(f"📋 Analyzing {len(opportunity_ids)} NAICS 721110 opportunities...")
    
    # Analyze each opportunity individually
    individual_results = []
    for opp_id in opportunity_ids:
        print(f"\n🔍 Analyzing: {opp_id}")
        try:
            result = analyze_opportunity_comprehensive(opp_id)
            individual_results.append(result)
            
            print(f"   Status: {result.get('status', 'unknown')}")
            print(f"   Confidence: {result.get('confidence_score', 0.0):.2f}")
            print(f"   Risk Level: {result.get('risk_level', 'unknown')}")
            print(f"   Priority: {result.get('priority_score', 0)}")
            
            recommendations = result.get('recommendations', [])
            if recommendations:
                print(f"   Recommendations: {len(recommendations)} items")
                for i, rec in enumerate(recommendations[:2], 1):  # Show first 2
                    print(f"     {i}. {rec}")
            
        except Exception as e:
            print(f"   Error: {e}")
    
    # Batch analysis
    print(f"\n🔄 Running batch analysis...")
    try:
        batch_result = batch_analyze_opportunities(opportunity_ids, max_concurrent=2)
        
        print(f"📈 Batch Analysis Summary:")
        print(f"   Total: {batch_result.get('total_opportunities', 0)}")
        print(f"   Successful: {batch_result.get('successful', 0)}")
        print(f"   Failed: {batch_result.get('failed', 0)}")
        
        # Show detailed results
        results = batch_result.get('results', [])
        successful_results = [r for r in results if r.get('status') == 'completed']
        
        if successful_results:
            print(f"\n✅ Successful Analyses:")
            for result in successful_results:
                opp_id = result.get('opportunity_id', 'N/A')
                confidence = result.get('confidence_score', 0.0)
                priority = result.get('priority_score', 0)
                risk = result.get('risk_level', 'unknown')
                print(f"   - {opp_id}: Confidence {confidence:.2f}, Priority {priority}, Risk {risk}")
        
        # Show coordination results
        for result in results:
            opp_id = result.get('opportunity_id', 'N/A')
            coordination = result.get('coordination_results', {})
            if coordination:
                print(f"\n🤝 Agent Coordination for {opp_id}:")
                for agent, info in coordination.items():
                    print(f"   - {agent}: {info.get('status', 'unknown')}")
    
    except Exception as e:
        print(f"   Batch analysis error: {e}")
    
    # Summary statistics
    print(f"\n📊 Analysis Summary:")
    completed_count = sum(1 for r in individual_results if r.get('status') == 'completed')
    avg_confidence = sum(r.get('confidence_score', 0.0) for r in individual_results if r.get('status') == 'completed') / max(completed_count, 1)
    avg_priority = sum(r.get('priority_score', 0) for r in individual_results if r.get('status') == 'completed') / max(completed_count, 1)
    
    print(f"   Completed Analyses: {completed_count}/{len(individual_results)}")
    print(f"   Average Confidence: {avg_confidence:.2f}")
    print(f"   Average Priority: {avg_priority:.1f}")
    
    # Risk level distribution
    risk_levels = {}
    for result in individual_results:
        if result.get('status') == 'completed':
            risk = result.get('risk_level', 'unknown')
            risk_levels[risk] = risk_levels.get(risk, 0) + 1
    
    if risk_levels:
        print(f"   Risk Level Distribution:")
        for risk, count in risk_levels.items():
            print(f"     - {risk}: {count}")

if __name__ == "__main__":
    analyze_naics_721110_opportunities()
    print(f"\n🎉 NAICS 721110 analysis completed!")
    print("=" * 70)
