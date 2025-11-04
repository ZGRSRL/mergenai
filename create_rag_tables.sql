-- RAG Service Required Tables
-- Run this on ZGR_AI database

-- Create documents table if not exists
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    kind VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    path VARCHAR(500) NOT NULL,
    meta_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create vector_chunks table if not exists (for RAG)
CREATE TABLE IF NOT EXISTS vector_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk TEXT NOT NULL,
    embedding JSONB,  -- Store embeddings as JSONB (array of floats)
    chunk_type VARCHAR(50),
    page_number INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_documents_kind ON documents(kind);
CREATE INDEX IF NOT EXISTS idx_vector_chunks_document_id ON vector_chunks(document_id);

-- Create other RAG-related tables
CREATE TABLE IF NOT EXISTS requirements (
    id SERIAL PRIMARY KEY,
    rfq_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    code VARCHAR(20) NOT NULL,
    text TEXT NOT NULL,
    category VARCHAR(50),
    priority VARCHAR(20) DEFAULT 'medium',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS evidence (
    id SERIAL PRIMARY KEY,
    requirement_id INTEGER NOT NULL REFERENCES requirements(id) ON DELETE CASCADE,
    source_doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    snippet TEXT NOT NULL,
    score FLOAT DEFAULT 0.0,
    evidence_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS facility_features (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    value TEXT,
    source_doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pricing_items (
    id SERIAL PRIMARY KEY,
    rfq_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    qty FLOAT DEFAULT 1.0,
    unit VARCHAR(50),
    unit_price FLOAT NOT NULL,
    total_price FLOAT,
    category VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS past_performance (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    client VARCHAR(200),
    scope TEXT,
    period VARCHAR(100),
    value FLOAT,
    ref_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_requirements_rfq_id ON requirements(rfq_id);
CREATE INDEX IF NOT EXISTS idx_evidence_requirement_id ON evidence(requirement_id);





