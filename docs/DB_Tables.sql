-- 1. Users Table
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email TEXT UNIQUE,
    password_hash TEXT,
    full_name TEXT,
    role TEXT DEFAULT 'analyst' CHECK (role IN ('analyst', 'admin')),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. Companies Table
CREATE TABLE companies (
    id BIGSERIAL PRIMARY KEY,
    symbol TEXT UNIQUE,
    company_name TEXT,
    sector TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Watchlists Table
CREATE TABLE watchlists (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(id) ON DELETE CASCADE,
    company_id BIGINT REFERENCES companies(id) ON DELETE CASCADE,
    frequency TEXT CHECK (frequency IN ('daily', 'weekly')),
    last_checked TIMESTAMP,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused'))
);

-- 4. Documents Table
CREATE TABLE documents (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT REFERENCES companies(id) ON DELETE CASCADE,
    document_type TEXT CHECK (document_type IN ('annual_report', 'announcement', 'other')),
    document_title TEXT,
    report_year TEXT,
    file_name TEXT,
    s3_key TEXT,
    source TEXT,
    upload_date TIMESTAMP DEFAULT NOW(),
    processing_status TEXT DEFAULT 'pending' CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed'))
);

-- 5. Chunks Table
CREATE TABLE chunks (
    id BIGSERIAL PRIMARY KEY,
    document_id BIGINT REFERENCES documents(id) ON DELETE CASCADE,
    pinecone_namespace TEXT,
    chunk_count INT
);

-- 6. Analyst Reports Table
CREATE TABLE analyst_reports (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT REFERENCES companies(id) ON DELETE CASCADE,
    broker_name TEXT,
    report_date DATE,
    s3_key TEXT,
    sentiment_score FLOAT CHECK (sentiment_score >= 0.0 AND sentiment_score <= 1.0)
);

-- 7. Update Logs Table
CREATE TABLE update_logs (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT REFERENCES companies(id) ON DELETE CASCADE,
    update_type TEXT CHECK (update_type IN ('mcp_refresh', 'rag_process', 'manual')),
    status TEXT CHECK (status IN ('success', 'failed', 'skipped')),
    message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 8. Annual Reports Table
CREATE TABLE annual_reports (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT REFERENCES companies(id) ON DELETE CASCADE,
    symbol TEXT,
    company_name TEXT,
    from_yr TEXT,
    to_yr TEXT,
    submission_type TEXT,
    broadcast_dttm TEXT,
    dissemination_date_time TEXT,
    time_taken TEXT,
    file_name TEXT UNIQUE,
    att_file_size TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 9. Integrated Filing Results Table
CREATE TABLE integrated_results (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT REFERENCES companies(id) ON DELETE CASCADE,
    seq_id TEXT UNIQUE,
    symbol TEXT,
    cm_name TEXT,
    sm_name TEXT,
    audited TEXT,
    consolidated TEXT,
    type TEXT,
    type_sub TEXT,
    qe_date TEXT,
    broadcast_date TEXT,
    creation_date TEXT,
    revised_date TEXT,
    revision_remark TEXT,
    diff TEXT,
    ixbrl TEXT,
    ixbrl_file_size TEXT,
    xbrl TEXT,
    xbrl_file_size TEXT,
    pdf_attach TEXT,
    att_file_size TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 10. NSE Corporate Announcements Table
CREATE TABLE nsc_announcements (
    id BIGSERIAL PRIMARY KEY,
    company_id BIGINT REFERENCES companies(id) ON DELETE CASCADE,
    seq_id TEXT UNIQUE,
    symbol TEXT,
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