"""Factory helpers for creating test data in integration tests."""

from typing import Any, Dict, List, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from models.resource import Resource, ResourceStatus
from models.user import User


async def make_resource(
    db_session: AsyncSession,
    user: User,
    content_type: str = "url",
    original_content: str = "https://example.com/test-article",
    prefer_provider: Optional[str] = None,
    title: Optional[str] = None,
    summary: Optional[str] = None,
    tags: Optional[List[str]] = None,
    status: ResourceStatus = ResourceStatus.PENDING,
    **kwargs
) -> Resource:
    """Create a resource with realistic test data.

    Args:
        db_session: Database session for creating the resource
        user: User who owns the resource
        content_type: Type of content (url, text, file, etc.)
        original_content: The original content/URL
        prefer_provider: Preferred provider for fetching (optional)
        title: Resource title (auto-generated if None)
        summary: Resource summary (auto-generated if None)
        tags: Resource tags (auto-generated if None)
        status: Resource processing status
        **kwargs: Additional fields to set on the resource

    Returns:
        Created Resource instance
    """
    # Generate realistic defaults based on content type
    if title is None:
        if content_type == "url":
            title = f"Article from {original_content}"
        elif content_type == "text":
            title = "Text Content"
        else:
            title = f"{content_type.title()} Resource"

    if summary is None:
        if content_type == "url":
            summary = f"This is a comprehensive summary of the content found at {original_content}. The article covers various important topics and provides valuable insights."
        elif content_type == "text":
            summary = "This is a summary of the provided text content, highlighting the main points and key takeaways."
        else:
            summary = f"Summary of {content_type} content with relevant details and analysis."

    if tags is None:
        if content_type == "url":
            tags = ["article", "web", "content", "technology"]
        elif content_type == "text":
            tags = ["text", "document", "content"]
        else:
            tags = ["resource", content_type, "content"]

    # Create the resource
    resource_data = {
        "owner_id": user.id,
        "content_type": content_type,
        "original_content": original_content,
        "prefer_provider": prefer_provider,
        "title": title,
        "summary": summary,
        "tags": tags,
        "status": status,
        **kwargs
    }

    resource = Resource(**resource_data)
    db_session.add(resource)
    await db_session.commit()
    await db_session.refresh(resource)

    return resource


def make_resource_data(
    content_type: str = "url",
    original_content: str = "https://example.com/test-article",
    prefer_provider: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """Create resource data dictionary for API requests.

    Args:
        content_type: Type of content (url, text, file, etc.)
        original_content: The original content/URL
        prefer_provider: Preferred provider for fetching (optional)
        **kwargs: Additional fields to include

    Returns:
        Dictionary suitable for API resource creation requests
    """
    data = {
        "content_type": content_type,
        "original_content": original_content,
    }

    if prefer_provider:
        data["prefer_provider"] = prefer_provider

    data.update(kwargs)
    return data


def make_sample_urls() -> List[str]:
    """Generate a list of sample URLs for testing.

    Returns:
        List of realistic test URLs
    """
    return [
        "https://example.com/tech-article",
        "https://blog.example.com/programming-tutorial",
        "https://news.example.com/latest-update",
        "https://docs.example.com/api-reference",
        "https://research.example.com/ai-paper",
        "https://github.com/example/project",
        "https://stackoverflow.com/questions/example",
        "https://medium.com/@author/article-title",
    ]


def make_sample_text_content() -> str:
    """Generate sample text content for testing.

    Returns:
        Realistic text content string
    """
    return """
    Artificial Intelligence and Machine Learning have revolutionized the way we approach
    problem-solving in technology. This comprehensive guide explores the fundamental concepts
    behind AI systems and their practical applications in modern software development.

    Key topics covered include:
    - Machine learning algorithms and their implementation
    - Deep learning networks and neural architecture
    - Natural language processing and understanding
    - Computer vision and image recognition
    - Ethical considerations in AI development

    The integration of AI into everyday applications has opened new possibilities for
    automation, personalization, and intelligent decision-making. As we continue to advance
    in this field, the importance of understanding these technologies becomes increasingly
    critical for developers and businesses alike.
    """


def make_llm_processed_data(
    title: str = "AI and Machine Learning Guide",
    summary: str = None,
    tags: List[str] = None
) -> Dict[str, Any]:
    """Create sample LLM-processed data for resources.

    Args:
        title: Processed title
        summary: Processed summary (auto-generated if None)
        tags: Processed tags (auto-generated if None)

    Returns:
        Dictionary with LLM-processed fields
    """
    if summary is None:
        summary = ("This article provides a comprehensive overview of artificial intelligence "
                  "and machine learning technologies, covering key concepts, algorithms, "
                  "and practical applications in modern software development.")

    if tags is None:
        tags = ["artificial-intelligence", "machine-learning", "technology", "programming", "automation"]

    return {
        "title": title,
        "summary": summary,
        "tags": tags,
        "status": ResourceStatus.READY
    }