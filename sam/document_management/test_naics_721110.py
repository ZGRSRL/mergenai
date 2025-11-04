#!/usr/bin/env python3
"""
Test NAICS 721110 (Hotels and Motels) opportunities - similar to 721100
"""

from autogen_analysis_center import analyze_opportunity_comprehensive, batch_analyze_opportunities
from database_manager import DatabaseUtils

def test_naics_721110():
    """Test analyzing NAICS 721110 opportunities (Hotels and Motels)"""
    print("🏨 Testing NAICS 721110 (Hotels and Motels) Opportunities")
    print("=" * 70)
    
    # Get NAICS 721110 opportunities from database
    print("📡 Fetching NAICS 721110 opportunities from database...")
    opportunities = DatabaseUtils.search_opportunities("", limit=50)  # Get all opportunities
    
    # Filter for NAICS 721110
    naics_721110_opps = [opp for opp in opportunities if opp.get('naics_code') == '721110']
    
    print(f"✅ Found {len(naics_721110_opps)} NAICS 721110 opportunities in database")
    
    if naics_721110_opps:
        print(f"\n📋 Available NAICS 721110 Opportunities:")
        for i, opp in enumerate(naics_721110_opps, 1):
            opp_id = opp.get('opportunity_id', 'N/A')
            title = opp.get('title', 'N/A')
            org = opp.get('agency', 'N/A')
            posted = opp.get('posted_date', 'N/A')
            
            print(f"   {i}. {opp_id}: {title}")
            print(f"      Organization: {org}")
            print(f"      Posted: {posted}")
            print()
        
        # Analyze first opportunity
        first_opp = naics_721110_opps[0]
        opp_id = first_opp.get('opportunity_id')
        
        if opp_id:
            print(f"🔍 Analyzing first opportunity: {opp_id}")
            analysis_result = analyze_opportunity_comprehensive(opp_id)
            
            print(f"\n📊 Analysis Results:")
            print(f"   Status: {analysis_result.get('status', 'unknown')}")
            print(f"   Confidence: {analysis_result.get('confidence_score', 0.0):.2f}")
            print(f"   Risk Level: {analysis_result.get('risk_level', 'unknown')}")
            print(f"   Priority: {analysis_result.get('priority_score', 0)}")
            
            recommendations = analysis_result.get('recommendations', [])
            if recommendations:
                print(f"\n💡 Recommendations:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"   {i}. {rec}")
            
            # Show analysis data details
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
        
        # Batch analyze all NAICS 721110 opportunities
        if len(naics_721110_opps) > 1:
            print(f"\n🔄 Running batch analysis on all NAICS 721110 opportunities...")
            opp_ids = [opp.get('opportunity_id') for opp in naics_721110_opps if opp.get('opportunity_id')]
            
            if opp_ids:
                batch_result = batch_analyze_opportunities(opp_ids, max_concurrent=3)
                
                print(f"📈 Batch Analysis Results:")
                print(f"   Total: {batch_result.get('total_opportunities', 0)}")
                print(f"   Successful: {batch_result.get('successful', 0)}")
                print(f"   Failed: {batch_result.get('failed', 0)}")
                
                # Show successful analyses summary
                results = batch_result.get('results', [])
                successful_results = [r for r in results if r.get('status') == 'completed']
                
                if successful_results:
                    print(f"\n✅ Successful Analyses Summary:")
                    for result in successful_results:
                        opp_id = result.get('opportunity_id', 'N/A')
                        confidence = result.get('confidence_score', 0.0)
                        priority = result.get('priority_score', 0)
                        risk = result.get('risk_level', 'unknown')
                        print(f"   - {opp_id}: Confidence {confidence:.2f}, Priority {priority}, Risk {risk}")
    
    else:
        print("⚠️ No NAICS 721110 opportunities found in database")

def show_naics_comparison():
    """Show comparison between NAICS 721100 and 721110"""
    print(f"\n📊 NAICS Code Comparison:")
    print("=" * 50)
    print("NAICS 721100: Traveler Accommodation")
    print("NAICS 721110: Hotels (except Casino Hotels) and Motels")
    print()
    print("Both codes are related to accommodation services:")
    print("- 721100 is broader (includes all traveler accommodation)")
    print("- 721110 is more specific (hotels and motels only)")
    print()
    print("For government contracts, both codes are commonly used")
    print("for hotel and accommodation service procurements.")

def show_streamlit_instructions():
    """Show instructions for using Streamlit interface"""
    print(f"\n🖥️ Streamlit Interface Instructions:")
    print("=" * 50)
    print("1. Open Streamlit app: http://localhost:8501")
    print("2. Navigate to 'SAM API v2 Access' page")
    print("3. In 'NAICS Codes' field, enter: 721110")
    print("   (or 721100 if you have valid SAM API key)")
    print("4. Set 'Days Back' to desired range (e.g., 30)")
    print("5. Set 'Limit' to desired number (e.g., 50)")
    print("6. Click 'Fetch Opportunities' button")
    print("7. Review the fetched opportunities")
    print("8. Use 'Opportunity Analysis' page to analyze specific opportunities")
    print()
    print("💡 Note: Without valid SAM API key, you can analyze")
    print("   existing opportunities in the database using")
    print("   the 'Opportunity Analysis' page.")

if __name__ == "__main__":
    test_naics_721110()
    show_naics_comparison()
    show_streamlit_instructions()
    
    print(f"\n🎉 NAICS 721110 testing completed!")
    print("=" * 70)
