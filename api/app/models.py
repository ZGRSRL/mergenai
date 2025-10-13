from sqlalchemy import Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .db import Base


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    kind = Column(String(50), nullable=False)  # rfq, sow, facility, past_performance, pricing
    title = Column(String(255), nullable=False)
    path = Column(String(500), nullable=False)
    meta_json = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    clauses = relationship("Clause", back_populates="document")
    requirements = relationship("Requirement", back_populates="rfq_document")
    facility_features = relationship("FacilityFeature", back_populates="source_document")
    pricing_items = relationship("PricingItem", back_populates="rfq_document")
    vector_chunks = relationship("VectorChunk", back_populates="document")


class Clause(Base):
    __tablename__ = "clauses"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    section = Column(String(100))
    text = Column(Text, nullable=False)
    tags = Column(JSON)  # ["far_52_204_24", "ipp_billing", etc.]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="clauses")


class Requirement(Base):
    __tablename__ = "requirements"
    
    id = Column(Integer, primary_key=True, index=True)
    rfq_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    code = Column(String(20), nullable=False)  # R-001, R-002, etc.
    text = Column(Text, nullable=False)
    category = Column(String(50))  # capacity, date, transport, av, invoice, clauses
    priority = Column(String(20), default="medium")  # low, medium, high, critical
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    rfq_document = relationship("Document", back_populates="requirements")
    evidence = relationship("Evidence", back_populates="requirement")


class Evidence(Base):
    __tablename__ = "evidence"
    
    id = Column(Integer, primary_key=True, index=True)
    requirement_id = Column(Integer, ForeignKey("requirements.id"), nullable=False)
    source_doc_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    snippet = Column(Text, nullable=False)
    score = Column(Float, default=0.0)  # 0.0 to 1.0
    evidence_type = Column(String(50))  # facility, past_performance, pricing
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    requirement = relationship("Requirement", back_populates="evidence")
    source_document = relationship("Document")


class FacilityFeature(Base):
    __tablename__ = "facility_features"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)  # shuttle, wifi, parking, etc.
    value = Column(Text)
    source_doc_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    source_document = relationship("Document", back_populates="facility_features")


class PricingItem(Base):
    __tablename__ = "pricing_items"
    
    id = Column(Integer, primary_key=True, index=True)
    rfq_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    qty = Column(Float, default=1.0)
    unit = Column(String(50))  # room_night, person, setup, etc.
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float)
    category = Column(String(50))  # lodging, av, food, service
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    rfq_document = relationship("Document", back_populates="pricing_items")


class PastPerformance(Base):
    __tablename__ = "past_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    client = Column(String(200))
    scope = Column(Text)
    period = Column(String(100))  # "2022-2023"
    value = Column(Float)  # contract value
    ref_info = Column(JSON)  # POC, contact details, etc.
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class VectorChunk(Base):
    __tablename__ = "vector_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    chunk = Column(Text, nullable=False)
    embedding = Column(JSON)  # vector embedding
    chunk_type = Column(String(50))  # paragraph, table, list, etc.
    page_number = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    document = relationship("Document", back_populates="vector_chunks")

