BOT_NAME = "trustme_scraper"
SPIDER_MODULES = ["trustme_scraper.spiders"]
NEWSPIDER_MODULE = "trustme_scraper.spiders"

ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 2
RANDOMIZE_DOWNLOAD_DELAY = True        # Actual delay: 1s–3s
CONCURRENT_REQUESTS_PER_DOMAIN = 2

DEFAULT_REQUEST_HEADERS = {
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Referer": "https://www.trustme.work/",
}

DOWNLOADER_MIDDLEWARES = {
    "trustme_scraper.middlewares.RotateUserAgentMiddleware": 400,
}

ITEM_PIPELINES = {
    "trustme_scraper.pipelines.DuplicateFilterPipeline": 100,
    "trustme_scraper.pipelines.CleaningPipeline": 200,
    "trustme_scraper.pipelines.JsonCsvExportPipeline": 300,
}

LOG_LEVEL = "INFO"
