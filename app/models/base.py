"""Base model for SQLAlchemy."""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

metadata = MetaData()


class Base(DeclarativeBase):
    """Base class for all database models."""

    metadata = metadata
