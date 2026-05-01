import scrapy
from w3lib.html import remove_tags
from trustme_scraper.items import JobItem


class EmploipartnerSpider(scrapy.Spider):
    """
    Spider for https://www.emploipartner.com — uses public Hydra/JSON-LD API.

    API: https://api-v4.emploipartner.com/api/jobs
    Format: Hydra Collection (Symfony API Platform)

    Confirmed structure:
    {
      "hydra:totalItems": 1425,
      "hydra:member": [
        {
          "id": 69372,
          "title": "Responsable Cellule Clientèle",
          "companyName": "EMPLOI PARTNER",
          "description": "<ul>...</ul>" or null,
          "slug": "responsable-cellule-clientele",
          "region": { "name": "Alger" },
          "contractTypes": [ { "name": "CDI" } ],
          "workplace": { "name": "sur site" },
          "expireDate": "2026-06-12T00:00:00+01:00",
          "refreshedDate": "2026-05-01T15:56:30+01:00",
          "careerLevel": { "name": "Débutant / Junior" },
          "hideCompany": false
        }
      ],
      "hydra:view": {
        "hydra:next": "/api/jobs?limit=10&order[refreshedDate]=desc&_page=2",
        "hydra:last": "/api/jobs?limit=10&order[refreshedDate]=desc&_page=143"
      }
    }
    """

    name = "emploipartner"
    allowed_domains = ["emploipartner.com", "api-v4.emploipartner.com"]

    API_BASE   = "https://api-v4.emploipartner.com"
    START_URL  = (
        "https://api-v4.emploipartner.com/api/jobs"
        "?_page=1&limit=20&order[refreshedDate]=desc"
    )
    SITE_BASE  = "https://www.emploipartner.com/fr/offres-emploi"

    def api_headers(self):
        return {
            "Accept": "application/ld+json",
            "Accept-Language": "fr",
            "Origin": "https://www.emploipartner.com",
            "Referer": "https://www.emploipartner.com/fr/offres-emploi",
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36"
            ),
        }

    async def start(self):
        yield scrapy.Request(
            url=self.START_URL,
            callback=self.parse,
            headers=self.api_headers(),
        )

    def parse(self, response):
        try:
            data = response.json()
        except Exception:
            self.logger.error(f"JSON parse error: {response.text[:200]}")
            return

        total  = data.get("hydra:totalItems", 0)
        jobs   = data.get("hydra:member", [])
        view   = data.get("hydra:view", {})
        next_p = view.get("hydra:next", "")

        self.logger.info(f"Total jobs: {total} — this page: {len(jobs)}")

        for job in jobs:

            # Company (hide if hideCompany=True)
            company = "" if job.get("hideCompany") else job.get("companyName", "")

            # Location
            region = job.get("region") or {}
            location = region.get("name", "")

            # Contract type (first item)
            contracts = job.get("contractTypes", []) or []
            contract_type = contracts[0].get("name", "") if contracts else ""

            # Remote via workplace
            workplace = job.get("workplace") or {}
            workplace_name = workplace.get("name", "sur site").lower()
            if "remote" in workplace_name or "télétravail" in workplace_name:
                remote = "remote_full"
            elif "hybride" in workplace_name:
                remote = "remote_partial"
            else:
                remote = "on-site"

            # Description (may be null → fetch detail page)
            raw_desc = job.get("description") or ""
            description = remove_tags(raw_desc).strip() if raw_desc else ""

            # Dates
            refreshed  = (job.get("refreshedDate") or "").split("T")[0]
            expire     = (job.get("expireDate") or "").split("T")[0]

            # URL
            slug = job.get("slug", str(job.get("id", "")))
            url  = f"{self.SITE_BASE}/{slug}"

            item = JobItem(
                title         = job.get("title", "").strip(),
                company       = company.strip(),
                location      = location.strip(),
                remote        = remote,
                category      = "",   # not in list response
                contract_type = contract_type.strip(),
                description   = description,
                published_at  = refreshed,
                deadline      = expire,
                url           = url,
                source        = "emploipartner",
            )

            # If description is empty → fetch detail page for full data
            if not description:
                job_id = job.get("id")
                detail_api = f"{self.API_BASE}/api/jobs/{job_id}"
                yield scrapy.Request(
                    url=detail_api,
                    callback=self.parse_detail,
                    headers=self.api_headers(),
                    cb_kwargs={"item": item}
                )
            else:
                yield item

        # Follow next page
        if next_p:
            yield scrapy.Request(
                url=f"{self.API_BASE}{next_p}",
                callback=self.parse,
                headers=self.api_headers(),
            )

    def parse_detail(self, response, item):
        """Fetch full description from individual job API endpoint."""
        try:
            data = response.json()
        except Exception:
            yield item
            return

        raw_desc = data.get("description") or ""
        item["description"] = remove_tags(raw_desc).strip() if raw_desc else ""

        # Also get category from function if available
        function = data.get("function") or {}
        item["category"] = function.get("name", "").strip()

        yield item
