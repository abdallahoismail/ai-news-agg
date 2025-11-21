"""Generic web scraper for news websites and articles."""

from datetime import datetime
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from markdownify import markdownify as md
from docling.document_converter import DocumentConverter

from app.scrapers.base import BaseScraper, ScrapedArticle


class WebScraper(BaseScraper):
    """Generic web scraper for extracting article content from websites."""

    def __init__(self):
        """Initialize WebScraper with docling converter."""
        super().__init__()
        self._docling_converter = None

    def convert_url_to_markdown(self, url: str) -> Optional[str]:
        """
        Convert web page content to markdown using docling.

        This function uses docling's document converter to fetch and convert
        web content to markdown format. It provides better structure preservation
        and handling compared to basic HTML parsing.

        Args:
            url: The URL of the web page to convert

        Returns:
            Markdown string of the page content, or None if conversion fails

        Example:
            >>> scraper = WebScraper()
            >>> markdown = scraper.convert_url_to_markdown("https://example.com/article")
            >>> print(markdown)
        """
        try:
            # Lazy initialize docling converter
            if self._docling_converter is None:
                self._docling_converter = DocumentConverter()

            print(f"Converting URL to markdown using docling: {url}")

            # Convert the URL to a document
            result = self._docling_converter.convert(url)

            # Export to markdown
            markdown_content = result.document.export_to_markdown()

            if not markdown_content or len(markdown_content.strip()) < 100:
                print(f"Warning: Docling conversion produced minimal content from {url}")
                return None

            return markdown_content.strip()

        except Exception as e:
            print(f"Error converting URL to markdown with docling: {e}")
            return None

    def _extract_article_content(self, soup: BeautifulSoup) -> Optional[str]:
        """
        Extract main article content from HTML.

        Tries common article content selectors.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            Extracted content as markdown, or None if not found
        """
        # Common article content selectors
        content_selectors = [
            "article",
            "main",
            ".article-content",
            ".post-content",
            ".entry-content",
            "#content",
            ".content",
            "[role='main']",
        ]

        for selector in content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Remove unwanted elements
                for unwanted in content_elem.select("script, style, nav, footer, aside, .advertisement"):
                    unwanted.decompose()

                # Convert to markdown
                content = md(str(content_elem), heading_style="ATX").strip()
                if content and len(content) > 100:  # Ensure meaningful content
                    return content

        # Fallback: try to get all paragraphs
        paragraphs = soup.find_all("p")
        if paragraphs:
            content = "\n\n".join([p.get_text().strip() for p in paragraphs if p.get_text().strip()])
            if content and len(content) > 100:
                return content

        return None

    def _extract_title(self, soup: BeautifulSoup, url: str) -> str:
        """
        Extract article title from HTML.

        Args:
            soup: BeautifulSoup object of the page
            url: URL of the page (used as fallback)

        Returns:
            Article title
        """
        # Try meta tags first
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"]

        # Try h1 tag
        h1 = soup.find("h1")
        if h1:
            return h1.get_text().strip()

        # Try title tag
        title = soup.find("title")
        if title:
            return title.get_text().strip()

        # Fallback to URL
        return url

    def _extract_published_date(self, soup: BeautifulSoup) -> Optional[datetime]:
        """
        Try to extract published date from HTML.

        Args:
            soup: BeautifulSoup object of the page

        Returns:
            Published date if found, None otherwise
        """
        # Try meta tags
        date_selectors = [
            ("meta", {"property": "article:published_time"}),
            ("meta", {"name": "publishdate"}),
            ("meta", {"name": "date"}),
            ("time", {"datetime": True}),
        ]

        for tag, attrs in date_selectors:
            elem = soup.find(tag, attrs)
            if elem:
                date_str = elem.get("content") or elem.get("datetime")
                if date_str:
                    try:
                        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    except (ValueError, AttributeError):
                        continue

        return None

    def scrape(self, source_url: str, config: Optional[dict] = None) -> List[ScrapedArticle]:
        """
        Scrape content from a web page.

        Args:
            source_url: URL of the web page to scrape
            config: Optional configuration with options:
                - use_docling (bool): If True, use docling for conversion (default: False)
                - fallback_to_bs4 (bool): If docling fails, fallback to BeautifulSoup (default: True)

        Returns:
            List containing a single scraped article (if successful)
        """
        use_docling = config.get("use_docling", False) if config else False
        fallback_to_bs4 = config.get("fallback_to_bs4", True) if config else True

        content = None
        title = None
        published_date = None

        try:
            # Try docling first if requested
            if use_docling:
                print(f"Using docling to scrape {source_url}")
                content = self.convert_url_to_markdown(source_url)

                if content:
                    # For docling, we need to extract title and date separately
                    response = self._make_request(source_url)
                    soup = BeautifulSoup(response.content, "html.parser")
                    title = self._extract_title(soup, source_url)
                    published_date = self._extract_published_date(soup)
                elif not fallback_to_bs4:
                    print(f"Warning: Docling failed and fallback is disabled for {source_url}")
                    return []

            # Use BeautifulSoup approach if docling not used or failed
            if not content:
                print(f"Using BeautifulSoup to scrape {source_url}")
                response = self._make_request(source_url)
                soup = BeautifulSoup(response.content, "html.parser")

                title = self._extract_title(soup, source_url)
                content = self._extract_article_content(soup)
                published_date = self._extract_published_date(soup)

            if not content:
                print(f"Warning: Could not extract meaningful content from {source_url}")
                return []

            article = ScrapedArticle(
                title=title or source_url,
                url=source_url,
                content=content,
                published_date=published_date
            )

            return [article]

        except Exception as e:
            print(f"Error scraping {source_url}: {e}")
            return []
