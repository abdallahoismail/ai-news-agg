# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI News Aggregator - scrapes AI/ML content from multiple sources (RSS feeds, YouTube channels, web pages), generates GPT-4 summaries, and sends daily digest emails.

## Common Commands

```bash
# Install dependencies
uv sync

# Run the application
uv run python main.py

# Run tests
uv run pytest

# Docker development
docker-compose up --build

# Database migrations
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

## Architecture

**Entry Point**: `main.py` runs `run_daily_digest()` which orchestrates the 6-step workflow:
1. Initialize database
2. Create digest run record
3. Load sources from `config/sources.yaml`
4. Scrape all sources via `ScrapingService`
5. Generate AI digest via `DigestService`
6. Send email via `EmailService`

**Key Services** (`app/services/`):
- `DatabaseService`: CRUD operations for sources, articles, digest runs
- `ScrapingService`: Coordinates scrapers, handles deduplication
- `DigestService`: GPT-4 summarization and insight extraction
- `EmailService`: SMTP delivery with Jinja2 HTML templates

**Scrapers** (`app/scrapers/`): Inherit from `BaseScraper`, implement `scrape()` method
- `RssScraper`: RSS/Atom feeds via feedparser
- `YouTubeScraper`: YouTube Data API + transcript extraction
- `WebScraper`: Generic web page scraping

**Models** (`app/models/`): SQLAlchemy models - `Source`, `Article`, `DigestRun`

**Configuration**:
- `app/config/settings.py`: Pydantic settings from environment variables
- `config/sources.yaml`: Source definitions (name, type, url, config)

## Tech Stack

- Python 3.12+, uv for dependency management
- SQLAlchemy 2.0 with PostgreSQL
- OpenAI API for summarization
- Jinja2 for email templates
- Docker for deployment, Render for hosting
