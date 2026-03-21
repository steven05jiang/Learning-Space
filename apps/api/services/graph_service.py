"""
Graph service for managing tag relationships in Neo4j.

This service handles creating, updating, and cleaning up tag relationships
in the knowledge graph based on user resource processing activities.
"""

import logging
from itertools import combinations
from typing import List

from services.neo4j_driver import get_neo4j_driver

logger = logging.getLogger(__name__)


class GraphService:
    """Service for managing tag relationships in Neo4j graph database."""

    def __init__(self):
        pass

    async def update_from_resource(self, owner_id: int, tags: List[str]) -> None:
        """
        Update graph with tags from a resource.

        Creates Tag nodes (if they don't exist) and RELATED_TO edges between all
        tag pairs, incrementing weights for existing relationships.

        Args:
            owner_id: User ID that owns the resource
            tags: List of tag names to process
        """
        if not tags or len(tags) < 2:
            logger.debug(
                f"Skipping graph update for owner_id={owner_id}: less than 2 tags"
            )
            return

        neo4j_driver = await get_neo4j_driver()

        # Normalize tags (strip whitespace, remove empty tags)
        normalized_tags = [tag.strip() for tag in tags if tag and tag.strip()]

        if len(normalized_tags) < 2:
            logger.debug(
                f"Skipping graph update for owner_id={owner_id}: "
                f"less than 2 valid tags after normalization"
            )
            return

        async with neo4j_driver.get_session() as session:
            # Create or merge Tag nodes with owner_id scoping
            for tag in normalized_tags:
                await session.run(
                    """
                    MERGE (t:Tag {name: $tag, owner_id: $owner_id})
                    ON CREATE SET t.created_at = datetime()
                    """,
                    tag=tag,
                    owner_id=owner_id,
                )

            # Create or update RELATED_TO relationships for all tag pairs
            tag_pairs = list(combinations(normalized_tags, 2))

            for tag1, tag2 in tag_pairs:
                # Create bidirectional relationships with weight increment
                await session.run(
                    """
                    MATCH (t1:Tag {name: $tag1, owner_id: $owner_id})
                    MATCH (t2:Tag {name: $tag2, owner_id: $owner_id})
                    MERGE (t1)-[r:RELATED_TO]-(t2)
                    ON CREATE SET r.weight = 1
                    ON MATCH SET r.weight = r.weight + 1
                    """,
                    tag1=tag1,
                    tag2=tag2,
                    owner_id=owner_id,
                )

        logger.info(
            f"Updated graph for owner_id={owner_id}: "
            f"{len(normalized_tags)} tags, {len(tag_pairs)} relationships"
        )

    async def remove_resource_tags(self, owner_id: int, old_tags: List[str]) -> None:
        """
        Remove tag relationships from the graph by decrementing weights.

        Decrements relationship weights and removes edges that reach zero weight.

        Args:
            owner_id: User ID that owns the resource
            old_tags: List of tag names to remove relationships for
        """
        if not old_tags or len(old_tags) < 2:
            logger.debug(
                f"Skipping graph removal for owner_id={owner_id}: less than 2 tags"
            )
            return

        neo4j_driver = await get_neo4j_driver()

        # Normalize tags
        normalized_tags = [tag.strip() for tag in old_tags if tag and tag.strip()]

        if len(normalized_tags) < 2:
            logger.debug(
                f"Skipping graph removal for owner_id={owner_id}: "
                f"less than 2 valid tags after normalization"
            )
            return

        async with neo4j_driver.get_session() as session:
            # Decrement weights for all tag pairs and remove zero-weight edges
            tag_pairs = list(combinations(normalized_tags, 2))

            for tag1, tag2 in tag_pairs:
                await session.run(
                    """
                    MATCH (t1:Tag {name: $tag1, owner_id: $owner_id})
                        -[r:RELATED_TO]-
                        (t2:Tag {name: $tag2, owner_id: $owner_id})
                    SET r.weight = r.weight - 1
                    WITH r
                    WHERE r.weight <= 0
                    DELETE r
                    """,
                    tag1=tag1,
                    tag2=tag2,
                    owner_id=owner_id,
                )

        logger.info(
            f"Removed relationships for owner_id={owner_id}: "
            f"{len(normalized_tags)} tags, {len(tag_pairs)} relationships"
        )

    async def cleanup_orphan_tags(self, owner_id: int) -> None:
        """
        Clean up Tag nodes that have no remaining RELATED_TO relationships.

        Args:
            owner_id: User ID to clean up orphan tags for
        """
        neo4j_driver = await get_neo4j_driver()

        async with neo4j_driver.get_session() as session:
            # Find and delete Tag nodes with no RELATED_TO relationships
            result = await session.run(
                """
                MATCH (t:Tag {owner_id: $owner_id})
                WHERE NOT (t)-[:RELATED_TO]-()
                WITH t.name AS tag_name
                DELETE t
                RETURN COUNT(*) AS deleted_count, COLLECT(tag_name) AS deleted_tags
                """,
                owner_id=owner_id,
            )

            record = await result.single()
            if record:
                deleted_count = record["deleted_count"]
                deleted_tags = record["deleted_tags"]
                if deleted_count > 0:
                    logger.info(
                        f"Cleaned up {deleted_count} orphan tags for "
                        f"owner_id={owner_id}: {deleted_tags}"
                    )
                else:
                    logger.debug(f"No orphan tags found for owner_id={owner_id}")

    async def get_tag_relationships(self, owner_id: int) -> List[dict]:
        """
        Get all tag relationships for debugging/testing purposes.

        Args:
            owner_id: User ID to get relationships for

        Returns:
            List of relationship dictionaries with tag1, tag2, and weight
        """
        neo4j_driver = await get_neo4j_driver()

        async with neo4j_driver.get_session() as session:
            result = await session.run(
                """
                MATCH (t1:Tag {owner_id: $owner_id})
                    -[r:RELATED_TO]-
                    (t2:Tag {owner_id: $owner_id})
                WHERE t1.name < t2.name  // Avoid duplicate pairs
                RETURN t1.name AS tag1, t2.name AS tag2, r.weight AS weight
                ORDER BY r.weight DESC, t1.name, t2.name
                """,
                owner_id=owner_id,
            )

            relationships = []
            async for record in result:
                relationships.append(
                    {
                        "tag1": record["tag1"],
                        "tag2": record["tag2"],
                        "weight": record["weight"],
                    }
                )

            return relationships

    async def get_graph(self, owner_id: int, root: str | None = None) -> dict:
        """
        Get graph data for the authenticated user.

        Args:
            owner_id: User ID to get graph data for
            root: Optional root tag name to scope the graph

        Returns:
            Dictionary with nodes and edges lists for the knowledge graph
        """
        neo4j_driver = await get_neo4j_driver()

        async with neo4j_driver.get_session() as session:
            if root is None:
                # Get all nodes and edges for the user
                result = await session.run(
                    """
                    MATCH (t:Tag {owner_id: $owner_id})
                    OPTIONAL MATCH (t)-[r:RELATED_TO]-(t2:Tag {owner_id: $owner_id})
                    WHERE t.name < t2.name  // avoid duplicates
                    RETURN t, t2, r
                    """,
                    owner_id=owner_id,
                )
            else:
                # Get rooted subgraph with three levels: root, children, and parents
                result = await session.run(
                    """
                    MATCH (root:Tag {name: $root, owner_id: $owner_id})
                    OPTIONAL MATCH (root)-[r1:RELATED_TO]-(child:Tag
                        {owner_id: $owner_id})
                    OPTIONAL MATCH (child)-[r2:RELATED_TO]-(parent:Tag
                        {owner_id: $owner_id})
                    WHERE parent.name <> root.name
                    RETURN root, child, r1, parent, r2
                    """,
                    root=root,
                    owner_id=owner_id,
                )

            nodes = []
            edges = []
            nodes_set = set()
            edges_set = set()  # Track edges to avoid duplicates

            async for record in result:
                if root is None:
                    # All nodes mode
                    tag = record["t"]
                    tag2 = record.get("t2")
                    relationship = record.get("r")

                    # Add main tag
                    if tag["name"] not in nodes_set:
                        nodes.append(
                            {"id": tag["name"], "label": tag["name"], "level": "root"}
                        )
                        nodes_set.add(tag["name"])

                    # Add related tag and edge if exists
                    if tag2 and relationship:
                        if tag2["name"] not in nodes_set:
                            nodes.append(
                                {
                                    "id": tag2["name"],
                                    "label": tag2["name"],
                                    "level": "root",
                                }
                            )
                            nodes_set.add(tag2["name"])

                        # Add edge (undirected, so we use consistent ordering)
                        edges.append(
                            {
                                "source": tag["name"],
                                "target": tag2["name"],
                                "weight": relationship["weight"],
                            }
                        )
                else:
                    # Rooted subgraph mode with three levels
                    root_tag = record["root"]
                    child = record.get("child")
                    r1 = record.get("r1")
                    parent = record.get("parent")
                    r2 = record.get("r2")

                    # Add root tag
                    if root_tag["name"] not in nodes_set:
                        nodes.append(
                            {
                                "id": root_tag["name"],
                                "label": root_tag["name"],
                                "level": "current",
                            }
                        )
                        nodes_set.add(root_tag["name"])

                    # Add child node and edge if exists
                    if child and r1:
                        if child["name"] not in nodes_set:
                            nodes.append(
                                {
                                    "id": child["name"],
                                    "label": child["name"],
                                    "level": "child",
                                }
                            )
                            nodes_set.add(child["name"])

                        # Add edge between root and child
                        edge_key = tuple(sorted([root_tag["name"], child["name"]]))
                        if edge_key not in edges_set:
                            edges.append(
                                {
                                    "source": root_tag["name"],
                                    "target": child["name"],
                                    "weight": r1["weight"],
                                }
                            )
                            edges_set.add(edge_key)

                    # Add parent node and edge if exists
                    if parent and r2 and child:
                        if parent["name"] not in nodes_set:
                            nodes.append(
                                {
                                    "id": parent["name"],
                                    "label": parent["name"],
                                    "level": "parent",
                                }
                            )
                            nodes_set.add(parent["name"])

                        # Add edge between child and parent
                        edge_key = tuple(sorted([child["name"], parent["name"]]))
                        if edge_key not in edges_set:
                            edges.append(
                                {
                                    "source": child["name"],
                                    "target": parent["name"],
                                    "weight": r2["weight"],
                                }
                            )
                            edges_set.add(edge_key)

            return {"nodes": nodes, "edges": edges}

    async def get_neighbors(
        self, owner_id: int, node_id: str, direction: str = "out"
    ) -> dict:
        """
        Get direct neighbors of a specific node.

        Args:
            owner_id: User ID to scope the query to
            node_id: Name of the tag node to expand
            direction: Direction of relationships ("out", "in", "both")

        Returns:
            Dictionary with nodes and edges lists for the expanded node's neighbors
        """
        # Validate direction
        if direction not in ("out", "in", "both"):
            direction = "out"  # safe default

        neo4j_driver = await get_neo4j_driver()

        async with neo4j_driver.get_session() as session:
            # Build query based on direction
            if direction == "out":
                query = """
                    MATCH (root:Tag {name: $node_id, owner_id: $owner_id})-[r:RELATED_TO]->(neighbor:Tag {owner_id: $owner_id})
                    RETURN root, neighbor, r
                """
            elif direction == "in":
                query = """
                    MATCH (root:Tag {name: $node_id, owner_id: $owner_id})<-[r:RELATED_TO]-(neighbor:Tag {owner_id: $owner_id})
                    RETURN root, neighbor, r
                """
            else:  # "both"
                query = """
                    MATCH (root:Tag {name: $node_id, owner_id: $owner_id})-[r:RELATED_TO]-(neighbor:Tag {owner_id: $owner_id})
                    RETURN root, neighbor, r
                """

            result = await session.run(
                query,
                node_id=node_id,
                owner_id=owner_id,
            )

            nodes = []
            edges = []
            nodes_set = set()

            async for record in result:
                root_tag = record["root"]
                neighbor = record["neighbor"]
                relationship = record["r"]

                # Add neighbor as a child node (root is not included in response)
                if neighbor["name"] not in nodes_set:
                    nodes.append(
                        {
                            "id": neighbor["name"],
                            "label": neighbor["name"],
                            "level": "child",
                        }
                    )
                    nodes_set.add(neighbor["name"])

                # Add edge from root to neighbor
                edges.append(
                    {
                        "source": root_tag["name"],
                        "target": neighbor["name"],
                        "weight": relationship["weight"],
                    }
                )

            return {"nodes": nodes, "edges": edges}


# Global instance
graph_service = GraphService()


async def get_graph_service() -> GraphService:
    """Dependency function to get the graph service."""
    return graph_service
