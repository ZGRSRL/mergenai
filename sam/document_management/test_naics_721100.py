#!/usr/bin/env python3
"""
Test NAICS 721100 (Traveler Accommodation) opportunities fetching
"""

from sam_document_access_v2 import fetch_opportunities
from autogen_analysis_center import analyze_opportunity_comprehensive, batch_analyze_opportunities

def test_naics_721100():
    """Test fetching and analyzing NAICS 721100 opportunities"""
    print("🏨 Testing NAICS 721100 (Traveler Accommodation) Opportunities")
    print("=" * 70)
    
    # Fetch NAICS 721100 opportunities
    print("📡 Fetching NAICS 721100 opportunities...")
    result = fetch_opportunities(
        keywords=None,  # Boş bırakabiliriz
        naics_codes=["721100"],
        days_back=30,   # Son 30 gün
        limit=50        # Maksimum 50 kayıt
    )
    
    if result and result.get('success'):
        opportunities = result.get('opportunities', [])
        count = result.get('count', 0)
        
        print(f"✅ Successfully fetched {count} NAICS 721100 opportunities")
        
        if opportunities:
            print(f"\n📋 Sample Opportunities:")
            for i, opp in enumerate(opportunities[:5], 1):  # İlk 5 tanesini göster
                title = opp.get('title', 'N/A')
                naics = opp.get('naicsCode', 'N/A')
                org = opp.get('fullParentPathName', 'N/A')
                posted = opp.get('postedDate', 'N/A')
                
                print(f"   {i}. {title}")
                print(f"      NAICS: {naics}")
                print(f"      Organization: {org}")
                print(f"      Posted: {posted}")
                print()
            
            # İlk fırsatı analiz et
            if opportunities:
                first_opp = opportunities[0]
                opp_id = first_opp.get('opportunityId', first_opp.get('id'))
                
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
            
            # Batch analiz için ilk 3 fırsatı seç
            if len(opportunities) >= 3:
                print(f"\n🔄 Running batch analysis on first 3 opportunities...")
                opp_ids = []
                for opp in opportunities[:3]:
                    opp_id = opp.get('opportunityId', opp.get('id'))
                    if opp_id:
                        opp_ids.append(opp_id)
                
                if opp_ids:
                    batch_result = batch_analyze_opportunities(opp_ids, max_concurrent=2)
                    
                    print(f"📈 Batch Analysis Results:")
                    print(f"   Total: {batch_result.get('total_opportunities', 0)}")
                    print(f"   Successful: {batch_result.get('successful', 0)}")
                    print(f"   Failed: {batch_result.get('failed', 0)}")
                    
                    # Başarılı analizlerin özetini göster
                    results = batch_result.get('results', [])
                    successful_results = [r for r in results if r.get('status') == 'completed']
                    
                    if successful_results:
                        print(f"\n✅ Successful Analyses:")
                        for result in successful_results:
                            opp_id = result.get('opportunity_id', 'N/A')
                            confidence = result.get('confidence_score', 0.0)
                            priority = result.get('priority_score', 0)
                            print(f"   - {opp_id}: Confidence {confidence:.2f}, Priority {priority}")
        
        else:
            print("⚠️ No opportunities found for NAICS 721100")
    
    else:
        print("❌ Failed to fetch opportunities")
        if result:
            print(f"   Error: {result.get('error', 'Unknown error')}")

def test_streamlit_interface():
    """Test instructions for Streamlit interface"""
    print(f"\n🖥️ Streamlit Interface Instructions:")
    print("=" * 50)
    print("1. Open Streamlit app: http://localhost:8501")
    print("2. Navigate to 'SAM API v2 Access' page")
    print("3. In 'NAICS Codes' field, enter: 721100")
    print("4. Set 'Days Back' to desired range (e.g., 30)")
    print("5. Set 'Limit' to desired number (e.g., 50)")
    print("6. Click 'Fetch Opportunities' button")
    print("7. Review the fetched opportunities")
    print("8. Use 'Opportunity Analysis' page to analyze specific opportunities")

if __name__ == "__main__":
    test_naics_721100()
    test_streamlit_interface()
    
    print(f"\n🎉 NAICS 721100 testing completed!")
    print("=" * 70)
