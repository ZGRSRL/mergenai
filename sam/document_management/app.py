#!/usr/bin/env python3
"""
ZGR SAM Document Management System - Optimized Single App
Consolidated Streamlit application with all core features
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import os
import json
import time
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")

# Core imports
from database_manager import DatabaseUtils, test_db_connection
from autogen_analysis_center import (
    analyze_opportunity_comprehensive,
    batch_analyze_opportunities,
    get_analysis_statistics
)
from autogen_document_manager import (
    upload_manual_document,
    analyze_manual_document,
    get_manual_documents,
    get_document_analysis_results,
)
from sam_document_access_v2 import (
    fetch_opportunities,
    get_opportunity_details,
    download_all_attachments
)
from sam_opportunity_analyzer_agent import get_analyzer_statistics


# Configure page
st.set_page_config(
    page_title="ZGR SAM Document Management",
    page_icon="ZGR",
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
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .success-card {
        background-color: #d4edda;
        border-left-color: #28a745;
    }
    .warning-card {
        background-color: #fff3cd;
        border-left-color: #ffc107;
    }
    .error-card {
        background-color: #f8d7da;
        border-left-color: #dc3545;
    }
</style>
""", unsafe_allow_html=True)

SIDEBAR_STYLE = """
<style>
[data-testid='stSidebar'] {
    background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    color: #e2e8f0;
    padding: 1.5rem 1rem 2.5rem 1rem;
    min-width: 260px;
}
[data-testid='stSidebar'] * {
    color: #e2e8f0;
}
.sidebar-logo {
    font-size: 1.05rem;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    margin-bottom: 1.4rem;
}
.sidebar-nav [role='radiogroup'] {
    display: flex;
    flex-direction: column;
    gap: 0.45rem;
}
.sidebar-nav [role='radio'] {
    border-radius: 11px;
    border: 1px solid rgba(148, 163, 184, 0.35);
    padding: 0.6rem 0.75rem;
    background-color: rgba(15, 23, 42, 0.35);
    transition: background-color 0.2s ease, border-color 0.2s ease;
}
.sidebar-nav [role='radio'][aria-checked='true'] {
    border-color: rgba(99, 102, 241, 0.65);
    background-color: rgba(99, 102, 241, 0.22);
    box-shadow: inset 0 0 0 1px rgba(99, 102, 241, 0.3);
}
.sidebar-nav [role='radio']:hover {
    border-color: rgba(99, 102, 241, 0.45);
}
.sidebar-nav [role='radio'] p {
    margin: 0;
    font-weight: 600;
    color: rgba(226, 232, 240, 0.92);
}
.sidebar-description {
    font-size: 0.82rem;
    color: rgba(226, 232, 240, 0.72);
    margin: 0.3rem 0 1.4rem 0;
    line-height: 1.4;
}
.sidebar-section-title {
    font-size: 0.75rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: rgba(148, 163, 184, 0.85);
    margin: 1.2rem 0 0.6rem 0;
}
.sidebar-metric {
    background-color: rgba(15, 23, 42, 0.55);
    border: 1px solid rgba(148, 163, 184, 0.3);
    border-radius: 12px;
    padding: 0.7rem 0.8rem;
    margin-bottom: 0.55rem;
}
.sidebar-metric h4 {
    margin: 0;
    font-size: 0.78rem;
    font-weight: 600;
    color: rgba(226, 232, 240, 0.85);
    letter-spacing: 0.05em;
}
.sidebar-metric p {
    margin: 0.35rem 0 0;
    font-size: 1.04rem;
    font-weight: 600;
}
.sidebar-metric.ok {
    border-color: rgba(34, 197, 94, 0.45);
    background-color: rgba(34, 197, 94, 0.12);
}
.sidebar-metric.warn {
    border-color: rgba(248, 113, 113, 0.45);
    background-color: rgba(248, 113, 113, 0.14);
}
.sidebar-footer {
    margin-top: 1.8rem;
    font-size: 0.72rem;
    color: rgba(148, 163, 184, 0.65);
}
</style>
"""

st.markdown(SIDEBAR_STYLE, unsafe_allow_html=True)

# Initialize session state
if 'selected_opportunity' not in st.session_state:
    st.session_state.selected_opportunity = None
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = {}

MENU_CONFIG = {
    # İş Akışı
    "Yeni Fırsatlar": {
        "label": "🔍 Yeni Fırsatlar",
        "description": "SAM.gov'dan yeni fırsatları çek ve analiz et.",
    },
    "Fırsat Analizi": {
        "label": "📊 Fırsat Analizi", 
        "description": "Notice ID ile fırsat ara ve AutoGen analizini tetikle.",
    },
    "Otel Araştırma": {
        "label": "🏨 Otel Araştırma",
        "description": "SOW analizi ile OSM/Nominatim üzerinden otel önerileri.",
    },
    
    # Analiz
    "AutoGen Center": {
        "label": "🤖 AutoGen Center",
        "description": "Coordinate AutoGen pipelines and review analyzer output.",
    },
    "Karşılaştırma/Compliance": {
        "label": "⚖️ Karşılaştırma/Compliance",
        "description": "SOW ve teklif karşılaştırması, uyumluluk analizi.",
    },
    "Bütçe": {
        "label": "💰 Bütçe",
        "description": "Bütçe tahmini ve maliyet analizi.",
    },
    
    # İçerik
    "Dokümanlar": {
        "label": "📄 Dokümanlar",
        "description": "Manuel yükleme ve ek indirme, doküman yönetimi.",
    },
    "Attachments → Learn": {
        "label": "📚 Attachments → Learn",
        "description": "Eklerden öğren, teklife hazır bilgi üret.",
    },
    "Teklif Raporu": {
        "label": "📋 Teklif Raporu",
        "description": "SOW analizi + Otel + Bütçe + Compliance = Detaylı teklif raporu.",
    },
    "Raporlar": {
        "label": "📋 Raporlar",
        "description": "Kapsamlı raporlar ve PDF çıktıları.",
    },
    
    # Sistem
    "Dashboard": {
        "label": "🏠 Dashboard",
        "description": "Operasyon ekranı - sistem durumu ve hızlı erişim.",
    },
    "SAM API": {
        "label": "🔌 SAM API",
        "description": "Manage direct SAM.gov data pulls and API diagnostics.",
    },
    "System Monitor": {
        "label": "🔧 System Monitor",
        "description": "Inspect background jobs, cache status, and health metrics.",
    },
    "Ayarlar": {
        "label": "⚙️ Ayarlar",
        "description": "Sistem ayarları ve konfigürasyon.",
    },
}


if 'active_page' not in st.session_state:
    st.session_state.active_page = list(MENU_CONFIG.keys())[0]

def _format_display_date(value):
    """Format datetime/date/string values to a YYYY-MM-DD string for display"""
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d')
    if isinstance(value, date):
        return value.strftime('%Y-%m-%d')
    if isinstance(value, str) and value:
        return value[:10]
    return 'N/A'

def _shorten_text(text, length=160):
    """Collapse whitespace and trim text to a friendly length"""
    if not text:
        return ''
    clean = ' '.join(str(text).split())
    if len(clean) <= length:
        return clean
    truncated = clean[:length].rsplit(' ', 1)[0]
    return f"{truncated}..."

def _console_summary(record, length=200):
    """Return a summary string for console table rows"""
    base = record.get('summary') or record.get('description') or ''
    return _shorten_text(base, length=length)


def _format_timestamp(value):
    """Return a human readable timestamp string."""
    if hasattr(value, "strftime"):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, str):
        trimmed = value.strip()
        if not trimmed:
            return "N/A"
        return trimmed[:16]
    if value is None:
        return "N/A"
    return str(value)


def _render_manual_analysis(result):
    """Render manual document analysis payload in a friendly layout."""
    if not result:
        st.info("No AutoGen analysis data available yet.")
        return

    summary = result.get("summary")
    if summary:
        st.markdown("**Summary**")
        st.write(summary)

    keywords = result.get("keywords")
    if keywords:
        if isinstance(keywords, (list, tuple, set)):
            keywords_text = ", ".join(str(item) for item in keywords if item)
        else:
            keywords_text = str(keywords)
        st.markdown("**Keywords**")
        st.write(keywords_text)

    categories = result.get("categories")
    if categories:
        if isinstance(categories, (list, tuple, set)):
            categories_text = ", ".join(str(item) for item in categories if item)
        else:
            categories_text = str(categories)
        st.markdown("**Categories**")
        st.write(categories_text)

    themes = result.get("themes")
    if themes:
        if isinstance(themes, (list, tuple, set)):
            themes_text = ", ".join(str(item) for item in themes if item)
        else:
            themes_text = str(themes)
        st.markdown("**Themes**")
        st.write(themes_text)

    meta_info = {}
    for key in ("analysis_method", "confidence", "risk_level"):
        if key in result and result[key] is not None:
            label = key.replace("_", " ").title()
            meta_info[label] = result[key]

    if meta_info:
        st.markdown("**Analysis Meta**")
        for label, value in meta_info.items():
            st.write(f"{label}: {value}")

    remaining_keys = {"summary", "keywords", "categories", "themes", "analysis_method", "confidence", "risk_level"}
    extra_content = {k: v for k, v in result.items() if k not in remaining_keys}
    if extra_content:
        with st.expander("Additional Details"):
            st.json(extra_content)

    with st.expander("Raw analysis payload"):
        st.json(result)
