"""
Simple standalone test for docling URL to markdown conversion.

Run this to test docling without needing all environment variables:
    python test_docling_simple.py

This demonstrates the core docling functionality.
"""

from docling.document_converter import DocumentConverter


def convert_url_to_markdown(url: str) -> str:
    """
    Convert a URL to markdown using docling.

    Args:
        url: The URL to convert

    Returns:
        Markdown string of the content
    """
    print(f"Converting URL: {url}")
    print("-" * 70)

    try:
        # Initialize docling converter
        converter = DocumentConverter()

        # Convert the URL
        print("Fetching and converting content...")
        result = converter.convert(url)

        # Export to markdown
        markdown = result.document.export_to_markdown()

        return markdown

    except Exception as e:
        print(f"Error: {e}")
        raise


def main():
    print("=" * 70)
    print("DOCLING URL TO MARKDOWN CONVERTER TEST")
    print("=" * 70)
    print()

    # Test URLs
    test_urls = [
        "https://en.wikipedia.org/wiki/Artificial_intelligence",
        "https://en.wikipedia.org/wiki/Machine_learning",
    ]

    for i, url in enumerate(test_urls, 1):
        print(f"\n[Test {i}/{len(test_urls)}]")
        print("=" * 70)

        try:
            markdown = convert_url_to_markdown(url)

            print(f"\n✓ Successfully converted to markdown")
            print(f"Content length: {len(markdown)} characters")
            print(f"Content lines: {len(markdown.splitlines())} lines")

            print(f"\nFirst 800 characters:\n")
            print("-" * 70)
            print(markdown[:800])
            print("\n...")
            print("-" * 70)

        except Exception as e:
            print(f"\n✗ Failed to convert: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 70)
    print("TEST COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
