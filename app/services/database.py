"""Database service for managing database operations."""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.models import Source, Article, DigestRun
from app.models.source import SourceType


class DatabaseService:
    """Service for database operations."""

    def __init__(self, db: Session):
        """
        Initialize database service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    # Source operations
    def get_active_sources(self) -> List[Source]:
        """Get all active sources."""
        return self.db.query(Source).filter(Source.active == True).all()

    def get_source_by_url(self, url: str) -> Optional[Source]:
        """Get source by URL."""
        return self.db.query(Source).filter(Source.url == url).first()

    def create_source(
        self,
        name: str,
        source_type: SourceType,
        url: str,
        config: Optional[dict] = None,
        active: bool = True
    ) -> Source:
        """
        Create a new source.

        Args:
            name: Source name
            source_type: Type of source (RSS, YouTube, Web)
            url: Source URL
            config: Optional configuration dictionary
            active: Whether source is active

        Returns:
            Created source
        """
        source = Source(
            name=name,
            source_type=source_type,
            url=url,
            config=config,
            active=active
        )
        self.db.add(source)
        self.db.flush()
        return source

    def create_sources_from_config(self, sources_config: List[dict]) -> List[Source]:
        """
        Create multiple sources from configuration list.

        Args:
            sources_config: List of source configuration dictionaries

        Returns:
            List of created sources
        """
        sources = []
        for config in sources_config:
            # Check if source already exists
            existing = self.get_source_by_url(config["url"])
            if existing:
                sources.append(existing)
                continue

            source = self.create_source(
                name=config["name"],
                source_type=SourceType(config["type"]),
                url=config["url"],
                config=config.get("config"),
                active=config.get("active", True)
            )
            sources.append(source)

        self.db.commit()
        return sources

    # Article operations
    def get_article_by_url(self, url: str) -> Optional[Article]:
        """Get article by URL."""
        return self.db.query(Article).filter(Article.url == url).first()

    def create_article(
        self,
        source_id: int,
        title: str,
        url: str,
        content: Optional[str] = None,
        summary: Optional[str] = None,
        transcript: Optional[str] = None,
        published_date: Optional[datetime] = None
    ) -> Article:
        """
        Create a new article.

        Args:
            source_id: ID of the source
            title: Article title
            url: Article URL
            content: Article content
            summary: Article summary
            transcript: Video transcript (for YouTube videos)
            published_date: Published date

        Returns:
            Created article
        """
        article = Article(
            source_id=source_id,
            title=title,
            url=url,
            content=content,
            summary=summary,
            transcript=transcript,
            published_date=published_date
        )
        self.db.add(article)
        self.db.flush()
        return article

    def get_recent_articles(self, days: int = 1) -> List[Article]:
        """
        Get articles scraped in the last N days.

        Args:
            days: Number of days to look back

        Returns:
            List of recent articles
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return (
            self.db.query(Article)
            .filter(Article.scraped_at >= cutoff_date)
            .order_by(desc(Article.scraped_at))
            .all()
        )

    def update_article_summary(self, article_id: int, summary: str) -> None:
        """
        Update article summary.

        Args:
            article_id: Article ID
            summary: Summary text
        """
        article = self.db.query(Article).filter(Article.id == article_id).first()
        if article:
            article.summary = summary
            self.db.flush()

    # DigestRun operations
    def create_digest_run(self) -> DigestRun:
        """
        Create a new digest run.

        Returns:
            Created digest run
        """
        digest_run = DigestRun(started_at=datetime.utcnow())
        self.db.add(digest_run)
        self.db.flush()
        return digest_run

    def complete_digest_run(
        self,
        digest_run_id: int,
        success: bool,
        articles_processed: int,
        overall_summary: Optional[str] = None,
        error_message: Optional[str] = None,
        email_sent: bool = False
    ) -> None:
        """
        Mark digest run as completed.

        Args:
            digest_run_id: Digest run ID
            success: Whether digest was successful
            articles_processed: Number of articles processed
            overall_summary: Overall summary text
            error_message: Error message if failed
            email_sent: Whether email was sent
        """
        digest_run = self.db.query(DigestRun).filter(DigestRun.id == digest_run_id).first()
        if digest_run:
            digest_run.completed_at = datetime.utcnow()
            digest_run.success = success
            digest_run.articles_processed = articles_processed
            digest_run.overall_summary = overall_summary
            digest_run.error_message = error_message
            digest_run.email_sent = email_sent
            self.db.flush()

    def get_last_digest_run(self) -> Optional[DigestRun]:
        """Get the most recent digest run."""
        return (
            self.db.query(DigestRun)
            .order_by(desc(DigestRun.started_at))
            .first()
        )
