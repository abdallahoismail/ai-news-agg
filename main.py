"""Main entry point for AI News Aggregator."""

import sys
from datetime import datetime
from pathlib import Path

import yaml

from app.config.database import init_db, get_db
from app.services import DatabaseService, ScrapingService, DigestService, EmailService


def load_sources_config(config_path: str = "config/sources.yaml") -> list:
    """
    Load sources configuration from YAML file.

    Args:
        config_path: Path to sources configuration file

    Returns:
        List of source configurations
    """
    config_file = Path(config_path)

    if not config_file.exists():
        print(f"Warning: Sources config not found at {config_path}")
        return []

    try:
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
            return config.get("sources", [])
    except Exception as e:
        print(f"Error loading sources config: {e}")
        return []


def run_daily_digest():
    """Run the complete daily digest workflow."""
    print("=" * 60)
    print(f"AI News Aggregator - Daily Digest")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    digest_run_id = None

    try:
        # Initialize database
        print("\n[1/6] Initializing database...")
        init_db()
        print("✓ Database initialized")

        with get_db() as db:
            db_service = DatabaseService(db)

            # Create digest run record
            print("\n[2/6] Creating digest run record...")
            digest_run = db_service.create_digest_run()
            digest_run_id = digest_run.id
            db.commit()
            print(f"✓ Digest run #{digest_run_id} created")

            # Load and create sources
            print("\n[3/6] Loading sources configuration...")
            sources_config = load_sources_config()

            if sources_config:
                db_service.create_sources_from_config(sources_config)
                print(f"✓ Loaded {len(sources_config)} sources")
            else:
                print("⚠ No sources configured")

            # Scrape all sources
            print("\n[4/6] Scraping sources...")
            scraping_service = ScrapingService(db)
            new_articles = scraping_service.scrape_all_sources()
            scraping_service.close()

            if not new_articles:
                print("⚠ No new articles found")
                # Check for recent articles in database
                new_articles = db_service.get_recent_articles(days=1)
                if not new_articles:
                    print("⚠ No recent articles in database either")
                    db_service.complete_digest_run(
                        digest_run_id=digest_run_id,
                        success=True,
                        articles_processed=0,
                        overall_summary="No new articles to process.",
                        email_sent=False
                    )
                    db.commit()
                    print("\nDigest completed (no articles to process)")
                    return

            print(f"✓ Found {len(new_articles)} articles to process")

            # Generate digest
            print("\n[5/6] Generating AI-powered digest...")
            digest_service = DigestService(db)
            digest = digest_service.generate_digest(new_articles)
            print("✓ Digest generated")

            # Send email
            print("\n[6/6] Sending digest email...")
            email_service = EmailService()
            email_sent = email_service.send_digest(digest)

            if email_sent:
                print("✓ Email sent successfully")
            else:
                print("✗ Failed to send email")

            # Complete digest run
            db_service.complete_digest_run(
                digest_run_id=digest_run_id,
                success=True,
                articles_processed=len(new_articles),
                overall_summary=digest.overall_summary,
                email_sent=email_sent
            )
            db.commit()

        print("\n" + "=" * 60)
        print("✓ Daily digest completed successfully!")
        print(f"Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Error during digest generation: {e}")
        import traceback
        traceback.print_exc()

        # Mark digest run as failed
        if digest_run_id:
            try:
                with get_db() as db:
                    db_service = DatabaseService(db)
                    db_service.complete_digest_run(
                        digest_run_id=digest_run_id,
                        success=False,
                        articles_processed=0,
                        error_message=str(e),
                        email_sent=False
                    )
                    db.commit()
            except Exception as db_error:
                print(f"Failed to update digest run: {db_error}")

        sys.exit(1)


def main():
    """Main entry point."""
    run_daily_digest()


if __name__ == "__main__":
    main()
