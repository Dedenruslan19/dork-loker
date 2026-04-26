# 🔔 Dork Loker

> Google Dork-based job alert via SMTP email, automated with GitHub Actions.

Sistem notifikasi lowongan kerja otomatis menggunakan Google Dork queries, Supabase database, dan GitHub Actions. Kirim email personalized ke setiap user berdasarkan subscription mereka.

---

## ✨ Features

- 🔍 **Google Dork Scraping** - Build custom search queries
- 🌐 **Multi-Engine Support** - Google, DuckDuckGo, Bing
- 🔑 **API Integration** - SerpAPI, Serper.dev
- 👥 **Multi-User System** - Per-user subscriptions & tracking
- 📧 **SMTP Email** - HTML templates dengan grouping
- 🗄️ **Supabase Database** - User management & job tracking
- ⏰ **GitHub Actions** - Automated daily cron job
- 🎨 **Web Dashboard** - Manage searches & subscriptions
- 🔐 **Authentication** - Email-based login system
- 📊 **Admin Panel** - User & search management

---

## 🏗️ Project Structure

```
dork-loker/
├── .github/workflows/
│   └── cron.yml              # GitHub Actions workflow
│
├── src/                      # Python source code
│   ├── __init__.py
│   ├── main.py               # Entry point
│   ├── scraper.py            # Scraping engine
│   ├── mailer.py             # Email engine
│   └── supabase_client.py    # Database client
│
├── public/                   # Frontend (GitHub Pages)
│   ├── index.html            # Standalone dashboard
│   └── dashboard.html        # Auth dashboard
│
├── migrations/               # Database migrations
│   ├── supabase_schema.sql
│   └── supabase_migration_auth.sql
│
├── config.json               # Optional config file
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
└── README.md                 # This file
```

---

## 🚀 Quick Setup

### 1. Fork & Clone

```bash
git clone https://github.com/USERNAME/dork-loker.git
cd dork-loker
```

### 2. Setup Supabase Database

