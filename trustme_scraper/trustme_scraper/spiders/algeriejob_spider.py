import scrapy
import re
import json
from curl_cffi.requests import Session as CfSession
from trustme_scraper.items import JobItem


class AlgeriejobSpider(scrapy.Spider):
    """
    Spider for https://www.algeriejob.com — Drupal + Cloudflare.

    Uses curl-cffi to mimic Chrome TLS fingerprint → bypasses Cloudflare
    without needing a fresh cf_clearance cookie.

    All HTTP calls use CfSession (not Scrapy's downloader) for the
    Cloudflare-protected pages. Results are yielded normally as items.
    """

    name = "algeriejob"

    custom_settings = {
        "ROBOTSTXT_OBEY":    False,
        "COOKIES_ENABLED":   False,
        "CONCURRENT_REQUESTS": 1,   # curl-cffi calls are synchronous
        "DOWNLOAD_DELAY":    2,
    }

    BASE_URL  = "https://www.algeriejob.com"
    LIST_PATH = "/recherche-jobs-algerie"

    HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9",
        "Referer": "https://www.algeriejob.com/recherche-jobs-algerie",
    }

    def _get(self, url):
        """Fetch a URL using curl-cffi impersonating Chrome."""
        with CfSession(impersonate="chrome") as s:
            r = s.get(url, headers=self.HEADERS, timeout=30)
        return r

    async def start(self):
        """Use a fake Scrapy request to trigger the crawl."""
        yield scrapy.Request(
            url=f"{self.BASE_URL}{self.LIST_PATH}?page=0",
            callback=self.parse_bootstrap,
            dont_filter=True,
        )

    def parse_bootstrap(self, response):
        """Bootstrap: use curl-cffi for page 0 to get total pages."""
        r = self._get(f"{self.BASE_URL}{self.LIST_PATH}?page=0")
        if r.status_code == 403:
            self.logger.error("⛔ Still 403 — install: pip install curl-cffi")
            return

        from parsel import Selector
        sel = Selector(text=r.text)
        yield from self._parse_sel(sel, page=0)

        # Find last page
        last_href = sel.css(
            "li.pager-last a::attr(href), "
            "a[title='Aller à la dernière page']::attr(href)"
        ).get(default="")
        last_page = 0
        m = re.search(r"page=(\d+)", last_href)
        if m:
            last_page = int(m.group(1))

        self.logger.info(f"📄 Last page: {last_page}")

        for page in range(1, last_page + 1):
            r2 = self._get(f"{self.BASE_URL}{self.LIST_PATH}?page={page}")
            if r2.status_code != 200:
                self.logger.warning(f"⚠️ Page {page} returned {r2.status_code}")
                continue
            sel2 = Selector(text=r2.text)
            self.logger.info(f"📄 Page {page}/{last_page}")
            yield from self._parse_sel(sel2, page=page)

    def _parse_sel(self, sel, page):
        """Parse job cards from a Selector and yield detail fetches."""
        cards = sel.css("div.card.card-job[data-href]")
        self.logger.info(f"  Found {len(cards)} cards on page {page}")

        for card in cards:
            detail_path = card.attrib.get("data-href", "")
            detail_url  = (
                detail_path if detail_path.startswith("http")
                else self.BASE_URL + detail_path
            )

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

            # Fetch detail page for description + category
            r = self._get(detail_url)
            description = ""
            category    = ""
            if r.status_code == 200:
                from parsel import Selector as S
                ds = S(text=r.text)
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

            # Remote detection
            d      = description.lower()
            remote = "on-site"
            if "full remote" in d or "télétravail complet" in d:
                remote = "remote_full"
            elif "hybride" in d or "télétravail partiel" in d:
                remote = "remote_partial"

            yield JobItem(
                title         = title,
                company       = company,
                location      = location,
                remote        = remote,
                category      = category,
                contract_type = contract_type,
                description   = description,
                published_at  = published_at,
                deadline      = "",
                url           = detail_url,
                source        = "algeriejob",
            )
