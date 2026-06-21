-- 1. Users Table
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    role TEXT DEFAULT 'analyst' CHECK (role IN ('analyst', 'admin')),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. Companies Table
CREATE TABLE companies (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT UNIQUE NOT NULL,
    company_name TEXT NOT NULL,
    sector TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Watchlists Table
CREATE TABLE watchlists (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id BIGINT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    frequency TEXT NOT NULL CHECK (frequency IN ('daily', 'weekly')),
    last_checked TIMESTAMP,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused'))
);

-- 4. Documents Table
CREATE TABLE documents (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
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
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    pinecone_namespace TEXT NOT NULL,
    chunk_count INT
);

-- 6. Analyst Reports Table
CREATE TABLE analyst_reports (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    broker_name TEXT,
    report_date DATE,
    s3_key TEXT,
    sentiment_score FLOAT CHECK (sentiment_score >= 0.0 AND sentiment_score <= 1.0)
);

-- 7. Update Logs Table
CREATE TABLE update_logs (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    update_type TEXT CHECK (update_type IN ('mcp_refresh', 'rag_process', 'manual')),
    status TEXT CHECK (status IN ('success', 'failed', 'skipped')),
    message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 8. NSE Corporate Announcements Table
CREATE TABLE nsc_announcements (
    id BIGSERIAL PRIMARY KEY,
    seq_id TEXT UNIQUE NOT NULL,
    symbol TEXT NOT NULL,
    sm_name TEXT,
    sm_isin TEXT,
    sm_industry TEXT,
    description TEXT,
    attchmnt_text TEXT,
    attchmnt_file TEXT,
    att_file_size TEXT,
    file_size TEXT,
    has_xbrl BOOLEAN,
    an_dt TEXT,
    exchdisstime TEXT,
    dt TEXT,
    sort_date TEXT,
    difference TEXT,
    bflag TEXT,
    csv_name TEXT,
    old_new TEXT,
    orgid TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);