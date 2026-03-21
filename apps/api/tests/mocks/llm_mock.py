"""
Mock LLM client for integration testing.

Provides deterministic responses for Anthropic Claude API without external calls.
"""

import json
from typing import Any, Dict, List
from unittest.mock import Mock


class MockLLMClient:
    """
    Mock Anthropic Claude client for testing.

    Provides deterministic responses based on input patterns to ensure
    integration tests are reliable and reproducible.
    """

    def __init__(self):
        self.messages = MockMessages()
        self._response_templates = {
            "title": {
                "example.com": "Example Website - Learn Something New",
                "github.com": "GitHub Repository - {repo_name}",
                "twitter.com": "Twitter Post by @{username}",
                "default": "Interesting Article - {domain}",
            },
            "summary": {
                "example.com": "This is an example website that demonstrates various "
                "web technologies and best practices.",
                "github.com": "A software repository containing code for {repo_name}. "
                "Includes documentation, source code, and config.",
                "twitter.com": "A social media post discussing current topics and "
                "engaging with the community.",
                "default": "An informative article covering various topics relevant "
                "to the content domain.",
            },
            "tags": {
                "example.com": ["web", "technology", "example"],
                "github.com": ["programming", "software", "development", "opensource"],
                "twitter.com": ["social", "media", "discussion"],
                "default": ["article", "information", "content"],
            },
        }

    def set_response_template(
        self, content_type: str, domain: str, template: Any
    ) -> None:
        """Set a custom response template for specific domain and content type."""
        if content_type not in self._response_templates:
            self._response_templates[content_type] = {}
        self._response_templates[content_type][domain] = template

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL for response templating."""
        try:
            from urllib.parse import urlparse

            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith("www."):
                domain = domain[4:]
            return domain
        except Exception:
            return "unknown.com"

    def _generate_response(self, content: str, url: str = "") -> Dict:
        """Generate a realistic LLM response based on content and URL."""
        domain = self._extract_domain(url) if url else "default"

        # Try domain-specific template, fall back to default
        title_template = self._response_templates["title"].get(
            domain, self._response_templates["title"]["default"]
        )
        summary_template = self._response_templates["summary"].get(
            domain, self._response_templates["summary"]["default"]
        )
        tags_template = self._response_templates["tags"].get(
            domain, self._response_templates["tags"]["default"]
        )

        # Extract some context for templating
        context = {
            "domain": domain,
            "repo_name": "sample-project",
            "username": "testuser",
        }

        # Format templates
        title = (
            title_template.format(**context)
            if isinstance(title_template, str)
            else title_template
        )
        summary = (
            summary_template.format(**context)
            if isinstance(summary_template, str)
            else summary_template
        )
        tags = tags_template if isinstance(tags_template, list) else ["general"]

        return {"title": title, "summary": summary, "tags": tags}

    async def generate(self, prompt: str) -> str:
        """
        Generate a mock LLM response for the given prompt.

        Returns a JSON string with title, summary, and tags.
        """
        return json.dumps(
            {
                "title": "Mock Resource Title",
                "summary": "This is a mock summary for integration testing.",
                "tags": ["AI", "Testing", "Mock"],
            }
        )

    def _create_mock_message(self, content: Dict) -> Mock:
        """Create a mock message object that mimics Anthropic's response format."""
        mock_message = Mock()
        mock_message.content = [Mock()]
        mock_message.content[0].text = json.dumps(content, indent=2)
        mock_message.model = "claude-3-5-sonnet-20241022"
        mock_message.role = "assistant"
        mock_message.stop_reason = "end_turn"
        mock_message.stop_sequence = None
        mock_message.usage = Mock()
        mock_message.usage.input_tokens = 150
        mock_message.usage.output_tokens = 75
        return mock_message


class MockMessages:
    """Mock messages interface for Anthropic client."""

    def __init__(self):
        self._client = None

    def create(self, **kwargs) -> Mock:
        """
        Mock the messages.create method.

        Returns deterministic responses based on the input content.
        """
        messages = kwargs.get("messages", [])

        # Extract the user content to determine response
        user_content = ""
        url = ""

        for message in messages:
            if message.get("role") == "user":
                content = message.get("content", "")
                if isinstance(content, str):
                    user_content = content
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            user_content += item.get("text", "")

        # Look for URL in the content
        import re

        url_pattern = r"https?://[^\s]+"
        urls = re.findall(url_pattern, user_content)
        if urls:
            url = urls[0]

        # Create mock client if needed
        if not self._client:
            self._client = MockLLMClient()

        # Generate response based on content
        response_data = self._client._generate_response(user_content, url)

        return self._client._create_mock_message(response_data)


def setup_llm_success_mock(
    title: str = "Mock Article Title",
    summary: str = "This is a mock summary generated for testing purposes.",
    tags: List[str] = None,
) -> MockLLMClient:
    """
    Set up successful LLM response mock.

    Returns a MockLLMClient configured with the specified responses.
    """
    if tags is None:
        tags = ["mock", "testing", "article"]

    mock_client = MockLLMClient()

    # Override default templates with provided values
    mock_client._response_templates = {
        "title": {"default": title},
        "summary": {"default": summary},
        "tags": {"default": tags},
    }

    return mock_client


def setup_llm_error_mock(error_type: str = "rate_limit") -> Mock:
    """
    Set up LLM error response mock for testing error scenarios.

    Args:
        error_type: Type of error to simulate (rate_limit, invalid_request, etc.)
    """
    mock_client = Mock()

    if error_type == "rate_limit":
        from anthropic import RateLimitError

        mock_client.messages.create.side_effect = RateLimitError("Rate limit exceeded")
    elif error_type == "invalid_request":
        from anthropic import BadRequestError

        mock_client.messages.create.side_effect = BadRequestError("Invalid request")
    elif error_type == "api_error":
        from anthropic import APIError

        mock_client.messages.create.side_effect = APIError(
            "API temporarily unavailable"
        )
    else:
        # Generic error
        mock_client.messages.create.side_effect = Exception(f"Mock {error_type} error")

    return mock_client


def create_mock_anthropic_client() -> MockLLMClient:
    """
    Create a mock Anthropic client for dependency injection in tests.

    Returns a MockLLMClient that can be used as a drop-in replacement
    for the real Anthropic client in LLMProcessorService.
    """
    return MockLLMClient()
