#!/usr/bin/env python3
"""
Streamlit SOW Dashboard
Interactive visualization for SOW analysis data
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor

# Page configuration
st.set_page_config(
    page_title="SOW Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database connection
@st.cache_resource
def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            database='ZGR_AI',
            user='postgres',
            password='postgres',
            port='5432'
        )
        return conn
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        return None

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_sow_data():
    """Load SOW data from database"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    notice_id,
                    period,
                    setup_deadline_ts,
                    rooms_per_night,
                    total_nights,
                    total_room_nights,
                    general_session_capacity,
                    breakout_rooms_count,
                    breakout_room_capacity,
                    total_capacity,
                    projector_lumens,
                    refreshments_frequency,
                    precon_meeting_date,
                    tax_exemption,
                    created_at,
                    updated_at
                FROM vw_sow_summary
                ORDER BY updated_at DESC
            """)
            
            data = cursor.fetchall()
            df = pd.DataFrame(data)
            
            # Convert datetime columns
            if not df.empty:
                df['setup_deadline_ts'] = pd.to_datetime(df['setup_deadline_ts'])
                df['created_at'] = pd.to_datetime(df['created_at'])
                df['updated_at'] = pd.to_datetime(df['updated_at'])
            
            return df
            
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

@st.cache_data(ttl=300)
def load_capacity_analysis():
    """Load capacity analysis data"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    notice_id,
                    period,
                    general_session_capacity,
                    breakout_rooms_count,
                    breakout_room_capacity,
                    total_capacity,
                    rooms_per_night,
                    event_size,
                    breakout_complexity
                FROM vw_sow_capacity_analysis
                ORDER BY total_capacity DESC
            """)
            
            data = cursor.fetchall()
            return pd.DataFrame(data)
            
    except Exception as e:
        st.error(f"Error loading capacity data: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

@st.cache_data(ttl=300)
def load_date_analysis():
    """Load date analysis data"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    notice_id,
                    period,
                    setup_deadline_ts,
                    precon_meeting_date,
                    setup_month,
                    setup_quarter,
                    setup_year,
                    setup_timeline
                FROM vw_sow_date_analysis
                ORDER BY setup_deadline_ts
            """)
            
            data = cursor.fetchall()
            df = pd.DataFrame(data)
            
            if not df.empty:
                df['setup_deadline_ts'] = pd.to_datetime(df['setup_deadline_ts'])
            
            return df
            
    except Exception as e:
        st.error(f"Error loading date data: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def get_sow_details(notice_id: str):
    """Get detailed SOW information"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT 
                    notice_id,
                    template_version,
                    sow_payload,
                    source_docs,
                    created_at,
                    updated_at
                FROM vw_active_sow
                WHERE notice_id = %s
            """, (notice_id,))
            
            result = cursor.fetchone()
            return dict(result) if result else None
            
    except Exception as e:
        st.error(f"Error loading SOW details: {e}")
        return None
    finally:
        conn.close()

def main():
    """Main dashboard function"""
    
    # Header
    st.title("📊 SOW Analysis Dashboard")
    st.markdown("---")
    
    # Load data
    with st.spinner("Loading SOW data..."):
        sow_data = load_sow_data()
        capacity_data = load_capacity_analysis()
        date_data = load_date_analysis()
    
    if sow_data.empty:
        st.warning("No SOW data available")
        return
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Capacity filter
    min_capacity = st.sidebar.slider(
        "Minimum Capacity",
        min_value=0,
        max_value=int(sow_data['general_session_capacity'].max()) if not sow_data.empty else 100,
        value=0
    )
    
    # Breakout rooms filter
    min_breakout = st.sidebar.slider(
        "Minimum Breakout Rooms",
        min_value=0,
        max_value=int(sow_data['breakout_rooms_count'].max()) if not sow_data.empty else 10,
        value=0
    )
    
    # Date range filter
    if not sow_data.empty and 'setup_deadline_ts' in sow_data.columns:
        date_range = st.sidebar.date_input(
            "Setup Deadline Range",
            value=(sow_data['setup_deadline_ts'].min().date(), sow_data['setup_deadline_ts'].max().date()),
            min_value=sow_data['setup_deadline_ts'].min().date(),
            max_value=sow_data['setup_deadline_ts'].max().date()
        )
    
    # Apply filters
    filtered_data = sow_data[
        (sow_data['general_session_capacity'] >= min_capacity) &
        (sow_data['breakout_rooms_count'] >= min_breakout)
    ]
    
    if 'date_range' in locals() and len(date_range) == 2:
        filtered_data = filtered_data[
            (filtered_data['setup_deadline_ts'].dt.date >= date_range[0]) &
            (filtered_data['setup_deadline_ts'].dt.date <= date_range[1])
        ]
    
    # Main content
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total SOWs",
            len(filtered_data),
            delta=len(filtered_data) - len(sow_data) if len(filtered_data) != len(sow_data) else None
        )
    
    with col2:
        avg_capacity = filtered_data['general_session_capacity'].mean()
        st.metric(
            "Avg Capacity",
            f"{avg_capacity:.0f}" if not pd.isna(avg_capacity) else "N/A"
        )
    
    with col3:
        total_rooms = filtered_data['total_room_nights'].sum()
        st.metric(
            "Total Room Nights",
            f"{total_rooms:,.0f}" if not pd.isna(total_rooms) else "N/A"
        )
    
    with col4:
        upcoming = len(filtered_data[filtered_data['setup_deadline_ts'] > datetime.now()])
        st.metric(
            "Upcoming Events",
            upcoming
        )
    
    st.markdown("---")
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Overview", "📊 Capacity Analysis", "📅 Timeline", "🔍 Details"])
    
    with tab1:
        st.subheader("SOW Overview")
        
        if not filtered_data.empty:
            # Display table
            display_columns = [
                'notice_id', 'period', 'general_session_capacity', 
                'breakout_rooms_count', 'total_capacity', 'rooms_per_night',
                'setup_deadline_ts', 'tax_exemption'
            ]
            
            st.dataframe(
                filtered_data[display_columns],
                use_container_width=True,
                hide_index=True
            )
            
            # Charts
            col1, col2 = st.columns(2)
            
            with col1:
                # Capacity distribution
                fig_capacity = px.histogram(
                    filtered_data,
                    x='general_session_capacity',
                    title="Capacity Distribution",
                    nbins=20
                )
                fig_capacity.update_layout(xaxis_title="Capacity", yaxis_title="Count")
                st.plotly_chart(fig_capacity, use_container_width=True)
            
            with col2:
                # Breakout rooms distribution
                fig_breakout = px.histogram(
                    filtered_data,
                    x='breakout_rooms_count',
                    title="Breakout Rooms Distribution",
                    nbins=10
                )
                fig_breakout.update_layout(xaxis_title="Breakout Rooms", yaxis_title="Count")
                st.plotly_chart(fig_breakout, use_container_width=True)
    
    with tab2:
        st.subheader("Capacity Analysis")
        
        if not capacity_data.empty:
            # Event size pie chart
            col1, col2 = st.columns(2)
            
            with col1:
                event_size_counts = capacity_data['event_size'].value_counts()
                fig_pie = px.pie(
                    values=event_size_counts.values,
                    names=event_size_counts.index,
                    title="Event Size Distribution"
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                # Capacity vs Breakout rooms scatter
                fig_scatter = px.scatter(
                    capacity_data,
                    x='general_session_capacity',
                    y='breakout_rooms_count',
                    size='total_capacity',
                    color='event_size',
                    title="Capacity vs Breakout Rooms",
                    hover_data=['notice_id', 'period']
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
            
            # Complexity analysis
            complexity_counts = capacity_data['breakout_complexity'].value_counts()
            fig_complexity = px.bar(
                x=complexity_counts.index,
                y=complexity_counts.values,
                title="Breakout Complexity Distribution"
            )
            fig_complexity.update_layout(xaxis_title="Complexity", yaxis_title="Count")
            st.plotly_chart(fig_complexity, use_container_width=True)
    
    with tab3:
        st.subheader("Timeline Analysis")
        
        if not date_data.empty:
            # Timeline chart
            fig_timeline = px.scatter(
                date_data,
                x='setup_deadline_ts',
                y='notice_id',
                color='setup_timeline',
                title="SOW Timeline",
                hover_data=['period', 'precon_meeting_date']
            )
            fig_timeline.update_layout(xaxis_title="Setup Deadline", yaxis_title="Notice ID")
            st.plotly_chart(fig_timeline, use_container_width=True)
            
            # Monthly distribution
            monthly_counts = date_data.groupby('setup_month').size()
            fig_monthly = px.bar(
                x=monthly_counts.index,
                y=monthly_counts.values,
                title="Monthly Distribution"
            )
            fig_monthly.update_layout(xaxis_title="Month", yaxis_title="Count")
            st.plotly_chart(fig_monthly, use_container_width=True)
    
    with tab4:
        st.subheader("Detailed SOW Information")
        
        # SOW selector
        selected_sow = st.selectbox(
            "Select SOW to view details:",
            options=filtered_data['notice_id'].tolist(),
            index=0
        )
        
        if selected_sow:
            details = get_sow_details(selected_sow)
            
            if details:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Basic Information")
                    st.write(f"**Notice ID:** {details['notice_id']}")
                    st.write(f"**Template Version:** {details['template_version']}")
                    st.write(f"**Created:** {details['created_at']}")
                    st.write(f"**Updated:** {details['updated_at']}")
                
                with col2:
                    st.subheader("SOW Payload")
                    st.json(details['sow_payload'])
                
                # Source documents
                if details['source_docs']:
                    st.subheader("Source Documents")
                    st.json(details['source_docs'])
            else:
                st.error("SOW details not found")

if __name__ == "__main__":
    main()
