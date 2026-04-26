# Source Code

Folder ini berisi source code Python untuk Loker Notifier.

## Structure

```
src/
├── __init__.py           # Package initialization
├── main.py               # Main entry point
├── scraper.py            # Job scraping engine
├── mailer.py             # Email notification engine
└── supabase_client.py    # Supabase database client
```

## Modules

### main.py
Entry point utama yang menjalankan complete flow:
1. Scrape jobs dari subscribed searches
2. Send email notifications ke users

**Usage:**
```bash
python src/main.py
```

### scraper.py
Core scraping engine dengan fitur:
- Build Google Dork queries dari Supabase config
- Multi-engine support (Google, DuckDuckGo, Bing)
- API support (SerpAPI, Serper.dev)
- Per-user job deduplication
- Subscription-based filtering

**Key Functions:**
- `load_config()` - Load config dari Supabase
- `build_dork(search)` - Build Google Dork query
- `run_all_searches(config)` - Run semua searches per-user
- `fetch_google()` - Fetch dengan API fallback

### mailer.py
Email notification engine dengan fitur:
- HTML email templates
- Per-user personalized emails
- SMTP support (Gmail, Outlook, custom)
- Grouped by search label

**Key Functions:**
- `send_email_to_user(recipient, jobs, config)` - Send ke single user
- `send_emails_per_user(results, config)` - Send ke multiple users
- `build_html_email(jobs, config)` - Build HTML template

### supabase_client.py
Database client untuk Supabase dengan fitur:
- User management (CRUD)
- Search management (global & per-user)
- Subscription management
- Seen jobs tracking
- Settings management
- Migration helpers

**Key Functions:**
- `get_all_users()` - Get active users
- `get_user_subscriptions(user_id)` - Get user's subscribed searches
- `bulk_mark_jobs_as_seen(user_id, jobs)` - Mark jobs as seen
- `get_config_for_scraper()` - Get config for backward compatibility

## Environment Variables

Required:
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase anon/service key
- `SMTP_HOST` - SMTP server host
- `SMTP_PORT` - SMTP server port
- `SMTP_USER` - SMTP username
- `SMTP_PASS` - SMTP password
- `SMTP_FROM` - Sender email address

Optional:
- `SERPAPI_KEY` - SerpAPI key (for Google search)
- `SERPER_API_KEY` - Serper.dev key (for Google search)

## Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Setup .env file
cp .env.example .env
# Edit .env dengan credentials kamu

# Run scraper only
python src/scraper.py

# Run mailer only (requires results.json)
python src/mailer.py

# Run complete flow
python src/main.py
```

## Import Structure

```python
# From other modules
from src.scraper import load_config, run_all_searches
from src.mailer import send_emails_per_user
from src.supabase_client import get_all_users

# From GitHub Actions
python src/main.py
```

## Notes

- Semua modules support `.env` file untuk local testing
- Production menggunakan environment variables dari GitHub Secrets
- Backward compatible dengan config.json format
- Per-user subscription system untuk personalized notifications
