"""DigestRun model for tracking digest execution."""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, DateTime, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class DigestRun(Base):
    """Model for tracking daily digest runs."""

    __tablename__ = "digest_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    articles_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    overall_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<DigestRun(id={self.id}, started_at={self.started_at}, success={self.success})>"
