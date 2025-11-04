#!/usr/bin/env python3
"""
SOW REST API Endpoints
FastAPI endpoints for SOW analysis data
"""

from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import psycopg2
from psycopg2.extras import RealDictCursor
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="SOW Analysis API",
    description="REST API for SOW analysis data",
    version="1.0.0"
)

# Database connection dependency
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
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(status_code=500, detail="Database connection failed")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SOW Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "sow": "/sow",
            "sow_by_id": "/sow/{notice_id}",
            "capacity_analysis": "/capacity-analysis",
            "timeline": "/timeline",
            "summary": "/summary"
        }
    }

@app.get("/sow")
async def get_all_sow(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    min_capacity: Optional[int] = Query(None, ge=0),
    min_breakout_rooms: Optional[int] = Query(None, ge=0),
    db_conn = Depends(get_db_connection)
):
    """Get all SOW analyses with optional filters"""
    try:
        with db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Build query with filters
            where_conditions = ["is_active = true"]
            params = []
            
            if min_capacity is not None:
                where_conditions.append("(sow_payload #>> '{function_space,general_session,capacity}')::int >= %s")
                params.append(min_capacity)
            
            if min_breakout_rooms is not None:
                where_conditions.append("(sow_payload #>> '{function_space,breakout_rooms,count}')::int >= %s")
                params.append(min_breakout_rooms)
            
            where_clause = " AND ".join(where_conditions)
            
            query = f"""
                SELECT 
                    notice_id,
                    template_version,
                    sow_payload,
                    source_docs,
                    created_at,
                    updated_at
                FROM sow_analysis
                WHERE {where_clause}
                ORDER BY updated_at DESC
                LIMIT %s OFFSET %s
            """
            
            params.extend([limit, offset])
            cursor.execute(query, params)
            
            results = cursor.fetchall()
            
            return {
                "data": [dict(row) for row in results],
                "count": len(results),
                "limit": limit,
                "offset": offset
            }
            
    except Exception as e:
        logger.error(f"Error fetching SOW data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_conn.close()

@app.get("/sow/{notice_id}")
async def get_sow_by_id(notice_id: str, db_conn = Depends(get_db_connection)):
    """Get specific SOW analysis by notice_id"""
    try:
        with db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
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
            
            if not result:
                raise HTTPException(status_code=404, detail="SOW not found")
            
            return dict(result)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching SOW {notice_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_conn.close()

@app.get("/summary")
async def get_sow_summary(db_conn = Depends(get_db_connection)):
    """Get SOW summary statistics"""
    try:
        with db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Get summary data
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_sows,
                    AVG((sow_payload #>> '{function_space,general_session,capacity}')::int) as avg_capacity,
                    MAX((sow_payload #>> '{function_space,general_session,capacity}')::int) as max_capacity,
                    MIN((sow_payload #>> '{function_space,general_session,capacity}')::int) as min_capacity,
                    SUM(((sow_payload #>> '{room_block,total_rooms_per_night}')::int * 
                         (sow_payload #>> '{room_block,nights}')::int)) as total_room_nights,
                    COUNT(CASE WHEN (sow_payload #>> '{tax_exemption}')::boolean = true THEN 1 END) as tax_exempt_count
                FROM sow_analysis
                WHERE is_active = true
            """)
            
            summary = cursor.fetchone()
            
            # Get capacity distribution
            cursor.execute("""
                SELECT 
                    CASE 
                        WHEN (sow_payload #>> '{function_space,general_session,capacity}')::int >= 100 THEN 'Large'
                        WHEN (sow_payload #>> '{function_space,general_session,capacity}')::int >= 50 THEN 'Medium'
                        ELSE 'Small'
                    END as event_size,
                    COUNT(*) as count
                FROM sow_analysis
                WHERE is_active = true
                GROUP BY event_size
            """)
            
            capacity_dist = cursor.fetchall()
            
            return {
                "summary": dict(summary),
                "capacity_distribution": [dict(row) for row in capacity_dist]
            }
            
    except Exception as e:
        logger.error(f"Error fetching summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_conn.close()

@app.get("/capacity-analysis")
async def get_capacity_analysis(db_conn = Depends(get_db_connection)):
    """Get capacity analysis data"""
    try:
        with db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
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
            
            results = cursor.fetchall()
            return [dict(row) for row in results]
            
    except Exception as e:
        logger.error(f"Error fetching capacity analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_conn.close()

@app.get("/timeline")
async def get_timeline_analysis(db_conn = Depends(get_db_connection)):
    """Get timeline analysis data"""
    try:
        with db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
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
            
            results = cursor.fetchall()
            return [dict(row) for row in results]
            
    except Exception as e:
        logger.error(f"Error fetching timeline analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_conn.close()

@app.get("/search")
async def search_sow(
    q: str = Query(..., description="Search query"),
    field: str = Query("notice_id", description="Field to search in"),
    db_conn = Depends(get_db_connection)
):
    """Search SOW analyses"""
    try:
        with db_conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Build search query based on field
            if field == "notice_id":
                cursor.execute("""
                    SELECT notice_id, template_version, sow_payload, created_at, updated_at
                    FROM vw_active_sow
                    WHERE notice_id ILIKE %s
                    ORDER BY updated_at DESC
                """, (f"%{q}%",))
            elif field == "period":
                cursor.execute("""
                    SELECT notice_id, template_version, sow_payload, created_at, updated_at
                    FROM vw_active_sow
                    WHERE (sow_payload->>'period_of_performance') ILIKE %s
                    ORDER BY updated_at DESC
                """, (f"%{q}%",))
            else:
                raise HTTPException(status_code=400, detail="Invalid search field")
            
            results = cursor.fetchall()
            return [dict(row) for row in results]
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching SOW: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_conn.close()

@app.post("/sow/{notice_id}/process")
async def process_sow_documents(
    notice_id: str,
    document_paths: List[str],
    db_conn = Depends(get_db_connection)
):
    """Process SOW documents and store results"""
    try:
        # Import the workflow pipeline
        import sys
        sys.path.append('.')
        from sow_autogen_workflow import SOWWorkflowPipeline
        
        # Initialize pipeline
        pipeline = SOWWorkflowPipeline()
        
        # Process documents
        analysis_id = pipeline.process_sow_documents(notice_id, document_paths)
        
        return {
            "message": "SOW processing completed",
            "notice_id": notice_id,
            "analysis_id": analysis_id,
            "processed_documents": len(document_paths)
        }
        
    except Exception as e:
        logger.error(f"Error processing SOW {notice_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db_conn.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
