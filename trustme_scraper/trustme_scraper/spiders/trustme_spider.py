import scrapy
import re
from trustme_scraper.items import JobItem


class TrustmeSpider(scrapy.Spider):
    """
    Spider for https://www.trustme.work — Algerian IT job board.

    Confirmed selectors from browser F12 inspection:
    - Job card wrapper   : div.MuiCardContent-root
    - Job title (card)   : h2.MuiTypography-h2  (or first h2 in card)
    - Company (card)     : h2.MuiTypography-subtitle1  ← confirmed via F12
    - Job link           : a[href*='/job-offer/'] inside card
    - Location (detail)  : .MuiGrid-justify-content-xs-space-between p::text
    - Contract type      : .MuiChip-label (chip 1)
    - Category           : .MuiChip-label (chip 2)
    - Published date     : text after 'Posté le'
    - Description        : div.offer-corp *::text
    """

    name = "trustme"
    allowed_domains = ["trustme.work"]
    start_urls = ["https://www.trustme.work/"]
    seen_urls = set()

    def parse(self, response):
        """Parse homepage — extract cards using confirmed MUI selectors."""

        cards = response.css("div.MuiCardContent-root")

        for card in cards:
            href = card.css("a[href*='/job-offer/']::attr(href)").get(default="")
            if not href:
                continue

            url = response.urljoin(href)
            if url in self.seen_urls:
                continue
            self.seen_urls.add(url)

            # ✅ Company confirmed selector: h2.MuiTypography-subtitle1
            company = card.css("h2.MuiTypography-subtitle1::text").get(default="").strip()

            # Job title: first h2 that is NOT subtitle1
            title = card.css(
                "h2:not(.MuiTypography-subtitle1)::text"
            ).get(default="").strip()

            yield scrapy.Request(
                url,
                callback=self.parse_job,
                cb_kwargs={
                    "card_title":   title,
                    "card_company": company,
                }
            )

        # Pagination
        next_page = response.css(
            "a[aria-label='Next']::attr(href), a[rel='next']::attr(href)"
        ).get()
        if next_page:
            yield scrapy.Request(response.urljoin(next_page), callback=self.parse)

    def parse_job(self, response, card_title="", card_company=""):
        """Parse a single job detail page."""

        # Title: from detail h1, fallback to card title
        title = response.css(
            "h1:not(.MuiTypography-alignCenter)::text"
        ).get(default="").strip() or card_title

        # Contract type (chip 1) + Category (chip 2)
        chips = response.css(".MuiChip-label::text").getall()
        contract_type = chips[0].strip() if chips else ""
        category      = chips[1].strip() if len(chips) > 1 else ""

        # Location + remote (from detail page)
        raw_location = response.css(
            ".MuiGrid-justify-content-xs-space-between p::text"
        ).get(default="").strip()
        remote, location = self.parse_remote(raw_location)

        # Published date (text after 'Posté le')
        published_at = ""
        all_text = [t.strip() for t in response.css("body *::text").getall() if t.strip()]
        for i, text in enumerate(all_text):
            if "Posté le" in text and i + 1 < len(all_text):
                published_at = all_text[i + 1].strip()
                break

        # Full description
        description = " ".join(
            response.css("div.offer-corp *::text").getall()
        ).strip()

        yield JobItem(
            title         = title,
            company       = card_company,
            location      = location,
            remote        = remote,
            category      = category,
            contract_type = contract_type,
            description   = description,
            published_at  = published_at,
            deadline      = "",
            url           = response.url,
            source        = "trustme",
        )

    def parse_remote(self, raw_location):
        remote = "on-site"
        location = raw_location
        if "#remote_full_time" in raw_location:
            remote = "remote_full"
            location = raw_location.replace("#remote_full_time", "").strip()
        elif "#remote_partial" in raw_location:
            remote = "remote_partial"
            location = raw_location.replace("#remote_partial", "").strip()
        return remote, location.strip()
