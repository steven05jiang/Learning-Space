"""LLM content processing service for extracting title, summary, and tags."""

import logging
from dataclasses import dataclass
from typing import List, Optional

import anthropic
from anthropic import Anthropic

from core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class LLMResult:
    """Result of LLM content processing operation."""

    success: bool
    title: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[List[str]] = None
    top_level_categories: Optional[List[str]] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None


class LLMProcessorService:
    """Service for processing content using Anthropic Claude to extract data."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-haiku-4-5-20251001",
    ):
        """Initialize the LLM processor service.

        Args:
            api_key: Anthropic API key (defaults to settings value)
            model: Claude model to use for processing
        """
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model
        self.client = None

        if self.api_key and self.api_key != "test-anthropic-key-for-development":
            try:
                self.client = Anthropic(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic client: {e}")

    async def process_content(self, content: str, content_type: str) -> LLMResult:
        """Process content to extract title, summary, and tags.

        Args:
            content: The content to process (text or HTML)
            content_type: Type of content (e.g., 'text/plain', 'text/html', 'url')

        Returns:
            LLMResult containing extracted data or error information
        """
        if not content or not content.strip():
            return LLMResult(
                success=False,
                error_type="validation_error",
                error_message="Content cannot be empty",
            )

        if not self.client:
            return LLMResult(
                success=False,
                error_type="configuration_error",
                error_message="Anthropic API key not configured or invalid",
            )

        logger.info(
            f"Processing content of type {content_type} ({len(content)} characters)"
        )

        try:
            # Prepare the content processing prompt
            system_prompt = self._build_system_prompt()
            user_message = self._build_user_message(content, content_type)

            # Define the tool for structured output
            process_content_tool = {
                "name": "extract_content_data",
                "description": "Extract title, summary, tags, and top-level categories",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": (
                                "A clear, concise title for the content (max 200 chars)"
                            ),
                        },
                        "summary": {
                            "type": "string",
                            "description": (
                                "A comprehensive summary of main points (100-500 words)"
                            ),
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "Relevant tags/keywords (3-8 tags, lowercase)"
                            ),
                        },
                        "top_level_categories": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "Top-level categories (1-3 from available list)"
                            ),
                        },
                    },
                    "required": ["title", "summary", "tags", "top_level_categories"],
                },
            }

            # Make the API call
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
                tools=[process_content_tool],
                tool_choice={"type": "tool", "name": "extract_content_data"},
            )

            # Extract the tool use result
            if not response.content or len(response.content) == 0:
                return LLMResult(
                    success=False,
                    error_type="api_error",
                    error_message="Empty response from LLM",
                )

            # Find tool use in response
            tool_use = None
            for content_block in response.content:
                if hasattr(content_block, "type") and content_block.type == "tool_use":
                    tool_use = content_block
                    break

            if not tool_use:
                return LLMResult(
                    success=False,
                    error_type="api_error",
                    error_message="No tool use found in LLM response",
                )

            # Extract structured data
            extracted_data = tool_use.input

            title = extracted_data.get("title", "").strip()
            summary = extracted_data.get("summary", "").strip()
            tags = extracted_data.get("tags", [])
            top_level_categories = extracted_data.get("top_level_categories", [])

            # Validate extracted data
            if not title:
                return LLMResult(
                    success=False,
                    error_type="extraction_error",
                    error_message="LLM failed to extract a valid title",
                )

            if not summary:
                return LLMResult(
                    success=False,
                    error_type="extraction_error",
                    error_message="LLM failed to extract a valid summary",
                )

            # Clean and validate tags
            if isinstance(tags, list):
                clean_tags = []
                for tag in tags:
                    if isinstance(tag, str) and tag.strip():
                        clean_tag = tag.strip().lower().replace(" ", "-")
                        if clean_tag and clean_tag not in clean_tags:
                            clean_tags.append(clean_tag)
                tags = clean_tags[:8]  # Limit to 8 tags
            else:
                tags = []

            # Clean and validate top_level_categories
            if isinstance(top_level_categories, list):
                clean_categories = []
                # For now, use placeholder categories until DEV-062
                default_categories = [
                    "Science & Technology",
                    "Business & Economics",
                    "Politics & Government",
                    "Society & Culture",
                    "Education & Knowledge",
                    "Health & Medicine",
                    "Environment & Sustainability",
                    "Arts & Entertainment",
                    "Sports & Recreation",
                    "Lifestyle & Personal Life",
                ]

                for category in top_level_categories:
                    if isinstance(category, str) and category.strip():
                        clean_category = category.strip()
                        # For now, just validate against default categories
                        if (clean_category in default_categories and
                            clean_category not in clean_categories):
                            clean_categories.append(clean_category)

                # If no valid categories found, default to "Science & Technology"
                if not clean_categories:
                    clean_categories = ["Science & Technology"]

                top_level_categories = clean_categories[:3]  # Limit to 3 categories
            else:
                top_level_categories = ["Science & Technology"]  # Default fallback

            logger.info(
                f"Successfully processed content: title='{title[:50]}...', "
                f"summary_len={len(summary)}, tags_count={len(tags)}, "
                f"categories_count={len(top_level_categories)}"
            )

            return LLMResult(
                success=True,
                title=title,
                summary=summary,
                tags=tags,
                top_level_categories=top_level_categories,
            )

        except anthropic.RateLimitError:
            error_message = "API rate limit exceeded"
            logger.warning(f"Rate limit error: {error_message}")
            return LLMResult(
                success=False,
                error_type="rate_limit",
                error_message=error_message,
            )

        except anthropic.APITimeoutError:
            error_message = "API request timed out"
            logger.warning(f"Timeout error: {error_message}")
            return LLMResult(
                success=False,
                error_type="timeout",
                error_message=error_message,
            )

        except anthropic.APIStatusError as e:
            error_message = f"API error: {e.status_code} - {e.message}"
            logger.warning(f"API status error: {error_message}")
            return LLMResult(
                success=False,
                error_type="api_error",
                error_message=error_message,
            )

        except anthropic.APIConnectionError:
            error_message = "Failed to connect to Anthropic API"
            logger.warning(f"Connection error: {error_message}")
            return LLMResult(
                success=False,
                error_type="connection_error",
                error_message=error_message,
            )

        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            logger.error(
                f"Unexpected error processing content: {error_message}", exc_info=True
            )
            return LLMResult(
                success=False,
                error_type="unknown_error",
                error_message=error_message,
            )

    def _build_system_prompt(self) -> str:
        """Build the system prompt for content processing."""
        return (
            "You are a content analysis assistant that extracts structured "
            "information from various types of content.\n\n"
            "Your task is to analyze the provided content and extract:\n"
            "1. A clear, concise title that captures the main topic\n"
            "2. A comprehensive summary of the key points and information\n"
            "3. Relevant tags/keywords for categorization\n"
            "4. Top-level categories that best classify the content\n\n"
            "Guidelines:\n"
            "- Title should be descriptive but concise (max 200 characters)\n"
            "- Summary should be comprehensive but readable (100-500 words)\n"
            "- Tags should be lowercase, hyphenated if multi-word\n"
            "- Categories from: Science & Technology, Business & Economics, "
            "Politics & Government, Society & Culture, Education & Knowledge, "
            "Health & Medicine, "
            "Environment & Sustainability, Arts & Entertainment, Sports & Recreation, "
            "Lifestyle & Personal Life\n"
            "- Select 1-3 most relevant categories\n"
            "- Focus on the main content, ignore navigation, ads, or boilerplate text\n"
            "- For HTML content, extract the meaningful text content\n"
            "- Be objective and factual in your analysis"
        )

    def _build_user_message(self, content: str, content_type: str) -> str:
        """Build the user message with content to process."""
        import re

        # For HTML content, strip tags/scripts/styles to plain text first so the
        # 3000-char window contains actual article text, not <head> boilerplate.
        if "html" in content_type:
            text = re.sub(r"<script[^>]*>.*?</script>", " ", content, flags=re.DOTALL)
            text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
        else:
            text = content

        content_preview = text[:3000] + ("..." if len(text) > 3000 else "")

        return (
            "Please analyze the following content and extract title, summary, tags.\n\n"
            f"Content Type: {content_type}\n"
            f"Content:\n{content_preview}\n\n"
            "Use the extract_content_data tool to provide the structured output."
        )


# Create singleton instance
llm_processor_service = LLMProcessorService()
