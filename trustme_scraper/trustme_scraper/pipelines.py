import csv
import json
import os
from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from w3lib.html import remove_tags
import dateparser


class DuplicateFilterPipeline:
    """Drops items with duplicate URLs."""

    def __init__(self):
        self.seen_urls = set()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        url = adapter.get("url", "")
        if url in self.seen_urls:
            raise DropItem(f"Duplicate job URL: {url}")
        self.seen_urls.add(url)
        return item


class CleaningPipeline:
    """Strips HTML, trims whitespace, normalizes dates."""

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        # Strip HTML from description
        if adapter.get("description"):
            adapter["description"] = remove_tags(adapter["description"]).strip()

        # Strip whitespace from all string fields
        for field in ["title", "company", "location", "category",
                      "contract_type", "remote", "source"]:
            if adapter.get(field):
                adapter[field] = adapter[field].strip()

        # Normalize dates to YYYY-MM-DD
        for date_field in ["published_at", "deadline"]:
            raw = adapter.get(date_field, "")
            if raw:
                parsed = dateparser.parse(raw, languages=["fr", "en", "ar"])
                if parsed:
                    adapter[date_field] = parsed.strftime("%Y-%m-%d")

        return item


class JsonCsvExportPipeline:
    """Saves scraped jobs to data/trustme_jobs.json and data/trustme_jobs.csv."""

    def open_spider(self, spider):
        os.makedirs("data", exist_ok=True)

        self.json_file = open("data/trustme_jobs.json", "w", encoding="utf-8")
        self.csv_file  = open("data/trustme_jobs.csv", "w", encoding="utf-8", newline="")

        self.fields = [
            "title", "company", "location", "remote", "category",
            "contract_type", "published_at", "deadline", "url", "source", "description"
        ]
        self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=self.fields, extrasaction="ignore")
        self.csv_writer.writeheader()
        self.count = 0

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        row = dict(adapter)

        # Write to JSON (one line per item)
        self.json_file.write(json.dumps(row, ensure_ascii=False) + "\n")

        # Write to CSV
        self.csv_writer.writerow(row)

        self.count += 1
        return item

    def close_spider(self, spider):
        self.json_file.close()
        self.csv_file.close()
        spider.logger.info(f"✅ Total jobs saved: {self.count}")
