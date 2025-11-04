#!/usr/bin/env python3
"""
ZgrSam Dashboard - Gelişmiş Analiz ve Ajan Workflow
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import sys
import os

# Add current directory to path
sys.path.append('.')

from streamlit_complete_with_mail import create_database_connection, get_live_sam_opportunities
from autogen_implementation import ZgrSamAutoGenOrchestrator, Document, DocumentType

# Page config
st.set_page_config(
    page_title="ZgrSam Dashboard",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_opportunities():
    """Fırsatları yükle"""
    conn = create_database_connection()
    if not conn:
        st.error("Veritabanı bağlantısı başarısız!")
        return []
    
    opportunities = get_live_sam_opportunities(conn, limit=100)
    conn.close()
    return opportunities

def create_metrics_cards(opportunities):
    """Metrik kartları oluştur"""
    if not opportunities:
        return
    
    # Temel metrikler
    total_opportunities = len(opportunities)
    today = datetime.now().date()
    today_opportunities = len([opp for opp in opportunities if opp.get('posted_date') and opp['posted_date'].date() == today])
    
    # En yaygın organizasyon tipi
    org_types = [opp.get('organization_type', 'Unknown') for opp in opportunities if opp.get('organization_type')]
    most_common_org = max(set(org_types), key=org_types.count) if org_types else 'N/A'
    
    # En yaygın sözleşme tipi
    contract_types = [opp.get('contract_type', 'Unknown') for opp in opportunities if opp.get('contract_type')]
    most_common_contract = max(set(contract_types), key=contract_types.count) if contract_types else 'N/A'
    
    # Metrik kartları
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Toplam Fırsat", total_opportunities)
    
    with col2:
        st.metric("Bugün Eklenen", today_opportunities)
    
    with col3:
        st.metric("En Yaygın Org", most_common_org)
    
    with col4:
        st.metric("En Yaygın Tip", most_common_contract)

def create_organization_chart(opportunities):
    """Organizasyon dağılımı grafiği"""
    if not opportunities:
        return
    
    org_data = {}
    for opp in opportunities:
        org_type = opp.get('organization_type', 'Unknown')
        org_data[org_type] = org_data.get(org_type, 0) + 1
    
    if org_data:
        df_org = pd.DataFrame(list(org_data.items()), columns=['Organization', 'Count'])
        fig_org = px.pie(df_org, values='Count', names='Organization', title='Organizasyon Dağılımı')
        fig_org.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig_org, use_container_width=True)

def create_contract_chart(opportunities):
    """Sözleşme tipi dağılımı grafiği"""
    if not opportunities:
        return
    
    contract_data = {}
    for opp in opportunities:
        contract_type = opp.get('contract_type', 'Unknown')
        contract_data[contract_type] = contract_data.get(contract_type, 0) + 1
    
    if contract_data:
        df_contract = pd.DataFrame(list(contract_data.items()), columns=['Contract Type', 'Count'])
        fig_contract = px.bar(df_contract, x='Contract Type', y='Count', title='Sözleşme Tipleri')
        fig_contract.update_layout(xaxis_tickangle=45)
        st.plotly_chart(fig_contract, use_container_width=True)

def run_agent_workflow(opportunity):
    """Ajan workflow'unu çalıştır"""
    st.subheader(f"🤖 Ajan Workflow: {opportunity['title'][:50]}...")
    
    # Document oluştur
    document = Document(
        id=opportunity['id'],
        type=DocumentType.RFQ,
        title=opportunity['title'],
        content=opportunity['description'],
        metadata={
            'opportunity_id': opportunity['opportunity_id'],
            'posted_date': str(opportunity['posted_date']),
            'naics_code': opportunity['naics_code'],
            'contract_type': opportunity['contract_type'],
            'organization_type': opportunity['organization_type']
        }
    )
    
    orchestrator = ZgrSamAutoGenOrchestrator()
    results = {}
    
        # Agent 1: Document Processor
    st.subheader("🤖 Agent 1: Document Processor")

    original_description = document.content or ""

    # Manuel belge yükleme seçeneği
    col1, col2 = st.columns([2, 1])

    with col1:
        st.info("Ham RFQ belgesini işliyor ve belgeleri indiriyor...")

    with col2:
        uploaded_file = st.file_uploader(
            "Manuel Belge Yükle",
            type=['pdf', 'docx', 'txt', 'xlsx'],
            help="PDF, Word, Excel veya metin dosyası yükleyin"
        )

    progress_bar = st.progress(0)
    status_text = st.empty()

    for i in range(100):
        progress_bar.progress(i + 1)
        if i < 20:
            status_text.text("Belge okunuyor...")
        elif i < 40:
            status_text.text("URL'ler taranıyor...")
        elif i < 70:
            status_text.text("Belgeler indiriliyor...")
        elif i < 90:
            status_text.text("Belgeler analiz ediliyor...")
        else:
            status_text.text("İşlenmiş belge hazırlanıyor...")
        time.sleep(0.02)

    manual_processing_success = False
    doc_result = {}

    if uploaded_file is not None:
        st.info(f"✅ Manuel belge yüklendi: {uploaded_file.name}")

        import tempfile

        file_bytes = uploaded_file.getvalue()
        tmp_file_path = ""
        downloader = None

        try:
            suffix = os.path.splitext(uploaded_file.name)[1] or ""
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(file_bytes)
                tmp_file_path = tmp_file.name

            from document_downloader import DocumentDownloader
            downloader = DocumentDownloader()

            manual_analysis = downloader.download_document(f"file://{tmp_file_path}", f"manual_{document.id}")

            if manual_analysis:
                manual_processing_success = True
                analysis_data = manual_analysis.get('analysis', {}) or {}
                manual_text = analysis_data.get('text_content', "") or ""
                combined_content = manual_text.strip()

                if original_description:
                    combined_content = (combined_content + "

--- ORIJINAL FIRSAT AÇIKLAMASI ---
" + original_description).strip()

                key_dates = orchestrator.document_processor._extract_dates(combined_content)
                requirements = orchestrator.document_processor._extract_requirements(combined_content)
                financial_info = orchestrator.document_processor._extract_financial_info(combined_content)

                document.metadata.update({
                    'manual_upload': True,
                    'manual_filename': uploaded_file.name
                })

                doc_result = {
                    'document_id': document.id,
                    'extracted_content': combined_content[:1000],
                    'enhanced_content': combined_content,
                    'key_dates': key_dates,
                    'requirements': requirements,
                    'financial_info': financial_info,
                    'downloaded_documents': [{
                        'url': 'manual-upload',
                        'filename': uploaded_file.name,
                        'content_type': uploaded_file.type or manual_analysis.get('content_type'),
                        'size': len(file_bytes),
                        'analysis': analysis_data,
                        'source': 'Manuel Yükleme'
                    }],
                    'metadata': document.metadata,
                    'processing_stats': {
                        'original_length': len(original_description),
                        'enhanced_length': len(combined_content),
                        'documents_downloaded': 1,
                        'total_words': len(combined_content.split())
                    }
                }

                document.content = combined_content
                st.success(f"✅ Manuel belge başarıyla işlendi: {uploaded_file.name}")
            else:
                st.error("❌ Manuel belge işlenemedi")
        except Exception as e:
            st.error(f"❌ Manuel belge işleme hatası: {e}")
        finally:
            if downloader:
                try:
                    downloader.cleanup()
                except Exception:
                    pass
            if tmp_file_path:
                try:
                    os.unlink(tmp_file_path)
                except Exception:
                    pass

        if not manual_processing_success:
            st.info("Manuel belge kullanılamadı, otomatik indirme devreye alınıyor...")
            doc_result = orchestrator.document_processor.process_document(document)
    else:
        doc_result = orchestrator.document_processor.process_document(document)
        st.success("✅ Belge başarıyla işlendi!")

    if doc_result.get('enhanced_content'):
        document.content = doc_result['enhanced_content']

    results['document'] = doc_result

    
    # Show document processing results
    if 'downloaded_documents' in doc_result and doc_result['downloaded_documents']:
        st.info(f"📥 {len(doc_result['downloaded_documents'])} belge indirildi ve analiz edildi")
        
        # Show downloaded documents
        for i, doc in enumerate(doc_result['downloaded_documents']):
            with st.expander(f"📄 İndirilen Belge {i+1}: {doc['filename']}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**URL:** {doc['url']}")
                    st.write(f"**Boyut:** {doc['size']:,} bytes")
                    st.write(f"**Tip:** {doc['content_type']}")
                with col2:
                    st.write(f"**Kelime Sayısı:** {doc['analysis']['word_count']:,}")
                    st.write(f"**Sayfa Sayısı:** {doc['analysis']['pages']}")
                    st.write(f"**Tablo Sayısı:** {doc['analysis']['tables']}")
                
                if doc['analysis']['text_content']:
                    st.write("**İçerik Önizleme:**")
                    st.text(doc['analysis']['text_content'][:1000] + "...")
    else:
        st.warning("⚠️ Hiç belge indirilemedi (içerikte URL bulunamadı)")
    
    # Show processing stats
    if 'processing_stats' in doc_result:
        stats = doc_result['processing_stats']
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Orijinal Uzunluk", f"{stats['original_length']:,} karakter")
        with col2:
            st.metric("Geliştirilmiş Uzunluk", f"{stats['enhanced_length']:,} karakter")
        with col3:
            st.metric("İndirilen Belgeler", stats['documents_downloaded'])
        with col4:
            st.metric("Toplam Kelime", f"{stats['total_words']:,}")
    
    # Show extracted information
    if 'key_dates' in doc_result and doc_result['key_dates']:
        st.write("**📅 Çıkarılan Tarihler:**")
        st.write(", ".join(doc_result['key_dates'][:5]))  # Show first 5 dates
    
    if 'financial_info' in doc_result and doc_result['financial_info'].get('amounts'):
        st.write("**💰 Çıkarılan Finansal Bilgiler:**")
        st.write(", ".join(doc_result['financial_info']['amounts'][:5]))  # Show first 5 amounts
    
    # Agent 2: Requirements Extractor
    st.subheader("🔍 Agent 2: Requirements Extractor")
    st.info("Gereksinimleri çıkarıyor...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(100):
        progress_bar.progress(i + 1)
        if i < 50:
            status_text.text("Gereksinimler taranıyor...")
        else:
            status_text.text("Gereksinimler kategorize ediliyor...")
        time.sleep(0.02)
    
    req_result = orchestrator.requirements_extractor.extract_requirements(document)
    results['requirements'] = req_result
    st.success("✅ Gereksinimler çıkarıldı!")
    
    # Show requirements
    if isinstance(req_result, dict) and req_result.get('requirements'):
        req_data = []
        for i, req in enumerate(req_result['requirements'][:10]):  # Show first 10
            if isinstance(req, dict):
                req_data.append({
                    'ID': i + 1,
                    'Gereksinim': req.get('text', 'N/A'),
                    'Kategori': req.get('category', 'N/A'),
                    'Öncelik': req.get('priority', 'N/A')
                })
            else:
                req_data.append({
                    'ID': i + 1,
                    'Gereksinim': str(req),
                    'Kategori': 'N/A',
                    'Öncelik': 'N/A'
                })
        
        if req_data:
            df_req = pd.DataFrame(req_data)
            st.dataframe(df_req, use_container_width=True)
    elif isinstance(req_result, list):
        st.write("**Çıkarılan Gereksinimler:**")
        for i, req in enumerate(req_result[:10], 1):
            st.write(f"{i}. {req}")
    else:
        st.write("**Gereksinimler:** N/A")
    
    # Agent 3: Compliance Analyst
    st.subheader("⚖️ Agent 3: Compliance Analyst")
    st.info("FAR uyumluluğunu analiz ediyor...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(100):
        progress_bar.progress(i + 1)
        if i < 50:
            status_text.text("FAR gereksinimleri kontrol ediliyor...")
        else:
            status_text.text("Uyumluluk skoru hesaplanıyor...")
        time.sleep(0.02)
    
    facility_data = {
        'location': opportunity.get('location', 'washington_dc'),
        'capabilities': ['meeting_rooms', 'catering', 'av_equipment'],
        'certifications': ['government_approved']
    }
    comp_result = orchestrator.compliance_analyst.analyze_compliance(req_result if isinstance(req_result, list) else req_result.get('requirements', []), facility_data)
    results['compliance'] = comp_result
    st.success("✅ Uyumluluk analizi tamamlandı!")
    
    # Show compliance matrix
    if isinstance(comp_result, dict) and comp_result.get('compliance_matrix'):
        compliance_matrix = comp_result['compliance_matrix']
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Karşılanan", compliance_matrix.get('met_requirements', 0))
        with col2:
            st.metric("Toplam", compliance_matrix.get('total_requirements', 0))
        with col3:
            st.metric("Risk", compliance_matrix.get('overall_risk', 'N/A'))
        with col4:
            compliance_rate = (compliance_matrix.get('met_requirements', 0) / max(compliance_matrix.get('total_requirements', 1), 1)) * 100
            st.metric("Oran", f"{compliance_rate:.1f}%")
    else:
        st.write("**Compliance Matrix:** N/A")
    
    # Agent 4: Pricing Specialist
    st.subheader("💰 Agent 4: Pricing Specialist")
    st.info("Fiyatlandırma hesaplıyor...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(100):
        progress_bar.progress(i + 1)
        if i < 50:
            status_text.text("Maliyet bileşenleri hesaplanıyor...")
        else:
            status_text.text("Toplam fiyat oluşturuluyor...")
        time.sleep(0.02)
    
    pricing_data = {
        'base_rate': 200,
        'duration_days': 3,
        'attendees': 50
    }
    pricing_result = orchestrator.pricing_specialist.calculate_pricing(pricing_data, req_result if isinstance(req_result, list) else req_result.get('requirements', []))
    results['pricing'] = pricing_result
    st.success("✅ Fiyatlandırma tamamlandı!")
    
    # Show pricing breakdown
    if isinstance(pricing_result, dict) and pricing_result.get('pricing'):
        pricing = pricing_result['pricing']
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Otel", f"${pricing.get('accommodation', {}).get('total', 0):,.0f}")
        with col2:
            st.metric("Yemek", f"${pricing.get('catering', {}).get('total', 0):,.0f}")
        with col3:
            st.metric("Ulaşım", f"${pricing.get('transportation', {}).get('shuttle_service', 0):,.0f}")
        with col4:
            st.metric("Toplam", f"${pricing.get('grand_total', 0):,.0f}")
    else:
        st.write("**Pricing Breakdown:** N/A")
    
    # Agent 5: Proposal Writer
    st.subheader("✍️ Agent 5: Proposal Writer")
    st.info("Profesyonel teklif yazıyor...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(100):
        progress_bar.progress(i + 1)
        if i < 50:
            status_text.text("Teklif bölümleri yazılıyor...")
        else:
            status_text.text("Teklif formatlanıyor...")
        time.sleep(0.02)
    
    proposal_data = {
        'opportunity_title': opportunity['title'],
        'requirements': req_result if isinstance(req_result, list) else req_result.get('requirements', []),
        'compliance': comp_result,
        'pricing': pricing_result
    }
    proposal_result = orchestrator.proposal_writer.write_proposal(proposal_data)
    results['proposal'] = proposal_result
    st.success("✅ Teklif yazıldı!")
    
    # Show proposal sections
    if isinstance(proposal_result, dict):
        if proposal_result.get('proposal_sections'):
            proposal = proposal_result['proposal_sections']
        else:
            proposal = proposal_result.get('proposal_sections', {})
        
        st.text_area("Executive Summary", proposal.get('executive_summary', 'N/A'), height=200)
    else:
        st.text_area("Executive Summary", "N/A", height=200)
    
    # Agent 6: Quality Assurance
    st.subheader("✅ Agent 6: Quality Assurance")
    st.info("Kalite kontrolü yapıyor...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i in range(100):
        progress_bar.progress(i + 1)
        if i < 50:
            status_text.text("Teklif kalitesi kontrol ediliyor...")
        else:
            status_text.text("Son kontroller yapılıyor...")
        time.sleep(0.02)
    
    qa_result = orchestrator.quality_assurance.review_quality(proposal_result)
    results['quality'] = qa_result
    st.success("✅ Kalite kontrolü tamamlandı!")
    
    # Show quality metrics
    if isinstance(qa_result, dict) and qa_result.get('quality_metrics'):
        quality_metrics = qa_result['quality_metrics']
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Genel Skor", f"{quality_metrics.get('overall_score', 0)}%")
        with col2:
            st.metric("Tamamlanma", f"{quality_metrics.get('completeness', 0)}%")
        with col3:
            st.metric("Doğruluk", f"{quality_metrics.get('accuracy', 0)}%")
        with col4:
            st.metric("Durum", quality_metrics.get('approval_status', 'N/A'))
    else:
        st.write("**Quality Metrics:** N/A")
    
    return results

def main():
    """Ana dashboard fonksiyonu"""
    st.title("📊 ZgrSam Dashboard")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.title("🎛️ Kontroller")
    
    # Fırsatları yükle
    with st.spinner("Fırsatlar yükleniyor..."):
        opportunities = load_opportunities()
    
    if not opportunities:
        st.error("Hiç fırsat bulunamadı!")
        return
    
    # Metrik kartları
    create_metrics_cards(opportunities)
    
    st.markdown("---")
    
    # ID Doğrulama Raporu
    st.subheader("🔍 ID Doğrulama Raporu")
    
    # ID analizi
    valid_ids = 0
    demo_ids = 0
    invalid_ids = 0
    
    for opp in opportunities:
        opp_id = opp['opportunity_id']
        if len(opp_id) == 32 and all(c in '0123456789abcdef' for c in opp_id.lower()):
            valid_ids += 1
        elif opp_id.startswith('DEMO-'):
            demo_ids += 1
        else:
            invalid_ids += 1
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Geçerli UUID", valid_ids)
    with col2:
        st.metric("Demo ID", demo_ids)
    with col3:
        st.metric("Şüpheli ID", invalid_ids)
    with col4:
        total = len(opportunities)
        valid_rate = ((valid_ids + demo_ids) / total * 100) if total > 0 else 0
        st.metric("Geçerlilik Oranı", f"{valid_rate:.1f}%")
    
    # Grafikler
    col1, col2 = st.columns(2)
    
    with col1:
        create_organization_chart(opportunities)
    
    with col2:
        create_contract_chart(opportunities)
    
    st.markdown("---")
    
    # Fırsat seçimi
    st.subheader("🎯 Fırsat Seçimi")
    
    # Fırsat listesi
    opportunity_titles = []
    for i, opp in enumerate(opportunities):
        # ID doğrulama durumu
        opp_id = opp['opportunity_id']
        if len(opp_id) == 32 and all(c in '0123456789abcdef' for c in opp_id.lower()):
            status = "✅"
        elif opp_id.startswith('DEMO-'):
            status = "ℹ️"
        else:
            status = "⚠️"
        
        title = f"{status} {opp['title'][:50]}... (ID: {opp['opportunity_id'][:8]}...)"
        opportunity_titles.append(title)
    
    selected_index = st.selectbox("Fırsat Seçin:", range(len(opportunities)), format_func=lambda x: opportunity_titles[x])
    
    if selected_index is not None:
        selected_opportunity = opportunities[selected_index]
        
        # Fırsat detayları
        with st.expander("📋 Seçilen Fırsat Detayları", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Fırsat ID:** {selected_opportunity['opportunity_id']}")
                st.write(f"**Başlık:** {selected_opportunity['title']}")
                st.write(f"**Sözleşme Tipi:** {selected_opportunity['contract_type'] or 'N/A'}")
                st.write(f"**NAICS Kodu:** {selected_opportunity['naics_code'] or 'N/A'}")
                
                # SAM.gov linki
                sam_link = f"https://sam.gov/workspace/contract/opp/{selected_opportunity['opportunity_id']}/view"
                st.write(f"**SAM.gov Link:** [Fırsatı Görüntüle]({sam_link})")
            
            with col2:
                st.write(f"**Organizasyon:** {selected_opportunity['organization_type'] or 'N/A'}")
                st.write(f"**Yayın Tarihi:** {selected_opportunity['posted_date']}")
                st.write(f"**Açıklama Uzunluğu:** {len(selected_opportunity['description'] or '')} karakter")
                
                # ID doğrulama durumu
                opp_id = selected_opportunity['opportunity_id']
                if len(opp_id) == 32 and all(c in '0123456789abcdef' for c in opp_id.lower()):
                    st.success("✅ ID formatı geçerli (UUID)")
                elif opp_id.startswith('DEMO-'):
                    st.info("ℹ️ Demo ID")
                else:
                    st.warning("⚠️ ID formatı şüpheli")
            
            if selected_opportunity['description']:
                st.text_area("Açıklama", selected_opportunity['description'], height=150)
                
                # Description'da ID referanslarını göster
                import re
                description = selected_opportunity['description']
                hex_ids = re.findall(r'[a-f0-9]{32}', description, re.I)
                if hex_ids:
                    st.write("**Description'da bulunan ID'ler:**")
                    for hex_id in hex_ids:
                        if hex_id.lower() == opp_id.lower():
                            st.success(f"✅ {hex_id} (eşleşiyor)")
                        else:
                            st.warning(f"⚠️ {hex_id} (farklı)")
        
        # Ajan workflow'unu çalıştır
        if st.button("🚀 Ajan Workflow'unu Başlat", type="primary"):
            # Workflow'u expander dışında çalıştır
            st.subheader("🤖 Ajan Workflow")
            results = run_agent_workflow(selected_opportunity)
            
            # Sonuçları göster
            st.subheader("📊 Workflow Sonuçları")
            st.json(results)

if __name__ == "__main__":
    main()
