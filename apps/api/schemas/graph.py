"""Pydantic schemas for graph API endpoints."""

from pydantic import BaseModel


class GraphNode(BaseModel):
    """A node in the knowledge graph."""

    id: str
    label: str
    level: str  # "root", "current", "child", "parent"


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
