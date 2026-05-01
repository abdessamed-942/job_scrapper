import re
import json
import csv
import time
from pathlib import Path
from parsel import Selector
from curl_cffi.requests import Session

BASE_URL  = "https://www.algeriejob.com"
LIST_PATH = "/recherche-jobs-algerie"
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9",
    "Referer": "https://www.algeriejob.com/",
}

def get(session, url, retries=3):
    for i in range(retries):
        try:
            r = session.get(url, headers=HEADERS, timeout=30)
            if r.status_code == 200:
                return r
            print(f"  ⚠️  {url} → {r.status_code} (attempt {i+1})")
        except Exception as e:
            print(f"  ❌ Error: {e} (attempt {i+1})")
        time.sleep(3)
    return None

def parse_card(card, session):
    detail_path = card.attrib.get("data-href", "")
    detail_url  = detail_path if detail_path.startswith("http") else BASE_URL + detail_path

    title   = card.css("h3 a::text").get(default="").strip()
    company = card.css("a.card-job-company::text").get(default="").strip()

    contract_type = ""
    location      = ""
    for li in card.css("ul li"):
        txt    = " ".join(li.css("::text").getall())
        strong = li.css("strong::text").get(default="").strip()
        if "Contrat" in txt:
            contract_type = strong
        elif "Région" in txt:
            location = strong

    published_at = card.css("time::attr(datetime)").get(default="")

    description = ""
    category    = ""
    r = get(session, detail_url)
    if r:
        ds = Selector(text=r.text)
        raw = " ".join(
            ds.css(
                "div.field-name-body .field-item *::text, "
                "div.field-type-text-with-summary *::text"
            ).getall()
        )
        description = re.sub(r"\s+", " ", raw).strip()
        category    = ds.css(
            "div.field-name-field-offre-metiers a::text"
        ).get(default="").strip()

    d      = description.lower()
    remote = "on-site"
    if "full remote" in d or "télétravail complet" in d:
        remote = "remote_full"
    elif "hybride" in d or "télétravail partiel" in d:
        remote = "remote_partial"

    return {
        "title":         title,
        "company":       company,
        "location":      location,
        "remote":        remote,
        "category":      category,
        "contract_type": contract_type,
        "description":   description,
        "published_at":  published_at,
        "deadline":      "",
        "url":           detail_url,
        "source":        "algeriejob",
    }

def scrape():
    jobs = []

    with Session(impersonate="chrome") as session:
        r = get(session, f"{BASE_URL}{LIST_PATH}?page=0")
        if not r:
            print("❌ Could not reach algeriejob.com")
            return

        sel = Selector(text=r.text)

        total_text = sel.css("h2.page-search-title span::text").get(default="0")
        total      = int(re.sub(r"\D", "", total_text) or 0)
        print(f"✅ Connected! Total jobs: {total}")

        last_href = sel.css(
            "li.pager-last a::attr(href), "
            "a[title='Aller à la dernière page']::attr(href)"
        ).get(default="")
        last_page = 0
        m = re.search(r"page=(\d+)", last_href)
        if m:
            last_page = int(m.group(1))
        print(f"📄 Pages: 0 → {last_page}")

        pages_html = {0: r.text}
        for page in range(1, last_page + 1):
            print(f"📄 Fetching page {page}/{last_page}…")
            rp = get(session, f"{BASE_URL}{LIST_PATH}?page={page}")
            if rp:
                pages_html[page] = rp.text
            time.sleep(1.5)

        for page, html in pages_html.items():
            psel  = Selector(text=html)
            cards = psel.css("div.card.card-job[data-href]")
            print(f"\n📋 Page {page}: {len(cards)} jobs")
            for i, card in enumerate(cards, 1):
                title = card.css("h3 a::text").get(default="?").strip()
                print(f"  [{i}/{len(cards)}] {title}")
                jobs.append(parse_card(card, session))
                time.sleep(1)

    json_path = OUTPUT_DIR / "algeriejob.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(jobs, f, ensure_ascii=False, indent=2)

    csv_path = OUTPUT_DIR / "algeriejob.csv"
    if jobs:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=jobs[0].keys())
            writer.writeheader()
            writer.writerows(jobs)

    print(f"\n✅ Done! {len(jobs)} jobs saved to:")
    print(f"   {json_path}")
    print(f"   {csv_path}")

if __name__ == "__main__":
    scrape()
