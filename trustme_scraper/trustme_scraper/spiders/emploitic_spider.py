import scrapy
from trustme_scraper.items import JobItem


class EmploiticSpider(scrapy.Spider):
    """
    Spider for https://emploitic.com — uses public JSON API.

    Real API structure (confirmed via curl):
    {
      "pagination": { "page":1, "pageSize":3, "total":4462, "totalPages":1488 },
      "results": [
        {
          "alias": "sales-engineer-58880e14...",
          "title": "Sales Engineer",
          "publishedAt": "...",
          "company": { "name": "Altaproc", "alias": "...", "sector": {...} },
          "criteria": {
            "contractType": [ { "label": "CDI" } ],
            "location":     [ { "label": "Alger" } ],
            "function":     [ { "label": "Commercial" } ],
            "remote":       true/false  (check)
          },
          "description": "..."
        }
      ]
    }
    """

    name = "emploitic"
    allowed_domains = ["emploitic.com"]

    API_BASE = "https://emploitic.com/api/v4/jobs"
    PAGE_SIZE = 20

    COOKIE = (
        "ph_phc_uLnxHQkYf6oCeISwpZKpu3RZKULKmfcirjJm9zI3hUM_posthog=%7B%22%24device_id%22"
        "%3A%22019a6361-dd61-7a96-94fa-4828ec415dc2%22%2C%22distinct_id%22%3A%22019a6361-dd61"
        "-7a96-94fa-4828ec415dc2%22%7D"
    )

    def build_url(self, page):
        return (
            f"{self.API_BASE}"
            f"?sort[0]=publishedAt_timestamp:desc"
            f"&pagination[page]={page}"
            f"&pagination[pageSize]={self.PAGE_SIZE}"
        )

    def api_headers(self):
        return {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "fr-FR,fr;q=0.9",
            "Referer": "https://emploitic.com/offres-d-emploi",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36",
            "Cookie": self.COOKIE,
        }

    async def start(self):
        yield scrapy.Request(
            url=self.build_url(1),
            callback=self.parse,
            headers=self.api_headers(),
            cb_kwargs={"page": 1}
        )

    def parse(self, response, page):
        try:
            data = response.json()
        except Exception:
            self.logger.error(f"Failed to parse JSON on page {page}: {response.text[:300]}")
            return

        pagination = data.get("pagination", {})
        total_pages = pagination.get("totalPages", 1)
        jobs = data.get("results", [])

        self.logger.info(f"Page {page}/{total_pages} — {len(jobs)} jobs")

        for job in jobs:

            # Contract type (first item in list)
            criteria = job.get("criteria", {})
            contract_list = criteria.get("contractType", [])
            contract_type = contract_list[0].get("label", "") if contract_list else ""

            # Location (first item in list)
            location_list = criteria.get("location", [])
            location = location_list[0].get("label", "") if location_list else ""

            # Function/category
            function_list = criteria.get("function", [])
            category = function_list[0].get("label", "") if function_list else ""

            # Remote
            remote_raw = criteria.get("remote", False) or job.get("remote", False)
            remote = "remote_full" if remote_raw else "on-site"

            # Company
            company_data = job.get("company", {}) or {}
            company = company_data.get("name", "").strip()

            # Job URL
            alias = job.get("alias", "")
            url = f"https://emploitic.com/offres-d-emploi/{alias}"

            # Published date
            published_at = job.get("publishedAt", "").strip()
            if "T" in published_at:
                published_at = published_at.split("T")[0]

            yield JobItem(
                title         = job.get("title", "").strip(),
                company       = company,
                location      = location,
                remote        = remote,
                category      = category,
                contract_type = contract_type,
                description   = job.get("description", "").strip(),
                published_at  = published_at,
                deadline      = job.get("applicationDeadline", "").strip() if job.get("applicationDeadline") else "",
                url           = url,
                source        = "emploitic",
            )

        # Follow next pages
        if page < total_pages:
            yield scrapy.Request(
                url=self.build_url(page + 1),
                callback=self.parse,
                headers=self.api_headers(),
                cb_kwargs={"page": page + 1}
            )
