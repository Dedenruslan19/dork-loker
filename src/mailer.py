"""
mailer.py — Loker Notifier Email Engine
Mengirim notifikasi email via SMTP dengan hasil scraping dari Supabase.
"""

import json
import os
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# Load .env file if exists (for local testing)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, use environment variables only

# Import Supabase client
from src.supabase_client import get_all_settings


# ─────────────────────────────────────────
# CONFIG (from Supabase)
# ─────────────────────────────────────────

def load_config():
    """Load config from Supabase settings."""
    settings = get_all_settings()
    return {
        "email_settings": {
            "subject_prefix": settings.get('subject_prefix', '[Loker Alert]')
        }
    }


def load_results(path="results.json") -> dict:
    """
    Load results per-user.
    Format: {"user@email.com": [job1, job2], ...}
    """
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ─────────────────────────────────────────
# EMAIL TEMPLATE
# ─────────────────────────────────────────

def build_html_email(jobs: list[dict], config: dict) -> str:
    now = datetime.now().strftime("%d %B %Y, %H:%M WIB")
    total = len(jobs)

    # Group by search label
    grouped = {}
    for job in jobs:
        label = job.get("search_label", "Umum")
        grouped.setdefault(label, []).append(job)

    # Build job cards per group
    group_html = ""
    for label, group_jobs in grouped.items():
        cards = ""
        for job in group_jobs:
            title = job.get("title", "Tanpa Judul")
            url = job.get("url", "#")
            snippet = job.get("snippet", "")
            dork = job.get("dork_used", "")

            cards += f"""
            <div style="background:#fff;border:1px solid #e2e8f0;border-radius:10px;
                        padding:16px;margin-bottom:12px;">
              <a href="{url}" target="_blank"
                 style="font-size:15px;font-weight:600;color:#2563eb;text-decoration:none;">
                {title}
              </a>
              <p style="color:#64748b;font-size:13px;margin:6px 0 10px;">{snippet}</p>
              <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
                <a href="{url}" target="_blank"
                   style="background:#2563eb;color:#fff;padding:6px 14px;border-radius:6px;
                          font-size:12px;text-decoration:none;font-weight:500;">
                  Lihat Loker →
                </a>
                <span style="font-size:11px;color:#94a3b8;font-family:monospace;">
                  🔍 {dork[:80]}{'...' if len(dork) > 80 else ''}
                </span>
              </div>
            </div>
            """

        group_html += f"""
        <div style="margin-bottom:28px;">
          <h3 style="color:#1e293b;font-size:14px;font-weight:700;
                     border-left:4px solid #2563eb;padding-left:10px;margin-bottom:12px;">
            📌 {label} ({len(group_jobs)} loker)
          </h3>
          {cards}
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="id">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
                 background:#f1f5f9;margin:0;padding:24px;">
      <div style="max-width:620px;margin:0 auto;">

        <!-- Header -->
        <div style="background:linear-gradient(135deg,#1e40af,#3b82f6);
                    border-radius:14px;padding:28px;text-align:center;margin-bottom:20px;">
          <h1 style="color:#fff;margin:0;font-size:22px;">🔔 Loker Alert</h1>
          <p style="color:#bfdbfe;margin:8px 0 0;font-size:13px;">{now}</p>
        </div>

        <!-- Summary -->
        <div style="background:#fff;border-radius:10px;padding:16px 20px;
                    margin-bottom:20px;border:1px solid #e2e8f0;text-align:center;">
          <span style="font-size:28px;font-weight:700;color:#2563eb;">{total}</span>
          <span style="color:#64748b;font-size:14px;"> loker baru ditemukan</span>
        </div>

        <!-- Job Results -->
        {group_html}

        <!-- Footer -->
        <div style="text-align:center;padding:20px;color:#94a3b8;font-size:12px;">
          <p>Email ini dikirim otomatis oleh <strong>Dork Loker</strong>.<br>
          Ubah filter pencarian di
          <a href="https://YOUR_USERNAME.github.io/dork-loker"
             style="color:#2563eb;">halaman pengaturan</a>.</p>
        </div>

      </div>
    </body>
    </html>
    """
    return html


def build_plain_text(jobs: list[dict]) -> str:
    lines = [f"🔔 LOKER ALERT — {len(jobs)} loker baru\n"]
    lines.append("=" * 50)
    for job in jobs:
        lines.append(f"\n📌 {job.get('search_label', 'Umum')}")
        lines.append(f"Judul   : {job.get('title', '-')}")
        lines.append(f"URL     : {job.get('url', '-')}")
        lines.append(f"Snippet : {job.get('snippet', '-')}")
        lines.append("-" * 40)
    return "\n".join(lines)


# ─────────────────────────────────────────
# SMTP SENDER
# ─────────────────────────────────────────

def send_email_to_user(recipient: str, jobs: list[dict], config: dict):
    """Send email to a single user with their personalized job list."""
    # Ambil kredensial dari environment variable (GitHub Secrets)
    smtp_host = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    sender    = os.environ.get("SMTP_FROM", smtp_user)

    if not smtp_user or not smtp_pass:
        raise ValueError("❌ SMTP_USER atau SMTP_PASS tidak ditemukan di environment!")

    email_cfg = config["email_settings"]
    subject_prefix = email_cfg.get("subject_prefix", "[Loker Alert]")

    subject = f"{subject_prefix} {len(jobs)} Loker Baru — {datetime.now().strftime('%d %b %Y')}"

    html_body = build_html_email(jobs, config)
    plain_body = build_plain_text(jobs)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = sender
    msg["To"]      = recipient

    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    print(f"📧 Mengirim ke {recipient}: {len(jobs)} loker")

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(sender, [recipient], msg.as_string())

    print(f"   ✅ Berhasil!")


def send_emails_per_user(results_per_user: dict, config: dict):
    """Send personalized emails to each user."""
    total_sent = 0
    
    for recipient, jobs in results_per_user.items():
        if jobs:  # Only send if user has new jobs
            send_email_to_user(recipient, jobs, config)
            total_sent += 1
            time.sleep(1)  # Rate limiting between emails
    
    return total_sent


# ─────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("📧 Loker Notifier — Mailer Engine")
    print("=" * 50 + "\n")

    config = load_config()
    results_per_user = load_results()

    if not results_per_user or all(len(jobs) == 0 for jobs in results_per_user.values()):
        send_empty = config["email_settings"].get("send_if_empty", False)
        if send_empty:
            print("⚠️  Tidak ada loker baru, tapi send_if_empty=true")
            # Kirim email kosong ke semua recipients
            recipients = config["email_settings"].get("recipients", [])
            for recipient in recipients:
                send_email_to_user(recipient, [], config)
        else:
            print("ℹ️  Tidak ada loker baru. Email tidak dikirim.")
    else:
        total_jobs = sum(len(jobs) for jobs in results_per_user.values())
        print(f"📦 {total_jobs} loker siap dikirim ke {len(results_per_user)} user...\n")
        total_sent = send_emails_per_user(results_per_user, config)
        print(f"\n✅ {total_sent} email berhasil dikirim!")
