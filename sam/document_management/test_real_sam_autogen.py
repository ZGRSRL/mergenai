#!/usr/bin/env python3
"""
Test real SAM.gov data with AutoGen flow
"""

from sam_document_access_v2 import fetch_opportunities
from autogen_analysis_center import analyze_opportunity_comprehensive, batch_analyze_opportunities
from database_manager import DatabaseUtils

def test_real_sam_data():
    """Test with real SAM.gov data"""
    print("🌐 Testing Real SAM.gov Data with AutoGen Flow")
    print("=" * 60)
    
    # Step 1: Fetch real SAM.gov opportunities
    print("📡 Step 1: Fetching real SAM.gov opportunities...")
    try:
        result = fetch_opportunities(
            naics_codes=['721100'],  # Traveler Accommodation
            days_back=7,
            limit=10
        )
        
        print(f"✅ Fetch Result:")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Count: {result.get('count', 0)}")
        print(f"   Opportunities: {len(result.get('opportunities', []))}")
        
        if result.get('success') and result.get('opportunities'):
            opportunities = result.get('opportunities', [])
            print(f"\n📋 Sample Real Opportunities:")
            for i, opp in enumerate(opportunities[:3], 1):
                opp_id = opp.get('opportunityId', 'N/A')
                title = opp.get('title', 'N/A')
                naics = opp.get('naicsCode', 'N/A')
                org = opp.get('fullParentPathName', 'N/A')
                posted = opp.get('postedDate', 'N/A')
                
                print(f"   {i}. {opp_id}")
                print(f"      Title: {title}")
                print(f"      NAICS: {naics}")
                print(f"      Organization: {org}")
                print(f"      Posted: {posted}")
                print()
            
            # Step 2: Analyze first opportunity with AutoGen
            first_opp = opportunities[0]
            opp_id = first_opp.get('opportunityId')
            
            if opp_id:
                print(f"🤖 Step 2: AutoGen Analysis for {opp_id}")
                print("-" * 40)
                
                analysis_result = analyze_opportunity_comprehensive(opp_id)
                
                print(f"📊 Analysis Results:")
                print(f"   Status: {analysis_result.get('status', 'unknown')}")
                print(f"   Confidence: {analysis_result.get('confidence_score', 0.0):.2f}")
                print(f"   Risk Level: {analysis_result.get('risk_level', 'unknown')}")
                print(f"   Priority: {analysis_result.get('priority_score', 0)}")
                
                recommendations = analysis_result.get('recommendations', [])
                if recommendations:
                    print(f"\n💡 Recommendations:")
                    for i, rec in enumerate(recommendations, 1):
                        print(f"   {i}. {rec}")
                
                # Show coordination results
                coordination = analysis_result.get('coordination_results', {})
                if coordination:
                    print(f"\n🤝 Agent Coordination:")
                    for agent, info in coordination.items():
                        print(f"   - {agent}: {info.get('status', 'unknown')}")
                
                # Step 3: Batch analysis if multiple opportunities
                if len(opportunities) > 1:
                    print(f"\n🔄 Step 3: Batch Analysis")
                    print("-" * 40)
                    
                    opp_ids = [opp.get('opportunityId') for opp in opportunities[:3] if opp.get('opportunityId')]
                    
                    if opp_ids:
                        batch_result = batch_analyze_opportunities(opp_ids, max_concurrent=2)
                        
                        print(f"📈 Batch Analysis Summary:")
                        print(f"   Total: {batch_result.get('total_opportunities', 0)}")
                        print(f"   Successful: {batch_result.get('successful', 0)}")
                        print(f"   Failed: {batch_result.get('failed', 0)}")
                        
                        # Show successful analyses
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
        
        else:
            print("❌ No opportunities fetched or fetch failed")
            if result:
                print(f"   Error: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

def check_database_status():
    """Check database status after fetching"""
    print(f"\n🗄️ Database Status Check:")
    print("-" * 40)
    
    try:
        # Check total opportunities
        total_count = DatabaseUtils.get_opportunity_count()
        print(f"   Total Opportunities: {total_count}")
        
        # Check recent opportunities
        recent_opps = DatabaseUtils.get_recent_opportunities(limit=5)
        print(f"   Recent Opportunities: {len(recent_opps)}")
        
        if recent_opps:
            print(f"\n📋 Recent Opportunities:")
            for i, opp in enumerate(recent_opps, 1):
                opp_id = opp.get('opportunity_id', 'N/A')
                title = opp.get('title', 'N/A')
                naics = opp.get('naics_code', 'N/A')
                print(f"   {i}. {opp_id}: {title} (NAICS: {naics})")
        
        # Check NAICS 721100 specifically
        naics_721100_opps = DatabaseUtils.search_opportunities("", limit=100)
        naics_721100_count = len([opp for opp in naics_721100_opps if opp.get('naics_code') == '721100'])
        print(f"\n🏨 NAICS 721100 Opportunities: {naics_721100_count}")
        
    except Exception as e:
        print(f"❌ Database check error: {e}")

if __name__ == "__main__":
    test_real_sam_data()
    check_database_status()
    
    print(f"\n🎉 Real SAM.gov + AutoGen testing completed!")
    print("=" * 60)
