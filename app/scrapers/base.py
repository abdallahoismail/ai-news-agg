"""Base scraper class with common functionality."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.config.settings import get_settings


@dataclass
class ScrapedArticle:
    """Data class for scraped article content."""

    title: str
    url: str
    content: Optional[str] = None
    transcript: Optional[str] = None
    published_date: Optional[datetime] = None


class BaseScraper(ABC):
    """Base class for all scrapers with common functionality."""

    def __init__(self):
        """Initialize base scraper with settings and HTTP session."""
        self.settings = get_settings()
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic."""
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set timeout and headers
        session.headers.update(
            {"User-Agent": "AI-News-Aggregator/1.0 (Educational Project)"}
        )

        return session

    def _make_request(
        self, url: str, timeout: Optional[int] = None
    ) -> requests.Response:
        """
        Make HTTP request with timeout and error handling.

        Args:
            url: URL to fetch
            timeout: Request timeout in seconds (uses setting default if not provided)

        Returns:
            Response object

        Raises:
            requests.RequestException: If request fails
        """
        timeout = timeout or self.settings.scraping_timeout
        response = self.session.get(url, timeout=timeout)
        response.raise_for_status()
        return response

    @abstractmethod
    def scrape(
        self, source_url: str, config: Optional[dict] = None
    ) -> List[ScrapedArticle]:
        """
        Scrape content from the source.

        Args:
            source_url: URL of the source to scrape
            config: Optional configuration dictionary for source-specific settings

        Returns:
            List of scraped articles

        Raises:
            Exception: If scraping fails
        """
        pass

    def close(self):
        """Close the HTTP session."""
        if self.session:
            self.session.close()
