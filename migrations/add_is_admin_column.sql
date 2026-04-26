-- ============================================
-- Migration: Add is_admin column to users table
-- ============================================

-- Add is_admin column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'users' AND column_name = 'is_admin'
    ) THEN
        ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT false;
    END IF;
END $$;

-- Set dedenruslan19@gmail.com as admin
UPDATE users 
SET is_admin = true 
WHERE email = 'dedenruslan19@gmail.com';

-- Insert admin user if not exists
INSERT INTO users (email, is_admin, active) 
VALUES ('dedenruslan19@gmail.com', true, true)
ON CONFLICT (email) DO UPDATE SET is_admin = true;

-- Drop global_searches table and related tables if they exist
DROP TABLE IF EXISTS user_search_subscriptions CASCADE;
DROP TABLE IF EXISTS global_searches CASCADE;

-- Verify the changes
SELECT email, is_admin, active FROM users ORDER BY is_admin DESC, email;
