"""Article model for storing scraped content."""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Article(Base):
    """Model for storing scraped articles and content."""

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False, unique=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    published_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    source: Mapped["Source"] = relationship(back_populates="articles")

    # Indexes
    __table_args__ = (
        Index("idx_articles_source_id", "source_id"),
        Index("idx_articles_published_date", "published_date"),
        Index("idx_articles_scraped_at", "scraped_at"),
    )

    def __repr__(self) -> str:
        return f"<Article(id={self.id}, title='{self.title[:50]}...', source_id={self.source_id})>"
