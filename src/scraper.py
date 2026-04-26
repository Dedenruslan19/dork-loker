"""
scraper.py — Loker Notifier Core Engine
Membangun Google Dork query dari Supabase dan scraping hasil pencarian.
"""

import json
import time
import hashlib
import os
import re
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urlencode
import urllib.request
import urllib.error

# Load .env file if exists (for local testing)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use environment variables only

# Import Supabase client
from src.supabase_client import (
    get_config_for_scraper,
    get_seen_jobs_dict,
    get_all_users,
    get_seen_jobs,
    bulk_mark_jobs_as_seen,
    get_user_by_email,
    get_user_searches
)


# ─────────────────────────────────────────
# CONFIG LOADER (from Supabase)
# ─────────────────────────────────────────

def load_config():
    """Load config from Supabase."""
    return get_config_for_scraper()


def load_seen_hashes():
    """
    Load seen jobs per-user from Supabase.
    Format: {"user@email.com": set(["hash1", "hash2"]), ...}
    """
    seen_dict = {}
    users = get_all_users()
    
    for user in users:
        seen_hashes = get_seen_jobs(user['id'])
        seen_dict[user['email']] = set(seen_hashes)
    
    return seen_dict


def save_seen_hashes(seen_per_user: dict):
    """
    Save seen jobs per-user to Supabase.
    This is called after filtering to mark new jobs as seen.
    """
    # Jobs are saved in filter_new_jobs_per_user via bulk_mark_jobs_as_seen
    pass  # No-op, already saved in real-time


# ─────────────────────────────────────────
# DORK BUILDER
# ─────────────────────────────────────────

def build_dork(search: dict) -> str:
    """
    Membangun Google Dork query dari satu search config.
    Semua field yang null akan dilewati (general mode).
    """
    parts = []

    # Site operator
    if search.get("platform"):
        parts.append(f'site:{search["platform"]}')

    # Keyword utama — wajib
    keyword = search.get("keyword", "lowongan kerja")
    parts.append(f'"{keyword}"')

    # Filter lokasi kerja
    if search.get("lokasi_kerja"):
        parts.append(f'"{search["lokasi_kerja"]}"')

    # Filter waktu kerja
    if search.get("waktu_kerja"):
        wkt = search["waktu_kerja"]
        # Tambah sinonim Indonesia
        sinonim = {
            "internship": '"internship" OR "magang"',
            "freelance": '"freelance"',
            "full-time": '"full-time" OR "fulltime"',
            "part-time": '"part-time" OR "paruh waktu"',
            "kontrak": '"kontrak" OR "PKWT"',
            "shift": '"shift"',
        }
        parts.append(sinonim.get(wkt, f'"{wkt}"'))

    # Filter kota
    if search.get("kota"):
        parts.append(search["kota"])

    # Exclude keywords
    exclude_keywords = search.get("exclude_keywords") or []
    for excl in exclude_keywords:
        parts.append(f'-"{excl}"')

    # Tahun otomatis
    current_year = datetime.now().year
    parts.append(str(current_year))

    dork = " ".join(parts)
    return dork


def build_search_url(dork: str, engine: str = "duckduckgo") -> str:
    """Konversi dork ke URL search engine."""
    encoded = quote_plus(dork)
    if engine == "google":
        return f"https://www.google.com/search?q={encoded}&num=20&tbs=qdr:w"
    elif engine == "bing":
        return f"https://www.bing.com/search?q={encoded}"
    elif engine == "duckduckgo":
        return f"https://html.duckduckgo.com/html/?q={encoded}"
    return f"https://www.google.com/search?q={encoded}"


# ─────────────────────────────────────────
# SCRAPER (Multi-Engine Support with API)
# ─────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}


def fetch_google_serpapi(dork: str, max_results: int = 15) -> list[dict]:
    """
    Fetch Google results using SerpAPI (official API).
    Requires SERPAPI_KEY in environment.
    """
    try:
        from serpapi import GoogleSearch
    except ImportError:
        print("  ⚠️  serpapi not installed. Run: pip install google-search-results")
        return []
    
    api_key = os.environ.get("SERPAPI_KEY")
    if not api_key:
        print("  ⚠️  SERPAPI_KEY not found in environment")
        return []
    
    results = []
    
    try:
        search = GoogleSearch({
            "q": dork,
            "location": "Indonesia",
            "hl": "id",
            "gl": "id",
            "num": max_results,
            "tbs": "qdr:w",
            "api_key": api_key
        })
        
        response = search.get_dict()
        
        # Extract organic results
        organic_results = response.get("organic_results", [])
        
        for item in organic_results[:max_results]:
            title = item.get("title", "")
            url = item.get("link", "")
            snippet = item.get("snippet", "")
            
            if title and url:
                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet[:200],
                })
        
        return results
    
    except Exception as e:
        print(f"  ⚠️  SerpAPI error: {e}")
        return []


