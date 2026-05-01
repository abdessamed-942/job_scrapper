import psycopg2
import hashlib
from datetime import datetime
from scrapy.exceptions import DropItem

# ─── Arabic date conversion ────────────────────────────────────────────────────
ARABIC_MONTHS = {
    'يناير': 1, 'فبراير': 2, 'مارس': 3, 'أبريل': 4,
    'مايو': 5,  'يونيو': 6,  'يوليو': 7, 'أغسطس': 8,
    'سبتمبر': 9,'أكتوبر': 10,'نوفمبر': 11,'ديسمبر': 12
}
ARABIC_DIGITS = str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')

def parse_arabic_date(date_str):
    if not date_str:
        return None
    try:
        date_str = str(date_str).translate(ARABIC_DIGITS).strip()
        parts = date_str.split()
        if len(parts) == 3:
            day   = int(parts[0])
            month = ARABIC_MONTHS.get(parts[1])
            year  = int(parts[2])
            if month:
                return datetime(year, month, day)
    except Exception:
        pass
    return None

def make_job_fingerprint(item):
    key = f"{item.get('title', '').lower().strip()}" \
          f"{item.get('company', '').lower().strip()}" \
          f"{item.get('location', '').lower().strip()}"
    return hashlib.md5(key.encode()).hexdigest()


# ─── Pipeline 1: Cleaning ─────────────────────────────────────────────────────
class CleaningPipeline:
    def process_item(self, item, spider):
        for key, value in item.items():
            if isinstance(value, str):
                item[key] = value.strip()
        return item


# ─── Pipeline 2: Duplicate Filter ────────────────────────────────────────────
class DuplicateFilterPipeline:
    def open_spider(self, spider):
        self.seen = set()

    def process_item(self, item, spider):
        fingerprint = make_job_fingerprint(item)
        if fingerprint in self.seen:
            raise DropItem(f"Duplicate: {item.get('title')}")
        self.seen.add(fingerprint)
        return item


# ─── Pipeline 3: PostgreSQL ───────────────────────────────────────────────────
class PostgreSQLPipeline:

    def open_spider(self, spider):
        self.conn = psycopg2.connect(
            host="postgres_db", port=5432,
            dbname="job_scrapper", user="admin", password="admin123"
        )
        self.cur = self.conn.cursor()

        # Get source_id
        self.cur.execute("SELECT id FROM sources WHERE name = %s", (spider.name,))
        row = self.cur.fetchone()
        self.source_id = row[0] if row else None

        # Init counters
        self.start_time      = datetime.now()
        self.crawl_count     = 0
        self.duplicate_count = 0
        self.error_message   = None

        # Insert crawl_log row with status=running
        self.cur.execute("""
            INSERT INTO crawl_logs (source_id, started_at, status)
            VALUES (%s, %s, 'running')
            RETURNING id
        """, (self.source_id, self.start_time))
        self.log_id = self.cur.fetchone()[0]

        # Mark source as started
        self.cur.execute("""
            UPDATE sources SET last_start_at = %s WHERE id = %s
        """, (self.start_time, self.source_id))
        self.conn.commit()

    def process_item(self, item, spider):
        published_at = parse_arabic_date(item.get('published_at'))
        fingerprint  = make_job_fingerprint(item)

        try:
            self.cur.execute("""
                INSERT INTO jobs (
                    source_id, external_id, url, title, company,
                    description, location, contract_type, sector,
                    category, experience_level, education_level,
                    salary, languages, skills,
                    published_at, scraped_at, fingerprint
                ) VALUES (
                    %s,%s,%s,%s,%s,
                    %s,%s,%s,%s,
                    %s,%s,%s,
                    %s,%s,%s,
                    %s,%s,%s
                )
                ON CONFLICT (fingerprint) DO UPDATE SET
                    url         = EXCLUDED.url,
                    description = EXCLUDED.description,
                    is_active   = TRUE,
                    scraped_at  = NOW()
            """, (
                self.source_id, item.get('external_id'), item.get('url'),
                item.get('title'), item.get('company'), item.get('description'),
                item.get('location'), item.get('contract_type'), item.get('sector'),
                item.get('category'), item.get('experience_level'),
                item.get('education_level'), item.get('salary'),
                item.get('languages'), item.get('skills'),
                published_at, datetime.now(), fingerprint
            ))
            self.conn.commit()

            if self.cur.rowcount == 1:
                self.crawl_count += 1
            else:
                self.duplicate_count += 1

        except Exception as e:
            self.conn.rollback()
            self.error_message = str(e)
            spider.logger.error(f"DB error: {e}")

        return item

    def close_spider(self, spider):
        end_time       = datetime.now()
        execution_secs = int((end_time - self.start_time).total_seconds())
        status         = 'failed' if self.error_message else 'success'

        total_jobs = 0
        try:
            self.cur.execute(
                "SELECT COUNT(*) FROM jobs WHERE source_id = %s",
                (self.source_id,)
            )
            total_jobs = self.cur.fetchone()[0]
        except Exception:
            pass

        # Update crawl_log
        try:
            self.cur.execute("""
                UPDATE crawl_logs SET
                    finished_at    = %s,
                    status         = %s,
                    new_jobs       = %s,
                    duplicate_jobs = %s,
                    total_jobs     = %s,
                    execution_time = %s,
                    error_message  = %s
                WHERE id = %s
            """, (
                end_time, status,
                self.crawl_count, self.duplicate_count,
                total_jobs, execution_secs,
                self.error_message, self.log_id
            ))

            # Update sources stats
            self.cur.execute("""
                UPDATE sources SET
                    last_crawl_at        = %s,
                    execution_time       = %s,
                    last_crawl_count     = %s,
                    last_duplicate_count = %s,
                    total_jobs_count     = %s
                WHERE id = %s
            """, (
                end_time, execution_secs,
                self.crawl_count, self.duplicate_count,
                total_jobs, self.source_id
            ))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            spider.logger.error(f"Stats update error: {e}")

        spider.logger.info(
            f"✅ Done | new: {self.crawl_count} | "
            f"duplicates: {self.duplicate_count} | "
            f"time: {execution_secs}s | status: {status}"
        )

        self.cur.close()
        self.conn.close()