1. Create account di [Supabase](https://supabase.com)
2. Create new project
3. Buka **SQL Editor**
4. Run migrations:
   - Copy-paste `migrations/supabase_schema.sql` → Run
   - Copy-paste `migrations/supabase_migration_auth.sql` → Run
5. Get credentials:
   - **Settings → API** → Copy `Project URL` dan `anon public` key

### 3. Setup GitHub Secrets

**Settings → Secrets and variables → Actions → New repository secret**

#### Required Secrets:

| Secret | Value | Example |
|--------|-------|---------|
| `SUPABASE_URL` | Supabase project URL | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | Supabase anon key | `eyJhbGc...` |
| `SMTP_HOST` | SMTP server | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USER` | Email address | `your@gmail.com` |
| `SMTP_PASS` | App password | `abcd efgh ijkl mnop` |
| `SMTP_FROM` | Sender email | `your@gmail.com` |

#### Optional Secrets (Recommended):

| Secret | Value | Get From |
|--------|-------|----------|
| `SERPAPI_KEY` | SerpAPI key | [serpapi.com](https://serpapi.com) (100 free/month) |
| `SERPER_API_KEY` | Serper key | [serper.dev](https://serper.dev) (2,500 free/month) |

#### SMTP Setup Guide:

**Gmail (Recommended):**
1. Enable 2FA di Google Account
2. Buka: https://myaccount.google.com/apppasswords
3. Create password untuk "Mail"
4. Copy 16 karakter → paste ke `SMTP_PASS`

**Outlook/Hotmail:**
- Host: `smtp-mail.outlook.com`
- Port: `587`

**Yahoo:**
- Host: `smtp.mail.yahoo.com`
- Port: `587`

### 4. Setup Frontend Configuration

Update `public/config.js` with your Supabase credentials:

```javascript
window.SUPABASE_CONFIG = {
  url: 'https://YOUR_PROJECT.supabase.co',
  anonKey: 'YOUR_ANON_KEY_HERE'
};
```

**Note:** The anon key is safe to expose in frontend. It only allows read access with Row Level Security (RLS) enabled.

Commit and push:
```bash
git add public/config.js
git commit -m "Update Supabase config"
git push
```

### 5. Enable GitHub Pages

1. **Settings → Pages**
2. Source: **Deploy from branch**
3. Branch: **main**
4. Folder: **/ (root)**
5. Save & wait ~1 minute

Access dashboard:
- Main: `https://USERNAME.github.io/dork-loker/public/`
- Auth: `https://USERNAME.github.io/dork-loker/public/dashboard.html`

### 6. Configure Searches

#### Option A: User Dashboard (Recommended)

1. Open `https://USERNAME.github.io/dork-loker/public/`
2. Login with your registered email
3. Create custom searches with filters
4. Subscribe to global searches (if available)
5. Done! You'll receive daily emails

#### Option B: Admin Dashboard

1. Open `https://USERNAME.github.io/dork-loker/public/dashboard.html`
2. Login with admin email (set `is_admin: true` in Supabase)
3. Add users to the system
4. Create global searches for all users
5. Users can subscribe via their dashboard

---

## 🔍 How It Works

### System Flow

```
┌─────────────────────────────────────────────────────────┐
│         GitHub Actions (Daily at 08:00 WIB)             │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                  src/main.py                            │
│              Orchestrate Flow                           │
└────────┬────────────────────────────┬───────────────────┘
         │                            │
         ▼                            ▼
┌────────────────────┐      ┌────────────────────┐
│  src/scraper.py    │      │   src/mailer.py    │
│  - Load config     │      │  - Build HTML      │
│  - Build dorks     │      │  - Send emails     │
│  - Fetch jobs      │      │  - Per-user        │
│  - Deduplicate     │      └────────────────────┘
└─────────┬──────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────┐
│            src/supabase_client.py                       │
│            Database Operations                          │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                Supabase Database                        │
│  users | global_searches | subscriptions | seen_jobs   │
└─────────────────────────────────────────────────────────┘
```

### Scraping Process

1. **Load Config** - Get user subscriptions from Supabase
2. **Build Dorks** - Generate Google Dork queries per search
3. **Fetch Results** - Try API first, fallback to HTML scraping
4. **Deduplicate** - Filter out jobs already seen by each user
5. **Save to DB** - Mark new jobs as seen in Supabase
6. **Generate Results** - Create `results.json` per-user

### Email Process

1. **Load Results** - Read `results.json` per-user
2. **Build HTML** - Generate personalized email template
3. **Group by Label** - Organize jobs by search label
4. **Send via SMTP** - Deliver to each user's inbox
5. **Rate Limiting** - 1 second delay between emails

### Search Engines

**Priority Order:**
1. **SerpAPI** (if `SERPAPI_KEY` available) - Most reliable
2. **Serper.dev** (if `SERPER_API_KEY` available) - Good alternative
3. **HTML Scraping** - Fallback (may get blocked)

**Handling Blocks:**
- If Google blocks: Skip run, no email sent
- Next run: GitHub Actions gets new IP
- Usually works on retry

---

## 🧪 Local Testing

### Setup Environment

```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your editor
```

### Test Components

```bash
# Test SMTP connection
python -c "from src.mailer import *; print('✅ SMTP OK')"

# Test scraper only
python src/scraper.py

# Test mailer only (requires results.json)
python src/mailer.py

# Run complete flow
python src/main.py
```

### Manual Workflow Trigger

1. Go to **Actions** tab
2. Select **Dork Loker** workflow
3. Click **Run workflow**
4. Select branch **main**
5. Click **Run workflow**
6. Wait ~5-10 minutes
7. Check logs & email inbox

---

## 📊 Database Schema

### Tables

**users**
- `id` (UUID, PK)
- `email` (TEXT, UNIQUE)
- `is_admin` (BOOLEAN)
- `active` (BOOLEAN)
- `created_at`, `updated_at`

**global_searches**
- `id` (UUID, PK)
- `label`, `keyword`, `platform`
- `lokasi_kerja`, `waktu_kerja`, `kota`
- `exclude_keywords` (TEXT[])
- `active` (BOOLEAN)

**user_search_subscriptions**
- `id` (UUID, PK)
- `user_id` (FK → users)
- `global_search_id` (FK → global_searches)
- UNIQUE(user_id, global_search_id)

**seen_jobs**
- `id` (UUID, PK)
- `user_id` (FK → users)
- `job_hash`, `job_title`, `job_url`
- `search_label`, `created_at`
- UNIQUE(user_id, job_hash)

**settings**
- `id` (UUID, PK)
- `key` (TEXT, UNIQUE)
- `value` (JSONB)

---

## 🎨 Dashboard Features

### User Dashboard (index.html)

**For Regular Users:**
- ✅ Email-based login
- ✅ Create custom searches with keyword filtering
- ✅ Edit/delete your own searches
- ✅ Subscribe to global searches (created by admin)
- ✅ Real-time Google Dork preview
- ✅ Active/inactive search toggle
- ✅ Receive daily personalized emails

**Features:**
- 🔍 Custom search creation with filters:
  - Keyword (e.g., "frontend developer")
  - Location type (remote/hybrid/on-site)
  - Employment type (full-time/part-time/freelance/internship)
  - City (Jakarta, Bandung, etc.)
  - Exclude keywords (senior, lead, manager)
- 🌐 Subscribe to global searches created by admin
- 📧 Get daily email notifications for matching jobs

### Admin Dashboard (dashboard.html)

**For Admins Only:**
- 👥 User management (add/remove users)
- 🔍 Global search management (shared searches)
- 📊 Statistics & overview
- 🔐 Admin-only access (auto-redirect non-admins)

**Admin Features:**
- Add/remove users from the system
- Create global searches that all users can subscribe to
- View all users and their admin status
- Manage search configurations

### Configuration Files

**public/config.js** - Supabase credentials (auto-loaded)
```javascript
window.SUPABASE_CONFIG = {
  url: 'YOUR_SUPABASE_URL',
  anonKey: 'YOUR_SUPABASE_ANON_KEY'
};
```

**Note:** The anon key is safe to expose in frontend (read-only with Row Level Security)

---

## 🔧 Configuration

### Google Dork Syntax

Build powerful search queries:

```
"software engineer" "remote" Jakarta 2026 -"senior" -"lead"
```

**Operators:**
- `"exact phrase"` - Exact match
- `site:linkedin.com` - Specific site
- `OR` - Alternative terms
- `-keyword` - Exclude term
- `*` - Wildcard

**Example Searches:**

```json
{
  "label": "Remote Developer Jakarta",
  "keyword": "software engineer",
  "lokasi_kerja": "remote",
  "waktu_kerja": "full-time",
  "kota": "Jakarta",
  "exclude_keywords": ["senior", "lead", "manager"]
}
```

Generates:
```
"software engineer" "remote" "full-time" Jakarta -"senior" -"lead" -"manager" 2026
```

### Email Settings

Customize in Supabase `settings` table:

```json
{
  "subject_prefix": "[Loker Alert]",
  "max_results_per_email": 20,
  "send_if_empty": false,
  "search_engine": "google"
}
```

### Cron Schedule

Edit `.github/workflows/cron.yml`:

```yaml
schedule:
  - cron: "0 1 * * *"  # 08:00 WIB (01:00 UTC)
```

**Examples:**
- `0 */6 * * *` - Every 6 hours
- `0 9,17 * * *` - 09:00 & 17:00 WIB
- `0 1 * * 1-5` - Weekdays only

---

## 🐛 Troubleshooting

### Workflow Failed

**Error: SMTP authentication failed**
- ✅ Check SMTP credentials in GitHub Secrets
- ✅ Use App Password (not account password)
- ✅ Verify SMTP_HOST and SMTP_PORT

**Error: Supabase connection failed**
- ✅ Check SUPABASE_URL and SUPABASE_KEY
- ✅ Verify migrations ran successfully
- ✅ Check Supabase project status

**Error: No results found**
- ✅ Google may have blocked GitHub Actions IP
- ✅ Use SerpAPI or Serper.dev (recommended)
- ✅ Wait for next run (new IP)

### Email Not Received

1. Check spam/junk folder
2. Verify email in database
3. Check SMTP logs in Actions
4. Test SMTP locally

### Dashboard Not Loading

1. Check GitHub Pages status
2. Verify branch & folder settings
3. Check browser console
4. Clear cache & reload

---

## 🔒 Security

### Best Practices

- ✅ Never commit secrets to repository
- ✅ Use GitHub Secrets for credentials
- ✅ Enable 2FA on all accounts
- ✅ Use App Passwords (not account passwords)
- ✅ Rotate secrets every 3-6 months
- ✅ Enable Row Level Security (RLS) in Supabase
- ✅ Use HTTPS/TLS for all connections

### Environment Variables

**Never commit:**
- `.env` file
- API keys
- Passwords
- Database credentials

**Always use:**
- `.env.example` as template
- GitHub Secrets for CI/CD
- Environment variables

---

## 📈 Scaling

### Current Limits

- **Users**: ~100 per run
- **Searches**: ~20 per user
- **Results**: ~15 per search
- **Rate Limiting**: 3s between searches, 1s between emails

### Free Tier Quotas

| Service | Free Tier | Upgrade |
|---------|-----------|---------|
| Supabase | 500MB, 50K rows | $25/month |
| SerpAPI | 100 searches/month | $50/month |
| Serper.dev | 2,500 searches/month | $50/month |
| GitHub Actions | 2,000 minutes/month | $4/month |
| SMTP | Unlimited (Gmail) | Free |

### Optimization Tips

1. Use API instead of HTML scraping
2. Reduce search frequency
3. Limit results per email
4. Enable caching
5. Batch operations

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork repository
2. Create feature branch
3. Make changes
4. Test locally
5. Submit pull request

### Code Style

- Python: PEP 8
- JavaScript: Standard JS
- SQL: PostgreSQL conventions

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

Copyright (c) 2026 Deden Ruslan

---

## 📞 Support

- **GitHub Issues**: [dork-loker/issues](https://github.com/dedenruslan19/dork-loker/issues)
- **Email**: dedenruslan19@gmail.com

---

## 🙏 Acknowledgments

- [Supabase](https://supabase.com) - Database platform
- [GitHub Actions](https://github.com/features/actions) - CI/CD
- [SerpAPI](https://serpapi.com) - Google Search API
- [Serper.dev](https://serper.dev) - Search API alternative

---

**Made with ❤️ by [@dedenruslan19](https://github.com/dedenruslan19)**

**Version**: 3.0.0 | **Last Updated**: 2026-04-24
