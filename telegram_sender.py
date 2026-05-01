#!/usr/bin/env python3

import psycopg2
import requests
import time
import re
from datetime import datetime

# ─── Config ───────────────────────────────────────────────────────────────────
TELEGRAM_TOKEN   = "8412920475:AAElaRqINzm6UgBhqNehS5VgZOmHKMWxbbE"
TELEGRAM_CHANNEL = "@algerian_jobs"
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "job_scrapper",
    "user":     "admin",
    "password": "admin123"
}
BATCH_SIZE = 10

# ─── Escape special chars for MarkdownV2 ──────────────────────────────────────
def escape_md(text):
    if not text:
        return "N/A"
    return re.sub(r'([_*\[\]()~`>#+\-=|{}.!\\])', r'\\\1', str(text))

# ─── Format job message ───────────────────────────────────────────────────────
def format_job(job):
    title     = escape_md(job['title'])
    company   = escape_md(job['company'])
    location  = escape_md(job['location'])
    contract  = escape_md(job['contract_type'])
    sector    = escape_md(job['sector'])
    url       = job['url'] or ""
    published = job['published_at'].strftime("%d %b %Y") if job['published_at'] else "N/A"
    published = escape_md(published)

    message = (
        f"🆕 *{title}*\n"
        f"🏢 {company}\n"
        f"📍 {location}\n"
        f"📄 {contract}\n"
        f"🏭 {sector}\n"
        f"📅 {published}\n"
    )
    if url:
        message += f"\n🔗 [Voir l'offre]({url})"

    return message

# ─── Send to Telegram ─────────────────────────────────────────────────────────
def send_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id":                  TELEGRAM_CHANNEL,
        "text":                     text,
        "parse_mode":               "MarkdownV2",
        "disable_web_page_preview": False
    }
    response = requests.post(url, json=payload, timeout=10)
    if not response.ok:
        print(f"    ⚠️  Telegram error: {response.json().get('description')}")
    return response.ok

# ─── Verify bot & channel connection ──────────────────────────────────────────
def verify_connection():
    print("🔍 Verifying bot...")
    r = requests.get(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe",
        timeout=10
    )
    if r.ok:
        bot = r.json()['result']
        print(f"  ✅ Bot: @{bot['username']} ({bot['first_name']})")
    else:
        print(f"  ❌ Bot error: {r.json()}")
        return False

    print(f"🔍 Verifying channel {TELEGRAM_CHANNEL}...")
    r = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getChat",
        json={"chat_id": TELEGRAM_CHANNEL},
        timeout=10
    )
    if r.ok:
        ch = r.json()['result']
        print(f"  ✅ Channel: {ch.get('title')} (id: {ch.get('id')})")
    else:
        print(f"  ❌ Channel error: {r.json().get('description')}")
        print(f"  👉 Make sure bot is admin in the channel with 'Post Messages' permission")
        return False

    return True

# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    if not verify_connection():
        return

    conn = psycopg2.connect(**DB_CONFIG)
    cur  = conn.cursor()

    print(f"\n[{datetime.now()}] Fetching unsent jobs...")

    # Only fetch jobs not yet sent to Telegram
    cur.execute("""
        SELECT id, title, company, location, contract_type,
               sector, url, published_at
        FROM jobs
        WHERE sent_to_telegram = FALSE
          AND is_active = TRUE
        ORDER BY scraped_at DESC
        LIMIT %s
    """, (BATCH_SIZE,))

    columns = [desc[0] for desc in cur.description]
    jobs    = [dict(zip(columns, row)) for row in cur.fetchall()]

    if not jobs:
        print("✅ No new jobs to send.")
        cur.close()
        conn.close()
        return

    print(f"📤 Sending {len(jobs)} jobs to Telegram...")

    sent_ids = []
    for job in jobs:
        message = format_job(job)
        success = send_message(message)
        if success:
            sent_ids.append(job['id'])
            print(f"  ✅ Sent: {job['title']} @ {job['company']}")
        else:
            print(f"  ❌ Failed: {job['title']}")
        time.sleep(0.5)  # avoid Telegram rate limit

    # Mark each job as sent one by one (safe — won't lose all if one fails)
    marked = 0
    for job_id in sent_ids:
        try:
            cur.execute("""
                UPDATE jobs SET sent_to_telegram = TRUE
                WHERE id = %s
            """, (job_id,))
            conn.commit()
            marked += 1
        except Exception as e:
            conn.rollback()
            print(f"  ⚠️  Could not mark job {job_id} as sent: {e}")

    print(f"\n✅ Done! {marked}/{len(jobs)} jobs sent and marked.")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
