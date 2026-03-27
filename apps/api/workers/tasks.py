"""Task definitions for the job queue."""

import logging
from datetime import datetime
from typing import Any, Dict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.category import Category
from models.database import AsyncSessionLocal
from models.resource import ProcessingStatus, Resource, ResourceStatus
from services.graph_service import graph_service
from services.llm_processor import llm_processor_service
from services.tiered_url_fetcher import tiered_url_fetcher_service

# Use tiered fetcher by default now
_fetcher = tiered_url_fetcher_service

logger = logging.getLogger(__name__)


async def process_resource(
    ctx: Dict[str, Any], resource_id: str, options: Dict[str, Any] | None = None
) -> Dict[str, Any]:
    """Process a resource through the full pipeline.

    Pipeline steps:
    1. Set status -> PROCESSING
    2. Fetch content (URL resources) or use original_content (text resources)
    3. LLM processing (extract title, summary, tags)
    4. Update resource in DB (status -> READY, write title/summary/tags)
    5. Trigger graph update (placeholder hook for now)
    6. Handle errors at each step -> status -> FAILED with status_message

    Args:
        resource_id: The ID of the resource to process
        options: Optional processing configuration

    Returns:
        Processing result dictionary

    Raises:
        ValueError: If resource_id is invalid
    """
    logger.info(f"Starting resource processing for resource_id={resource_id}")

    if not resource_id:
        raise ValueError("resource_id cannot be empty")

    async with AsyncSessionLocal() as session:
        try:
            # Step 1: Get resource and set status to PROCESSING
            result = await session.execute(
                select(Resource).where(Resource.id == int(resource_id))
            )
            resource = result.scalar_one_or_none()

            if not resource:
                raise ValueError(f"Resource with id {resource_id} not found")

            # Check if resource is already in terminal processing state
            terminal_states = [ProcessingStatus.SUCCESS, ProcessingStatus.FAILED]
            if resource.processing_status in terminal_states:
                status_value = resource.processing_status.value
                logger.info(
                    f"Skipping resource {resource_id}: already in terminal "
                    f"processing state {status_value}"
                )
                return {
                    "resource_id": resource_id,
                    "status": "skipped",
                    "reason": f"Already in terminal state: {status_value}",
                    "processing_status": status_value,
                }

            logger.info(
                f"Processing resource {resource_id}: "
                f"content_type={resource.content_type}, "
                f"status={resource.status.value}, "
                f"processing_status={resource.processing_status.value}"
            )

            # Set status to PROCESSING and processing_status to PROCESSING
            resource.status = ResourceStatus.PROCESSING
            resource.processing_status = ProcessingStatus.PROCESSING
            resource.status_message = None
            resource.updated_at = datetime.utcnow()
            await session.commit()

            # Step 2: Fetch content
            content_to_process = None
            final_content_type = resource.content_type

            if resource.content_type == "url":
                # Use tiered URL fetcher for URL resources
                fetch_result = await _fetcher.fetch_url_content(
                    resource.original_content, resource.owner_id
                )

                if not fetch_result.success:
                    # Set appropriate error fields based on fetch result
                    resource.fetch_error_type = fetch_result.error_type

                    # Map error types to user-friendly messages
                    error_msg = _get_user_friendly_error_message(
                        fetch_result.error_type, fetch_result.error_message
                    )

                    await _set_resource_failed(session, resource, error_msg)
                    return {
                        "resource_id": resource_id,
                        "status": "failed",
                        "error": error_msg,
                        "stage": "content_fetch",
                        "fetch_tier": fetch_result.fetch_tier,
                        "fetch_error_type": fetch_result.error_type,
                    }

                # Record which tier succeeded
                resource.fetch_tier = fetch_result.fetch_tier
                content_to_process = fetch_result.content
                final_content_type = fetch_result.content_type or "text/html"

                logger.info(
                    f"Fetched content for resource {resource_id} "
                    f"via {fetch_result.fetch_tier}: "
                    f"{len(content_to_process)} chars, type: {final_content_type}"
                )
            else:
                # Use original_content directly for text resources
                content_to_process = resource.original_content
                logger.info(
                    f"Using original content for resource {resource_id}: "
                    f"{len(content_to_process)} chars"
                )

            # Step 3a: Fetch existing user tags and valid categories
            existing_user_tags = await graph_service.get_user_tags(resource.owner_id)

            # Get valid categories (system + user-created)
            categories_result = await session.execute(
                select(Category.name)
                .where(
                    (Category.owner_id == resource.owner_id)
                    | (Category.owner_id.is_(None))
                )
                .order_by(Category.name)
            )
            valid_categories = [row.name for row in categories_result.fetchall()]

            # Step 3b: LLM processing with context
            llm_result = await llm_processor_service.process_content(
                content_to_process,
                final_content_type,
                existing_user_tags,
                valid_categories,
            )

            if not llm_result.success:
                # Handle specific validation errors with appropriate error types
                if llm_result.error_type in ["CATEGORY_REQUIRED", "INVALID_CATEGORY"]:
                    error_msg = (
                        f"Category validation failed: {llm_result.error_message}"
                    )
                    resource.fetch_error_type = llm_result.error_type
                else:
                    error_msg = f"LLM processing failed: {llm_result.error_message}"

                await _set_resource_failed(session, resource, error_msg)
                return {
                    "resource_id": resource_id,
                    "status": "failed",
                    "error": error_msg,
                    "stage": "llm_processing",
                    "error_type": llm_result.error_type,
                }

            logger.info(
                f"LLM processing completed for resource {resource_id}: "
                f"title='{llm_result.title[:50] if llm_result.title else 'None'}...', "
                f"summary_len={len(llm_result.summary) if llm_result.summary else 0}, "
                f"tags_count={len(llm_result.tags) if llm_result.tags else 0}"
            )

            # Step 4: Update resource in DB
            resource.title = llm_result.title
            resource.summary = llm_result.summary
            resource.tags = llm_result.tags or []
            resource.top_level_categories = llm_result.top_level_categories or []
            resource.status = ResourceStatus.READY
            resource.processing_status = ProcessingStatus.SUCCESS
            resource.status_message = None
            resource.updated_at = datetime.utcnow()
            await session.commit()

            # Step 5: Hierarchical graph update
            try:
                if llm_result.tags and llm_result.top_level_categories:
                    await graph_service.update_graph(
                        resource.owner_id,
                        llm_result.tags,
                        llm_result.top_level_categories,
                    )
                    logger.info(
                        f"Hierarchical graph updated for resource {resource_id} "
                        f"with {len(llm_result.tags)} tags and "
                        f"{len(llm_result.top_level_categories)} categories"
                    )

                    # Also update old-style tag relationships for backward compatibility
                    if len(llm_result.tags) >= 2:
                        await graph_service.update_from_resource(
                            resource.owner_id, llm_result.tags
                        )
                else:
                    tag_count = len(llm_result.tags) if llm_result.tags else 0
                    cat_count = (
                        len(llm_result.top_level_categories)
                        if llm_result.top_level_categories
                        else 0
                    )
                    logger.info(
                        f"Skipping graph update for resource {resource_id}: "
                        f"insufficient tags ({tag_count}) or categories ({cat_count})"
                    )
            except Exception as e:
                # Don't fail the entire job for graph update errors
                logger.warning(
                    f"Graph update failed for resource {resource_id} "
                    f"but resource processing completed: {e}"
                )

            processing_result = {
                "resource_id": resource_id,
                "status": "ready",
                "processed_at": datetime.utcnow().isoformat(),
                "title": llm_result.title,
                "summary_length": len(llm_result.summary) if llm_result.summary else 0,
                "tags_count": len(llm_result.tags) if llm_result.tags else 0,
                "fetch_tier": resource.fetch_tier,
                "stages_completed": [
                    "status_update",
                    (
                        "content_fetch"
                        if resource.content_type == "url"
                        else "content_direct"
                    ),
                    "llm_processing",
                    "db_update",
                    "graph_update",
                ],
            }

            logger.info(f"Resource processing completed for resource_id={resource_id}")
            return processing_result

        except ValueError as e:
            # Re-raise ValueError (validation errors)
            logger.error(f"Validation error processing resource {resource_id}: {e}")
            raise
        except Exception as e:
            # Handle any other unexpected errors
            logger.error(
                f"Unexpected error processing resource {resource_id}: {e}",
                exc_info=True,
            )
            try:
                # Try to set resource status to FAILED
                await _set_resource_failed(
                    session, resource, f"Unexpected error: {str(e)}"
                )
            except Exception:
                # If we can't even set the status, just log and re-raise
                logger.error(f"Failed to set error status for resource {resource_id}")
            raise


