-- Drops NOT NULL constraints left over from original table creation,
-- to bring the live database in line with docs/DB_Tables.sql.

ALTER TABLE users ALTER COLUMN email DROP NOT NULL;

ALTER TABLE companies ALTER COLUMN symbol DROP NOT NULL;
ALTER TABLE companies ALTER COLUMN company_name DROP NOT NULL;

ALTER TABLE watchlists ALTER COLUMN user_id DROP NOT NULL;
ALTER TABLE watchlists ALTER COLUMN company_id DROP NOT NULL;
ALTER TABLE watchlists ALTER COLUMN frequency DROP NOT NULL;

ALTER TABLE documents ALTER COLUMN company_id DROP NOT NULL;
ALTER TABLE documents ALTER COLUMN document_type DROP NOT NULL;

ALTER TABLE chunks ALTER COLUMN document_id DROP NOT NULL;
ALTER TABLE chunks ALTER COLUMN pinecone_namespace DROP NOT NULL;

ALTER TABLE analyst_reports ALTER COLUMN company_id DROP NOT NULL;

ALTER TABLE update_logs ALTER COLUMN company_id DROP NOT NULL;

ALTER TABLE annual_reports ALTER COLUMN company_id DROP NOT NULL;
ALTER TABLE annual_reports ALTER COLUMN symbol DROP NOT NULL;

ALTER TABLE nsc_announcements ALTER COLUMN seq_id DROP NOT NULL;
ALTER TABLE nsc_announcements ALTER COLUMN symbol DROP NOT NULL;