def fetch_google_serper(dork: str, max_results: int = 15) -> list[dict]:
    """
    Fetch Google results using Serper.dev API.
    Requires SERPER_API_KEY in environment.
    """
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        print("  ⚠️  SERPER_API_KEY not found in environment")
        return []
    
    results = []
    
    try:
        import json
        
        url = "https://google.serper.dev/search"
        headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json"
        }
        data = json.dumps({
            "q": dork,
            "gl": "id",  # Lokasi Indonesia
            "hl": "id",  # Bahasa Indonesia
            "num": max_results,
            "tbs": "qdr:w"  # Filter: last week
        })
        
        req = urllib.request.Request(
            url, 
            data=data.encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=15) as resp:
            response = json.loads(resp.read().decode('utf-8'))
        
        # Extract organic results
        organic_results = response.get("organic", [])
        
        for item in organic_results[:max_results]:
            title = item.get("title", "")
            url = item.get("link", "")
            snippet = item.get("snippet", "")
            
            if title and url:
                results.append({
                    "title": title,
                    "url": url,
                    "snippet": snippet[:200],
                })
        
        return results
    
    except Exception as e:
        print(f"  ⚠️  Serper.dev error: {e}")
        return []


def fetch_google_html(dork: str, max_results: int = 15) -> list[dict]:
    """
    Scraping Google Search HTML (fallback method).
    Return list of {title, url, snippet}
    """
    results = []
    url = f"https://www.google.com/search?q={quote_plus(dork)}&num={max_results}&tbs=qdr:w"
    
    import random
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    ]
    
    headers = HEADERS.copy()
    headers["User-Agent"] = random.choice(user_agents)
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        
        # Jika kena block → langsung return kosong (silent)
        if "captcha" in html.lower() or "unusual traffic" in html.lower():
            return []
        
        blocks = re.findall(
            r'<div class="[^"]*g[^"]*".*?'
            r'<a href="(/url\?q=|)(https?://[^"&]+).*?".*?'
            r'<h3[^>]*>(.*?)</h3>.*?'
            r'<div[^>]*>(.*?)</div>',
            html, re.DOTALL
        )
        
        for _, url_raw, title_raw, snippet_raw in blocks[:max_results]:
            title = re.sub(r'<[^>]+>', '', title_raw).strip()
            snippet = re.sub(r'<[^>]+>', '', snippet_raw).strip()
            actual_url = url_raw.split('&')[0]
            
            if title and actual_url.startswith("http"):
                results.append({
                    "title": title,
                    "url": actual_url,
                    "snippet": snippet[:200],
                })
    
    except:
        return []
    
    return results


def fetch_google(dork: str, max_results: int = 15) -> list[dict]:
    """
    Fetch Google results with automatic fallback:
    1. Try SerpAPI (official, most reliable)
    2. Fallback to Serper.dev
    3. Last resort: HTML scraping
    """
    # Try SerpAPI first
    results = fetch_google_serpapi(dork, max_results)
    if results:
        return results
    
    # Fallback to Serper.dev
    print("  🔄 Fallback to Serper.dev...")
    results = fetch_google_serper(dork, max_results)
    if results:
        return results
    
    # Last resort: HTML scraping
    print("  🔄 Fallback to HTML scraping...")
    results = fetch_google_html(dork, max_results)
    return results


def fetch_duckduckgo(dork: str, max_results: int = 15) -> list[dict]:
    """
    Scraping DuckDuckGo HTML (tidak butuh API key).
    Return list of {title, url, snippet}
    """
    results = []
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(dork)}"

    req = urllib.request.Request(url, headers=HEADERS)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")

        blocks = re.findall(
            r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>.*?'
            r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>',
            html, re.DOTALL
        )

        for url_raw, title_raw, snippet_raw in blocks[:max_results]:
            title = re.sub(r'<[^>]+>', '', title_raw).strip()
            snippet = re.sub(r'<[^>]+>', '', snippet_raw).strip()
            actual_url = url_raw
            uddg_match = re.search(r'uddg=([^&]+)', url_raw)
            if uddg_match:
                from urllib.parse import unquote
                actual_url = unquote(uddg_match.group(1))

            if title and actual_url:
                results.append({
                    "title": title,
                    "url": actual_url,
                    "snippet": snippet,
                })

    except:
        return []

    return results


def fetch_bing(dork: str, max_results: int = 15) -> list[dict]:
    """
    Scraping Bing Search HTML.
    Return list of {title, url, snippet}
    """
    results = []
    url = f"https://www.bing.com/search?q={quote_plus(dork)}&count={max_results}"
    
    req = urllib.request.Request(url, headers=HEADERS)
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        
        blocks = re.findall(
            r'<li class="b_algo".*?'
            r'<h2><a href="([^"]+)".*?>(.*?)</a></h2>.*?'
            r'<p[^>]*>(.*?)</p>',
            html, re.DOTALL
        )
        
        for url_raw, title_raw, snippet_raw in blocks[:max_results]:
            title = re.sub(r'<[^>]+>', '', title_raw).strip()
            snippet = re.sub(r'<[^>]+>', '', snippet_raw).strip()
            
            if title and url_raw and url_raw.startswith('http'):
                results.append({
                    "title": title,
                    "url": url_raw,
                    "snippet": snippet[:200],
                })
    
    except:
        return []
    
    return results


