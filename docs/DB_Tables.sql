-- Enable UUID extension (useful if you want to use gen_random_uuid() or uuid_generate_v4())
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'analyst' CHECK (role IN ('analyst', 'admin')),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. Companies Table
CREATE TABLE companies (
    id UUID PRIMARY KEY,
    symbol TEXT UNIQUE NOT NULL,
    company_name TEXT NOT NULL,
    sector TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Watchlists Table
CREATE TABLE watchlists (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    frequency TEXT NOT NULL CHECK (frequency IN ('daily', 'weekly')),
    last_checked TIMESTAMP,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused'))
);

-- 4. Documents Table
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    document_type TEXT NOT NULL CHECK (document_type IN ('annual_report', 'announcement', 'other')),
    document_title TEXT,
    report_year TEXT,
    s3_key TEXT,
    source TEXT,
    upload_date TIMESTAMP DEFAULT NOW(),
    processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed'))
);

-- 5. Chunks Table
CREATE TABLE chunks (
    id UUID PRIMARY KEY,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    pinecone_namespace TEXT NOT NULL,
    chunk_count INT
);

-- 6. Analyst Reports Table
CREATE TABLE analyst_reports (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    broker_name TEXT,
    report_date DATE,
    s3_key TEXT,
    sentiment_score FLOAT CHECK (sentiment_score >= 0.0 AND sentiment_score <= 1.0)
);

-- 7. Update Logs Table
CREATE TABLE update_logs (
    id UUID PRIMARY KEY,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    update_type TEXT CHECK (update_type IN ('mcp_refresh', 'rag_process', 'manual')),
    status TEXT CHECK (status IN ('success', 'failed', 'skipped')),
    message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);