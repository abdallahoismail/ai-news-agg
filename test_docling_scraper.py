"""
Test script for docling-based web scraping.

Run this to test the docling URL to markdown conversion:
    python test_docling_scraper.py

Tests both the standalone convert_url_to_markdown() function
and the integrated scrape() method with docling enabled.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.scrapers.web_scraper import WebScraper


def test_convert_url_to_markdown():
    """Test the convert_url_to_markdown function."""
    print("=" * 70)
    print("Test 1: convert_url_to_markdown() Function")
    print("=" * 70)

    scraper = WebScraper()

    # Test URL - using a well-structured article
    test_url = "https://en.wikipedia.org/wiki/Artificial_intelligence"

    print(f"\nConverting URL: {test_url}")
    print("-" * 70)

    try:
        markdown = scraper.convert_url_to_markdown(test_url)

        if markdown:
            print(f"\n✓ Successfully converted to markdown")
            print(f"Content length: {len(markdown)} characters")
            print(f"\nFirst 500 characters of markdown:\n")
            print("-" * 70)
            print(markdown[:500])
            print("...")
            print("-" * 70)
            return True
        else:
            print("\n✗ Conversion returned None or empty content")
            return False

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        scraper.close()


def test_scrape_with_docling():
    """Test the scrape method with docling enabled."""
    print("\n" + "=" * 70)
    print("Test 2: scrape() Method with use_docling=True")
    print("=" * 70)

    scraper = WebScraper()

    # Test URL
    test_url = "https://en.wikipedia.org/wiki/Machine_learning"

    print(f"\nScraping URL with docling: {test_url}")
    print("-" * 70)

    try:
        # Scrape with docling enabled
        config = {"use_docling": True, "fallback_to_bs4": True}
        articles = scraper.scrape(test_url, config)

        if articles:
            article = articles[0]
            print(f"\n✓ Successfully scraped article")
            print(f"\nTitle: {article.title}")
            print(f"URL: {article.url}")
            print(f"Published Date: {article.published_date}")
            print(f"Content length: {len(article.content) if article.content else 0} characters")

            if article.content:
                print(f"\nFirst 500 characters of content:\n")
                print("-" * 70)
                print(article.content[:500])
                print("...")
                print("-" * 70)

            return True
        else:
            print("\n✗ Scraping returned no articles")
            return False

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        scraper.close()


def test_scrape_comparison():
    """Test both BeautifulSoup and docling methods side by side."""
    print("\n" + "=" * 70)
    print("Test 3: Comparison - BeautifulSoup vs Docling")
    print("=" * 70)

    test_url = "https://en.wikipedia.org/wiki/Deep_learning"

    print(f"\nScraping URL: {test_url}")
    print("-" * 70)

    # Test with BeautifulSoup
    print("\n[Method 1: BeautifulSoup]")
    scraper_bs4 = WebScraper()
    try:
        articles_bs4 = scraper_bs4.scrape(test_url, {"use_docling": False})
        if articles_bs4:
            print(f"✓ Content length: {len(articles_bs4[0].content) if articles_bs4[0].content else 0} chars")
        else:
            print("✗ Failed to scrape")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        scraper_bs4.close()

    # Test with docling
    print("\n[Method 2: Docling]")
    scraper_docling = WebScraper()
    try:
        articles_docling = scraper_docling.scrape(test_url, {"use_docling": True})
        if articles_docling:
            print(f"✓ Content length: {len(articles_docling[0].content) if articles_docling[0].content else 0} chars")
        else:
            print("✗ Failed to scrape")
    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        scraper_docling.close()


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("DOCLING WEB SCRAPER TESTS")
    print("=" * 70)

    test1_passed = test_convert_url_to_markdown()
    test2_passed = test_scrape_with_docling()
    test_scrape_comparison()

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Test 1 (convert_url_to_markdown): {'✓ PASSED' if test1_passed else '✗ FAILED'}")
    print(f"Test 2 (scrape with docling):     {'✓ PASSED' if test2_passed else '✗ FAILED'}")
    print(f"Test 3 (comparison):               ✓ COMPLETED")
    print("=" * 70)
