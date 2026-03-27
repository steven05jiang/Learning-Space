"""LLM content processing service for extracting title, summary, and tags."""

import json
import logging
from dataclasses import dataclass
from typing import List, Optional

import anthropic
from anthropic import Anthropic

from core.config import settings
from services.llm_client import get_direct_client

logger = logging.getLogger(__name__)

_OPENAI_COMPAT_PROVIDERS = {"siliconflow", "fireworks", "groq"}

_TOOL_NAME = "extract_content_data"
_TOOL_PROPERTIES = {
    "title": {
        "type": "string",
        "description": "A clear, concise title for the content (max 200 chars)",
    },
    "summary": {
        "type": "string",
        "description": "A comprehensive summary of main points (100-500 words)",
    },
    "tags": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Exactly 3 specific tags/keywords (lowercase, hyphenated if multi-word)",
    },
    "top_level_categories": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Top-level categories (1-3 from available list)",
    },
}
_TOOL_REQUIRED = ["title", "summary", "tags", "top_level_categories"]


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
    """Service for processing content using LLM to extract data."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-haiku-4-5-20251001",
    ):
        """Initialize the LLM processor service.

        Args:
            api_key: Optional Anthropic API key for legacy/test use. When omitted,
                     the active LLM provider from settings is used instead.
            model: Model override (only applies when api_key is provided).
        """
        self.provider = settings.llm_provider.lower()
        self.client = None

        if api_key is not None:
            # Legacy / test path: explicit key always initialises an Anthropic client.
            self.api_key = api_key
            self.model = model
            self._use_openai_compat = False
            if api_key and api_key != "test-anthropic-key-for-development":
                try:
                    self.client = Anthropic(api_key=api_key)
                except Exception as e:
                    logger.warning(f"Failed to initialize Anthropic client: {e}")
        else:
            # Production path: delegate to the configured provider via get_direct_client().
            self.api_key = None
            model_map = {
                "anthropic": settings.anthropic_model,
                "groq": settings.groq_model,
                "siliconflow": settings.siliconflow_model,
                "fireworks": settings.fireworks_model,
            }
            self.model = model_map.get(self.provider, settings.anthropic_model)
            self._use_openai_compat = self.provider in _OPENAI_COMPAT_PROVIDERS
            try:
                self.client = get_direct_client()
            except Exception as e:
                logger.warning(f"Failed to initialize LLM client: {e}")

    # ------------------------------------------------------------------
    # Internal API call helpers
    # ------------------------------------------------------------------

    def _invoke_anthropic(self, system_prompt: str, user_message: str) -> dict:
        """Call the Anthropic messages API and return extracted_data dict."""
        tool_def = {
            "name": _TOOL_NAME,
            "description": "Extract title, summary, tags, and top-level categories",
            "input_schema": {
                "type": "object",
                "properties": _TOOL_PROPERTIES,
                "required": _TOOL_REQUIRED,
            },
        }
        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
            tools=[tool_def],
            tool_choice={"type": "tool", "name": _TOOL_NAME},
        )

        if not response.content:
            raise ValueError("empty_response")

        tool_use = next(
            (b for b in response.content if getattr(b, "type", None) == "tool_use"),
            None,
        )
        if not tool_use:
            raise ValueError("no_tool_use")

        return tool_use.input

    def _invoke_openai_compat(self, system_prompt: str, user_message: str) -> dict:
        """Call an OpenAI-compatible chat completions API and return extracted_data dict."""
        tool_def = {
            "type": "function",
            "function": {
                "name": _TOOL_NAME,
                "description": "Extract title, summary, tags, and top-level categories",
                "parameters": {
                    "type": "object",
                    "properties": _TOOL_PROPERTIES,
                    "required": _TOOL_REQUIRED,
                },
            },
        }
        response = self.client.chat.completions.create(
            model=self.model,
            max_tokens=1500,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            tools=[tool_def],
            tool_choice={"type": "function", "function": {"name": _TOOL_NAME}},
        )

        choices = getattr(response, "choices", None)
        if not choices:
            raise ValueError("empty_response")

        tool_calls = getattr(choices[0].message, "tool_calls", None)
        if not tool_calls:
            raise ValueError("no_tool_use")

        return json.loads(tool_calls[0].function.arguments)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def process_content(
        self,
        content: str,
        content_type: str,
        existing_user_tags: Optional[List[str]] = None,
        valid_categories: Optional[List[str]] = None,
    ) -> LLMResult:
        """Process content to extract title, summary, tags, and categories."""
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
                error_message="LLM client not configured or invalid",
            )

        logger.info(
            f"Processing content of type {content_type} ({len(content)} characters)"
        )

        system_prompt = self._build_system_prompt(existing_user_tags, valid_categories)
        user_message = self._build_user_message(content, content_type)

        try:
            if self._use_openai_compat:
                extracted_data = self._invoke_openai_compat(system_prompt, user_message)
            else:
                extracted_data = self._invoke_anthropic(system_prompt, user_message)

        except ValueError as e:
            msg = str(e)
            if msg == "empty_response":
                return LLMResult(
                    success=False,
                    error_type="api_error",
                    error_message="Empty response from LLM",
                )
            if msg == "no_tool_use":
                return LLMResult(
                    success=False,
                    error_type="api_error",
                    error_message="No tool use found in LLM response",
                )
            return LLMResult(
                success=False,
                error_type="api_error",
                error_message=f"API error: {msg}",
            )

        except anthropic.RateLimitError:
            logger.warning("Rate limit error")
            return LLMResult(
                success=False,
                error_type="rate_limit",
                error_message="API rate limit exceeded",
            )

        except anthropic.APITimeoutError:
            logger.warning("Timeout error")
            return LLMResult(
                success=False,
                error_type="timeout",
                error_message="API request timed out",
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
            logger.warning("Connection error")
            return LLMResult(
                success=False,
                error_type="connection_error",
                error_message="Failed to connect to Anthropic API",
            )

        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            logger.error(f"Unexpected error processing content: {error_message}", exc_info=True)
            return LLMResult(
                success=False,
                error_type="unknown_error",
                error_message=error_message,
            )

        # --- Validate and clean extracted_data ---

        title = extracted_data.get("title", "").strip()
        summary = extracted_data.get("summary", "").strip()
        tags = extracted_data.get("tags", [])
        top_level_categories = extracted_data.get("top_level_categories", [])

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
            tags = clean_tags[:8]
        else:
            tags = []

        # Clean and validate top_level_categories
        if isinstance(top_level_categories, list):
            clean_categories = []

            if valid_categories:
                allowed_categories = valid_categories
            else:
                allowed_categories = [
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
                    if (
                        clean_category in allowed_categories
                        and clean_category not in clean_categories
                    ):
                        clean_categories.append(clean_category)
                    elif clean_category not in allowed_categories:
                        return LLMResult(
                            success=False,
                            error_type="INVALID_CATEGORY",
                            error_message=(
                                f"Category '{clean_category}' is not a valid "
                                f"category. Valid categories: {allowed_categories}"
                            ),
                        )

            if not clean_categories:
                return LLMResult(
                    success=False,
                    error_type="CATEGORY_REQUIRED",
                    error_message="At least one top-level category is required.",
                )

            top_level_categories = clean_categories[:3]
        else:
            return LLMResult(
                success=False,
                error_type="CATEGORY_REQUIRED",
                error_message="At least one top-level category is required.",
            )

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

    def _build_system_prompt(
        self,
        existing_user_tags: Optional[List[str]] = None,
        valid_categories: Optional[List[str]] = None,
    ) -> str:
        """Build the system prompt for content processing."""
        prompt = (
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
            "- Generate exactly 3 specific, descriptive tags "
            "(lowercase, hyphenated if multi-word)\n"
        )

        if existing_user_tags:
            prompt += (
                f"- Existing user tags (reuse when applicable): {existing_user_tags}\n"
            )

        if valid_categories:
            prompt += f"- Available categories: {valid_categories}\n"
        else:
            prompt += (
                "- Categories from: Science & Technology, Business & Economics, "
                "Politics & Government, Society & Culture, Education & Knowledge, "
                "Health & Medicine, Environment & Sustainability, "
                "Arts & Entertainment, Sports & Recreation, Lifestyle & Personal Life\n"
            )

        prompt += (
            "- Select 1-3 most relevant categories (REQUIRED)\n"
            "- Focus on the main content, ignore navigation, ads, or boilerplate text\n"
            "- For HTML content, extract the meaningful text content\n"
            "- Be objective and factual in your analysis"
        )

        return prompt

    def _build_user_message(self, content: str, content_type: str) -> str:
        """Build the user message with content to process."""
        import re

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
