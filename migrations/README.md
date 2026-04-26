# Database Migrations

Folder ini berisi SQL migration files untuk Supabase database.

## Files

1. **supabase_schema.sql** - Initial database schema
   - Tables: users, searches, seen_jobs, settings
   - Indexes, triggers, RLS policies
   - Sample data
   - **NOTE:** Global searches feature has been removed

2. **supabase_migration_auth.sql** - Authentication & subscription system (DEPRECATED)
   - This file is no longer needed as global searches feature has been removed

3. **add_is_admin_column.sql** - Add admin role and cleanup
   - Add is_admin column to users table
   - Set dedenruslan19@gmail.com as admin
   - Remove global_searches and user_search_subscriptions tables

## Current System Design

### User Roles
- **Admin** (dedenruslan19@gmail.com only)
  - Can manage users (add/remove)
  - Can create 1 personal search for themselves
  - Cannot create global searches (feature removed)

- **Regular Users**
  - Can create 1 personal search for themselves
  - Cannot manage users

### Search Limits
- **1 search per user** (maximum)
- Each user can only have their own personal search
- No global/shared searches anymore

## How to Run

### Via Supabase Dashboard
1. Login ke [Supabase Dashboard](https://app.supabase.com)
2. Pilih project kamu
3. Buka **SQL Editor**
4. Copy-paste isi file SQL
5. Klik **Run**

### Via Supabase CLI
```bash
# Install Supabase CLI
npm install -g supabase

# Login
supabase login

# Link to your project
supabase link --project-ref YOUR_PROJECT_REF

# Run migrations
supabase db push

# Or run specific file
psql -h YOUR_DB_HOST -U postgres -d postgres -f migrations/supabase_schema.sql
```

## Migration Order

Jalankan migrations sesuai urutan:
1. `supabase_schema.sql` (base schema)
2. `add_is_admin_column.sql` (add admin role and cleanup)

## Notes

- Semua migrations menggunakan `IF NOT EXISTS` untuk idempotency
- Safe untuk dijalankan multiple times
- RLS (Row Level Security) sudah enabled
- Service role memiliki full access
- Global searches feature has been completely removed
