"""Scrapers for different content sources."""

from app.scrapers.base import BaseScraper, ScrapedArticle
from app.scrapers.rss_scraper import RSSFeedScraper
from app.scrapers.youtube_scraper import YouTubeScraper
from app.scrapers.web_scraper import WebScraper

__all__ = [
    "BaseScraper",
    "ScrapedArticle",
    "RSSFeedScraper",
    "YouTubeScraper",
    "WebScraper",
]
