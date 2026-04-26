"""
supabase_client.py — Supabase Database Client
Helper functions untuk interact dengan Supabase database.
"""

import os
from typing import List, Dict, Optional

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Lazy load Supabase client to avoid import errors
_supabase_client = None

def _get_client():
    """Get or create Supabase client instance (internal use)."""
    global _supabase_client
    if _supabase_client is None:
        # Get credentials
        SUPABASE_URL = os.environ.get("SUPABASE_URL")
        SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        from supabase import create_client
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client


# ─────────────────────────────────────────
# USERS
# ─────────────────────────────────────────

def get_all_users() -> List[Dict]:
    """Get all active users."""
    response = _get_client().table('users').select('*').eq('active', True).execute()
    return response.data


def get_user_by_email(email: str) -> Optional[Dict]:
    """Get user by email."""
    response = _get_client().table('users').select('*').eq('email', email).execute()
    return response.data[0] if response.data else None


def create_user(email: str, is_admin: bool = False) -> Dict:
    """Create new user."""
    response = _get_client().table('users').insert({'email': email, 'is_admin': is_admin}).execute()
    return response.data[0]


def delete_user(user_id: str):
    """Delete user (cascade delete searches and seen_jobs)."""
    _get_client().table('users').delete().eq('id', user_id).execute()


def is_user_admin(email: str) -> bool:
    """Check if user is admin."""
    user = get_user_by_email(email)
    return user and user.get('is_admin', False)


# ─────────────────────────────────────────
# USER SUBSCRIPTIONS (DEPRECATED - Global searches removed)
# ─────────────────────────────────────────

# These functions are no longer used as global searches feature has been removed
# Keeping them commented for reference during migration

# def get_user_subscriptions(user_id: str) -> List[Dict]:
#     """Get all global searches that user is subscribed to."""
#     response = _get_client().table('user_search_subscriptions')\
#         .select('*, global_searches(*)')\
#         .eq('user_id', user_id)\
#         .execute()
#     
#     if not response.data:
#         return []
#     
#     return [item['global_searches'] for item in response.data if item.get('global_searches')]


# def subscribe_user_to_search(user_id: str, global_search_id: str):
#     """Subscribe user to a global search."""
#     try:
#         _get_client().table('user_search_subscriptions').insert({
#             'user_id': user_id,
#             'global_search_id': global_search_id
#         }).execute()
#     except Exception as e:
#         if 'duplicate' not in str(e).lower():
#             raise


# def unsubscribe_user_from_search(user_id: str, global_search_id: str):
#     """Unsubscribe user from a global search."""
#     _get_client().table('user_search_subscriptions')\
#         .delete()\
#         .eq('user_id', user_id)\
#         .eq('global_search_id', global_search_id)\
#         .execute()


# def get_subscribed_users_for_search(global_search_id: str) -> List[Dict]:
#     """Get all users subscribed to a specific global search."""
#     response = _get_client().table('user_search_subscriptions')\
#         .select('*, users(*)')\
#         .eq('global_search_id', global_search_id)\
#         .execute()
#     return [item['users'] for item in response.data if item.get('users') and item['users'].get('active')]


# ─────────────────────────────────────────
# SEARCHES
# ─────────────────────────────────────────

def get_user_searches(user_id: str, active_only: bool = True) -> List[Dict]:
    """Get all searches for a user."""
    query = _get_client().table('searches').select('*').eq('user_id', user_id)
    if active_only:
        query = query.eq('active', True)
    response = query.execute()
    return response.data


def get_all_active_searches() -> List[Dict]:
    """Get all active searches from all users."""
    response = _get_client().table('searches').select('*, users(email)').eq('active', True).execute()
    return response.data


# ─────────────────────────────────────────
# GLOBAL SEARCHES (DEPRECATED - Feature removed)
# ─────────────────────────────────────────

# Global searches feature has been removed. Each user now has their own personal search.
# Keeping these functions commented for reference during migration

