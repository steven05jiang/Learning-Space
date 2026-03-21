# ADJUST IMPORT TO MATCH ACTUAL CODEBASE PATH:
from models.resource import Resource  # or app.models.resource, etc.


async def make_resource(db, owner_id, **kwargs) -> Resource:
    defaults = {
        "content_type": "url",
        "original_content": "https://example.com/article",
        "status": "READY",
        "title": "Test Article",
        "summary": "A test summary.",
        "tags": ["AI", "Testing"],
    }
    resource = Resource(owner_id=owner_id, **{**defaults, **kwargs})
    db.add(resource)
    await db.flush()
    return resource