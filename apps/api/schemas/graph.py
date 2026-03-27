"""Pydantic schemas for graph API endpoints."""

from pydantic import BaseModel, field_validator


class GraphNode(BaseModel):
    """A node in the knowledge graph."""

    id: str
    label: str
    level: str  # "root", "current", "child", "parent"
    node_type: str  # "root", "category", "topic"
    resource_count: int = 0  # Number of resources associated with this node


class GraphEdge(BaseModel):
    """An edge between two nodes in the knowledge graph."""

    source: str
    target: str
    weight: int


class GraphResponse(BaseModel):
    """Response schema for graph data."""

    nodes: list[GraphNode]
    edges: list[GraphEdge]


class GraphExpandRequest(BaseModel):
    """Request schema for expanding a graph node."""

    node_id: str
    direction: str = "out"  # "out", "in", "both"

    @field_validator("direction")
    @classmethod
    def validate_direction(cls, v: str) -> str:
        if v not in ("out", "in", "both"):
            raise ValueError("direction must be one of: out, in, both")
        return v
