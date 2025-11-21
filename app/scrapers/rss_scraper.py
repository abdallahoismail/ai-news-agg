"""RSS feed scraper for blog posts and news feeds."""

from datetime import datetime
from typing import List, Optional
import time

import feedparser
from markdownify import markdownify as md

from app.scrapers.base import BaseScraper, ScrapedArticle


class RSSFeedScraper(BaseScraper):
    """Scraper for RSS/Atom feeds."""

    def scrape(self, source_url: str, config: Optional[dict] = None) -> List[ScrapedArticle]:
        """
        Scrape articles from an RSS/Atom feed.

        Args:
            source_url: URL of the RSS/Atom feed
            config: Optional configuration (e.g., max_articles)

        Returns:
            List of scraped articles from the feed
        """
        max_articles = config.get("max_articles", self.settings.max_articles_per_source) if config else self.settings.max_articles_per_source

        # Parse the feed
        feed = feedparser.parse(source_url)

        if feed.bozo:
            # Feed has errors but might still be parseable
            if hasattr(feed, "bozo_exception"):
                print(f"Warning: Feed parsing error for {source_url}: {feed.bozo_exception}")

        articles = []

        for entry in feed.entries[:max_articles]:
            try:
                # Extract basic information
                title = entry.get("title", "No Title")
                url = entry.get("link", "")

                if not url:
                    continue

                # Extract content (prefer content over summary)
                content = None
                if hasattr(entry, "content") and entry.content:
                    content = entry.content[0].value
                elif hasattr(entry, "summary"):
                    content = entry.summary
                elif hasattr(entry, "description"):
                    content = entry.description

                # Convert HTML to markdown if content exists
                if content:
                    content = md(content, heading_style="ATX").strip()

                # Extract published date
                published_date = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    published_date = datetime(*entry.updated_parsed[:6])

                article = ScrapedArticle(
                    title=title,
                    url=url,
                    content=content,
                    published_date=published_date
                )

                articles.append(article)

            except Exception as e:
                print(f"Error parsing feed entry from {source_url}: {e}")
                continue

        return articles
