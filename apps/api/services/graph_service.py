"""
Graph service for managing hierarchical relationships in Neo4j.

This service handles creating, updating, and cleaning up hierarchical relationships
(Root -> Category -> Tag) in the knowledge graph based on user resource processing
activities.
"""

import logging
from itertools import combinations
from typing import List

from services.neo4j_driver import get_neo4j_driver

logger = logging.getLogger(__name__)


class GraphService:
    """Service for managing hierarchical relationships in Neo4j graph database."""

    def __init__(self):
        pass

    async def update_graph(
        self, owner_id: int, tags: List[str], top_level_categories: List[str]
    ) -> None:
        """
        Update graph with hierarchical structure: Root -> Category -> Tag.

        Creates/merges Root, Category, and Tag nodes with proper relationships:
        - Root node (one per user): "My Learning Space"
        - Category nodes: from top_level_categories
        - Tag nodes: from tags (LLM output)
        - CHILD_OF: Category -> Root
        - BELONGS_TO: Tag -> Category (for each category in top_level_categories)
        - RELATED_TO: Tag <-> Tag (co-occurrence edges)

        Args:
            owner_id: User ID that owns the resource
            tags: List of tag names from LLM processing
            top_level_categories: List of category names from LLM processing
        """
        if not tags or not top_level_categories:
            tag_count = len(tags) if tags else 0
            cat_count = len(top_level_categories) if top_level_categories else 0
            logger.debug(
                f"Skipping graph update for owner_id={owner_id}: "
                f"missing tags ({tag_count}) or categories ({cat_count})"
            )
            return

        neo4j_driver = await get_neo4j_driver()

        # Normalize inputs
        normalized_tags = [tag.strip() for tag in tags if tag and tag.strip()]
        normalized_categories = [
            cat.strip() for cat in top_level_categories if cat and cat.strip()
        ]

        if not normalized_tags or not normalized_categories:
            logger.debug(
                f"Skipping graph update for owner_id={owner_id}: "
                f"no valid tags or categories after normalization"
            )
            return

        async with neo4j_driver.get_session() as session:
            # 1. Create/merge Root node
            await session.run(
                """
                MERGE (r:Root {owner_id: $owner_id})
                ON CREATE SET r.name = 'My Learning Space',
                              r.node_type = 'root',
                              r.created_at = datetime()
                """,
                owner_id=str(owner_id),
            )

            # 2. Create/merge Category nodes and CHILD_OF relationships to Root
            for category in normalized_categories:
                await session.run(
                    """
                    MERGE (c:Category {id: $category, owner_id: $owner_id})
                    ON CREATE SET c.name = $category,
                                  c.node_type = 'category',
                                  c.created_at = datetime()
                    WITH c
                    MATCH (r:Root {owner_id: $owner_id})
                    MERGE (c)-[:CHILD_OF]->(r)
                    """,
                    category=category,
                    owner_id=str(owner_id),
                )

            # 3. Create/merge Tag nodes
            for tag in normalized_tags:
                await session.run(
                    """
                    MERGE (t:Tag {id: $tag, owner_id: $owner_id})
                    ON CREATE SET t.name = $tag,
                                  t.node_type = 'topic',
                                  t.created_at = datetime()
                    """,
                    tag=tag,
                    owner_id=str(owner_id),
                )

            # 4. Create BELONGS_TO relationships: Tag -> Category
            for tag in normalized_tags:
                for category in normalized_categories:
                    await session.run(
                        """
                        MATCH (t:Tag {id: $tag, owner_id: $owner_id})
                        MATCH (c:Category {id: $category, owner_id: $owner_id})
                        MERGE (t)-[b:BELONGS_TO]->(c)
                        ON CREATE SET b.weight = 1
                        ON MATCH SET b.weight = b.weight + 1
                        """,
                        tag=tag,
                        category=category,
                        owner_id=str(owner_id),
                    )

            # 5. Create/update RELATED_TO relationships between Tags (co-occurrence)
            if len(normalized_tags) >= 2:
                tag_pairs = list(combinations(normalized_tags, 2))
                for tag1, tag2 in tag_pairs:
                    await session.run(
                        """
                        MATCH (t1:Tag {id: $tag1, owner_id: $owner_id})
                        MATCH (t2:Tag {id: $tag2, owner_id: $owner_id})
                        MERGE (t1)-[r:RELATED_TO]-(t2)
                        ON CREATE SET r.weight = 1
                        ON MATCH SET r.weight = r.weight + 1
                        """,
                        tag1=tag1,
                        tag2=tag2,
                        owner_id=str(owner_id),
                    )

        logger.info(
            f"Updated hierarchical graph for owner_id={owner_id}: "
            f"{len(normalized_tags)} tags, {len(normalized_categories)} categories"
        )

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
                    owner_id=str(owner_id),
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
                    owner_id=str(owner_id),
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
                    owner_id=str(owner_id),
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
                WITH t, t.name AS tag_name
                DELETE t
                RETURN COUNT(*) AS deleted_count, COLLECT(tag_name) AS deleted_tags
                """,
                owner_id=str(owner_id),
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

    async def purge_orphan_nodes(
        self, owner_id: int, valid_tags: list, valid_categories: list
    ) -> dict:
        """
        Remove Tag and Category nodes that no longer exist in Postgres.

        Called with the full set of tags/categories currently in use by
        the user's resources, so anything not in those lists is orphaned.

        Args:
            owner_id: User ID to scope the cleanup
            valid_tags: All tag strings still used by at least one resource
            valid_categories: All category strings still used by at least one resource

        Returns:
            dict with deleted_tags and deleted_categories counts
        """
        neo4j_driver = await get_neo4j_driver()

        async with neo4j_driver.get_session() as session:
            # Delete Tag nodes whose id is not in the valid set
            tag_result = await session.run(
                """
                MATCH (t:Tag {owner_id: $owner_id})
                WHERE NOT t.id IN $valid_tags
                WITH t, t.id AS tag_id
                DETACH DELETE t
                RETURN COUNT(*) AS deleted, COLLECT(tag_id) AS deleted_ids
                """,
                owner_id=str(owner_id),
                valid_tags=valid_tags,
            )
            tag_record = await tag_result.single()
            deleted_tags = tag_record["deleted"] if tag_record else 0

            # Delete Category nodes whose id is not in the valid set
            cat_result = await session.run(
                """
                MATCH (c:Category {owner_id: $owner_id})
                WHERE NOT c.id IN $valid_categories
                WITH c, c.id AS cat_id
                DETACH DELETE c
                RETURN COUNT(*) AS deleted, COLLECT(cat_id) AS deleted_ids
                """,
                owner_id=str(owner_id),
                valid_categories=valid_categories,
            )
            cat_record = await cat_result.single()
            deleted_categories = cat_record["deleted"] if cat_record else 0

        logger.info(
            f"Purged orphan graph nodes for owner_id={owner_id}: "
            f"{deleted_tags} tags, {deleted_categories} categories"
        )
        return {
            "deleted_tags": deleted_tags,
            "deleted_categories": deleted_categories,
        }

    async def delete_tag_node(self, owner_id: int, tag: str) -> None:
        """
        Delete a Tag node and all its relationships from the graph.

        Used when a tag is no longer associated with any resource.

        Args:
            owner_id: User ID that owns the tag
            tag: Tag name to delete
        """
        neo4j_driver = await get_neo4j_driver()

        async with neo4j_driver.get_session() as session:
            result = await session.run(
                """
                MATCH (t:Tag {id: $tag, owner_id: $owner_id})
                DETACH DELETE t
                RETURN COUNT(t) AS deleted
                """,
                tag=tag,
                owner_id=str(owner_id),
            )
            record = await result.single()
            if record and record["deleted"] > 0:
                logger.info(f"Deleted orphan tag '{tag}' for owner_id={owner_id}")

    async def get_user_tags(self, owner_id: int) -> List[str]:
        """
        Get all existing tag names for a user.

        Args:
            owner_id: User ID to get tags for

        Returns:
            List of tag names
        """
        neo4j_driver = await get_neo4j_driver()

        async with neo4j_driver.get_session() as session:
            result = await session.run(
                """
                MATCH (t:Tag {owner_id: $owner_id})
                RETURN t.name AS tag_name
                ORDER BY t.name
                """,
                owner_id=str(owner_id),
            )

            tags = []
            async for record in result:
                tags.append(record["tag_name"])

            return tags

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
                owner_id=str(owner_id),
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
        Get hierarchical graph data for the authenticated user.

        Returns hierarchical structure with Root -> Category -> Tag levels.
        Includes node_type field on all nodes.

        Args:
            owner_id: User ID to get graph data for
            root: Optional node name to scope the graph (can be category or tag)

        Returns:
            Dictionary with nodes and edges lists for the knowledge graph
        """
        neo4j_driver = await get_neo4j_driver()

        async with neo4j_driver.get_session() as session:
            if root is None:
                # Get default view: Root node + all categories + all tags
                result = await session.run(
                    """
                    MATCH (r:Root {owner_id: $owner_id})
                    OPTIONAL MATCH (c:Category {owner_id: $owner_id})-[:CHILD_OF]->(r)
                    OPTIONAL MATCH (t:Tag {owner_id: $owner_id})-[:BELONGS_TO]->(c)
                    RETURN r, c, t
                    """,
                    owner_id=str(owner_id),
                )
            else:
                # Get expanded view centered on a specific node
                # First check if it's a category node
                result = await session.run(
                    """
                    MATCH (root_node {owner_id: $owner_id})
                    WHERE root_node.id = $root OR root_node.name = $root

                    // If it's a Category, get its Tags
                    OPTIONAL MATCH (root_node:Category)-[:CHILD_OF]->(r:Root)
                    OPTIONAL MATCH (t:Tag)-[bt:BELONGS_TO]->(root_node:Category)
                    // Add Tag resource count for visibility filtering
                    OPTIONAL MATCH (t)-[:RELATED_TO]-()
                    WITH root_node, r, t, bt,
                         CASE WHEN t IS NOT NULL THEN 1 ELSE 0 END as tag_resource_count
                    WHERE tag_resource_count >= 1 OR t IS NULL
                    // Only show tags with resources

                    // If it's a Tag, get its Category and related Tags
                    OPTIONAL MATCH (root_node:Tag)-[bt2:BELONGS_TO]->(c:Category)
                    OPTIONAL MATCH (root_node:Tag)-[rt:RELATED_TO]-(related_tag:Tag)

                    RETURN root_node, r, t, bt, c, bt2, related_tag, rt
                    """,
                    root=root,
                    owner_id=str(owner_id),
                )

            nodes = []
            edges = []
            nodes_set = set()
            edges_set = set()

            async for record in result:
                if root is None:
                    # Default view: Root + Categories + Tags
                    root_node = record.get("r")
                    category = record.get("c")
                    tag = record.get("t")

                    # Add Root node
                    if root_node and root_node.get("owner_id") not in nodes_set:
                        nodes.append(
                            {
                                "id": "My Learning Space",
                                "label": "My Learning Space",
                                "node_type": "root",
                                "level": "root",
                                "resource_count": 0,
                            }
                        )
                        nodes_set.add(root_node.get("owner_id"))

                    # Add Category nodes
                    if category and category.get("id") not in nodes_set:
                        nodes.append(
                            {
                                "id": category["id"],
                                "label": category["name"],
                                "node_type": "category",
                                "level": "current",
                                "resource_count": 0,
                            }
                        )
                        nodes_set.add(category["id"])

                        # Add CHILD_OF edge
                        edges.append(
                            {
                                "source": category["id"],
                                "target": "My Learning Space",
                                "weight": 1,
                            }
                        )

                    # Add Tag nodes
                    if tag:
                        if tag.get("id") not in nodes_set:
                            nodes.append(
                                {
                                    "id": tag["id"],
                                    "label": tag["name"],
                                    "node_type": "topic",
                                    "level": "child",
                                    "resource_count": 1,
                                }
                            )
                            nodes_set.add(tag["id"])

                        # Add BELONGS_TO edge (tag -> category) — outside
                        # the nodes_set guard so multi-category tags get all edges
                        if category:
                            edge_key = (tag["id"], category["id"])
                            if edge_key not in edges_set:
                                edges.append(
                                    {
                                        "source": tag["id"],
                                        "target": category["id"],
                                        "weight": 1,
                                    }
                                )
                                edges_set.add(edge_key)
                else:
                    # Expanded view
                    root_node = record["root_node"]
                    t = record.get("t")
                    c = record.get("c")
                    related_tag = record.get("related_tag")

                    # Add the center node
                    if root_node and root_node.get("id") not in nodes_set:
                        nodes.append(
                            {
                                "id": root_node["id"],
                                "label": root_node.get("name", root_node["id"]),
                                "node_type": root_node.get("node_type", "unknown"),
                                "level": "current",
                                "resource_count": 1,
                            }
                        )
                        nodes_set.add(root_node["id"])

                    # Add child tags (if expanding a category)
                    if t and t.get("id") not in nodes_set:
                        nodes.append(
                            {
                                "id": t["id"],
                                "label": t["name"],
                                "node_type": "topic",
                                "level": "child",
                                "resource_count": 1,  # Already filtered for >= 1
                            }
                        )
                        nodes_set.add(t["id"])

                        # Add BELONGS_TO edge
                        edge_key = (t["id"], root_node["id"])
                        if edge_key not in edges_set:
                            edges.append(
                                {
                                    "source": t["id"],
                                    "target": root_node["id"],
                                    "weight": record.get("bt", {}).get("weight", 1),
                                }
                            )
                            edges_set.add(edge_key)

                    # Add parent categories (if expanding a tag)
                    if c and c.get("id") not in nodes_set:
                        nodes.append(
                            {
                                "id": c["id"],
                                "label": c["name"],
                                "node_type": "category",
                                "level": "parent",
                                "resource_count": 0,  # Categories always shown
                            }
                        )
                        nodes_set.add(c["id"])

                        # Add BELONGS_TO edge
                        edge_key = (root_node["id"], c["id"])
                        if edge_key not in edges_set:
                            edges.append(
                                {
                                    "source": root_node["id"],
                                    "target": c["id"],
                                    "weight": record.get("bt2", {}).get("weight", 1),
                                }
                            )
                            edges_set.add(edge_key)

                    # Add related tags (if expanding a tag)
                    if related_tag and related_tag.get("id") not in nodes_set:
                        nodes.append(
                            {
                                "id": related_tag["id"],
                                "label": related_tag["name"],
                                "node_type": "topic",
                                "level": "child",
                                "resource_count": 1,
                            }
                        )
                        nodes_set.add(related_tag["id"])

                        # Add RELATED_TO edge
                        edge_key = tuple(sorted([root_node["id"], related_tag["id"]]))
                        if edge_key not in edges_set:
                            edges.append(
                                {
                                    "source": root_node["id"],
                                    "target": related_tag["id"],
                                    "weight": record.get("rt", {}).get("weight", 1),
                                }
                            )
                            edges_set.add(edge_key)

            return {"nodes": nodes, "edges": edges}

    async def get_neighbors(
        self, owner_id: int, node_id: str, direction: str = "out"
    ) -> dict:
        """
        Get direct neighbors of a specific node in the hierarchical graph.

        For Category nodes: returns child Tag nodes (BELONGS_TO)
        For Tag nodes: returns related Tag nodes (RELATED_TO) and parent
        Categories (BELONGS_TO)

        Args:
            owner_id: User ID to scope the query to
            node_id: ID of the node to expand
            direction: Direction of relationships ("out", "in", "both")

        Returns:
            Dictionary with nodes and edges lists for the expanded node's neighbors
        """
        # Validate direction
        if direction not in ("out", "in", "both"):
            direction = "out"  # safe default

        neo4j_driver = await get_neo4j_driver()

        async with neo4j_driver.get_session() as session:
            # Query to get neighbors based on node type
            query = """
                MATCH (root_node {id: $node_id, owner_id: $owner_id})

                // If it's a Category, get child Tags
                OPTIONAL MATCH (child_tag:Tag)-[:BELONGS_TO]->(root_node:Category)
                WHERE EXISTS((child_tag)-[:RELATED_TO]-())  // Only tags with resources

                // If it's a Tag, get related Tags and parent Categories
                OPTIONAL MATCH (root_node:Tag)-[:RELATED_TO]-(related_tag:Tag)
                OPTIONAL MATCH (root_node:Tag)-[:BELONGS_TO]->(parent_cat:Category)

                RETURN root_node, child_tag, related_tag, parent_cat
            """

            result = await session.run(
                query,
                node_id=node_id,
                owner_id=str(owner_id),
            )

            nodes = []
            edges = []
            nodes_set = set()

            async for record in result:
                child_tag = record.get("child_tag")
                related_tag = record.get("related_tag")
                parent_cat = record.get("parent_cat")

                # Add child tags (if expanding a category)
                if child_tag and child_tag.get("id") not in nodes_set:
                    nodes.append(
                        {
                            "id": child_tag["id"],
                            "label": child_tag["name"],
                            "node_type": "topic",
                            "level": "child",
                            "resource_count": 1,
                        }
                    )
                    nodes_set.add(child_tag["id"])

                    # Add BELONGS_TO edge from child tag to category
                    edges.append(
                        {
                            "source": child_tag["id"],
                            "target": node_id,
                            "weight": 1,
                        }
                    )

                # Add related tags (if expanding a tag)
                if (
                    related_tag
                    and related_tag.get("id") not in nodes_set
                    and related_tag.get("id") != node_id
                ):
                    nodes.append(
                        {
                            "id": related_tag["id"],
                            "label": related_tag["name"],
                            "node_type": "topic",
                            "level": "child",
                            "resource_count": 1,
                        }
                    )
                    nodes_set.add(related_tag["id"])

                    # Add RELATED_TO edge
                    edges.append(
                        {
                            "source": node_id,
                            "target": related_tag["id"],
                            "weight": 1,
                        }
                    )

                # Add parent categories (if expanding a tag)
                if parent_cat and parent_cat.get("id") not in nodes_set:
                    nodes.append(
                        {
                            "id": parent_cat["id"],
                            "label": parent_cat["name"],
                            "node_type": "category",
                            "level": "parent",
                            "resource_count": 0,
                        }
                    )
                    nodes_set.add(parent_cat["id"])

                    # Add BELONGS_TO edge from tag to parent category
                    edges.append(
                        {
                            "source": node_id,
                            "target": parent_cat["id"],
                            "weight": 1,
                        }
                    )

            return {"nodes": nodes, "edges": edges}


# Global instance
graph_service = GraphService()


async def get_graph_service() -> GraphService:
    """Dependency function to get the graph service."""
    return graph_service
