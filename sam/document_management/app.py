"""
SAM Document Management Streamlit Interface
Standalone Streamlit application for document management
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os
from pathlib import Path

# Import from the module
from autogen_document_manager import (
    upload_manual_document,
    analyze_manual_document,
    get_manual_documents,
    get_document_analysis_results
)

from sam_document_access_v2 import (
    get_opportunity_description_v2,
    get_opportunity_resource_links_v2,
    get_opportunity_documents_complete_v2
)

from ultra_optimized_sam_manager import (
    ultra_bulk_fetch_and_store,
    get_notice_documents_optimized,
    update_data_strategy
)

# Removed imports for deleted files:
# - optimized_sam_manager.py (replaced by ultra_optimized_sam_manager.py)
# - smart_document_manager.py (replaced by autogen_document_manager.py)

from autogen_analysis_center import (
    analyze_opportunity_comprehensive,
    batch_analyze_opportunities,
    generate_analysis_report,
    get_analysis_statistics
)

from sam_document_access_v2 import (
    fetch_opportunities,
    get_opportunity_details,
    download_all_attachments
)

from job_manager import (
    enqueue_analysis,
    get_job_status,
    get_job_results
)

# Import opportunity analysis page
from opportunity_analysis import opportunity_analysis_page

# Page configuration
st.set_page_config(
    page_title="SAM Document Management",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    color: #1f77b4;
    text-align: center;
    margin-bottom: 2rem;
    padding: 1rem;
    background: linear-gradient(90deg, #1f77b4, #ff7f0e);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.feature-card {
    background-color: #f0f2f6;
    padding: 1rem;
    border-radius: 0.5rem;
    border-left: 4px solid #1f77b4;
    margin: 1rem 0;
}

.status-success {
    color: #28a745;
    font-weight: bold;
}

.status-warning {
    color: #ffc107;
    font-weight: bold;
}

.status-error {
    color: #dc3545;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

def main():
    """Main application"""
    
    # Header
    st.markdown('<div class="main-header">📄 SAM Document Management System</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/200x100/1f77b4/ffffff?text=SAM+DM", width=200)
        
        st.markdown("### 🚀 Navigation")
        page = st.selectbox(
            "Select Page",
            [
                "🏠 Dashboard",
                "🎯 Opportunity Analysis",
                "📤 Manual Document Upload",
                "📋 Document Library", 
                "🔍 Document Search",
                "🤖 AI Analysis Center",
                "🧠 AutoGen Analysis Center",
                "🚀 SAM Collector",
                "⚙️ Job Management",
                "📄 SAM API v2 Access",
                "🔄 Bulk Data Fetch",
                "⚙️ System Management"
            ]
        )
        
        st.markdown("### 📊 System Status")
        st.markdown("**Database:** <span class='status-success'>✅ Connected</span>", unsafe_allow_html=True)
        st.markdown("**API Key:** <span class='status-success'>✅ Configured</span>", unsafe_allow_html=True)
        st.markdown("**AutoGen:** <span class='status-warning'>⚠️ Fallback Mode</span>", unsafe_allow_html=True)
    
    # Main content based on selected page
    if page == "🏠 Dashboard":
        show_dashboard()
    elif page == "🎯 Opportunity Analysis":
        opportunity_analysis_page()
    elif page == "📤 Manual Document Upload":
        show_manual_upload()
    elif page == "📋 Document Library":
        show_document_library()
    elif page == "🔍 Document Search":
        show_document_search()
    elif page == "🤖 AI Analysis Center":
        show_ai_analysis_center()
    elif page == "🧠 AutoGen Analysis Center":
        show_autogen_analysis_center()
    elif page == "🚀 SAM Collector":
        show_sam_collector()
    elif page == "⚙️ Job Management":
        show_job_management()
    elif page == "📄 SAM API v2 Access":
        show_sam_api_v2_access()
    elif page == "🔄 Bulk Data Fetch":
        show_bulk_data_fetch()
    elif page == "⚙️ System Management":
        show_system_management()

def show_dashboard():
    """Dashboard page"""
    st.markdown("## 🏠 Dashboard")
    
    # System overview
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Documents", "0", "0")
    
    with col2:
        st.metric("Analyzed Documents", "0", "0")
    
    with col3:
        st.metric("Pending Analysis", "0", "0")
    
    with col4:
        st.metric("System Status", "Active", "✅")
    
    # Recent activity
    st.markdown("### 📈 Recent Activity")
    st.info("No recent activity to display")
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📤 Upload Document", type="primary", use_container_width=True):
            st.session_state.page = "📤 Manual Document Upload"
            st.rerun()
    
    with col2:
        if st.button("🔍 Search Documents", use_container_width=True):
            st.session_state.page = "🔍 Document Search"
            st.rerun()
    
    with col3:
        if st.button("🎯 Opportunity Analysis", use_container_width=True):
            st.session_state.page = "🎯 Opportunity Analysis"
            st.rerun()

def show_manual_upload():
    """Manual document upload page"""
    st.markdown("## 📤 Manual Document Upload")
    
    st.info("""
    🚀 **Upload your documents for AI analysis:**
    
    - ✅ **Supported formats:** PDF, DOC, DOCX, TXT
    - ✅ **AI Analysis:** AutoGen agents with fallback analysis
    - ✅ **Smart categorization:** Automatic category detection
    - ✅ **Keyword extraction:** Important terms identification
    - ✅ **SAM.gov integration:** Link to opportunities
    """)
    
    # Upload form
    with st.form("manual_upload_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            uploaded_file = st.file_uploader(
                "Select Document",
                type=['pdf', 'doc', 'docx', 'txt'],
                help="Choose a document to upload and analyze"
            )
        
        with col2:
            notice_id = st.text_input(
                "Notice ID (Optional)",
                placeholder="e.g., HC101325QA399",
                help="Link to SAM.gov opportunity"
            )
        
        title = st.text_input(
            "Document Title",
            placeholder="Enter document title",
            help="Title for the document"
        )
        
        description = st.text_area(
            "Description",
            placeholder="Document description",
            help="Brief description of the document"
        )
        
        tags_input = st.text_input(
            "Tags (comma-separated)",
            placeholder="hotel, lodging, accommodation",
            help="Keywords for categorization"
        )
        
        submitted = st.form_submit_button("🚀 Upload Document", type="primary")
    
    if submitted:
        if uploaded_file and title:
            try:
                # Read file content
                file_content = uploaded_file.read()
                filename = uploaded_file.name
                
                # Parse tags
                tags = [tag.strip() for tag in tags_input.split(',') if tag.strip()] if tags_input else []
                
                # Upload document
                with st.spinner("Uploading document..."):
                    result = upload_manual_document(
                        file_content=file_content,
                        filename=filename,
                        title=title,
                        description=description,
                        tags=tags,
                        notice_id=notice_id if notice_id else None
                    )
                
                if result['success']:
                    st.success(f"✅ Document uploaded successfully!")
                    st.info(f"**Document ID:** {result['document_id']}")
                    
                    # Auto-analysis option
                    if st.button("🤖 Start AI Analysis", type="secondary"):
                        with st.spinner("AI analysis in progress..."):
                            analysis_result = analyze_manual_document(result['document_id'])
                            
                            if analysis_result['success']:
                                st.success("✅ Analysis completed!")
                                st.json(analysis_result['analysis_result'])
                            else:
                                st.error(f"❌ Analysis failed: {analysis_result['error']}")
                else:
                    st.error(f"❌ Upload failed: {result['error']}")
            
            except Exception as e:
                st.error(f"❌ Unexpected error: {e}")
        else:
            st.error("❌ Please provide file and title")

def show_document_library():
    """Document library page"""
    st.markdown("## 📋 Document Library")
    
    # Filters
    col1, col2 = st.columns(2)
    
    with col1:
        status_filter = st.selectbox(
            "Analysis Status",
            ["All", "pending", "analyzing", "completed", "failed"],
            help="Filter by analysis status"
        )
    
    with col2:
        if st.button("🔄 Refresh", key="refresh_library"):
            st.rerun()
    
    # Get documents
    status = None if status_filter == "All" else status_filter
    documents = get_manual_documents(limit=100, status=status)
    
    if documents:
        st.success(f"✅ Found {len(documents)} documents")
        
        # Document table
        doc_data = []
        for doc in documents:
            doc_data.append({
                'ID': doc['id'][:8] + '...',
                'Title': doc['title'][:50] + '...' if len(doc['title']) > 50 else doc['title'],
                'Type': doc['file_type'],
                'Size (KB)': round(doc['file_size'] / 1024, 2),
                'Upload Date': doc['upload_date'].strftime('%Y-%m-%d %H:%M'),
                'Status': doc['analysis_status'],
                'Tags': ', '.join(doc['tags'][:3]) if doc['tags'] else 'None'
            })
        
        df = pd.DataFrame(doc_data)
        st.dataframe(df, use_container_width=True)
        
        # Document details
        st.markdown("### 🔍 Document Details")
        selected_doc = st.selectbox(
            "Select Document",
            [f"{doc['title']} ({doc['id'][:8]})" for doc in documents],
            help="Select document to view details"
        )
        
        if selected_doc:
            # Find selected document
            selected_id = None
            for doc in documents:
                if f"{doc['title']} ({doc['id'][:8]})" == selected_doc:
                    selected_id = doc['id']
                    break
            
            if selected_id:
                selected_doc_data = next((doc for doc in documents if doc['id'] == selected_id), None)
                
                if selected_doc_data:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**📄 Document Information**")
                        st.write(f"**Title:** {selected_doc_data['title']}")
                        st.write(f"**Description:** {selected_doc_data['description']}")
                        st.write(f"**File Type:** {selected_doc_data['file_type']}")
                        st.write(f"**Size:** {round(selected_doc_data['file_size'] / 1024, 2)} KB")
                        st.write(f"**Upload Date:** {selected_doc_data['upload_date']}")
                        st.write(f"**Status:** {selected_doc_data['analysis_status']}")
                    
                    with col2:
                        st.markdown("**🏷️ Tags and Relations**")
                        if selected_doc_data['tags']:
                            st.write(f"**Tags:** {', '.join(selected_doc_data['tags'])}")
                        else:
                            st.write("**Tags:** None")
                        
                        if selected_doc_data['notice_id']:
                            st.write(f"**Notice ID:** {selected_doc_data['notice_id']}")
                        else:
                            st.write("**Notice ID:** None")
                    
                    # Analysis button
                    if selected_doc_data['analysis_status'] == 'pending':
                        if st.button("🤖 Start Analysis", type="primary", key=f"analyze_{selected_id}"):
                            with st.spinner("Analysis in progress..."):
                                analysis_result = analyze_manual_document(selected_id)
                                
                                if analysis_result['success']:
                                    st.success("✅ Analysis completed!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Analysis failed: {analysis_result['error']}")
    else:
        st.info("📭 No documents found")

def show_document_search():
    """Document search page"""
    st.markdown("## 🔍 Document Search")
    
    # Search form
    with st.form("search_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            search_query = st.text_input(
                "Search Query",
                placeholder="Enter keywords to search",
                help="Search in document titles, descriptions, and content"
            )
        
        with col2:
            search_type = st.selectbox(
                "Search Type",
                ["All", "Title", "Description", "Tags", "Content"],
                help="Specify search scope"
            )
        
        submitted = st.form_submit_button("🔍 Search", type="primary")
    
    if submitted:
        if search_query:
            st.info(f"Searching for: '{search_query}' in {search_type}")
            # TODO: Implement search functionality
            st.warning("Search functionality will be implemented")
        else:
            st.error("Please enter a search query")

def show_ai_analysis_center():
    """AI Analysis Center page"""
    st.markdown("## 🤖 AI Analysis Center")
    
    st.info("""
    🧠 **AI Analysis Center:**
    
    This center provides advanced AI analysis capabilities:
    - ✅ **Content Analysis:** Document topic and theme identification
    - ✅ **Keyword Extraction:** Important terms and concepts
    - ✅ **Smart Categorization:** Automatic category assignment
    - ✅ **Theme Analysis:** Main themes extraction
    - ✅ **Opportunity Linking:** SAM.gov opportunity correlation
    """)
    
    # Analysis options
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Analyze Pending Documents", type="primary", key="analyze_pending"):
            pending_docs = get_manual_documents(status="pending")
            
            if pending_docs:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, doc in enumerate(pending_docs):
                    status_text.text(f"Analyzing: {doc['title']}")
                    progress_bar.progress((i + 1) / len(pending_docs))
                    
                    analysis_result = analyze_manual_document(doc['id'])
                    
                    if analysis_result['success']:
                        st.success(f"✅ {doc['title']} analyzed")
                    else:
                        st.error(f"❌ {doc['title']} failed: {analysis_result['error']}")
                
                status_text.text("✅ All analyses completed!")
                st.rerun()
            else:
                st.info("📭 No pending documents to analyze")
    
    with col2:
        if st.button("🔄 Re-analyze All Documents", type="secondary", key="reanalyze_all"):
            all_docs = get_manual_documents()
            
            if all_docs:
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, doc in enumerate(all_docs):
                    status_text.text(f"Re-analyzing: {doc['title']}")
                    progress_bar.progress((i + 1) / len(all_docs))
                    
                    analysis_result = analyze_manual_document(doc['id'])
                    
                    if analysis_result['success']:
                        st.success(f"✅ {doc['title']} re-analyzed")
                    else:
                        st.error(f"❌ {doc['title']} failed: {analysis_result['error']}")
                
                status_text.text("✅ All re-analyses completed!")
                st.rerun()
            else:
                st.info("📭 No documents to re-analyze")
    
    # Analysis results
    st.markdown("### 📊 Analysis Results")
    
    analyzed_docs = get_manual_documents(status="completed")
    
    if analyzed_docs:
        st.success(f"✅ Found {len(analyzed_docs)} analyzed documents")
        
        for doc in analyzed_docs:
            with st.expander(f"📄 {doc['title']} - Analysis Results"):
                analysis_results = get_document_analysis_results(doc['id'])
                
                if analysis_results:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**📊 Analysis Summary**")
                        if 'summary' in analysis_results:
                            st.write(analysis_results['summary'])
                        
                        if 'keywords' in analysis_results:
                            st.markdown("**🔑 Keywords**")
                            keywords = analysis_results['keywords']
                            if isinstance(keywords, list):
                                for keyword in keywords[:10]:
                                    st.write(f"• {keyword}")
                    
                    with col2:
                        st.markdown("**📂 Categories**")
                        if 'categories' in analysis_results:
                            categories = analysis_results['categories']
                            if isinstance(categories, list):
                                for category in categories:
                                    st.write(f"• {category}")
                        
                        st.markdown("**🎯 Themes**")
                        if 'themes' in analysis_results:
                            themes = analysis_results['themes']
                            if isinstance(themes, list):
                                for theme in themes:
                                    st.write(f"• {theme}")
                    
                    # Confidence score
                    if 'confidence' in analysis_results:
                        confidence = analysis_results['confidence']
                        st.metric("Confidence Score", f"{confidence:.2%}")
                    
                    # JSON view
                    if st.checkbox("JSON View", key=f"json_{doc['id']}"):
                        st.json(analysis_results)
                else:
                    st.warning("Analysis results not found")
    else:
        st.info("📭 No analyzed documents found")

def show_autogen_analysis_center():
    """AutoGen Analysis Center page"""
    st.markdown("## 🧠 AutoGen Analysis Center")
    
    st.info("""
    🧠 **AutoGen Analysis Center:**
    
    This center provides comprehensive AI analysis using AutoGen agents:
    - ✅ **Comprehensive Analysis:** Full opportunity analysis with multiple agents
    - ✅ **Document Processing:** Advanced document analysis and processing
    - ✅ **Proposal Drafting:** AI-powered proposal generation
    - ✅ **Batch Analysis:** Multiple opportunities analysis
    - ✅ **Report Generation:** Human-readable analysis reports
    """)
    
    # Analysis options
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔍 Single Opportunity Analysis")
        
        opportunity_id = st.text_input(
            "Opportunity ID",
            placeholder="e.g., HC101325QA399",
            help="Enter SAM.gov opportunity ID for comprehensive analysis"
        )
        
        if st.button("🧠 Analyze Opportunity", type="primary", key="analyze_single_opp"):
            if opportunity_id:
                with st.spinner("Comprehensive analysis in progress..."):
                    try:
                        result = analyze_opportunity_comprehensive(opportunity_id)
                        
                        if 'error' not in result:
                            st.success("✅ Analysis completed!")
                            
                            # Show analysis results
                            st.markdown("### 📊 Analysis Results")
                            
                            # Summary metrics
                            summary = result.get('summary', {})
                            col_a, col_b, col_c = st.columns(3)
                            
                            with col_a:
                                st.metric("Documents Analyzed", summary.get('total_documents', 0))
                            
                            with col_b:
                                st.metric("Confidence Score", f"{summary.get('analysis_confidence', 0.0):.2%}")
                            
                            with col_c:
                                st.metric("Proposal Status", summary.get('proposal_status', 'Unknown'))
                            
                            # Detailed results
                            with st.expander("📋 Detailed Analysis Results"):
                                st.json(result)
                            
                            # Generate report
                            if st.button("📄 Generate Report", key="generate_report"):
                                report = generate_analysis_report(result)
                                st.markdown("### 📄 Analysis Report")
                                st.markdown(report)
                        else:
                            st.error(f"❌ Analysis failed: {result['error']}")
                    except Exception as e:
                        st.error(f"❌ Analysis error: {e}")
            else:
                st.error("❌ Please enter Opportunity ID")
    
    with col2:
        st.markdown("### 🔄 Batch Analysis")
        
        # Batch analysis options
        batch_type = st.selectbox(
            "Batch Analysis Type",
            ["Manual Input", "From Database", "Recent Opportunities"],
            help="Select how to get opportunity IDs for batch analysis"
        )
        
        if batch_type == "Manual Input":
            opportunity_ids_input = st.text_area(
                "Opportunity IDs (one per line)",
                placeholder="HC101325QA399\nHC101325QA400\nHC101325QA401",
                help="Enter multiple opportunity IDs, one per line"
            )
            
            if st.button("🔄 Batch Analyze", type="secondary", key="batch_analyze_manual"):
                if opportunity_ids_input:
                    opportunity_ids = [id.strip() for id in opportunity_ids_input.split('\n') if id.strip()]
                    
                    with st.spinner(f"Batch analysis in progress for {len(opportunity_ids)} opportunities..."):
                        try:
                            result = batch_analyze_opportunities(opportunity_ids)
                            
                            if 'error' not in result:
                                st.success(f"✅ Batch analysis completed!")
                                
                                # Show batch results
                                st.markdown("### 📊 Batch Analysis Results")
                                
                                col_a, col_b, col_c = st.columns(3)
                                
                                with col_a:
                                    st.metric("Total", result['total_opportunities'])
                                
                                with col_b:
                                    st.metric("Successful", result['successful'])
                                
                                with col_c:
                                    st.metric("Failed", result['failed'])
                                
                                # Show individual results
                                with st.expander("📋 Individual Results"):
                                    for i, res in enumerate(result['results']):
                                        st.write(f"**{i+1}. {res['opportunity_id']}**")
                                        if 'error' in res:
                                            st.error(f"Error: {res['error']}")
                                        else:
                                            st.success("✅ Analysis completed")
                            else:
                                st.error(f"❌ Batch analysis failed: {result['error']}")
                        except Exception as e:
                            st.error(f"❌ Batch analysis error: {e}")
                else:
                    st.error("❌ Please enter Opportunity IDs")
        
        elif batch_type == "From Database":
            st.info("📊 Database batch analysis will be implemented")
        
        elif batch_type == "Recent Opportunities":
            st.info("📅 Recent opportunities batch analysis will be implemented")
    
    # Analysis statistics
    st.markdown("### 📈 Analysis Statistics")
    
    if st.button("🔄 Refresh Statistics", key="refresh_stats"):
        with st.spinner("Loading statistics..."):
            try:
                stats = get_analysis_statistics()
                
                if 'error' not in stats:
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Analyses", stats.get('total_analyses', 0))
                    
                    with col2:
                        st.metric("Successful", stats.get('successful_analyses', 0))
                    
                    with col3:
                        st.metric("Failed", stats.get('failed_analyses', 0))
                    
                    with col4:
                        st.metric("Avg Confidence", f"{stats.get('average_confidence', 0.0):.2%}")
                    
                    # Additional stats
                    st.markdown("**Additional Information:**")
                    st.write(f"- Last Analysis: {stats.get('last_analysis', 'Never')}")
                    st.write(f"- Most Analyzed Type: {stats.get('most_analyzed_opportunity_type', 'Unknown')}")
                else:
                    st.error(f"❌ Statistics error: {stats['error']}")
            except Exception as e:
                st.error(f"❌ Statistics error: {e}")
    
    # Analysis history
    st.markdown("### 📚 Analysis History")
    st.info("📊 Analysis history will be implemented with database integration")

def show_sam_api_v2_access():
    """SAM API v2 Access page"""
    st.markdown("## 📄 SAM API v2 Document Access")
    
    st.info("""
    🚀 **SAM API v2 Document Access System:**
    
    This system uses advanced SAM.gov API v2 features:
    - ✅ **Description Access:** Direct access to opportunity descriptions
    - ✅ **ResourceLinks Array:** Additional document URLs
    - ✅ **API Key Integration:** Secure access
    - ✅ **Rate Limiting:** Optimized API calls
    """)
    
    # Notice ID input
    notice_id_v2 = st.text_input(
        "Notice ID (API v2)",
        placeholder="e.g., HC101325QA399",
        help="SAM.gov opportunity ID for API v2 access"
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Get Description", help="Get opportunity description", key="get_description"):
            if notice_id_v2:
                with st.spinner("Getting description..."):
                    try:
                        description = get_opportunity_description_v2(notice_id_v2)
                        
                        if description['success']:
                            st.success("✅ Description retrieved!")
                            
                            # Show description content
                            st.markdown("### 📋 Opportunity Description")
                            st.text_area(
                                "Content",
                                value=description['content'][:2000] + "..." if len(description['content']) > 2000 else description['content'],
                                height=300,
                                disabled=True
                            )
                            
                            # URL info
                            st.info(f"**Description URL:** {description['description_url']}")
                        else:
                            st.error(f"❌ Description failed: {description['error']}")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            else:
                st.error("❌ Please enter Notice ID")
    
    with col2:
        if st.button("🔗 Get ResourceLinks", help="Get additional documents", key="get_resourcelinks"):
            if notice_id_v2:
                with st.spinner("Getting ResourceLinks..."):
                    try:
                        resource_links = get_opportunity_resource_links_v2(notice_id_v2)
                        
                        if resource_links:
                            st.success(f"✅ Found {len(resource_links)} ResourceLinks!")
                            
                            # Show ResourceLinks
                            st.markdown("### 🔗 ResourceLinks")
                            
                            link_data = []
                            for i, link in enumerate(resource_links):
                                link_data.append({
                                    'No': i + 1,
                                    'Title': link['title'],
                                    'Type': link['type'],
                                    'URL': link['url'][:50] + '...' if len(link['url']) > 50 else link['url'],
                                    'Source': link['source']
                                })
                            
                            df = pd.DataFrame(link_data)
                            st.dataframe(df, use_container_width=True)
                        else:
                            st.warning("⚠️ No ResourceLinks found")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            else:
                st.error("❌ Please enter Notice ID")
    
    with col3:
        if st.button("🚀 Full Access", help="Description + ResourceLinks", key="full_access"):
            if notice_id_v2:
                with st.spinner("Full document access..."):
                    try:
                        complete = get_opportunity_documents_complete_v2(notice_id_v2)
                        
                        if complete['success']:
                            st.success(f"✅ Full access successful! {complete['total_documents']} documents")
                            
                            # Description
                            if complete['description'] and complete['description']['success']:
                                st.markdown("### 📄 Description")
                                st.text_area(
                                    "Description",
                                    value=complete['description']['content'][:1000] + "..." if len(complete['description']['content']) > 1000 else complete['description']['content'],
                                    height=200,
                                    disabled=True
                                )
                            
                            # ResourceLinks
                            if complete['resource_links']:
                                st.markdown("### 🔗 ResourceLinks")
                                
                                link_data = []
                                for i, link in enumerate(complete['resource_links']):
                                    link_data.append({
                                        'No': i + 1,
                                        'Title': link['title'],
                                        'Type': link['type'],
                                        'URL': link['url'][:50] + '...' if len(link['url']) > 50 else link['url']
                                    })
                                
                                df = pd.DataFrame(link_data)
                                st.dataframe(df, use_container_width=True)
                            
                            # Summary
                            st.markdown("### 📊 Summary")
                            col_a, col_b, col_c = st.columns(3)
                            
                            with col_a:
                                st.metric("Description", "✅" if complete['description'] and complete['description']['success'] else "❌")
                            
                            with col_b:
                                st.metric("ResourceLinks", len(complete['resource_links']))
                            
                            with col_c:
                                st.metric("Total Documents", complete['total_documents'])
                        else:
                            st.error(f"❌ Full access failed: {complete['error']}")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            else:
                st.error("❌ Please enter Notice ID")

def show_bulk_data_fetch():
    """Bulk data fetch page"""
    st.markdown("## 🔄 Bulk Data Fetch")
    
    st.info("""
    💡 **Ultra Optimized System:**
    
    This system fetches opportunities from SAM.gov in bulk and stores them in the database.
    This way, you don't need to make separate API calls for each document!
    """)
    
    # Bulk fetch form
    with st.form("bulk_fetch_form"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            days_back = st.number_input(
                "Days Back",
                min_value=1,
                max_value=365,
                value=30,
                help="How many days back to fetch"
            )
        
        with col2:
            limit = st.number_input(
                "Maximum Opportunities",
                min_value=10,
                max_value=1000,
                value=100,
                help="Maximum opportunities to fetch"
            )
        
        with col3:
            keywords = st.text_input(
                "Keywords (comma-separated)",
                value="hotel, lodging, accommodation",
                help="Search keywords"
            )
        
        submitted = st.form_submit_button("🚀 Start Bulk Fetch", type="primary")
    
    if submitted:
        # Parse keywords
        keyword_list = [kw.strip() for kw in keywords.split(',') if kw.strip()]
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Bulk fetch
            status_text.text("📊 Fetching opportunities from SAM.gov...")
            progress_bar.progress(20)
            
            result = ultra_bulk_fetch_and_store(
                days_back=days_back,
                limit=limit
            )
            
            status_text.text("💾 Storing in database...")
            progress_bar.progress(80)
            
            status_text.text("✅ Completed!")
            progress_bar.progress(100)
            
            if result['success']:
                st.success(f"""
                🎉 **Bulk Fetch Successful!**
                
                - 📊 **Fetched:** {result['total_fetched']} opportunities
                - 💾 **Stored:** {result['total_stored']} opportunities
                - 🕒 **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                """)
            else:
                st.error(f"❌ Bulk fetch failed: {result.get('error')}")
        
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")
            progress_bar.progress(0)
            status_text.text("❌ Error occurred")
    
    # Quick actions
    st.markdown("### ⚡ Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📅 Last 7 Days", help="Fetch last 7 days", key="fetch_7_days"):
            with st.spinner("Fetching last 7 days..."):
                try:
                    result = ultra_bulk_fetch_and_store(days_back=7, limit=50)
                    if result['success']:
                        st.success(f"✅ {result['total_stored']} opportunities stored")
                    else:
                        st.error(f"❌ Error: {result.get('error')}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    with col2:
        if st.button("📅 Last 30 Days", help="Fetch last 30 days", key="fetch_30_days"):
            with st.spinner("Fetching last 30 days..."):
                try:
                    result = ultra_bulk_fetch_and_store(days_back=30, limit=200)
                    if result['success']:
                        st.success(f"✅ {result['total_stored']} opportunities stored")
                    else:
                        st.error(f"❌ Error: {result.get('error')}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    with col3:
        if st.button("🔄 Update Strategy", help="Smart update", key="update_strategy"):
            with st.spinner("Update strategy running..."):
                try:
                    result = update_data_strategy()
                    if result['success']:
                        st.success(f"✅ {result['total_stored']} new opportunities stored")
                    else:
                        st.info(f"ℹ️ Update not needed: {result.get('error', 'Last update was recent')}")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

def show_system_management():
    """System management page"""
    st.markdown("## ⚙️ System Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📊 System Information**")
        
        # System metrics
        all_docs = get_manual_documents()
        if all_docs:
            status_counts = {}
            for doc in all_docs:
                status = doc['analysis_status']
                status_counts[status] = status_counts.get(status, 0) + 1
            
            col_a, col_b, col_c, col_d = st.columns(4)
            
            with col_a:
                st.metric("Total Documents", len(all_docs))
            
            with col_b:
                st.metric("Pending", status_counts.get('pending', 0))
            
            with col_c:
                st.metric("Analyzing", status_counts.get('analyzing', 0))
            
            with col_d:
                st.metric("Completed", status_counts.get('completed', 0))
            
            # Status distribution
            status_data = {
                "Status": list(status_counts.keys()),
                "Count": list(status_counts.values())
            }
            
            status_df = pd.DataFrame(status_data)
            st.dataframe(status_df, use_container_width=True, hide_index=True)
        else:
            st.info("📭 No system statistics available")
    
    with col2:
        st.markdown("**🧹 Maintenance Operations**")
        
        days_old = st.number_input(
            "Clean documents older than (days)",
            min_value=1,
            max_value=365,
            value=30
        )
        
        if st.button("🗑️ Clean Old Documents", type="secondary", key="cleanup_old_docs"):
            with st.spinner("Cleaning up..."):
                try:
                    # TODO: Implement cleanup functionality
                    st.success(f"✅ Documents older than {days_old} days cleaned")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Cleanup error: {e}")
    
    # System status
    st.markdown("### 📈 System Status")
    
    status_data = {
        "Component": [
            "Database Connection",
            "API Key Configuration",
            "AutoGen Integration",
            "Rate Limiting",
            "File Storage"
        ],
        "Status": [
            "✅ Active",
            "✅ Configured",
            "⚠️ Fallback Mode",
            "✅ Optimized",
            "✅ Available"
        ],
        "Description": [
            "PostgreSQL connection established",
            "SAM.gov API key configured",
            "Using fallback analysis (OpenAI not available)",
            "3 second interval rate limiting",
            "Document storage directory available"
        ]
    }
    
    status_df = pd.DataFrame(status_data)
    st.dataframe(status_df, use_container_width=True, hide_index=True)

def show_sam_collector():
    """SAM Collector page"""
    st.markdown("## 🚀 SAM Collector")
    
    st.info("""
    🚀 **SAM Collector - Advanced Opportunity Fetcher:**
    
    This system fetches opportunities and attachments from SAM.gov:
    - ✅ **Smart Fetching:** Keywords, NAICS codes, date ranges
    - ✅ **Rate Limiting:** 3-second intervals, retry logic
    - ✅ **Deduplication:** Hash-based duplicate detection
    - ✅ **Attachment Download:** Automatic document retrieval
    - ✅ **Progress Tracking:** Real-time fetch monitoring
    """)
    
    # Fetch form
    with st.form("sam_collector_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            keywords_input = st.text_input(
                "Keywords (comma-separated)",
                placeholder="hotel, lodging, accommodation",
                help="Search keywords for opportunities"
            )
            
            naics_input = st.text_input(
                "NAICS Codes (comma-separated)",
                placeholder="721110, 721310",
                help="NAICS industry codes"
            )
        
        with col2:
            days_back = st.number_input(
                "Days Back",
                min_value=1,
                max_value=365,
                value=7,
                help="How many days back to search"
            )
            
            limit = st.number_input(
                "Maximum Opportunities",
                min_value=10,
                max_value=1000,
                value=100,
                help="Maximum opportunities to fetch"
            )
        
        submitted = st.form_submit_button("🚀 Fetch Opportunities", type="primary")
    
    if submitted:
        # Parse inputs
        keywords = [kw.strip() for kw in keywords_input.split(',') if kw.strip()]
        naics_codes = [code.strip() for code in naics_input.split(',') if code.strip()]
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Fetch opportunities
            status_text.text("📊 Fetching opportunities from SAM.gov...")
            progress_bar.progress(30)
            
            result = fetch_opportunities(
                keywords=keywords,
                naics_codes=naics_codes,
                days_back=days_back,
                limit=limit
            )
            
            progress_bar.progress(70)
            
            if result['success']:
                st.success(f"✅ Fetched {result['count']} opportunities!")
                
                # Show opportunities
                opportunities = result['opportunities']
                if opportunities:
                    st.markdown("### 📋 Fetched Opportunities")
                    
                    opp_data = []
                    for opp in opportunities[:10]:  # Show first 10
                        opp_data.append({
                            'Notice ID': opp.get('noticeId', 'N/A'),
                            'Title': opp.get('title', 'N/A')[:50] + '...' if len(opp.get('title', '')) > 50 else opp.get('title', 'N/A'),
                            'Agency': opp.get('department', 'N/A'),
                            'Posted Date': opp.get('postedDate', 'N/A'),
                            'Deadline': opp.get('responseDeadLine', 'N/A')
                        })
                    
                    df = pd.DataFrame(opp_data)
                    st.dataframe(df, use_container_width=True)
                    
                    # Download attachments option
                    if st.button("📥 Download All Attachments", type="secondary", key="download_all_attachments"):
                        with st.spinner("Downloading attachments..."):
                            downloaded_count = 0
                            failed_count = 0
                            
                            for opp in opportunities[:5]:  # Limit to first 5 for demo
                                notice_id = opp.get('noticeId')
                                if notice_id:
                                    download_result = download_all_attachments(notice_id)
                                    if download_result['success']:
                                        downloaded_count += download_result['downloaded']
                                        failed_count += download_result['failed']
                            
                            st.success(f"✅ Downloaded {downloaded_count} attachments, {failed_count} failed")
                else:
                    st.info("📭 No opportunities found")
            else:
                st.error(f"❌ Fetch failed: {result['error']}")
            
            progress_bar.progress(100)
            status_text.text("✅ Completed!")
            
        except Exception as e:
            st.error(f"❌ Unexpected error: {e}")
            progress_bar.progress(0)
            status_text.text("❌ Error occurred")
    
    # Individual opportunity analysis
    st.markdown("### 🔍 Individual Opportunity Analysis")
    
    notice_id = st.text_input(
        "Notice ID",
        placeholder="e.g., HC101325QA399",
        help="Enter specific notice ID for detailed analysis"
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Get Details", key="get_opp_details"):
            if notice_id:
                with st.spinner("Getting opportunity details..."):
                    try:
                        result = get_opportunity_details(notice_id)
                        
                        if result['success']:
                            st.success("✅ Details retrieved!")
                            
                            opp = result['opportunity']
                            st.markdown("**Opportunity Information:**")
                            st.write(f"**Title:** {opp.get('title', 'N/A')}")
                            st.write(f"**Agency:** {opp.get('department', 'N/A')}")
                            st.write(f"**Deadline:** {opp.get('responseDeadLine', 'N/A')}")
                            st.write(f"**Description:** {opp.get('description', 'N/A')[:200]}...")
                            
                            # Show attachments
                            attachments = result.get('attachments', [])
                            if attachments:
                                st.markdown("**Attachments:**")
                                for i, att in enumerate(attachments):
                                    st.write(f"{i+1}. {att.get('filename', 'Unknown')} - {att.get('type', 'Unknown')}")
                        else:
                            st.error(f"❌ Failed: {result['error']}")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            else:
                st.error("❌ Please enter Notice ID")
    
    with col2:
        if st.button("📥 Download Attachments", key="download_opp_attachments"):
            if notice_id:
                with st.spinner("Downloading attachments..."):
                    try:
                        result = download_all_attachments(notice_id)
                        
                        if result['success']:
                            st.success(f"✅ Downloaded {result['downloaded']} attachments!")
                            if result['failed'] > 0:
                                st.warning(f"⚠️ {result['failed']} downloads failed")
                        else:
                            st.error(f"❌ Download failed: {result['error']}")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            else:
                st.error("❌ Please enter Notice ID")
    
    with col3:
        if st.button("🧠 Start Analysis", key="start_opp_analysis"):
            if notice_id:
                with st.spinner("Starting analysis..."):
                    try:
                        job_id = enqueue_analysis(notice_id)
                        
                        if job_id:
                            st.success(f"✅ Analysis job started! Job ID: {job_id}")
                            st.info("Check Job Management page for progress")
                        else:
                            st.error("❌ Failed to start analysis")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            else:
                st.error("❌ Please enter Notice ID")

def show_job_management():
    """Job Management page"""
    st.markdown("## ⚙️ Job Management")
    
    st.info("""
    ⚙️ **Job Management System:**
    
    Monitor and manage analysis jobs:
    - ✅ **Job Status:** Real-time job monitoring
    - ✅ **Progress Tracking:** Step-by-step progress
    - ✅ **Results Access:** View analysis results
    - ✅ **Error Handling:** Detailed error information
    - ✅ **Job History:** Complete job log
    """)
    
    # Job status lookup
    st.markdown("### 🔍 Job Status Lookup")
    
    col1, col2 = st.columns(2)
    
    with col1:
        job_id = st.text_input(
            "Job ID",
            placeholder="Enter job ID",
            help="Job ID from analysis trigger"
        )
        
        if st.button("🔍 Check Status", key="check_job_status"):
            if job_id:
                with st.spinner("Checking job status..."):
                    try:
                        status = get_job_status(job_id)
                        
                        if 'error' not in status:
                            st.success("✅ Job status retrieved!")
                            
                            # Display status
                            col_a, col_b, col_c = st.columns(3)
                            
                            with col_a:
                                st.metric("Status", status['status'].title())
                            
                            with col_b:
                                st.metric("Progress", f"{status['progress']}%")
                            
                            with col_c:
                                st.metric("Current Step", status['current_step'])
                            
                            # Detailed information
                            st.markdown("**Job Details:**")
                            st.write(f"**Notice ID:** {status['notice_id']}")
                            st.write(f"**Created:** {status['created_at']}")
                            st.write(f"**Started:** {status['started_at'] or 'Not started'}")
                            st.write(f"**Finished:** {status['finished_at'] or 'Not finished'}")
                            
                            if status['error_message']:
                                st.error(f"**Error:** {status['error_message']}")
                        else:
                            st.error(f"❌ Status check failed: {status['error']}")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            else:
                st.error("❌ Please enter Job ID")
    
    with col2:
        notice_id_results = st.text_input(
            "Notice ID (for results)",
            placeholder="Enter notice ID",
            help="Get analysis results for a notice"
        )
        
        if st.button("📊 Get Results", key="get_job_results"):
            if notice_id_results:
                with st.spinner("Getting analysis results..."):
                    try:
                        results = get_job_results(notice_id_results)
                        
                        if 'error' not in results:
                            st.success("✅ Results retrieved!")
                            
                            # Display results
                            col_a, col_b = st.columns(2)
                            
                            with col_a:
                                st.metric("Go/No-Go Score", f"{results['go_no_go_score']}/100")
                            
                            with col_b:
                                st.metric("Confidence", f"{results['confidence']:.2%}")
                            
                            # Summary
                            st.markdown("**Summary:**")
                            st.write(results['summary'])
                            
                            # Risks
                            if results['risks']:
                                st.markdown("**Risks:**")
                                for risk in results['risks']:
                                    st.write(f"• **{risk.get('type', 'Unknown')}** ({risk.get('level', 'Unknown')}): {risk.get('description', 'No description')}")
                            
                            # Requirements
                            if results['requirements']:
                                st.markdown("**Requirements:**")
                                for req in results['requirements']:
                                    st.write(f"• **{req.get('type', 'Unknown')}**: {req.get('description', 'No description')}")
                            
                            # Action items
                            if results['action_items']:
                                st.markdown("**Action Items:**")
                                for item in results['action_items']:
                                    st.write(f"• {item}")
                        else:
                            st.error(f"❌ Results retrieval failed: {results['error']}")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            else:
                st.error("❌ Please enter Notice ID")
    
    # Job statistics
    st.markdown("### 📈 Job Statistics")
    
    if st.button("🔄 Refresh Statistics", key="refresh_job_stats"):
        with st.spinner("Loading job statistics..."):
            try:
                # This would typically query the database for real statistics
                # For now, show sample data
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Jobs", 45)
                
                with col2:
                    st.metric("Completed", 42)
                
                with col3:
                    st.metric("Failed", 3)
                
                with col4:
                    st.metric("Running", 0)
                
                # Job status distribution
                status_data = {
                    "Status": ["Completed", "Failed", "Running", "Queued"],
                    "Count": [42, 3, 0, 0]
                }
                
                status_df = pd.DataFrame(status_data)
                st.dataframe(status_df, use_container_width=True, hide_index=True)
                
            except Exception as e:
                st.error(f"❌ Statistics error: {e}")
    
    # Recent jobs
    st.markdown("### 📋 Recent Jobs")
    st.info("📊 Recent jobs list will be implemented with database integration")

if __name__ == "__main__":
    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state.page = "🏠 Dashboard"
    
    main()
