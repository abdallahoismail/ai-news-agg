"""Digest service for generating daily summaries."""

from typing import List

from sqlalchemy.orm import Session

from app.models import Article
from app.agent import AISummarizer
from app.agent.summarizer import DigestSummary, ArticleSummary
from app.services.database import DatabaseService


class DigestService:
    """Service for generating daily digest with AI summaries."""

    def __init__(self, db: Session):
        """
        Initialize digest service.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db
        self.db_service = DatabaseService(db)
        self.summarizer = AISummarizer()

    def generate_digest(self, articles: List[Article]) -> DigestSummary:
        """
        Generate a complete digest from a list of articles.

        Args:
            articles: List of articles to include in digest

        Returns:
            Complete digest summary with overall analysis and article summaries
        """
        if not articles:
            return DigestSummary(
                overall_summary="No new articles to summarize.",
                insights=[],
                article_summaries=[]
            )

        print(f"Generating digest for {len(articles)} articles...")

        # Generate individual article summaries
        article_summaries: List[ArticleSummary] = []

        for article in articles:
            print(f"Summarizing: {article.title[:50]}...")

            summary = self.summarizer.generate_article_snippet(
                article_id=article.id,
                title=article.title,
                url=article.url,
                content=article.content,
                transcript=article.transcript
            )

            article_summaries.append(summary)

            # Save summary to database
            self.db_service.update_article_summary(article.id, summary.snippet)

        self.db.commit()

        # Generate overall summary and insights
        print("Generating overall summary and insights...")
        digest = self.summarizer.generate_overall_summary(article_summaries)

        print("Digest generation complete!")
        return digest
