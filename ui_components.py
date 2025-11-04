#!/usr/bin/env python3
"""
UI Components for ZGR SAM System
Reusable UI components for consistent design
"""

import streamlit as st
from datetime import datetime
from typing import List, Tuple, Optional

def status_badge(text: str, tone: str = "ok"):
    """Status badge component"""
    colors = {
        "ok": "#22c55e",
        "warn": "#f59e0b", 
        "err": "#ef4444",
        "info": "#3b82f6",
        "neutral": "#6b7280"
    }
    color = colors.get(tone, "#3b82f6")
    st.markdown(f"""
    <span style="background:{color}1A;color:{color};padding:.25rem .5rem;border-radius:.5rem;font-weight:600;font-size:0.875rem">
      {text}
    </span>
    """, unsafe_allow_html=True)

def sticky_action_bar(*buttons):
    """Sticky action bar at top of page"""
    st.markdown("""
    <div style='position:sticky;top:0;z-index:9;background:rgba(11,18,32,0.8);backdrop-filter:blur(6px);padding:.75rem;border-bottom:1px solid #374151;margin:-1rem -1rem 1rem -1rem;'>
    """, unsafe_allow_html=True)
    
    cols = st.columns(len(buttons))
    for i, (label, key, kind) in enumerate(buttons):
        with cols[i]:
            if kind == "primary":
                st.button(label, key=key, type="primary", use_container_width=True)
            elif kind == "secondary":
                st.button(label, key=key, type="secondary", use_container_width=True)
            else:
                st.button(label, key=key, use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

def metric_card(title: str, value: str, delta: Optional[str] = None, icon: str = ""):
    """Metric card component"""
    delta_html = ""
    if delta:
        delta_color = "#22c55e" if delta.startswith("+") else "#ef4444"
        delta_html = f'<div style="color:{delta_color};font-size:0.875rem;font-weight:600">{delta}</div>'
    
    st.markdown(f"""
    <div style="background:#111827;padding:1.5rem;border-radius:0.75rem;border:1px solid #374151;">
        <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem;">
            <span style="font-size:1.25rem;">{icon}</span>
            <span style="color:#9ca3af;font-size:0.875rem;font-weight:500;">{title}</span>
        </div>
        <div style="font-size:2rem;font-weight:700;color:#f9fafb;margin-bottom:0.25rem;">{value}</div>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)

def opportunity_card(notice_id: str, title: str, naics: str, date: str, poc: str, summary: str):
    """Opportunity card component"""
    st.markdown(f"""
    <div style="background:#111827;padding:1.5rem;border-radius:0.75rem;border:1px solid #374151;margin-bottom:1rem;">
        <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:1rem;">
            <div>
                <h4 style="color:#f9fafb;margin:0;font-size:1.125rem;">{title[:50]}{'...' if len(title) > 50 else ''}</h4>
                <div style="color:#6b7280;font-size:0.875rem;margin-top:0.25rem;">{notice_id}</div>
            </div>
            <div style="text-align:right;">
                <div style="color:#9ca3af;font-size:0.75rem;">NAICS</div>
                <div style="color:#f9fafb;font-weight:600;">{naics}</div>
            </div>
        </div>
        <div style="color:#9ca3af;font-size:0.875rem;margin-bottom:0.5rem;">📅 {date} • 👤 {poc[:30]}{'...' if len(poc) > 30 else ''}</div>
        <div style="color:#d1d5db;font-size:0.875rem;line-height:1.4;">{summary[:120]}{'...' if len(summary) > 120 else ''}</div>
    </div>
    """, unsafe_allow_html=True)

def hotel_card(name: str, distance: float, score: float, phone: str, website: str, address: str, selected: bool = False):
    """Hotel card component"""
    score_color = "#22c55e" if score >= 0.9 else "#f59e0b" if score >= 0.7 else "#ef4444"
    distance_color = "#22c55e" if distance <= 3 else "#f59e0b" if distance <= 5 else "#ef4444"
    
    st.markdown(f"""
    <div style="background:#111827;padding:1rem;border-radius:0.75rem;border:1px solid #374151;margin-bottom:0.75rem;{'border-color:#6366f1;' if selected else ''}">
        <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:0.75rem;">
            <h5 style="color:#f9fafb;margin:0;font-size:1rem;">{name}</h5>
            <div style="display:flex;gap:0.5rem;">
                <span style="background:{distance_color}1A;color:{distance_color};padding:0.25rem 0.5rem;border-radius:0.375rem;font-size:0.75rem;font-weight:600;">
                    📍 {distance}km
                </span>
                <span style="background:{score_color}1A;color:{score_color};padding:0.25rem 0.5rem;border-radius:0.375rem;font-size:0.75rem;font-weight:600;">
                    ⭐ {score:.2f}
                </span>
            </div>
        </div>
        <div style="color:#9ca3af;font-size:0.875rem;margin-bottom:0.5rem;">{address[:60]}{'...' if len(address) > 60 else ''}</div>
        <div style="display:flex;gap:1rem;color:#6b7280;font-size:0.75rem;">
            <span>☎️ {phone or 'N/A'}</span>
            <span>🌐 {website or 'N/A'}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def skeleton_loader(text: str = "Yükleniyor...", progress: int = 35):
    """Skeleton loader component"""
    st.markdown(f"""
    <div style="background:#111827;padding:2rem;border-radius:0.75rem;border:1px solid #374151;text-align:center;">
        <div style="color:#9ca3af;font-size:1rem;margin-bottom:1rem;">{text}</div>
        <div style="background:#374151;height:0.5rem;border-radius:0.25rem;overflow:hidden;">
            <div style="background:#6366f1;height:100%;width:{progress}%;transition:width 0.3s ease;"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def empty_state(icon: str, title: str, description: str, action_text: str = None, action_key: str = None):
    """Empty state component"""
    action_html = ""
    if action_text and action_key:
        action_html = f'<button onclick="document.querySelector(\'[data-testid=\\"{action_key}\\"]\').click()" style="background:#6366f1;color:white;border:none;padding:0.75rem 1.5rem;border-radius:0.5rem;font-weight:600;cursor:pointer;margin-top:1rem;">{action_text}</button>'
    
    st.markdown(f"""
    <div style="background:#111827;padding:3rem 2rem;border-radius:0.75rem;border:1px solid #374151;text-align:center;">
        <div style="font-size:3rem;margin-bottom:1rem;">{icon}</div>
        <h3 style="color:#f9fafb;margin:0 0 0.5rem 0;">{title}</h3>
        <p style="color:#9ca3af;margin:0;line-height:1.5;">{description}</p>
        {action_html}
    </div>
    """, unsafe_allow_html=True)

def status_strip(api_status: str, db_status: str, queue_status: str):
    """Status strip component"""
    api_color = "#22c55e" if api_status == "OK" else "#f59e0b" if api_status == "DEGRADED" else "#ef4444"
    db_color = "#22c55e" if db_status == "CONNECTED" else "#ef4444"
    queue_color = "#22c55e" if queue_status == "IDLE" else "#f59e0b" if queue_status == "RUNNING" else "#ef4444"
    
    st.markdown(f"""
    <div style="background:#111827;padding:0.75rem 1rem;border-radius:0.5rem;border:1px solid #374151;margin-bottom:1rem;">
        <div style="display:flex;gap:2rem;align-items:center;font-size:0.875rem;">
            <div style="display:flex;align-items:center;gap:0.5rem;">
                <div style="width:0.5rem;height:0.5rem;border-radius:50%;background:{api_color};"></div>
                <span style="color:#9ca3af;">SAM API:</span>
                <span style="color:{api_color};font-weight:600;">{api_status}</span>
            </div>
            <div style="display:flex;align-items:center;gap:0.5rem;">
                <div style="width:0.5rem;height:0.5rem;border-radius:50%;background:{db_color};"></div>
                <span style="color:#9ca3af;">DB:</span>
                <span style="color:{db_color};font-weight:600;">{db_status}</span>
            </div>
            <div style="display:flex;align-items:center;gap:0.5rem;">
                <div style="width:0.5rem;height:0.5rem;border-radius:50%;background:{queue_color};"></div>
                <span style="color:#9ca3af;">Queue:</span>
                <span style="color:{queue_color};font-weight:600;">{queue_status}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def page_header(title: str, description: str):
    """Page header component"""
    st.markdown(f"""
    <div style="margin-bottom:2rem;">
        <h1 style="color:#f9fafb;margin:0 0 0.5rem 0;font-size:2rem;font-weight:700;">{title}</h1>
        <p style="color:#9ca3af;margin:0;font-size:1rem;line-height:1.5;">{description}</p>
    </div>
    """, unsafe_allow_html=True)

def tab_container(tabs: List[str], active_tab: int = 0):
    """Tab container component"""
    tab_html = ""
    for i, tab in enumerate(tabs):
        active_class = "active" if i == active_tab else ""
        tab_html += f'<button class="tab-button {active_class}" onclick="setActiveTab({i})">{tab}</button>'
    
    st.markdown(f"""
    <div style="border-bottom:1px solid #374151;margin-bottom:1.5rem;">
        <div style="display:flex;gap:0;">
            {tab_html}
        </div>
    </div>
    <style>
    .tab-button {{
        background:none;border:none;padding:0.75rem 1.5rem;color:#9ca3af;cursor:pointer;border-bottom:2px solid transparent;font-weight:500;
    }}
    .tab-button.active {{
        color:#6366f1;border-bottom-color:#6366f1;
    }}
    .tab-button:hover {{
        color:#d1d5db;
    }}
    </style>
    """, unsafe_allow_html=True)

