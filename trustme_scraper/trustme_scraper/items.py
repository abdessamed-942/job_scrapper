import scrapy


class JobItem(scrapy.Item):
    title         = scrapy.Field()  # Job title
    company       = scrapy.Field()  # Company name
    location      = scrapy.Field()  # Wilaya / city (clean, no hashtags)
    remote        = scrapy.Field()  # "remote_full" | "remote_partial" | "on-site"
    category      = scrapy.Field()  # Category page (e.g. "Développeur")
    contract_type = scrapy.Field()  # CDI, CDD, Stage, Freelance...
    description   = scrapy.Field()  # Full job description (HTML stripped)
    published_at  = scrapy.Field()  # Post date → YYYY-MM-DD
    deadline      = scrapy.Field()  # Application deadline → YYYY-MM-DD or ""
    url           = scrapy.Field()  # Full URL of the job detail page
    source        = scrapy.Field()  # Always "trustme"