def fetch_with_fallback(dork: str, engine: str = "google", max_results: int = 15) -> list[dict]:
    """
    Fetch dengan engine yang dipilih (single engine, no fallback).
    """
    engines = {
        "google": fetch_google,
        "duckduckgo": fetch_duckduckgo,
        "bing": fetch_bing,
    }
    
    if engine in engines:
        return engines[engine](dork, max_results)
    
    return fetch_google(dork, max_results)


# ─────────────────────────────────────────
# DEDUPLICATION
# ─────────────────────────────────────────

def make_hash(job: dict) -> str:
    raw = f"{job['title']}|{job['url']}"
    return hashlib.md5(raw.encode()).hexdigest()


def filter_new_jobs_per_user(jobs: list[dict], seen_per_user: dict, recipients: list[str]) -> dict:
    """
    Filter jobs per-user and save to Supabase.
    Return: {"user@email.com": [job1, job2], ...}
    """
    results_per_user = {email: [] for email in recipients}
    jobs_to_save = {email: [] for email in recipients}  # Track jobs to bulk save
    
    for email in recipients:
        seen = seen_per_user.get(email, set())
        user = get_user_by_email(email)
        
        if not user:
            print(f"  ⚠️  User {email} not found in database, skipping...")
            continue
        
        for job in jobs:
            h = make_hash(job)
            if h not in seen:
                job_copy = job.copy()
                job_copy["hash"] = h
                results_per_user[email].append(job_copy)
                jobs_to_save[email].append(job_copy)
                # Mark as seen in memory
                seen.add(h)
        
        # Bulk save to Supabase
        if jobs_to_save[email]:
            bulk_mark_jobs_as_seen(user['id'], jobs_to_save[email])
    
    return results_per_user


# ─────────────────────────────────────────
# MAIN RUNNER
# ─────────────────────────────────────────

def run_all_searches(config: dict) -> dict:
    """
    Jalankan semua search berdasarkan user's personal search.
    Setiap user hanya mendapat job dari search mereka sendiri (max 1 search per user).
    Return dict per-user: {"user@email.com": [job1, job2], ...}
    """
    seen_per_user = load_seen_hashes()
    max_per_email = config["email_settings"].get("max_results_per_email", 20)
    
    # Get search engine preference from config (default: google)
    search_engine = config.get("search_engine", "google")
    
    # Get all active users
    users = get_all_users()
    
    # Initialize results per user
    results_per_user = {}
    
    print(f"🔍 Processing {len(users)} active users...")
    print(f"🌐 Search engine: {search_engine.title()}\n")
    
    for user in users:
        email = user['email']
        user_id = user['id']
        results_per_user[email] = []
        
        # Get user's personal searches (max 1 per user)
        user_searches = get_user_searches(user_id, active_only=True)
        
        if not user_searches or len(user_searches) == 0:
            print(f"👤 {email}: No active search")
            continue
        
        print(f"👤 {email}: {len(user_searches)} active search(es)")
        
        # Run each search for this user
        user_jobs = []
        for search in user_searches:
            label = search.get("label", search["id"])
            dork = build_dork(search)
            search_url = build_search_url(dork, engine=search_engine)
            
            print(f"   📌 [{label}]")
            print(f"      Dork: {dork}")
            
            jobs = fetch_with_fallback(dork, engine=search_engine, max_results=15)
            
            if not jobs:
                print(f"      ⚠️  No results")
                continue
            
            for job in jobs:
                job["search_label"] = label
                job["dork_used"] = dork
                user_jobs.append(job)
            
            print(f"      ✅ {len(jobs)} results found")
            time.sleep(3)  # Rate limiting
        
        # Filter new jobs for this user
        if user_jobs:
            seen = seen_per_user.get(email, set())
            jobs_to_save = []
            
            for job in user_jobs:
                h = make_hash(job)
                if h not in seen:
                    job_copy = job.copy()
                    job_copy["hash"] = h
                    results_per_user[email].append(job_copy)
                    jobs_to_save.append(job_copy)
                    seen.add(h)
            
            # Bulk save to Supabase
            if jobs_to_save:
                bulk_mark_jobs_as_seen(user_id, jobs_to_save)
                print(f"      💾 Saved {len(jobs_to_save)} new jobs")
        
        # Limit results per user
        results_per_user[email] = results_per_user[email][:max_per_email]
        print(f"   ✅ Total: {len(results_per_user[email])} new jobs for {email}\n")
    
    # Print summary
    print(f"\n{'=' * 50}")
    print("📊 Summary:")
    for email, jobs in results_per_user.items():
        print(f"   {email}: {len(jobs)} new jobs")
    print("=" * 50)
    
    return results_per_user


# ─────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Loker Notifier — Scraper Engine")
    print(f"   Waktu : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50 + "\n")

    config = load_config()
    results_per_user = run_all_searches(config)

    # Simpan hasil sementara untuk mailer (per-user)
    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(results_per_user, f, ensure_ascii=False, indent=2)

    total_jobs = sum(len(jobs) for jobs in results_per_user.values())
    print(f"\n✅ Hasil disimpan ke results.json")
    print(f"   Total: {total_jobs} notifikasi untuk {len(results_per_user)} user")
