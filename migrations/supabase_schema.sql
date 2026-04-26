-- ============================================
-- Loker Notifier - Supabase Database Schema
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- Table: users
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    is_admin BOOLEAN DEFAULT false,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for faster email lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(active);

-- ============================================
-- Table: searches
-- ============================================
CREATE TABLE IF NOT EXISTS searches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    label TEXT NOT NULL,
    keyword TEXT NOT NULL,
    platform TEXT,
    lokasi_kerja TEXT,
    waktu_kerja TEXT,
    kota TEXT,
    exclude_keywords TEXT[],
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_searches_user_id ON searches(user_id);
CREATE INDEX IF NOT EXISTS idx_searches_active ON searches(active);

-- ============================================
-- Table: seen_jobs
-- ============================================
CREATE TABLE IF NOT EXISTS seen_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    job_hash TEXT NOT NULL,
    job_title TEXT NOT NULL,
    job_url TEXT NOT NULL,
    job_snippet TEXT,
    search_label TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_seen_jobs_user_id ON seen_jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_seen_jobs_hash ON seen_jobs(job_hash);
CREATE INDEX IF NOT EXISTS idx_seen_jobs_user_hash ON seen_jobs(user_id, job_hash);

-- Unique constraint to prevent duplicate job tracking per user
CREATE UNIQUE INDEX IF NOT EXISTS idx_seen_jobs_unique ON seen_jobs(user_id, job_hash);

-- ============================================
-- Table: global_searches (REMOVED - not used anymore)
-- ============================================
-- Global searches feature has been removed
-- Each user now has their own personal search only

-- ============================================
-- Table: settings (global settings)
-- ============================================
CREATE TABLE IF NOT EXISTS settings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key TEXT UNIQUE NOT NULL,
    value JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default settings
INSERT INTO settings (key, value) VALUES
    ('search_engine', '"google"'::jsonb),
    ('subject_prefix', '"[Loker Alert]"'::jsonb),
    ('max_results_per_email', '20'::jsonb),
    ('send_if_empty', 'false'::jsonb),
    ('cron_schedule', '"0 8 * * *"'::jsonb),
    ('timezone', '"Asia/Jakarta"'::jsonb)
ON CONFLICT (key) DO NOTHING;

-- ============================================
-- Functions
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_searches_updated_at ON searches;
CREATE TRIGGER update_searches_updated_at BEFORE UPDATE ON searches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Removed: global_searches trigger

DROP TRIGGER IF EXISTS update_settings_updated_at ON settings;
CREATE TRIGGER update_settings_updated_at BEFORE UPDATE ON settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- Row Level Security (RLS)
-- ============================================
-- IMPORTANT: RLS is enabled for security
-- Backend uses SERVICE ROLE key (not anon key) so it has full access
-- Frontend does NOT use anon key directly - all operations go through backend

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE searches ENABLE ROW LEVEL SECURITY;
ALTER TABLE seen_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE settings ENABLE ROW LEVEL SECURITY;

-- Policies: Allow all operations for service role (backend)
-- These policies allow the backend (using service role key) to perform all operations
DROP POLICY IF EXISTS "Allow all for service role" ON users;
CREATE POLICY "Allow all for service role" ON users FOR ALL USING (true);

DROP POLICY IF EXISTS "Allow all for service role" ON searches;
CREATE POLICY "Allow all for service role" ON searches FOR ALL USING (true);

DROP POLICY IF EXISTS "Allow all for service role" ON seen_jobs;
CREATE POLICY "Allow all for service role" ON seen_jobs FOR ALL USING (true);

DROP POLICY IF EXISTS "Allow all for service role" ON settings;
CREATE POLICY "Allow all for service role" ON settings FOR ALL USING (true);

-- ============================================
-- Sample Data (Optional)
-- ============================================

-- Insert admin user
INSERT INTO users (email, is_admin) VALUES ('dedenruslan19@gmail.com', true)
ON CONFLICT (email) DO UPDATE SET is_admin = true;

-- Removed: sample global search (feature removed)

-- ============================================
-- Views (Optional - for easier queries)
-- ============================================

-- View: User with search count
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    u.id,
    u.email,
    u.active,
    COUNT(DISTINCT s.id) as search_count,
    COUNT(DISTINCT sj.id) as seen_jobs_count,
    u.created_at
FROM users u
LEFT JOIN searches s ON u.id = s.user_id
LEFT JOIN seen_jobs sj ON u.id = sj.user_id
GROUP BY u.id, u.email, u.active, u.created_at;

-- ============================================
-- Indexes for Performance
-- ============================================

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_searches_user_active ON searches(user_id, active);
CREATE INDEX IF NOT EXISTS idx_seen_jobs_created_at ON seen_jobs(created_at DESC);

-- ============================================
-- Comments
-- ============================================

COMMENT ON TABLE users IS 'Email recipients for job notifications';
COMMENT ON TABLE searches IS 'Per-user search configurations (max 1 per user)';
COMMENT ON TABLE seen_jobs IS 'Track which jobs have been sent to which users';
COMMENT ON TABLE settings IS 'Global application settings';

-- ============================================
-- Done!
-- ============================================

-- Verify tables
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE schemaname = 'public'
AND tablename IN ('users', 'searches', 'seen_jobs', 'settings')
ORDER BY tablename;
