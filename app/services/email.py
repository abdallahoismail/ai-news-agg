"""Email service for sending digest emails."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path

from jinja2 import Template

from app.config.settings import get_settings
from app.agent.summarizer import DigestSummary


class EmailService:
    """Service for sending emails via SMTP."""

    def __init__(self):
        """Initialize email service with settings."""
        self.settings = get_settings()

    def _render_html_email(self, digest: DigestSummary, date: str) -> str:
        """
        Render HTML email from digest using Jinja2 template.

        Args:
            digest: Digest summary to render
            date: Date string for the digest

        Returns:
            Rendered HTML email content
        """
        template_path = Path(__file__).parent.parent / "templates" / "digest_email.html"

        try:
            with open(template_path, "r") as f:
                template_str = f.read()

            template = Template(template_str)
            html = template.render(
                date=date,
                overall_summary=digest.overall_summary,
                insights=digest.insights,
                articles=digest.article_summaries
            )
            return html

        except FileNotFoundError:
            print(f"Warning: Template not found at {template_path}, using fallback")
            return self._render_fallback_html(digest, date)

    def _render_fallback_html(self, digest: DigestSummary, date: str) -> str:
        """
        Render simple HTML email without template (fallback).

        Args:
            digest: Digest summary to render
            date: Date string for the digest

        Returns:
            Simple HTML email content
        """
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #34495e; margin-top: 30px; }}
                .article {{ margin: 20px 0; padding: 15px; background: #f8f9fa; border-left: 4px solid #007bff; }}
                .article h3 {{ margin-top: 0; }}
                .key-points {{ margin: 10px 0; }}
                .insights {{ background: #e8f4f8; padding: 15px; border-radius: 5px; }}
                a {{ color: #007bff; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>AI News Digest - {date}</h1>

                <h2>Overall Summary</h2>
                <p>{digest.overall_summary}</p>

                <div class="insights">
                    <h2>Key Insights</h2>
                    <ul>
                        {"".join([f"<li>{insight}</li>" for insight in digest.insights])}
                    </ul>
                </div>

                <h2>Article Summaries</h2>
                {"".join([f'''
                <div class="article">
                    <h3>{article.title}</h3>
                    <p>{article.snippet}</p>
                    {"<div class='key-points'><strong>Key Points:</strong><ul>" + "".join([f"<li>{point}</li>" for point in article.key_points]) + "</ul></div>" if article.key_points else ""}
                    <p><a href="{article.url}">Read more →</a></p>
                </div>
                ''' for article in digest.article_summaries])}
            </div>
        </body>
        </html>
        """
        return html

    def send_digest(self, digest: DigestSummary) -> bool:
        """
        Send digest email via SMTP.

        Args:
            digest: Digest summary to send

        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = self.settings.smtp_from_email
            msg["To"] = self.settings.smtp_to_email
            msg["Subject"] = f"AI News Digest - {datetime.now().strftime('%Y-%m-%d')}"

            # Render HTML email
            date_str = datetime.now().strftime("%B %d, %Y")
            html_content = self._render_html_email(digest, date_str)

            # Attach HTML part
            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)

            # Connect to SMTP server and send
            print(f"Connecting to SMTP server: {self.settings.smtp_host}:{self.settings.smtp_port}")

            if self.settings.smtp_use_tls:
                server = smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port)

            # Login if credentials provided
            if self.settings.smtp_username and self.settings.smtp_password:
                server.login(self.settings.smtp_username, self.settings.smtp_password)

            # Send email
            server.send_message(msg)
            server.quit()

            print(f"Digest email sent successfully to {self.settings.smtp_to_email}")
            return True

        except Exception as e:
            print(f"Error sending email: {e}")
            return False
