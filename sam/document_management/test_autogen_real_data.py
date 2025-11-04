#!/usr/bin/env python3
"""
Test AutoGen flow with real database opportunities
"""

from autogen_analysis_center import analyze_opportunity_comprehensive, batch_analyze_opportunities
from database_manager import DatabaseUtils
import psycopg2

def test_autogen_with_real_data():
    """Test AutoGen flow with real database opportunities"""
    print("🤖 Testing AutoGen Flow with Real Database Opportunities")
    print("=" * 70)
    
    # Get real opportunities from database
    print("📡 Step 1: Getting real opportunities from database...")
    
    try:
        conn = psycopg2.connect(host='localhost', database='ZGR_AI', user='postgres', password='sarlio41')
        cur = conn.cursor()
        
        # Get opportunities with NAICS codes
        cur.execute("""
            SELECT opportunity_id, title, naics_code, organization_type, posted_date 
            FROM opportunities 
            WHERE naics_code IS NOT NULL AND naics_code != '' 
            ORDER BY posted_date DESC 
            LIMIT 5
        """)
        
        opportunities = cur.fetchall()
        conn.close()
        
        print(f"✅ Found {len(opportunities)} real opportunities with NAICS codes")
        
        if opportunities:
            print(f"\n📋 Real Opportunities:")
            for i, (opp_id, title, naics, org, posted) in enumerate(opportunities, 1):
                print(f"   {i}. {opp_id}")
                print(f"      Title: {title}")
                print(f"      NAICS: {naics}")
                print(f"      Organization: {org}")
                print(f"      Posted: {posted}")
                print()
            
            # Step 2: AutoGen Analysis for first opportunity
            first_opp_id = opportunities[0][0]
            print(f"🤖 Step 2: AutoGen Analysis for {first_opp_id}")
            print("-" * 50)
            
            analysis_result = analyze_opportunity_comprehensive(first_opp_id)
            
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
            
            # Show detailed analysis data
            analysis_data = analysis_result.get('analysis_data', {})
            if analysis_data:
                print(f"\n📈 Detailed Analysis:")
                
                # AI Analysis
                ai_analysis = analysis_data.get('ai_analysis', {})
                if ai_analysis:
                    print(f"   AI Analysis Score: {ai_analysis.get('opportunity_score', 'N/A')}")
                    print(f"   Risk Level: {ai_analysis.get('risk_level', 'N/A')}")
                
                # Summary
                summary = analysis_data.get('summary', {})
                if summary:
                    key_info = summary.get('key_info', {})
                    print(f"   Job Type: {key_info.get('job_type', 'N/A')}")
                    print(f"   Duration: {key_info.get('duration', 'N/A')}")
                
                # Document Analysis
                doc_analysis = analysis_data.get('document_analysis', {})
                if doc_analysis:
                    docs = doc_analysis.get('documents', [])
                    print(f"   Documents Processed: {len(docs)}")
            
            # Show coordination results
            coordination = analysis_result.get('coordination_results', {})
            if coordination:
                print(f"\n🤝 Agent Coordination:")
                for agent, info in coordination.items():
                    print(f"   - {agent}: {info.get('status', 'unknown')}")
            
            # Step 3: Batch analysis for multiple opportunities
            if len(opportunities) > 1:
                print(f"\n🔄 Step 3: Batch Analysis")
                print("-" * 50)
                
                opp_ids = [opp[0] for opp in opportunities[:3]]  # First 3 opportunities
                
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
                
                # Show analyzer statistics
                analyzer_stats = batch_result.get('analyzer_statistics', {})
                if analyzer_stats:
                    print(f"\n📊 Analyzer Statistics:")
                    print(f"   Total Opportunities: {analyzer_stats.get('total_opportunities', 0)}")
                    print(f"   Cache Size: {analyzer_stats.get('cache_size', 0)}")
                    print(f"   Analyzer Status: {analyzer_stats.get('analyzer_status', 'unknown')}")
        
        else:
            print("❌ No opportunities found in database")
    
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

def test_naics_specific_analysis():
    """Test analysis for specific NAICS codes"""
    print(f"\n🏨 Step 4: NAICS-Specific Analysis")
    print("-" * 50)
    
    try:
        conn = psycopg2.connect(host='localhost', database='ZGR_AI', user='postgres', password='sarlio41')
        cur = conn.cursor()
        
        # Get NAICS 721110 opportunities (Hotels and Motels)
        cur.execute("""
            SELECT opportunity_id, title, naics_code 
            FROM opportunities 
            WHERE naics_code = '721110'
            ORDER BY posted_date DESC
        """)
        
        naics_721110_opps = cur.fetchall()
        
        print(f"🏨 NAICS 721110 (Hotels and Motels): {len(naics_721110_opps)} opportunities")
        
        if naics_721110_opps:
            print(f"\n📋 NAICS 721110 Opportunities:")
            for i, (opp_id, title, naics) in enumerate(naics_721110_opps, 1):
                print(f"   {i}. {opp_id}: {title}")
            
            # Analyze first NAICS 721110 opportunity
            first_opp_id = naics_721110_opps[0][0]
            print(f"\n🔍 Analyzing NAICS 721110 opportunity: {first_opp_id}")
            
            analysis_result = analyze_opportunity_comprehensive(first_opp_id)
            
            print(f"📊 NAICS 721110 Analysis Results:")
            print(f"   Status: {analysis_result.get('status', 'unknown')}")
            print(f"   Confidence: {analysis_result.get('confidence_score', 0.0):.2f}")
            print(f"   Risk Level: {analysis_result.get('risk_level', 'unknown')}")
            print(f"   Priority: {analysis_result.get('priority_score', 0)}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ NAICS-specific analysis error: {e}")

if __name__ == "__main__":
    test_autogen_with_real_data()
    test_naics_specific_analysis()
    
    print(f"\n🎉 AutoGen flow with real data testing completed!")
    print("=" * 70)