# def get_global_searches(active_only: bool = True) -> List[Dict]:
#     """Get global searches (shared by all users)."""
#     query = _get_client().table('global_searches').select('*')
#     if active_only:
#         query = query.eq('active', True)
#     response = query.execute()
#     return response.data


# def create_global_search(search_data: Dict) -> Dict:
#     """Create new global search."""
#     response = _get_client().table('global_searches').insert(search_data).execute()
#     return response.data[0]


# def update_global_search(search_id: str, search_data: Dict) -> Dict:
#     """Update existing global search."""
#     response = _get_client().table('global_searches').update(search_data).eq('id', search_id).execute()
#     return response.data[0]


# def delete_global_search(search_id: str):
#     """Delete global search."""
#     _get_client().table('global_searches').delete().eq('id', search_id).execute()


def create_search(user_id: str, search_data: Dict) -> Dict:
    """Create new search for user."""
    search_data['user_id'] = user_id
    response = _get_client().table('searches').insert(search_data).execute()
    return response.data[0]


def update_search(search_id: str, search_data: Dict) -> Dict:
    """Update existing search."""
    response = _get_client().table('searches').update(search_data).eq('id', search_id).execute()
    return response.data[0]


def delete_search(search_id: str):
    """Delete search."""
    _get_client().table('searches').delete().eq('id', search_id).execute()


# ─────────────────────────────────────────
# SEEN JOBS
# ─────────────────────────────────────────

def get_seen_jobs(user_id: str) -> List[str]:
    """Get all seen job hashes for a user."""
    response = _get_client().table('seen_jobs').select('job_hash').eq('user_id', user_id).execute()
    return [job['job_hash'] for job in response.data]


def mark_job_as_seen(user_id: str, job_data: Dict):
    """Mark a job as seen for a user."""
    data = {
        'user_id': user_id,
        'job_hash': job_data['hash'],
        'job_title': job_data['title'],
        'job_url': job_data['url'],
        'job_snippet': job_data.get('snippet', ''),
        'search_label': job_data.get('search_label', '')
    }
    try:
        _get_client().table('seen_jobs').insert(data).execute()
    except Exception as e:
        # Ignore duplicate errors (job already marked as seen)
        if 'duplicate' not in str(e).lower():
            raise


def bulk_mark_jobs_as_seen(user_id: str, jobs: List[Dict]):
    """Mark multiple jobs as seen for a user."""
    data = []
    for job in jobs:
        data.append({
            'user_id': user_id,
            'job_hash': job['hash'],
            'job_title': job['title'],
            'job_url': job['url'],
            'job_snippet': job.get('snippet', ''),
            'search_label': job.get('search_label', '')
        })
    
    if data:
        try:
            _get_client().table('seen_jobs').insert(data).execute()
        except Exception as e:
            # Ignore duplicate errors
            if 'duplicate' not in str(e).lower():
                raise


# ─────────────────────────────────────────
# SETTINGS
# ─────────────────────────────────────────

def get_setting(key: str) -> any:
    """Get a setting value."""
    response = _get_client().table('settings').select('value').eq('key', key).execute()
    if response.data:
        return response.data[0]['value']
    return None


def set_setting(key: str, value: any):
    """Set a setting value."""
    _get_client().table('settings').upsert(
        {'key': key, 'value': value},
        on_conflict='key'
    ).execute()


def get_all_settings() -> Dict:
    """Get all settings as a dictionary."""
    response = _get_client().table('settings').select('*').execute()
    return {item['key']: item['value'] for item in response.data}


# ─────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────

