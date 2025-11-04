#!/usr/bin/env python3
"""
Initialize RAG database tables
Creates all required tables for RAG service
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'api'))

from sqlalchemy import create_engine
from app.db import Base, engine
from app.models import (
    Document, Clause, Requirement, Evidence, 
    FacilityFeature, PricingItem, PastPerformance, VectorChunk
)
from app.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Create all database tables"""
    logger.info("Initializing RAG database...")
    logger.info(f"Database URL: {settings.database_url}")
    
    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully!")
        
        # Verify tables
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Created tables: {', '.join(tables)}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)