def _get_user_friendly_error_message(error_type: str, original_error: str) -> str:
    """Map error types to user-friendly messages.

    Args:
        error_type: Machine-readable error type
        original_error: Original error message

    Returns:
        User-friendly error message
    """
    error_messages = {
        "API_REQUIRED": (
            "This link requires a linked account. Go to Settings to link your account."
        ),
        "NOT_SUPPORTED": "Fetching content from this platform is not yet supported.",
        "BOT_BLOCKED": (
            "This page blocked automated access. Try pasting the content manually."
        ),
        "FETCH_ERROR": "Could not reach this URL. Check the link and try again.",
        "validation_error": original_error,
        "not_found": "The page was not found (404).",
        "forbidden": "Access to this page is forbidden.",
        "unauthorized": "Authentication required to access this page.",
        "rate_limited": "Rate limit exceeded. Please try again later.",
        "timeout": "Request timed out. The page may be slow or unavailable.",
        "network_error": "Network error. Check your connection and try again.",
    }

    return error_messages.get(error_type, f"Failed to fetch content: {original_error}")


async def _set_resource_failed(
    session: AsyncSession, resource: Resource, error_message: str
) -> None:
    """Set resource status to FAILED with error message."""
    resource.status = ResourceStatus.FAILED
    resource.processing_status = ProcessingStatus.FAILED
    resource.status_message = error_message
    resource.updated_at = datetime.utcnow()
    await session.commit()
    logger.error(f"Resource {resource.id} marked as FAILED: {error_message}")