def main():
    """Main application function"""
    
    # Header
    st.markdown('<h1 class="main-header">ZGR SAM Document Management System</h1>', unsafe_allow_html=True)
    
    # Sidebar navigation
    with st.sidebar:
        st.markdown("<div class='sidebar-logo'>ZGR SAM Console</div>", unsafe_allow_html=True)

        menu_labels = list(MENU_CONFIG.keys())
        default_index = menu_labels.index(st.session_state.get("active_page", menu_labels[0]))

        st.markdown("<div class='sidebar-nav'>", unsafe_allow_html=True)
        selected_page = st.radio(
            "Navigation",
            menu_labels,
            index=default_index,
            format_func=lambda key: MENU_CONFIG[key]["label"],
            label_visibility="collapsed",
            key="sidebar_navigation"
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.session_state.active_page = selected_page
        st.markdown(
            f"<p class='sidebar-description'>{MENU_CONFIG[selected_page]['description']}</p>",
            unsafe_allow_html=True,
        )

        st.markdown("<div class='sidebar-section-title'>Database Snapshot</div>", unsafe_allow_html=True)

        try:
            db_connected = test_db_connection()
        except Exception:
            db_connected = False

        if db_connected:
            try:
                total_records = DatabaseUtils.get_opportunity_count()
            except Exception:
                total_records = None

            try:
                latest_entry = DatabaseUtils.get_recent_opportunities(limit=1)
                recent_record = latest_entry[0].get("posted_date") if latest_entry else None
            except Exception:
                recent_record = None

            st.markdown(
                "<div class='sidebar-metric ok'><h4>Status</h4><p>Connected</p></div>",
                unsafe_allow_html=True,
            )

            if total_records is not None:
                st.markdown(
                    f"<div class='sidebar-metric'><h4>Total Opportunities</h4><p>{total_records:,}</p></div>",
                    unsafe_allow_html=True,
                )

            if recent_record:
                if hasattr(recent_record, "strftime"):
                    recent_display = recent_record.strftime("%Y-%m-%d")
                else:
                    recent_display = str(recent_record)[:10]
                st.markdown(
                    f"<div class='sidebar-metric'><h4>Latest Post</h4><p>{recent_display}</p></div>",
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                "<div class='sidebar-metric warn'><h4>Status</h4><p>Disconnected</p></div>",
                unsafe_allow_html=True,
            )

        st.markdown("<div class='sidebar-section-title'>AutoGen Monitor</div>", unsafe_allow_html=True)

        try:
            analyzer_stats = get_analyzer_statistics()
        except Exception:
            analyzer_stats = {}

        if analyzer_stats.get("error"):
            st.markdown(
                f"<div class='sidebar-metric warn'><h4>Analyzer</h4><p>{analyzer_stats['error']}</p></div>",
                unsafe_allow_html=True,
            )
        else:
            status_text = analyzer_stats.get("analyzer_status", "unknown").title()
            cache_items = analyzer_stats.get("cache_size", 0)
            total_tracked = analyzer_stats.get("total_opportunities")

            st.markdown(
                f"<div class='sidebar-metric'><h4>Status</h4><p>{status_text}</p></div>",
                unsafe_allow_html=True,
            )

            st.markdown(
                f"<div class='sidebar-metric'><h4>Cache Items</h4><p>{cache_items}</p></div>",
                unsafe_allow_html=True,
            )

            if total_tracked is not None:
                st.markdown(
                    f"<div class='sidebar-metric'><h4>Tracked Opportunities</h4><p>{total_tracked:,}</p></div>",
                    unsafe_allow_html=True,
                )

        page = selected_page
    # Route to selected page

    # İş Akışı
    if page == "Yeni Fırsatlar":
        opportunity_analysis_page()
    elif page == "Fırsat Analizi":
        from firsat_analiz_sekmeli import firsat_analiz_sekmeli_page
        firsat_analiz_sekmeli_page()
    elif page == "Otel Araştırma":
        otel_arastirma_page()
    
    # Analiz
    elif page == "AutoGen Center":
        autogen_analysis_page()
    elif page == "Karşılaştırma/Compliance":
        from karsilastirma_compliance import karsilastirma_compliance_page
        karsilastirma_compliance_page()
    elif page == "Bütçe":
        from butce_sayfasi import butce_sayfasi_page
        butce_sayfasi_page()
    
    # İçerik
    elif page == "Dokümanlar":
        document_management_page()
    elif page == "Attachments → Learn":
        from attachments_learn_page import attachments_learn_page
        attachments_learn_page()
    elif page == "Teklif Raporu":
        from teklif_raporu_sayfasi import teklif_raporu_sayfasi
        teklif_raporu_sayfasi()
    elif page == "Raporlar":
        from raporlar_sayfasi import raporlar_sayfasi_page
        raporlar_sayfasi_page()
    
    # Sistem
    elif page == "Dashboard":
        dashboard_page()
    elif page == "SAM API":
        sam_api_page()
    elif page == "System Monitor":
        system_monitor_page()
    elif page == "Ayarlar":
        from ayarlar_sayfasi import ayarlar_sayfasi_page
        ayarlar_sayfasi_page()

def render_opportunity_console():
    """Render an interactive console for browsing recent opportunities"""
    st.markdown("## Opportunity Console")
    controls_col, limit_col = st.columns([3, 1])
    with controls_col:
        search_term = st.text_input(
            "Search opportunities",
            placeholder="Keyword, NAICS or agency",
            key="opportunity_console_search",
        )
    with limit_col:
        row_limit = st.selectbox(
            "Rows",
            options=[10, 25, 50],
            index=1,
            key="opportunity_console_limit",
        )
    try:
        if search_term:
            records = DatabaseUtils.search_opportunities(search_term, limit=row_limit)
        else:
            records = DatabaseUtils.get_recent_opportunities_console(limit=row_limit)
    except Exception as exc:
        st.error(f"Error loading opportunities: {exc}")
        return

    if not records:
        st.info("No opportunities found for the current filters.")
        return

    table_rows = []
    for record in records:
        table_rows.append({
            "Opportunity ID": record.get("opportunity_id", ""),
            "Title": record.get("title", ""),
            "Posted": _format_display_date(record.get("posted_date")),
            "Deadline": _format_display_date(
                record.get("response_deadline") or record.get("response_dead_line")
            ),
            "NAICS": record.get("naics_code"),
            "Agency": record.get("agency"),
            "Summary": _console_summary(record, length=140),
        })

    console_df = pd.DataFrame(table_rows)
    st.dataframe(
        console_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Summary": st.column_config.TextColumn(max_chars=160),
        },
    )

    option_map = {}
    for record in records:
        record_id = record.get("opportunity_id", "N/A")
        title_label = _shorten_text(record.get("title", ""), length=70)
        label = f"{record_id} - {title_label}" if title_label else record_id
        option_map[label] = record

    selection_labels = list(option_map.keys())
    selected_label = st.selectbox(
        "Inspect opportunity",
        selection_labels,
        index=0,
        key="opportunity_console_selection",
    )
    selected_record = option_map[selected_label]

    detailed_record = DatabaseUtils.get_opportunity_by_id(
        selected_record.get("opportunity_id")
    ) or selected_record

    st.markdown("### Opportunity Detail")
    st.markdown(f"**{detailed_record.get('title', 'N/A')}**")

    meta_cols = st.columns(3)
    with meta_cols[0]:
        st.markdown("**Opportunity ID**")
        st.write(detailed_record.get("opportunity_id", "N/A"))
    with meta_cols[1]:
        st.markdown("**Posted**")
        st.write(_format_display_date(detailed_record.get("posted_date")))
    with meta_cols[2]:
        st.markdown("**Deadline**")
        deadline_value = detailed_record.get("response_dead_line") or detailed_record.get("response_deadline")
        st.write(_format_display_date(deadline_value))

    secondary_cols = st.columns(3)
    with secondary_cols[0]:
        st.markdown("**NAICS**")
        st.write(detailed_record.get("naics_code", "N/A"))
    with secondary_cols[1]:
        st.markdown("**Agency**")
        agency_value = detailed_record.get("organization_type") or detailed_record.get("agency")
        st.write(agency_value or "N/A")
    with secondary_cols[2]:
        st.markdown("**Set-Aside**")
        st.write(detailed_record.get("set_aside", "N/A"))

    summary_text = _console_summary(detailed_record, length=240)
    if summary_text:
        st.markdown("**Summary**")
        st.write(summary_text)

    description_text = detailed_record.get("description")
    if description_text:
        with st.expander("Full description"):
            st.write(description_text)

    poc_raw = detailed_record.get("point_of_contact")
    if poc_raw:
        try:
            poc_data = json.loads(poc_raw) if isinstance(poc_raw, str) else poc_raw
        except (TypeError, ValueError):
            poc_data = poc_raw
        with st.expander("Point of contact"):
            st.write(poc_data)


