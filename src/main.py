#!/usr/bin/env python3
"""
main.py — Loker Notifier Main Entry Point
Run this to execute the complete job notification flow:
1. Scrape jobs from subscribed searches
2. Send email notifications to users
"""

import sys
import json
from datetime import datetime

# Import scraper
from src.scraper import load_config, run_all_searches

# Import mailer
from src.mailer import load_results, send_emails_per_user


def main():
    """Main entry point for the job notifier."""
    print("=" * 60)
    print("🚀 Loker Notifier — Complete Flow")
    print(f"   Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Step 1: Scrape jobs
    print("\n📍 STEP 1: Scraping Jobs")
    print("-" * 60)
    
    try:
        config = load_config()
        results_per_user = run_all_searches(config)
        
        # Save results for mailer
        with open("results.json", "w", encoding="utf-8") as f:
            json.dump(results_per_user, f, ensure_ascii=False, indent=2)
        
        total_jobs = sum(len(jobs) for jobs in results_per_user.values())
        print(f"\n✅ Scraping complete: {total_jobs} new jobs found")
        
    except Exception as e:
        print(f"\n❌ Scraping failed: {e}")
        sys.exit(1)
    
    # Step 2: Send emails
    print("\n📍 STEP 2: Sending Email Notifications")
    print("-" * 60)
    
    try:
        results = load_results()
        
        if not results or all(len(jobs) == 0 for jobs in results.values()):
            print("\n⚠️  No new jobs to send. Skipping email.")
        else:
            send_emails_per_user(results, config)
            print("\n✅ Email notifications sent successfully")
        
    except Exception as e:
        print(f"\n❌ Email sending failed: {e}")
        sys.exit(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ Job Notification Flow Complete!")
    print(f"   Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