def get_config_for_scraper() -> Dict:
    """
    Get configuration in the same format as config.json
    for backward compatibility with scraper.py
    
    NOTE: Global searches feature has been removed.
    This function now only returns basic config without searches list.
    Scraper will get searches directly from each user's personal searches.
    """
    settings = get_all_settings()
    users = get_all_users()
    
    # Build config structure (without searches - each user has their own)
    config = {
        "meta": {
            "version": "3.0.0",
            "last_updated": "",
            "description": "Config from Supabase - Personal searches per user"
        },
        "search_engine": settings.get('search_engine', 'google'),
        "email_settings": {
            "recipients": [user['email'] for user in users],
            "subject_prefix": settings.get('subject_prefix', '[Loker Alert]'),
            "max_results_per_email": settings.get('max_results_per_email', 20),
            "send_if_empty": settings.get('send_if_empty', False)
        },
        "schedule": {
            "cron": settings.get('cron_schedule', '0 8 * * *'),
            "timezone": settings.get('timezone', 'Asia/Jakarta'),
            "description": "Setiap hari jam 08:00 WIB"
        },
        "searches": []  # Empty - searches are now per-user, not global
    }
    
    return config


def get_seen_jobs_dict() -> Dict[str, List[str]]:
    """
    Get seen jobs in the same format as seen_jobs.json
    for backward compatibility.
    """
    users = get_all_users()
    seen_jobs_dict = {}
    
    for user in users:
        seen_hashes = get_seen_jobs(user['id'])
        seen_jobs_dict[user['email']] = seen_hashes
    
    return seen_jobs_dict


def save_seen_jobs_from_dict(seen_jobs_dict: Dict[str, List[str]]):
    """
    Save seen jobs from dictionary format (for migration).
    """
    for email, hashes in seen_jobs_dict.items():
        user = get_user_by_email(email)
        if not user:
            user = create_user(email)
        
        for job_hash in hashes:
            try:
                mark_job_as_seen(user['id'], {
                    'hash': job_hash,
                    'title': 'Migrated job',
                    'url': '',
                    'snippet': ''
                })
            except:
                pass  # Ignore duplicates


# ─────────────────────────────────────────
# MIGRATION HELPERS (DEPRECATED)
# ─────────────────────────────────────────

# These migration helpers are no longer needed as global searches feature has been removed

# def migrate_from_config_json(config: Dict):
#     """Migrate data from config.json to Supabase."""
#     print("🔄 Migrating from config.json to Supabase...")
#     
#     # Migrate settings
#     set_setting('search_engine', config.get('search_engine', 'google'))
#     set_setting('subject_prefix', config['email_settings'].get('subject_prefix', '[Loker Alert]'))
#     set_setting('max_results_per_email', config['email_settings'].get('max_results_per_email', 20))
#     set_setting('send_if_empty', config['email_settings'].get('send_if_empty', False))
#     set_setting('cron_schedule', config['schedule'].get('cron', '0 8 * * *'))
#     set_setting('timezone', config['schedule'].get('timezone', 'Asia/Jakarta'))
#     
#     # Migrate users
#     for email in config['email_settings']['recipients']:
#         if not get_user_by_email(email):
#             create_user(email)
#             print(f"  ✅ Created user: {email}")
#     
#     # Note: Searches are no longer global, users need to create their own
#     print("✅ Migration complete!")


# def migrate_from_seen_jobs_json(seen_jobs: Dict[str, List[str]]):
#     """Migrate data from seen_jobs.json to Supabase."""
#     print("🔄 Migrating from seen_jobs.json to Supabase...")
#     
#     for email, hashes in seen_jobs.items():
#         user = get_user_by_email(email)
#         if not user:
#             user = create_user(email)
#         
#         print(f"  Migrating {len(hashes)} jobs for {email}...")
#         for job_hash in hashes:
#             try:
#                 mark_job_as_seen(user['id'], {
#                     'hash': job_hash,
#                     'title': 'Migrated',
#                     'url': '',
#                     'snippet': ''
#                 })
#             except:
#                 pass  # Ignore duplicates
#         
#         print(f"  ✅ Migrated {len(hashes)} jobs for {email}")
#     
#     print("✅ Migration complete!")