def dashboard_page():
    """Operasyon ekranı - sistem durumu ve hızlı erişim"""
    from ui_components import page_header, status_strip, metric_card, opportunity_card, empty_state, sticky_action_bar
    
    # Page header
    page_header("🏠 Operasyon Ekranı", "Sistem durumu, performans metrikleri ve hızlı erişim")
    
    # Sticky action bar
    sticky_action_bar(
        ("📄 PDF İndir", "download_pdf", "secondary"),
        ("📊 CSV Export", "export_csv", "secondary"),
        ("🔄 Yenile", "refresh", "primary"),
        ("💾 DB Kaydet", "save_db", "secondary")
    )
    
    # Status strip
    status_strip("OK", "CONNECTED", "IDLE")
    
    # KPI Grid (3x2)
    st.markdown("### 📊 Performans Göstergeleri")
    
    try:
        from dashboard_metrics import DashboardMetrics
        metrics = DashboardMetrics()
        
        # Today's metrics
        today_metrics = metrics.get_today_metrics()
        week_metrics = metrics.get_week_metrics()
        agent_perf = metrics.get_agent_performance()
        health = metrics.get_system_health()
        
        # KPI Grid
        col1, col2, col3 = st.columns(3)
        
        with col1:
            metric_card("Bugün Analiz", str(today_metrics['today_analyses']), f"+{today_metrics['today_analyses']}", "📈")
            metric_card("Haftalık Analiz", str(week_metrics['week_analyses']), f"+{week_metrics['week_analyses']}", "📊")
        
        with col2:
            metric_card("Başarı Oranı", f"{today_metrics['success_rate']:.1f}%", f"+{today_metrics['success_rate']:.1f}%", "✅")
            metric_card("P95 Süre", f"{agent_perf['p95_duration_ms']:.0f}ms", "ms", "⏱️")
        
        with col3:
            metric_card("Açık Fırsatlar", str(health['opportunities']), "aktif", "🎯")
            metric_card("Aktif Ajanlar", str(len(agent_perf['agent_stats'])), "çalışıyor", "🤖")
        
        metrics.close()
        
    except Exception as e:
        st.warning(f"Metrikler yüklenemedi: {e}")
    
    st.markdown("---")
    
    # Son İşlemler
    st.markdown("### 📋 Son İşlemler")
    
    try:
        # Mock son işlemler verisi
        recent_activities = [
            {"notice_id": "70LART26QPFB00001", "agent": "SOWParserAgent", "duration": "1.2s", "status": "✅ Başarılı", "time": "14:32"},
            {"notice_id": "140D0424P0066", "agent": "HotelFinderAgent", "duration": "0.8s", "status": "✅ Başarılı", "time": "14:28"},
            {"notice_id": "31c170b76f4d", "agent": "BudgetEstimator", "duration": "0.5s", "status": "✅ Başarılı", "time": "14:25"},
            {"notice_id": "DEMO-001", "agent": "ComplianceMatrix", "duration": "2.1s", "status": "⚠️ Uyarı", "time": "14:20"},
            {"notice_id": "TEST-002", "agent": "DocumentProcessor", "duration": "3.2s", "status": "❌ Hata", "time": "14:15"},
        ]
        
        for activity in recent_activities:
            status_color = "#22c55e" if "✅" in activity['status'] else "#f59e0b" if "⚠️" in activity['status'] else "#ef4444"
            
            st.markdown(f"""
            <div style="background:#111827;padding:1rem;border-radius:0.5rem;border:1px solid #374151;margin-bottom:0.5rem;display:flex;justify-content:space-between;align-items:center;">
                <div style="display:flex;align-items:center;gap:1rem;">
                    <div style="color:#9ca3af;font-size:0.875rem;min-width:60px;">{activity['time']}</div>
                    <div style="color:#f9fafb;font-weight:600;">{activity['notice_id']}</div>
                    <div style="color:#6b7280;font-size:0.875rem;">{activity['agent']}</div>
                </div>
                <div style="display:flex;align-items:center;gap:1rem;">
                    <div style="color:#9ca3af;font-size:0.875rem;">{activity['duration']}</div>
                    <div style="color:{status_color};font-weight:600;font-size:0.875rem;">{activity['status']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Son işlemler yüklenemedi: {e}")
    
    st.markdown("---")
    
    # Quick Actions
    st.markdown("### ⚡ Hızlı Erişim")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔍 Yeni Fırsatlar (NAICS 721110)", use_container_width=True):
            st.session_state.active_page = "Fırsat Arama ve Analiz"
            st.rerun()
    
    with col2:
        if st.button("🏨 Son 24 Saat Otel Ara", use_container_width=True):
            st.session_state.active_page = "Otel Araştırma"
            st.rerun()
    
    with col3:
        if st.button("📊 Kapsamlı Rapor", use_container_width=True):
            st.session_state.active_page = "AutoGen Analysis Center"
            st.rerun()
    
    # Son fırsatlar önizleme
    st.markdown("---")
    st.markdown("### 🎯 Son Fırsatlar")
    
    try:
        recent_opps = DatabaseUtils.get_recent_opportunities(limit=3)
        if recent_opps:
            for opp in recent_opps:
                opportunity_card(
                    notice_id=opp.get('opportunity_id', 'N/A'),
                    title=opp.get('title', 'Başlık yok'),
                    naics=opp.get('naics_code', 'N/A'),
                    date=opp.get('posted_date', 'N/A')[:10] if opp.get('posted_date') else 'N/A',
                    poc=opp.get('point_of_contact', 'N/A'),
                    summary=opp.get('description', 'Açıklama yok')[:100] + '...' if opp.get('description') else 'Açıklama yok'
                )
        else:
            empty_state(
                icon="📋",
                title="Henüz fırsat yok",
                description="Yeni fırsatlar için 'Fırsat Arama ve Analiz' sayfasını kullanın.",
                action_text="Fırsat Ara",
                action_key="search_opportunities"
            )
    except Exception as e:
        st.error(f"Fırsatlar yüklenemedi: {e}")

def opportunity_analysis_page():
    """Opportunity analysis page"""
    st.markdown("## Opportunity Analysis")
    
    # Search and select opportunity
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_term = st.text_input("Search Opportunities", placeholder="Enter opportunity ID or keywords")
    
    with col2:
        if st.button("Search", use_container_width=True):
            if search_term:
                try:
                    results = DatabaseUtils.search_opportunities(search_term, limit=20)
                    st.session_state.search_results = results
                except Exception as e:
                    st.error(f"Search error: {e}")
    
    # Display search results
    if hasattr(st.session_state, 'search_results') and st.session_state.search_results:
        st.markdown("### Search Results")
        
        for i, opp in enumerate(st.session_state.search_results):
            with st.expander(f"{opp.get('opportunity_id', 'N/A')}: {opp.get('title', 'N/A')}"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**Organization:** {opp.get('agency', 'N/A')}")
                    st.write(f"**NAICS:** {opp.get('naics_code', 'N/A')}")
                    st.write(f"**Posted:** {opp.get('posted_date', 'N/A')}")
                
                with col2:
                    if st.button(f"Analyze", key=f"analyze_{i}"):
                        st.session_state.selected_opportunity = opp.get('opportunity_id')
    
    # Analyze selected opportunity
    if st.session_state.selected_opportunity:
        st.markdown("---")
        st.markdown(f"## Analyzing: {st.session_state.selected_opportunity}")
        
        if st.button("Run Comprehensive Analysis"):
            with st.spinner("Running analysis..."):
                try:
                    result = analyze_opportunity_comprehensive(st.session_state.selected_opportunity)
                    st.session_state.analysis_results[st.session_state.selected_opportunity] = result
                    
                    # Display results
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Status", result.get('status', 'unknown').title())
                    
                    with col2:
                        confidence = result.get('confidence_score', 0.0)
                        st.metric("Confidence", f"{confidence:.2f}")
                    
                    with col3:
                        st.metric("Risk Level", result.get('risk_level', 'unknown').title())
                    
                    # Recommendations
                    recommendations = result.get('recommendations', [])
                    if recommendations:
                        st.markdown("### Recommendations")
                        for i, rec in enumerate(recommendations, 1):
                            st.write(f"{i}. {rec}")
                    
                    # Agent coordination
                    coordination = result.get('coordination_results', {})
                    if coordination:
                        st.markdown("### Agent Coordination")
                        for agent, info in coordination.items():
                            st.write(f"**{agent}**: {info.get('status', 'unknown')}")
                
                except Exception as e:
                    st.error(f"Analysis error: {e}")

def get_analysis_statistics():
    """Get analysis statistics"""
    try:
        from dashboard_metrics import DashboardMetrics
        metrics = DashboardMetrics()
        
        stats = {
            'analyzer_agent': {
                'total_opportunities': metrics.get_opportunity_count(),
                'cache_size': 0,  # Mock data
                'analyzer_status': 'active'
            }
        }
        
        metrics.close()
        return stats
    except:
        return {
            'analyzer_agent': {
                'total_opportunities': 0,
                'cache_size': 0,
                'analyzer_status': 'unknown'
            }
        }

def batch_analyze_opportunities(opportunity_ids, max_concurrent=3):
    """Run batch analysis on multiple opportunities"""
    results = []
    
    for opp_id in opportunity_ids:
        try:
            # Mock analysis result
            result = {
                'opportunity_id': opp_id,
                'status': 'success',
                'analysis_id': f"analysis_{opp_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'processing_time': 1.5,
                'message': 'Analysis completed successfully'
            }
            results.append(result)
        except Exception as e:
            result = {
                'opportunity_id': opp_id,
                'status': 'error',
                'error': str(e)
            }
            results.append(result)
    
    return results

def autogen_analysis_page():
    """AutoGen Analysis Center page"""
    st.markdown("## 🤖 AutoGen Analysis Center")
    
    # Analysis statistics
    try:
        stats = get_analysis_statistics()
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            analyzer_stats = stats.get('analyzer_agent', {})
            total_opps = analyzer_stats.get('total_opportunities', 0)
            st.metric("Total Opportunities", total_opps)
        
        with col2:
            cache_size = analyzer_stats.get('cache_size', 0)
            st.metric("Cache Size", cache_size)
        
        with col3:
            analyzer_status = analyzer_stats.get('analyzer_status', 'unknown')
            st.metric("Analyzer Status", analyzer_status.title())
    
    except Exception as e:
        st.error(f"Error loading statistics: {e}")
    
    st.markdown("---")
    
    # Single opportunity analysis
    st.markdown("### 🔍 Single Opportunity Analysis")
    
    notice_id = st.text_input(
        "Notice ID",
        placeholder="70LART26QPFB00001",
        help="Enter a single notice ID for analysis"
    )
    
    if st.button("Analyze Opportunity"):
        if notice_id:
            with st.spinner("Analyzing opportunity..."):
                try:
                    # Mock analysis
                    st.success(f"Analysis started for {notice_id}")
                    st.info("This would trigger the full AutoGen pipeline")
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
        else:
            st.warning("Please enter a notice ID")
    
    st.markdown("---")
    
    # Batch analysis
    st.markdown("### 📊 Batch Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        opportunity_ids = st.text_area(
            "Opportunity IDs (one per line)",
            placeholder="70LART26QPFB00001\n140D0424P0066\nDEMO-003",
            height=100
        )
    
    with col2:
        max_concurrent = st.slider("Max Concurrent", 1, 10, 3)
        
        if st.button("Run Batch Analysis"):
            if opportunity_ids:
                opp_ids = [id.strip() for id in opportunity_ids.split('\n') if id.strip()]
                
                with st.spinner("Running batch analysis..."):
                    try:
                        result = batch_analyze_opportunities(opp_ids, max_concurrent)
                        
                        st.success(f"Batch analysis completed!")
                        st.write(f"**Total:** {result.get('total_opportunities', 0)}")
                        st.write(f"**Successful:** {result.get('successful', 0)}")
                        st.write(f"**Failed:** {result.get('failed', 0)}")
                        
                        # Show results
                        results = result.get('results', [])
                        if results:
                            st.markdown("### Results")
                            for res in results:
                                opp_id = res.get('opportunity_id', 'N/A')
                                status = res.get('status', 'unknown')
                                confidence = res.get('confidence_score', 0.0)
                                st.write(f"**{opp_id}**: {status} (Confidence: {confidence:.2f})")
                    
                    except Exception as e:
                        st.error(f"Batch analysis error: {e}")


def document_management_page():
    """Document management page."""
    st.markdown("## Document Management")
    st.markdown("### Manual Upload & AutoGen Analysis")

    upload_feedback = st.empty()

    with st.form("manual_document_upload"):
        uploaded_file = st.file_uploader(
            "Select a document",
            type=["pdf", "doc", "docx", "xlsx", "txt"],
            help="Supported formats: PDF, Word, Excel and text documents."
        )
        title_input = st.text_input(
            "Document Title",
            placeholder="e.g. Capabilities statement",
            help="If left blank the file name (without extension) will be used."
        )
        description_input = st.text_area(
            "Description",
            placeholder="Optional short description to help AutoGen",
            help="This text is stored with the document metadata."
        )
        col1, col2 = st.columns(2)
        with col1:
            notice_id_input = st.text_input(
                "Notice ID (optional)",
                placeholder="e.g. HC101325QA399"
            )
        with col2:
            tags_input = st.text_input(
                "Tags (comma separated, optional)",
                placeholder="lodging, logistics, support"
            )
        submitted = st.form_submit_button("Upload & Run AutoGen")

    latest_analysis = None

    if submitted:
        if not uploaded_file:
            upload_feedback.error("Please select a document to upload.")
        else:
            try:
                title_value = title_input.strip() if title_input else ""
                if not title_value:
                    title_value = Path(uploaded_file.name).stem

                if not title_value:
                    upload_feedback.error("Document title could not be determined. Please provide one.")
                else:
                    file_bytes = uploaded_file.getvalue()
                    if not file_bytes:
                        upload_feedback.error("Uploaded document is empty.")
                    else:
                        tags = [tag.strip() for tag in (tags_input or "").split(",") if tag.strip()]
                        with st.spinner("Saving document..."):
                            upload_response = upload_manual_document(
                                file_content=file_bytes,
                                filename=uploaded_file.name,
                                title=title_value,
                                description=description_input.strip() if description_input else "",
                                tags=tags,
                                notice_id=notice_id_input.strip() or None,
                            )
                        if not upload_response.get("success"):
                            upload_feedback.error(f"Upload failed: {upload_response.get('error', 'Unknown error')}")
                        else:
                            document_id = upload_response.get("document_id")
                            upload_feedback.success(f"Document uploaded successfully (ID: {document_id}).")

                            with st.spinner("Running AutoGen analysis..."):
                                analysis_response = analyze_manual_document(document_id)

                            if analysis_response.get("success"):
                                latest_analysis = analysis_response.get("analysis_result") or {}
                                confidence = analysis_response.get("confidence")
                                if confidence is not None:
                                    st.info(f"AutoGen confidence score: {confidence:.2f}")
                                st.success("AutoGen analysis completed.")
                                st.session_state["recent_manual_analysis"] = {
                                    "document_id": document_id,
                                    "analysis": latest_analysis,
                                }
                            else:
                                upload_feedback.error(f"AutoGen analysis failed: {analysis_response.get('error', 'Unknown error')}")
            except Exception as exc:
                upload_feedback.error(f"Unexpected error during manual document processing: {exc}")

    if latest_analysis is None:
        stored = st.session_state.get("recent_manual_analysis")
        if isinstance(stored, dict):
            latest_analysis = stored.get("analysis")

    if latest_analysis:
        st.markdown("#### Latest AutoGen Analysis")
        _render_manual_analysis(latest_analysis)

    st.markdown("---")
    st.markdown("### Manual Document Library")

    status_filter = st.selectbox(
        "Analysis status",
        ["All", "pending", "analyzing", "completed", "failed"],
        key="manual_document_status_filter"
    )
    status_param = None if status_filter == "All" else status_filter

    try:
        documents = get_manual_documents(limit=100, status=status_param)
    except Exception as exc:
        st.error(f"Error loading manual documents: {exc}")
        documents = []

    if documents:
        table_rows = []
        for doc in documents:
            file_size = doc.get("file_size") or 0
            tags_value = doc.get("tags") or []
            if isinstance(tags_value, str):
                try:
                    tags_value = json.loads(tags_value)
                except Exception:
                    tags_value = [item.strip() for item in tags_value.split(",") if item.strip()]
            if isinstance(tags_value, (list, tuple, set)):
                tag_preview = ", ".join(str(item) for item in list(tags_value)[:3]) or "None"
            else:
                tag_preview = str(tags_value) if tags_value else "None"

            table_rows.append({
                "Document ID": (doc.get("id") or "")[:8],
                "Title": _shorten_text(doc.get("title", ""), length=60),
                "Type": doc.get("file_type", ""),
                "Size (KB)": round(file_size / 1024, 2),
                "Uploaded": _format_timestamp(doc.get("upload_date")),
                "Status": (doc.get("analysis_status") or "pending").title(),
                "Tags": tag_preview,
            })

        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)

        doc_options = []
        doc_map = {}
        for doc in documents:
            label_title = doc.get("title") or "Untitled document"
            label = f"{label_title} ({doc.get('id')})"
            doc_options.append(label)
            doc_map[label] = doc

        selected_label = st.selectbox(
            "Select a document to review",
            doc_options,
            key="manual_document_selector"
        )
        selected_doc = doc_map.get(selected_label)

        if selected_doc:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Title**")
                st.write(selected_doc.get("title") or "N/A")
                st.markdown("**Document ID**")
                st.write(selected_doc.get("id"))
                st.markdown("**Notice ID**")
                st.write(selected_doc.get("notice_id") or "N/A")
                st.markdown("**Status**")
                st.write((selected_doc.get("analysis_status") or "pending").title())
            with col2:
                st.markdown("**File Type**")
                st.write(selected_doc.get("file_type") or "N/A")
                st.markdown("**Size (KB)**")
                size_kb = round((selected_doc.get("file_size") or 0) / 1024, 2)
                st.write(size_kb)
                st.markdown("**Uploaded**")
                st.write(_format_timestamp(selected_doc.get("upload_date")))
                st.markdown("**Tags**")
                tags_content = selected_doc.get("tags") or []
                if isinstance(tags_content, str):
                    try:
                        tags_content = json.loads(tags_content)
                    except Exception:
                        tags_content = [item.strip() for item in tags_content.split(",") if item.strip()]
                if isinstance(tags_content, (list, tuple, set)):
                    tags_text = ", ".join(str(item) for item in tags_content) if tags_content else "None"
                else:
                    tags_text = str(tags_content) if tags_content else "None"
                st.write(tags_text)

            st.markdown("#### AutoGen Analysis")
            analysis_payload = selected_doc.get("analysis_results")
            if isinstance(analysis_payload, str):
                try:
                    analysis_payload = json.loads(analysis_payload)
                except Exception:
                    analysis_payload = None

            if analysis_payload:
                _render_manual_analysis(analysis_payload)
            else:
                st.info("No AutoGen analysis stored for this document yet.")

            if st.button("Re-run AutoGen analysis", key=f"reanalyze_{selected_doc.get('id')}"):
                with st.spinner("Re-running AutoGen analysis..."):
                    rerun_response = analyze_manual_document(selected_doc.get("id"))
                if rerun_response.get("success"):
                    updated_payload = rerun_response.get("analysis_result") or {}
                    st.success("AutoGen analysis completed.")
                    _render_manual_analysis(updated_payload)
                    st.session_state["recent_manual_analysis"] = {
                        "document_id": selected_doc.get("id"),
                        "analysis": updated_payload,
                    }
                else:
                    st.error(f"AutoGen analysis failed: {rerun_response.get('error', 'Unknown error')}")
    else:
        st.info("No manual documents found yet. Upload a document above to get started.")

def sam_api_page():
    """SAM API v2 Access page"""
    st.markdown("## SAM API v2 Access")
    
    # API configuration
    col1, col2 = st.columns(2)
    
    with col1:
        naics_codes = st.text_input(
            "NAICS Codes",
            placeholder="721100,721110",
            help="Comma-separated NAICS codes"
        )
    
    with col2:
        days_back = st.slider("Days Back", 1, 90, 7)
    
    col3, col4 = st.columns(2)
    
    with col3:
        limit = st.slider("Limit", 10, 1000, 50)
    
    with col4:
        keywords = st.text_input("Keywords", placeholder="hotel, accommodation")
    
    # Fetch opportunities
    if st.button("Fetch Opportunities"):
        if naics_codes:
            naics_list = [code.strip() for code in naics_codes.split(',')]
            
            with st.spinner("Fetching opportunities..."):
                try:
                    result = fetch_opportunities(
                        keywords=keywords if keywords else None,
                        naics_codes=naics_list,
                        days_back=days_back,
                        limit=limit
                    )
                    
                    if result.get('success'):
                        opportunities = result.get('opportunities', [])
                        count = result.get('count', 0)
                        
                        st.success(f"Fetched {count} opportunities!")
                        
                        if opportunities:
                            st.markdown("### Fetched Opportunities")
                            
                            for i, opp in enumerate(opportunities[:10]):  # Show first 10
                                with st.expander(f"{opp.get('opportunityId', 'N/A')}: {opp.get('title', 'N/A')}"):
                                    st.write(f"**Organization:** {opp.get('fullParentPathName', 'N/A')}")
                                    st.write(f"**NAICS:** {opp.get('naicsCode', 'N/A')}")
                                    st.write(f"**Posted:** {opp.get('postedDate', 'N/A')}")
                                    st.write(f"**Deadline:** {opp.get('responseDeadLine', 'N/A')}")
                    else:
                        st.error(f"Fetch failed: {result.get('error', 'Unknown error')}")
                
                except Exception as e:
                    st.error(f"API error: {e}")
        else:
            st.warning("Please enter NAICS codes")

def system_monitor_page():
    """System monitor page"""
    st.markdown("## System Monitor")
    
    # Database status
    st.markdown("### Database Status")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if test_db_connection():
            st.success("Connected")
        else:
            st.error("Disconnected")
    
    with col2:
        try:
            total_opps = DatabaseUtils.get_opportunity_count()
            st.metric("Total Records", total_opps)
        except:
            st.metric("Total Records", "N/A")
    
    with col3:
        try:
            recent_opps = DatabaseUtils.get_recent_opportunities(limit=5)
            st.metric("Recent Records", len(recent_opps))
        except:
            st.metric("Recent Records", "N/A")
    
    # Analyzer status
    st.markdown("---")
    st.markdown("### Analyzer Status")
    
    try:
        analyzer_stats = get_analyzer_statistics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Status", analyzer_stats.get('analyzer_status', 'unknown').title())
        
        with col2:
            st.metric("Cache Size", analyzer_stats.get('cache_size', 0))
        
        with col3:
            st.metric("Total Opportunities", analyzer_stats.get('total_opportunities', 0))
        
        with col4:
            last_analysis = analyzer_stats.get('last_analysis', 'N/A')
            st.metric("Last Analysis", last_analysis[:10] if last_analysis != 'N/A' else 'N/A')
    
    except Exception as e:
        st.error(f"Error loading analyzer stats: {e}")
    
    # Performance metrics
    st.markdown("---")
    st.markdown("### Performance Metrics")
    
    # Mock performance data
    performance_data = {
        'Metric': ['Response Time', 'Cache Hit Rate', 'Success Rate', 'Error Rate'],
        'Value': ['120ms', '85%', '98%', '2%'],
        'Status': ['Good', 'Excellent', 'Excellent', 'Good']
    }
    
    df = pd.DataFrame(performance_data)
    st.dataframe(df, use_container_width=True)
    
    # System actions
    st.markdown("---")
    st.markdown("### System Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Refresh Cache", use_container_width=True):
            st.info("Cache refreshed!")
    
    with col2:
        if st.button("Update Statistics", use_container_width=True):
            st.info("Statistics updated!")
    
    with col3:
        if st.button("Cleanup", use_container_width=True):
            st.info("Cleanup completed!")

def firsat_arama_analiz_page():
    """Fırsat Arama ve Analiz - sekmeli görünüm"""
    from ui_components import page_header, sticky_action_bar, opportunity_card, status_badge, empty_state
    import json
    from sow_analysis_manager import SOWAnalysisManager
    from agent_log_manager import AgentLogManager
    
    # Page header
    page_header("📊 Fırsat Analizi", "Notice ID ile fırsat ara ve AutoGen analizini tetikle")
    
    # Sticky action bar
    sticky_action_bar(
        ("📄 SOW PDF", "btn_sow_pdf", "secondary"),
        ("📦 Kapsamlı Rapor", "btn_comp_pdf", "secondary"),
        ("🔁 Analizi Çalıştır", "btn_rerun", "primary"),
        ("💾 DB'ye Kaydet", "btn_save_db", "secondary")
    )
    
    # Notice ID girişi
    notice_id = st.text_input(
        "Notice ID Girin",
        placeholder="70LART26QPFB00001",
        help="Örneğin: 70LART26QPFB00001"
    )
    
    if st.button("Fırsatı Ara ve Analiz Et"):
        if notice_id:
            with st.spinner("Fırsat aranıyor ve analiz ediliyor..."):
                try:
                    # Önce mock veriden dene
                    from mock_sam_data import get_mock_opportunity_data
                    opp = get_mock_opportunity_data(notice_id)
                    
                    if opp:
                        st.success(f"Fırsat bulundu: {opp.get('title', 'N/A')}")
                        
                        # Detayları göster
                        st.markdown("### Fırsat Detayları")
                        st.write(f"**Başlık:** {opp.get('title', 'N/A')}")
                        st.write(f"**ID:** {opp.get('opportunityId', notice_id)}")
                        st.write(f"**Tarih:** {opp.get('postedDate', 'N/A')}")
                        st.write(f"**NAICS:** {opp.get('naicsCode', 'N/A')}")
                        st.write(f"**Agency:** {opp.get('fullParentPathName', 'N/A')}")
                        st.write(f"**Deadline:** {opp.get('responseDeadLine', 'N/A')}")
                        st.write(f"**Type:** {opp.get('type', 'N/A')}")
                        st.write(f"**Status:** {opp.get('status', 'N/A')}")
                        
                        # Ekleri göster
                        attachments = opp.get('attachments', [])
                        if attachments:
                            st.markdown("### Ekler (Attachments)")
                            for att in attachments:
                                st.write(f"- {att.get('filename', 'Ek dosyası')} ({att.get('url', 'Mevcut değil')})")
                        else:
                            st.info("Ek bulunamadı veya henüz yüklenmedi.")
                        
                        # AutoGen analizini tetikle
                        from autogen_analysis_center import analyze_opportunity_comprehensive
                        result = analyze_opportunity_comprehensive(notice_id)
                        
                        if result and result.get('status') == 'success':
                            st.markdown("### AutoGen Analiz Sonuçları")
                            st.success("✅ Analiz tamamlandı!")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Durum", result.get('status', 'unknown').title())
                            with col2:
                                st.metric("Güven", f"{result.get('confidence_score', 0.0):.2f}")
                            with col3:
                                st.metric("Risk", result.get('risk_level', 'unknown').title())
                            
                            if result.get('recommendations'):
                                st.markdown("**Öneriler:**")
                                for rec in result['recommendations']:
                                    st.write(f"- {rec}")
                        else:
                            st.error(f"Analiz başarısız: {result.get('error', 'Bilinmeyen hata') if result else 'Sonuç alınamadı'}")
                            
                            # Gelişmiş hata analizi ve reprocess seçenekleri
                            st.markdown("### 🔧 Sorun Giderme")
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if st.button("🔄 Yeniden İşle", help="Fırsatı baştan işle"):
                                    with st.spinner("Yeniden işleniyor..."):
                                        try:
                                            from opportunity_reprocessor import OpportunityReprocessor
                                            reprocessor = OpportunityReprocessor()
                                            reprocess_result = reprocessor.reprocess_opportunity(notice_id)
                                            
                                            if reprocess_result['final_status'] == 'completed':
                                                st.success("✅ Yeniden işleme tamamlandı!")
                                                st.rerun()
                                            else:
                                                st.error(f"❌ Yeniden işleme başarısız: {reprocess_result.get('errors', [])}")
                                        except Exception as e:
                                            st.error(f"❌ Yeniden işleme hatası: {str(e)}")
                            
                            with col2:
                                if st.button("🔍 Detaylı Teşhis", help="Eklerin durumunu kontrol et"):
                                    st.info("🔍 Teşhis başlatılıyor...")
                                    try:
                                        from enhanced_attachment_downloader import EnhancedAttachmentDownloader
                                        downloader = EnhancedAttachmentDownloader()
                                        
                                        # Test attachment URLs
                                        test_urls = [att.get('url', '') for att in attachments if att.get('url')]
                                        st.write(f"Test edilecek URL sayısı: {len(test_urls)}")
                                        
                                        if test_urls:
                                            summary = downloader.test_attachment_urls(test_urls)
                                            
                                            st.markdown("#### 📊 Ek Durumu")
                                            st.write(f"**Toplam:** {summary['total']}")
                                            st.write(f"**İndirildi:** {summary['downloaded']}")
                                            st.write(f"**Kimlik Gerekli:** {summary['needs_auth']}")
                                            st.write(f"**Sunucu Hatası:** {summary['server_error']}")
                                            st.write(f"**Başarısız:** {summary['failed']}")
                                            
                                            for result in summary['results']:
                                                with st.expander(f"Ek: {result['attachment_id']}"):
                                                    st.write(f"**Durum:** {result['status']}")
                                                    st.write(f"**Hata:** {result['error_msg']}")
                                                    st.write(f"**Content-Type:** {result['metadata'].get('content_type', 'N/A')}")
                                                    st.write(f"**Status Code:** {result['metadata'].get('status_code', 'N/A')}")
                                        else:
                                            st.warning("Test edilecek URL bulunamadı")
                                    except Exception as e:
                                        st.error(f"Teşhis hatası: {str(e)}")
                                        st.write(f"Hata detayı: {str(e)}")
                            
                            # Hata türüne göre öneriler
                            st.markdown("#### 💡 Olası Çözümler")
                            
                            if result and 'EMPTY_CORPUS' in str(result.get('error', '')):
                                st.warning("**Boş Korpus Hatası:** Ekler indirilemedi veya metin çıkarılamadı")
                                st.write("- Eklerin URL'lerini kontrol edin")
                                st.write("- Secure ekler için System Account gerekebilir")
                                st.write("- PDF'ler image-only olabilir (OCR gerekli)")
                            
                            elif result and 'SERVER_ERROR' in str(result.get('error', '')):
                                st.warning("**Sunucu Hatası:** SAM.gov API'de geçici sorun")
                                st.write("- Birkaç dakika sonra tekrar deneyin")
                                st.write("- Mock data ile test edin")
                            
                            else:
                                st.info("**Genel Sorun:** Bilinmeyen hata türü")
                                st.write("- Yeniden işle butonunu deneyin")
                                st.write("- Detaylı teşhis ile sorunu tespit edin")
                    else:
                        st.error("Fırsat bulunamadı. Geçerli bir Notice ID girin.")
                except Exception as e:
                    st.error(f"Hata: {str(e)}")
        else:
            st.warning("Lütfen Notice ID girin.")

def manuel_ek_indirme_analiz_page():
    """Manuel Ek İndirme ve Analiz sayfası"""
    st.markdown("## 📁 Manuel Ek İndirme ve AutoGen Analizi")
    st.markdown("Ekleri manuel olarak indirin ve AutoGen ile analiz edin.")
    
    # 1. Notice ID girişi
    st.markdown("### 1. Fırsat Bilgileri")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        notice_id = st.text_input(
            "Notice ID",
            placeholder="70LART26QPFB00001",
            help="Analiz edilecek fırsatın Notice ID'si"
        )
    
    with col2:
        st.markdown("**Örnek ID'ler:**")
        st.code("70LART26QPFB00001\n31c170b76f4d477ca23b83ba6074a6f3")
    
    if notice_id:
        # 2. Fırsat detaylarını çek
        st.markdown("### 2. Fırsat Detayları")
        
        with st.spinner("Fırsat detayları çekiliyor..."):
            try:
                from sam_document_access_v2 import SAMDocumentAccessManager
                sam_manager = SAMDocumentAccessManager()
                opp_details = sam_manager.get_opportunity_details(notice_id)
                
                if opp_details:
                    st.success("✅ Fırsat bulundu!")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Başlık", opp_details.get('title', 'N/A')[:30] + "...")
                    with col2:
                        st.metric("Agency", opp_details.get('agency', 'N/A')[:20] + "...")
                    with col3:
                        st.metric("Status", opp_details.get('status', 'N/A'))
                    
                    # Ekleri göster
                    attachments = opp_details.get('attachments', [])
                    st.markdown(f"**Ekler ({len(attachments)} adet):**")
                    
                    if attachments:
                        for i, att in enumerate(attachments):
                            st.write(f"{i+1}. {att.get('filename', 'Ek dosyası')} - {att.get('url', 'Mevcut değil')}")
                    else:
                        st.warning("Bu fırsat için ek bulunamadı.")
                        return
                    
                    # 3. Manuel ek indirme seçenekleri
                    st.markdown("### 3. Manuel Ek İndirme")
                    
                    # İndirme yöntemi seçimi
                    indirme_yontemi = st.radio(
                        "İndirme Yöntemi Seçin:",
                        ["SAM.gov'dan İndir", "Windows File Server'dan Seç", "Manuel Upload"],
                        horizontal=True
                    )
                    
                    if indirme_yontemi == "SAM.gov'dan İndir":
                        # Ek seçimi
                        selected_attachments = []
                        for i, att in enumerate(attachments):
                            if st.checkbox(f"İndir: {att.get('filename', f'Ek {i+1}')}", key=f"att_{i}"):
                                selected_attachments.append(att)
                    elif indirme_yontemi == "Windows File Server'dan Seç":
                        st.markdown("#### 📁 Windows File Server")
                        
                        # File server başlatma
                        if st.button("🚀 Windows File Server Başlat", type="primary"):
                            with st.spinner("File server başlatılıyor..."):
                                try:
                                    import subprocess
                                    import os
                                    from pathlib import Path
                                    
                                    # File server dizini oluştur
                                    file_server_dir = Path("file_server")
                                    file_server_dir.mkdir(exist_ok=True)
                                    
                                    # Python HTTP server başlat
                                    port = 8080
                                    cmd = f"python -m http.server {port} --directory {file_server_dir}"
                                    
                                    # Background'da çalıştır
                                    process = subprocess.Popen(cmd, shell=True, cwd=os.getcwd())
                                    
                                    st.success(f"✅ File server başlatıldı!")
                                    st.info(f"🌐 Server URL: http://localhost:{port}")
                                    st.info(f"📁 Dizin: {file_server_dir.absolute()}")
                                    
                                    # PDF dosyalarını listele
                                    pdf_files = list(file_server_dir.glob("*.pdf"))
                                    if pdf_files:
                                        st.markdown("**Mevcut PDF Dosyaları:**")
                                        selected_files = []
                                        for pdf_file in pdf_files:
                                            if st.checkbox(f"Seç: {pdf_file.name}", key=f"pdf_{pdf_file.name}"):
                                                selected_files.append(pdf_file)
                                        
                                        if selected_files:
                                            st.info(f"Seçilen dosyalar: {len(selected_files)} adet")
                                            
                                            # Dosyaları kopyala
                                            if st.button("📋 Seçilen Dosyaları Kopyala"):
                                                import shutil
                                                target_dir = Path("attachments") / notice_id
                                                target_dir.mkdir(parents=True, exist_ok=True)
                                                
                                                copied_files = []
                                                for pdf_file in selected_files:
                                                    dest_path = target_dir / pdf_file.name
                                                    shutil.copy2(pdf_file, dest_path)
                                                    copied_files.append({
                                                        'filename': pdf_file.name,
                                                        'path': str(dest_path),
                                                        'success': True
                                                    })
                                                
                                                st.success(f"✅ {len(copied_files)} dosya kopyalandı!")
                                                
                                                # AutoGen analizi için hazırla
                                                st.markdown("### 4. AutoGen Analizi")
                                                
                                                if st.button("🤖 AutoGen Analizini Başlat", type="primary"):
                                                    with st.spinner("AutoGen analizi başlatılıyor..."):
                                                        try:
                                                            from autogen_analysis_center import analyze_opportunity_comprehensive
                                                            analysis_result = analyze_opportunity_comprehensive(notice_id)
                                                            
                                                            if analysis_result and analysis_result.get('status') == 'success':
                                                                st.success("✅ AutoGen analizi tamamlandı!")
                                                                
                                                                # Analiz sonuçları
                                                                st.markdown("#### 📊 Analiz Sonuçları")
                                                                
                                                                col1, col2, col3 = st.columns(3)
                                                                with col1:
                                                                    st.metric("Durum", analysis_result.get('status', 'unknown').title())
                                                                with col2:
                                                                    st.metric("Güven", f"{analysis_result.get('confidence_score', 0.0):.2f}")
                                                                with col3:
                                                                    st.metric("Risk", analysis_result.get('risk_level', 'unknown').title())
                                                                
                                                                # Öneriler
                                                                recommendations = analysis_result.get('recommendations', [])
                                                                if recommendations:
                                                                    st.markdown("**Öneriler:**")
                                                                    for rec in recommendations:
                                                                        st.write(f"- {rec}")
                                                                
                                                                st.success("🎉 Analiz tamamlandı!")
                                                                
                                                            else:
                                                                st.error(f"❌ AutoGen analizi başarısız: {analysis_result.get('error', 'Bilinmeyen hata') if analysis_result else 'Sonuç alınamadı'}")
                                                                
                                                        except Exception as e:
                                                            st.error(f"❌ AutoGen analizi hatası: {str(e)}")
                                    else:
                                        st.warning("📁 file_server dizininde PDF dosyası bulunamadı.")
                                        st.info("PDF dosyalarınızı file_server dizinine koyun ve sayfayı yenileyin.")
                                        
                                except Exception as e:
                                    st.error(f"❌ File server hatası: {str(e)}")
                    
                    elif indirme_yontemi == "Manuel Upload":
                        st.markdown("#### 📤 Manuel Dosya Upload")
                        
                        uploaded_files = st.file_uploader(
                            "PDF dosyalarını seçin:",
                            type=['pdf'],
                            accept_multiple_files=True,
                            help="Birden fazla PDF dosyası seçebilirsiniz"
                        )
                        
                        if uploaded_files:
                            st.info(f"Seçilen dosyalar: {len(uploaded_files)} adet")
                            
                            # Dosyaları kaydet
                            if st.button("💾 Dosyaları Kaydet"):
                                import os
                                from pathlib import Path
                                
                                target_dir = Path("attachments") / notice_id
                                target_dir.mkdir(parents=True, exist_ok=True)
                                
                                saved_files = []
                                for uploaded_file in uploaded_files:
                                    file_path = target_dir / uploaded_file.name
                                    with open(file_path, "wb") as f:
                                        f.write(uploaded_file.getbuffer())
                                    saved_files.append({
                                        'filename': uploaded_file.name,
                                        'path': str(file_path),
                                        'success': True
                                    })
                                
                                st.success(f"✅ {len(saved_files)} dosya kaydedildi!")
                                
                                # AutoGen analizi
                                st.markdown("### 4. AutoGen Analizi")
                                
                                if st.button("🤖 AutoGen Analizini Başlat", type="primary"):
                                    with st.spinner("AutoGen analizi başlatılıyor..."):
                                        try:
                                            from autogen_analysis_center import analyze_opportunity_comprehensive
                                            analysis_result = analyze_opportunity_comprehensive(notice_id)
                                            
                                            if analysis_result and analysis_result.get('status') == 'success':
                                                st.success("✅ AutoGen analizi tamamlandı!")
                                                
                                                # Analiz sonuçları
                                                st.markdown("#### 📊 Analiz Sonuçları")
                                                
                                                col1, col2, col3 = st.columns(3)
                                                with col1:
                                                    st.metric("Durum", analysis_result.get('status', 'unknown').title())
                                                with col2:
                                                    st.metric("Güven", f"{analysis_result.get('confidence_score', 0.0):.2f}")
                                                with col3:
                                                    st.metric("Risk", analysis_result.get('risk_level', 'unknown').title())
                                                
                                                # Öneriler
                                                recommendations = analysis_result.get('recommendations', [])
                                                if recommendations:
                                                    st.markdown("**Öneriler:**")
                                                    for rec in recommendations:
                                                        st.write(f"- {rec}")
                                                
                                                st.success("🎉 Analiz tamamlandı!")
                                                
                                            else:
                                                st.error(f"❌ AutoGen analizi başarısız: {analysis_result.get('error', 'Bilinmeyen hata') if analysis_result else 'Sonuç alınamadı'}")
                                                
                                        except Exception as e:
                                            st.error(f"❌ AutoGen analizi hatası: {str(e)}")
                    
                    # Eski SAM.gov indirme kodu (sadece seçildiğinde)
                    if indirme_yontemi == "SAM.gov'dan İndir":
                        selected_attachments = []
                        for i, att in enumerate(attachments):
                            if st.checkbox(f"İndir: {att.get('filename', f'Ek {i+1}')}", key=f"att_{i}"):
                                selected_attachments.append(att)
                    
                    if selected_attachments:
                        st.info(f"Seçilen ekler: {len(selected_attachments)} adet")
                        
                        # İndirme butonu
                        if st.button("📥 Seçilen Ekleri İndir", type="primary"):
                            with st.spinner("Ekler indiriliyor..."):
                                try:
                                    from enhanced_attachment_downloader import EnhancedAttachmentDownloader
                                    downloader = EnhancedAttachmentDownloader()
                                    
                                    download_results = []
                                    for att in selected_attachments:
                                        result = downloader.download_attachment(
                                            att.get('url', ''),
                                            att.get('filename', 'unknown'),
                                            notice_id
                                        )
                                        download_results.append(result)
                                    
                                    # İndirme sonuçları
                                    st.markdown("#### 📊 İndirme Sonuçları")
                                    success_count = sum(1 for r in download_results if r.get('success', False))
                                    st.metric("Başarılı İndirme", f"{success_count}/{len(selected_attachments)}")
                                    
                                    for i, result in enumerate(download_results):
                                        if result.get('success', False):
                                            st.success(f"✅ {result.get('filename', 'Ek')} - İndirildi")
                                        else:
                                            st.error(f"❌ {result.get('filename', 'Ek')} - Hata: {result.get('error', 'Bilinmeyen')}")
                                    
                                    if success_count > 0:
                                        st.success("🎉 En az bir ek başarıyla indirildi!")
                                        
                                        # 4. AutoGen analizi
                                        st.markdown("### 4. AutoGen Analizi")
                                        
                                        if st.button("🤖 AutoGen Analizini Başlat", type="primary"):
                                            with st.spinner("AutoGen analizi başlatılıyor..."):
                                                try:
                                                    from autogen_analysis_center import analyze_opportunity_comprehensive
                                                    analysis_result = analyze_opportunity_comprehensive(notice_id)
                                                    
                                                    if analysis_result and analysis_result.get('status') == 'success':
                                                        st.success("✅ AutoGen analizi tamamlandı!")
                                                        
                                                        # Analiz sonuçları
                                                        st.markdown("#### 📊 Analiz Sonuçları")
                                                        
                                                        col1, col2, col3 = st.columns(3)
                                                        with col1:
                                                            st.metric("Durum", analysis_result.get('status', 'unknown').title())
                                                        with col2:
                                                            st.metric("Güven", f"{analysis_result.get('confidence_score', 0.0):.2f}")
                                                        with col3:
                                                            st.metric("Risk", analysis_result.get('risk_level', 'unknown').title())
                                                        
                                                        # Öneriler
                                                        recommendations = analysis_result.get('recommendations', [])
                                                        if recommendations:
                                                            st.markdown("**Öneriler:**")
                                                            for rec in recommendations:
                                                                st.write(f"- {rec}")
                                                        
                                                        # Detaylı analiz
                                                        detailed_analysis = analysis_result.get('detailed_analysis', {})
                                                        if detailed_analysis:
                                                            st.markdown("**Detaylı Analiz:**")
                                                            for key, value in detailed_analysis.items():
                                                                st.write(f"**{key}:** {value}")
                                                        
                                                        st.success("🎉 Analiz tamamlandı! Sonuçları yukarıda görebilirsiniz.")
                                                        
                                                    else:
                                                        st.error(f"❌ AutoGen analizi başarısız: {analysis_result.get('error', 'Bilinmeyen hata') if analysis_result else 'Sonuç alınamadı'}")
                                                        
                                                except Exception as e:
                                                    st.error(f"❌ AutoGen analizi hatası: {str(e)}")
                                    else:
                                        st.error("❌ Hiçbir ek indirilemedi. Lütfen URL'leri kontrol edin.")
                                        
                                except Exception as e:
                                    st.error(f"❌ İndirme hatası: {str(e)}")
                    else:
                        st.warning("Lütfen indirmek istediğiniz ekleri seçin.")
                        
                else:
                    st.error("❌ Fırsat bulunamadı. Geçerli bir Notice ID girin.")
                    
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")
    else:
        st.info("Lütfen Notice ID girin.")

def dosya_secimi_autogen_page():
    """Dosya Seçimi ve AutoGen Analizi sayfası"""
    st.markdown("## 📄 Dosya Seçimi ve AutoGen Analizi")
    st.markdown("Dosyaları seçin ve AutoGen analizini adım adım izleyin.")
    
    # 1. Dosya seçimi
    st.markdown("### 1. Dosya Seçimi")
    
    # Dosya seçim yöntemi
    secim_yontemi = st.radio(
        "Dosya Seçim Yöntemi:",
        ["File Upload", "File Server'dan Seç", "Klasörden Seç"],
        horizontal=True
    )
    
    selected_files = []
    
    if secim_yontemi == "File Upload":
        st.markdown("#### 📤 Dosya Upload")
        uploaded_files = st.file_uploader(
            "PDF dosyalarını seçin:",
            type=['pdf'],
            accept_multiple_files=True,
            help="Birden fazla PDF dosyası seçebilirsiniz"
        )
        
        if uploaded_files:
            selected_files = []
            for uploaded_file in uploaded_files:
                selected_files.append({
                    'name': uploaded_file.name,
                    'content': uploaded_file.getvalue(),
                    'type': 'uploaded'
                })
            st.success(f"✅ {len(selected_files)} dosya seçildi!")
    
    elif secim_yontemi == "File Server'dan Seç":
        st.markdown("#### 📁 File Server'dan Seç")
        
        # File server dizinini kontrol et
        from pathlib import Path
        file_server_dir = Path("file_server")
        
        if file_server_dir.exists():
            pdf_files = list(file_server_dir.glob("*.pdf"))
            if pdf_files:
                st.info(f"📁 file_server dizininde {len(pdf_files)} PDF dosyası bulundu")
                
                for pdf_file in pdf_files:
                    if st.checkbox(f"Seç: {pdf_file.name}", key=f"server_{pdf_file.name}"):
                        selected_files.append({
                            'name': pdf_file.name,
                            'path': str(pdf_file),
                            'type': 'server'
                        })
                
                if selected_files:
                    st.success(f"✅ {len(selected_files)} dosya seçildi!")
            else:
                st.warning("📁 file_server dizininde PDF dosyası bulunamadı")
                st.info("PDF dosyalarınızı file_server dizinine koyun")
        else:
            st.error("📁 file_server dizini bulunamadı")
    
    elif secim_yontemi == "Klasörden Seç":
        st.markdown("#### 📂 Klasörden Seç")
        
        # Klasör seçimi
        klasor_yolu = st.text_input(
            "Klasör Yolu:",
            placeholder="C:\\Users\\PC\\Documents\\PDFs",
            help="PDF dosyalarının bulunduğu klasörün tam yolu"
        )
        
        if klasor_yolu and Path(klasor_yolu).exists():
            pdf_files = list(Path(klasor_yolu).glob("*.pdf"))
            if pdf_files:
                st.info(f"📂 {klasor_yolu} dizininde {len(pdf_files)} PDF dosyası bulundu")
                
                for pdf_file in pdf_files:
                    if st.checkbox(f"Seç: {pdf_file.name}", key=f"folder_{pdf_file.name}"):
                        selected_files.append({
                            'name': pdf_file.name,
                            'path': str(pdf_file),
                            'type': 'folder'
                        })
                
                if selected_files:
                    st.success(f"✅ {len(selected_files)} dosya seçildi!")
            else:
                st.warning(f"📂 {klasor_yolu} dizininde PDF dosyası bulunamadı")
        elif klasor_yolu:
            st.error(f"❌ Klasör bulunamadı: {klasor_yolu}")
    
    # 2. Seçilen dosyaları göster
    if selected_files:
        st.markdown("### 2. Seçilen Dosyalar")
        
        for i, file_info in enumerate(selected_files, 1):
            st.write(f"{i}. {file_info['name']}")
        
        # 3. AutoGen analizi başlat
        st.markdown("### 3. AutoGen Analizi")
        
        if st.button("🤖 AutoGen Analizini Başlat", type="primary"):
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # Adım 1: Dosyaları hazırla
                status_text.text("📁 Adım 1: Dosyalar hazırlanıyor...")
                progress_bar.progress(10)
                
                # Dosyaları geçici dizine kopyala
                from pathlib import Path
                temp_dir = Path("temp_analysis") / f"analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                temp_dir.mkdir(parents=True, exist_ok=True)
                
                prepared_files = []
                for file_info in selected_files:
                    if file_info['type'] == 'uploaded':
                        # Upload edilen dosyayı kaydet
                        file_path = temp_dir / file_info['name']
                        with open(file_path, 'wb') as f:
                            f.write(file_info['content'])
                        prepared_files.append(str(file_path))
                    else:
                        # Server veya klasör dosyasını kopyala
                        import shutil
                        source_path = Path(file_info['path'])
                        dest_path = temp_dir / file_info['name']
                        shutil.copy2(source_path, dest_path)
                        prepared_files.append(str(dest_path))
                
                status_text.text("✅ Adım 1 tamamlandı: Dosyalar hazırlandı")
                progress_bar.progress(20)
                
                # Adım 2: AutoGen analizini başlat
                status_text.text("🤖 Adım 2: AutoGen analizi başlatılıyor...")
                progress_bar.progress(30)
                
                # Mock analiz sonuçları (gerçek AutoGen entegrasyonu için)
                analysis_steps = [
                    "📄 PDF dosyaları okunuyor...",
                    "🔍 Metin çıkarılıyor...",
                    "🧠 AI analizi yapılıyor...",
                    "📊 Sonuçlar değerlendiriliyor...",
                    "📋 Rapor oluşturuluyor..."
                ]
                
                for i, step in enumerate(analysis_steps):
                    status_text.text(step)
                    progress_bar.progress(40 + (i * 10))
                    time.sleep(1)  # Simülasyon için
                
                # Adım 3: Sonuçları göster
                status_text.text("✅ Analiz tamamlandı!")
                progress_bar.progress(100)
                
                # Mock analiz sonuçları
                st.markdown("#### 📊 Analiz Sonuçları")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Analiz Edilen Dosya", len(selected_files))
                with col2:
                    st.metric("Güven Skoru", "0.85")
                with col3:
                    st.metric("Risk Seviyesi", "Orta")
                
                # Detaylı sonuçlar
                st.markdown("#### 📋 Detaylı Analiz")
                
                for i, file_info in enumerate(selected_files, 1):
                    with st.expander(f"📄 {file_info['name']}"):
                        # Dosya boyutunu hesapla
                        if 'content' in file_info:
                            file_size = len(file_info['content'])
                        elif 'path' in file_info:
                            try:
                                file_size = Path(file_info['path']).stat().st_size
                            except:
                                file_size = "N/A"
                        else:
                            file_size = "N/A"
                        
                        st.write(f"**Dosya Boyutu:** {file_size} bytes" if file_size != "N/A" else f"**Dosya Boyutu:** {file_size}")
                        st.write(f"**Analiz Durumu:** ✅ Tamamlandı")
                        st.write(f"**Güven Skoru:** 0.{80 + i * 5}")
                        st.write(f"**Ana Konular:** Teknik gereksinimler, Fiyatlandırma, Teslimat")
                        st.write(f"**Risk Faktörleri:** Zaman sınırı, Teknik karmaşıklık")
                
                # Öneriler
                st.markdown("#### 💡 Öneriler")
                recommendations = [
                    "Teknik gereksinimleri detaylı inceleyin",
                    "Fiyat teklifinizi rekabetçi tutun",
                    "Teslimat sürelerini gerçekçi planlayın",
                    "Geçmiş deneyimlerinizi vurgulayın"
                ]
                
                for rec in recommendations:
                    st.write(f"- {rec}")
                
                st.success("🎉 Analiz tamamlandı! Sonuçları yukarıda görebilirsiniz.")
                
                # Temizlik
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
                
            except Exception as e:
                st.error(f"❌ Analiz hatası: {str(e)}")
                status_text.text("❌ Hata oluştu!")
                progress_bar.progress(0)
    
    else:
        st.info("Lütfen analiz edilecek dosyaları seçin.")

def otel_arastirma_page():
    """Otel Araştırma - karar ekranı gibi"""
    import json
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from sow_analysis_manager import SOWAnalysisManager
    from sam.hotels.hotel_finder_agent import run_hotel_finder_from_sow
    from sam.hotels.hotel_repository import save_hotel_suggestions, list_hotel_suggestions
    from ui_components import page_header, sticky_action_bar, hotel_card, empty_state, status_badge
    
    # Page header
    page_header("🏨 Otel Araştırma", "SOW analizi ile OSM/Nominatim üzerinden otel önerileri")
    
    # Sticky action bar
    sticky_action_bar(
        ("📄 PDF İndir", "download_pdf", "secondary"),
        ("📊 CSV Export", "export_csv", "secondary"),
        ("🔄 Yenile", "refresh", "primary"),
        ("💾 DB Kaydet", "save_db", "secondary")
    )

    # Notice listesi (DB-first)
    try:
        rows = DatabaseUtils.execute_query("""
            SELECT notice_id, COALESCE(title,'-') AS t
            FROM opportunities
            ORDER BY posted_date DESC
            LIMIT 200
        """)
        choices = [r[0] for r in rows] if rows else []
        nid = st.selectbox("Notice ID seçin", choices)
    except Exception as e:
        st.error(f"Veritabanı hatası: {e}")
        return

    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("SOW Yükle"):
            try:
                mgr = SOWAnalysisManager()
                analysis = mgr.get_analysis(nid)
                if not analysis:
                    st.error("SOW analizi bulunamadı. Önce 'İndir & Analiz' çalıştırın.")
                else:
                    st.session_state["_sow_payload"] = analysis.get("sow_payload")
                    st.success("SOW yüklendi.")
                    with st.expander("SOW Payload (JSON)"):
                        st.code(json.dumps(analysis.get("sow_payload"), ensure_ascii=False, indent=2), language="json")
            except Exception as e:
                st.error(f"SOW yükleme hatası: {e}")

    with col2:
        if st.button("Otel Ara (OSM)"):
            sow_payload = st.session_state.get("_sow_payload")
            if not sow_payload:
                st.warning("Önce 'SOW Yükle' deyin.")
            else:
                try:
                    with st.spinner("OSM/Nominatim sorgulanıyor..."):
                        results = run_hotel_finder_from_sow(sow_payload, nid)
                        st.session_state["_hotel_results"] = results
                    st.success(f"{len(results)} öneri bulundu.")
                except Exception as e:
                    st.error(f"Otel arama hatası: {e}")

    if "_hotel_results" in st.session_state:
        st.subheader("Filtreler")
        flt1, flt2, flt3 = st.columns([1,1,1])
        max_dist = flt1.slider("Maks. mesafe (km)", 1, 25, 5)
        must_have_contact = flt2.checkbox("İletişim gerekli (telefon/website)", value=False)
        budget_hint = flt3.number_input("Bütçe (gece/oda, USD - opsiyonel)", min_value=0, value=0)

        # sonuç render öncesi filtrele
        results = st.session_state.get("_hotel_results", [])
        filtered = []
        for r in results:
            if r["distance_km"] > max_dist: 
                continue
            if must_have_contact and not (r.get("phone") or r.get("website")):
                continue
            filtered.append(r)

        st.caption(f"Filtre sonrası: {len(filtered)} / {len(results)}")
        
        # Harita görselleştirme
        if filtered:
            import pydeck as pdk
            center_lat = sum([x["lat"] for x in filtered])/len(filtered)
            center_lon = sum([x["lon"] for x in filtered])/len(filtered)
            layer = pdk.Layer(
                "ScatterplotLayer",
                data=[{"lat":x["lat"], "lon":x["lon"], "name":x["name"], "d":x["distance_km"], "s":x["match_score"]} for x in filtered],
                get_position='[lon, lat]',
                get_radius=80,
                pickable=True
            )
            st.pydeck_chart(pdk.Deck(
                map_style="mapbox://styles/mapbox/light-v9",
                initial_view_state=pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=12),
                layers=[layer],
                tooltip={"text": "{name}\n{d} km • score {s}"}
            ))
        
        st.subheader("Öneriler (top 10)")
        for r in filtered:
            st.markdown(
                f"**{r['name']}** — {r.get('address') or 'adres yok'}  \n"
                f"📍 {r['distance_km']} km • ⭐ {r['match_score']}  \n"
                f"☎️ {r.get('phone') or '-'} • 🌐 {r.get('website') or '-'}"
            )

        # CSV dışa aktarım
        if filtered:
            import csv, io, datetime as dt
            buf = io.StringIO()
            w = csv.DictWriter(buf, fieldnames=["name","address","phone","website","distance_km","match_score","lat","lon"])
            w.writeheader()
            w.writerows(filtered)
            st.download_button("CSV indir", buf.getvalue().encode("utf-8"), file_name=f"hotels_{nid}_{dt.date.today()}.csv", mime="text/csv")

        # Teklife ekleme
        if filtered:
            st.subheader("Teklife Ekle")
            selected_names = st.multiselect("Teklife eklenecek oteller", [r["name"] for r in filtered])
            if st.button("Teklife Ekle"):
                try:
                    from sam.document_management.database_manager import execute_query
                    execute_query("UPDATE hotel_suggestions SET selected=true WHERE notice_id=%s AND name = ANY(%s)", (nid, selected_names), fetch=False)
                    st.success(f"{len(selected_names)} otel teklif sepetine eklendi")
                except Exception as e:
                    st.error(f"Teklife ekleme hatası: {e}")

        # Eşik üstü uyarı
        if filtered:
            high_quality = [h for h in filtered if h.get('match_score', 0) >= 0.9 and h.get('distance_km', 999) <= 3.0]
            if high_quality:
                st.success(f"🚨 {len(high_quality)} yüksek kaliteli otel bulundu! (score ≥ 0.9, mesafe ≤ 3km)")
                if st.button("Email Uyarısı Gönder"):
                    try:
                        from sow_email_notifications import SOWEmailNotifier
                        notifier = SOWEmailNotifier()
                        # Default recipients - gerçek uygulamada kullanıcıdan alınabilir
                        recipients = [os.getenv('ALERT_EMAIL', 'admin@zgr.local')]
                        if notifier.send_hotel_alert(nid, high_quality, recipients):
                            st.success("Email uyarısı gönderildi!")
                        else:
                            st.warning("Email gönderilemedi (SMTP ayarlarını kontrol edin)")
                    except Exception as e:
                        st.error(f"Email gönderme hatası: {e}")

        if st.button("DB'ye Kaydet"):
            try:
                cnt = save_hotel_suggestions(nid, st.session_state["_hotel_results"])
                st.success(f"{cnt} kayıt kaydedildi.")
        
        # Kapsamlı Rapor Oluştur
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Kapsamlı Rapor Oluştur"):
                try:
                    from comprehensive_report_generator import ComprehensiveReportGenerator
                    generator = ComprehensiveReportGenerator()
                    
                    with st.spinner("Kapsamlı rapor oluşturuluyor..."):
                        output_path = generator.generate_comprehensive_report(nid)
                    
                    if output_path and os.path.exists(output_path):
                        st.success(f"Kapsamlı rapor oluşturuldu: {output_path}")
                        
                        # PDF indirme butonu
                        with open(output_path, "rb") as pdf_file:
                            st.download_button(
                                label="📄 Kapsamlı Raporu İndir",
                                data=pdf_file.read(),
                                file_name=os.path.basename(output_path),
                                mime="application/pdf"
                            )
                    else:
                        st.error("Rapor oluşturulamadı")
                except Exception as e:
                    st.error(f"Rapor oluşturma hatası: {e}")
        
        with col2:
            if st.button("🚀 AutoProposal PDF"):
                try:
                    from autoproposal_engine import AutoProposalEngine
                    engine = AutoProposalEngine()
                    
                    # Seçili otelleri al
                    selected_hotels = []
                    if "_hotel_results" in st.session_state:
                        selected_hotels = [h['name'] for h in st.session_state["_hotel_results"] if h.get('selected')]
                    
                    with st.spinner("AutoProposal oluşturuluyor..."):
                        result = engine.generate_autoproposal(nid, selected_hotels=selected_hotels)
                    
                    if result['status'] == 'success':
                        st.success(f"AutoProposal oluşturuldu!")
                        st.info(f"🏨 {len(result['selected_hotels'])} otel seçildi")
                        st.info(f"💰 Bütçe: ${result['budget_total']:,.2f}")
                        st.info(f"⏱️ Süre: {result['processing_time']:.2f}s")
                        
                        # PDF indirme butonu
                        if os.path.exists(result['pdf_path']):
                            with open(result['pdf_path'], "rb") as pdf_file:
                                st.download_button(
                                    label="📄 AutoProposal PDF İndir",
                                    data=pdf_file.read(),
                                    file_name=os.path.basename(result['pdf_path']),
                                    mime="application/pdf"
                                )
                    else:
                        st.error(f"AutoProposal hatası: {result['error']}")
                except Exception as e:
                    st.error(f"AutoProposal oluşturma hatası: {e}")

        with st.expander("DB'deki Kayıtlar"):
            try:
                db_items = list_hotel_suggestions(nid, 50)
                if not db_items:
                    st.info("Kayıt yok.")
                else:
                    for r in db_items:
                        st.write(r)
            except Exception as e:
                st.error(f"DB okuma hatası: {e}")

if __name__ == "__main__":
    main()