async def sync_graph(
    ctx: Dict[str, Any],
    entity_id: str,
    operation: str = "update",
    owner_id: int = None,
    tags: list = None,
) -> Dict[str, Any]:
    """Synchronize entity data with the knowledge graph.

    Args:
        entity_id: The ID of the entity to sync
        operation: Type of sync operation ('create', 'update', 'delete')
        owner_id: Owner ID for delete operations
        tags: Tag list for delete operations

    Returns:
        Synchronization result dictionary

    Raises:
        ValueError: If entity_id is invalid or operation is unsupported
    """
    logger.info(f"Starting graph sync for entity_id={entity_id}, operation={operation}")

    if not entity_id:
        raise ValueError("entity_id cannot be empty")

    valid_operations = {"create", "update", "delete"}
    if operation not in valid_operations:
        raise ValueError(
            f"operation must be one of {valid_operations}, got: {operation}"
        )

    if operation == "delete" and owner_id is not None and tags:
        await graph_service.remove_resource_tags(owner_id, tags)
        await graph_service.cleanup_orphan_tags(owner_id)
        return {"entity_id": entity_id, "operation": operation, "status": "synced"}

    # create/update not yet implemented (placeholder)
    return {"entity_id": entity_id, "operation": operation, "status": "noop"}


# Job failure handler
async def job_failed(ctx, job_id: str, exception: Exception):
    """Handle job failures by logging details.

    Args:
        ctx: ARQ context
        job_id: Failed job ID
        exception: The exception that caused the failure
    """
    logger.error(
        f"Job {job_id} failed with exception: {type(exception).__name__}: {exception}",
        exc_info=exception,
    )
