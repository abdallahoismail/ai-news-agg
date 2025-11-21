"""Source model for storing content sources."""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.models.base import Base


class SourceType(str, enum.Enum):
    """Types of sources that can be scraped."""

    RSS = "rss"
    YOUTUBE = "youtube"
    WEB = "web"


class Source(Base):
    """Model for storing content sources (RSS feeds, YouTube channels, websites)."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(SQLEnum(SourceType), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False, unique=True)
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    articles: Mapped[list["Article"]] = relationship(back_populates="source", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Source(id={self.id}, name='{self.name}', type={self.source_type})>"
