"""AI summarizer using OpenAI for content analysis."""

from typing import List, Dict, Optional
from dataclasses import dataclass

from openai import OpenAI

from app.config.settings import get_settings


@dataclass
class ArticleSummary:
    """Data class for article summary and snippet."""

    article_id: int
    title: str
    url: str
    snippet: str
    key_points: List[str]


@dataclass
class DigestSummary:
    """Data class for complete digest summary."""

    overall_summary: str
    insights: List[str]
    article_summaries: List[ArticleSummary]


class AISummarizer:
    """AI-powered summarizer using OpenAI for content analysis."""

    def __init__(self):
        """Initialize AI summarizer with OpenAI client."""
        self.settings = get_settings()
        self.client = OpenAI(api_key=self.settings.openai_api_key)
        self.model = self.settings.openai_model

    def generate_article_snippet(
        self,
        article_id: int,
        title: str,
        url: str,
        content: Optional[str],
        transcript: Optional[str]
    ) -> ArticleSummary:
        """
        Generate a short snippet and key points for a single article.

        Args:
            article_id: Database ID of the article
            title: Article title
            url: Article URL
            content: Article content (if available)
            transcript: Video transcript (if available)

        Returns:
            ArticleSummary with snippet and key points
        """
        # Prepare content for analysis
        text_to_analyze = ""
        if content:
            text_to_analyze = content[:3000]  # Limit to avoid token limits
        elif transcript:
            text_to_analyze = transcript[:3000]

        if not text_to_analyze:
            # Fallback if no content available
            return ArticleSummary(
                article_id=article_id,
                title=title,
                url=url,
                snippet="Content not available for analysis.",
                key_points=[]
            )

        # Create prompt for snippet generation
        prompt = f"""Analyze the following article and provide:
1. A concise 2-3 sentence snippet summarizing the main point
2. 2-4 key takeaways as bullet points

Title: {title}
Content:
{text_to_analyze}

Provide your response in this format:
SNIPPET: [your snippet here]
KEY POINTS:
- [point 1]
- [point 2]
- [point 3]"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.settings.agent_system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=300
            )

            result = response.choices[0].message.content.strip()

            # Parse response
            snippet = ""
            key_points = []

            if "SNIPPET:" in result:
                snippet_part = result.split("SNIPPET:")[1].split("KEY POINTS:")[0].strip()
                snippet = snippet_part

            if "KEY POINTS:" in result:
                points_part = result.split("KEY POINTS:")[1].strip()
                key_points = [
                    line.strip("- ").strip()
                    for line in points_part.split("\n")
                    if line.strip() and line.strip().startswith("-")
                ]

            return ArticleSummary(
                article_id=article_id,
                title=title,
                url=url,
                snippet=snippet or "Unable to generate snippet.",
                key_points=key_points
            )

        except Exception as e:
            print(f"Error generating snippet for article {article_id}: {e}")
            return ArticleSummary(
                article_id=article_id,
                title=title,
                url=url,
                snippet="Error generating summary.",
                key_points=[]
            )

    def generate_overall_summary(self, article_summaries: List[ArticleSummary]) -> DigestSummary:
        """
        Generate overall summary and insights from multiple article summaries.

        Args:
            article_summaries: List of individual article summaries

        Returns:
            Complete digest summary with overall analysis and insights
        """
        if not article_summaries:
            return DigestSummary(
                overall_summary="No articles to summarize.",
                insights=[],
                article_summaries=[]
            )

        # Prepare aggregated content for analysis
        articles_text = "\n\n".join([
            f"Article {i+1}: {summary.title}\n{summary.snippet}\nKey points: {', '.join(summary.key_points)}"
            for i, summary in enumerate(article_summaries)
        ])

        prompt = f"""Based on the following collection of tech news articles, provide:
1. An overall summary (3-4 sentences) of the main themes and developments
2. 3-5 key insights or trends emerging from these articles

Articles:
{articles_text}

Provide your response in this format:
OVERALL SUMMARY: [your summary here]

KEY INSIGHTS:
- [insight 1]
- [insight 2]
- [insight 3]
- [insight 4]
- [insight 5]"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.settings.agent_system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            result = response.choices[0].message.content.strip()

            # Parse response
            overall_summary = ""
            insights = []

            if "OVERALL SUMMARY:" in result:
                summary_part = result.split("OVERALL SUMMARY:")[1].split("KEY INSIGHTS:")[0].strip()
                overall_summary = summary_part

            if "KEY INSIGHTS:" in result:
                insights_part = result.split("KEY INSIGHTS:")[1].strip()
                insights = [
                    line.strip("- ").strip()
                    for line in insights_part.split("\n")
                    if line.strip() and line.strip().startswith("-")
                ]

            return DigestSummary(
                overall_summary=overall_summary or "Unable to generate overall summary.",
                insights=insights,
                article_summaries=article_summaries
            )

        except Exception as e:
            print(f"Error generating overall summary: {e}")
            return DigestSummary(
                overall_summary="Error generating overall summary.",
                insights=[],
                article_summaries=article_summaries
            )
