"""Scraping service to orchestrate content scraping from sources."""

from typing import List

from sqlalchemy.orm import Session

from app.models import Source, Article
from app.models.source import SourceType
from app.scrapers import RSSFeedScraper, YouTubeScraper, WebScraper, ScrapedArticle
from app.services.database import DatabaseService


class ScrapingService:
    """Service to orchestrate scraping from multiple sources."""

    def __init__(self, db: Session):
        """
        Initialize scraping service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.db_service = DatabaseService(db)

        # Initialize scrapers
        self.rss_scraper = RSSFeedScraper()
        self.youtube_scraper = YouTubeScraper()
        self.web_scraper = WebScraper()

    def _get_scraper(self, source_type: SourceType):
        """
        Get appropriate scraper for source type.

        Args:
            source_type: Type of source

        Returns:
            Scraper instance
        """
        if source_type == SourceType.RSS:
            return self.rss_scraper
        elif source_type == SourceType.YOUTUBE:
            return self.youtube_scraper
        elif source_type == SourceType.WEB:
            return self.web_scraper
        else:
            raise ValueError(f"Unknown source type: {source_type}")

    def _save_scraped_articles(
        self,
        source: Source,
        scraped_articles: List[ScrapedArticle]
    ) -> List[Article]:
        """
        Save scraped articles to database, avoiding duplicates.

        Args:
            source: Source object
            scraped_articles: List of scraped articles

        Returns:
            List of saved Article objects
        """
        saved_articles = []

        for scraped in scraped_articles:
            # Check if article already exists
            existing = self.db_service.get_article_by_url(scraped.url)
            if existing:
                print(f"Article already exists: {scraped.url}")
                continue

            # Create new article
            article = self.db_service.create_article(
                source_id=source.id,
                title=scraped.title,
                url=scraped.url,
                content=scraped.content,
                transcript=scraped.transcript,
                published_date=scraped.published_date
            )
            saved_articles.append(article)

        self.db.commit()
        return saved_articles

    def scrape_source(self, source: Source) -> List[Article]:
        """
        Scrape a single source and save articles.

        Args:
            source: Source to scrape

        Returns:
            List of newly saved articles
        """
        print(f"Scraping source: {source.name} ({source.source_type})")

        try:
            scraper = self._get_scraper(source.source_type)
            scraped_articles = scraper.scrape(source.url, source.config)

            print(f"Found {len(scraped_articles)} articles from {source.name}")

            saved_articles = self._save_scraped_articles(source, scraped_articles)
            print(f"Saved {len(saved_articles)} new articles from {source.name}")

            return saved_articles

        except Exception as e:
            print(f"Error scraping source {source.name}: {e}")
            return []

    def scrape_all_sources(self) -> List[Article]:
        """
        Scrape all active sources and save articles.

        Returns:
            List of all newly saved articles
        """
        sources = self.db_service.get_active_sources()
        print(f"Found {len(sources)} active sources to scrape")

        all_articles = []
        for source in sources:
            articles = self.scrape_source(source)
            all_articles.extend(articles)

        print(f"Total: Scraped {len(all_articles)} new articles")
        return all_articles

    def close(self):
        """Close all scrapers."""
        self.rss_scraper.close()
        self.youtube_scraper.close()
        self.web_scraper.close()
