"""
Recursive-CTE queries for traversing the family graph, plus the logic that
assembles results into the nested TreeNode shape react-d3-tree expects.

Because a family "tree" can contain cycles at the graph level (e.g. cousin
marriages) even though ancestor/descendant lines are acyclic, every recursive
query tracks a `visited` path and stops recursing if a person is revisited.
"""
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.person import Person
from app.schemas.person import PersonRead
from app.schemas.tree import AncestryPathNode, TreeNode

MAX_DEPTH = 25  # safety valve against pathological/cyclic data


async def get_ancestors(db: AsyncSession, person_id: uuid.UUID, tree_id: uuid.UUID) -> list[AncestryPathNode]:
    """Walk PARENT_CHILD edges upward (child -> parent) using a recursive CTE."""
    query = text(
        """
        WITH RECURSIVE ancestors AS (
            SELECT
                p.id AS person_id,
                0 AS generation,
                ARRAY[p.id] AS visited,
                NULL::text AS relation_subtype
            FROM persons p
            WHERE p.id = :person_id

            UNION ALL

            SELECT
                r.person_a_id AS person_id,          -- parent
                a.generation + 1,
                a.visited || r.person_a_id,
                r.parent_child_subtype::text
            FROM ancestors a
            JOIN relationships r
                ON r.person_b_id = a.person_id       -- r.person_b_id = child
                AND r.relationship_type = 'parent_child'
                AND r.tree_id = :tree_id
            WHERE NOT (r.person_a_id = ANY(a.visited))
              AND a.generation < :max_depth
        )
        SELECT DISTINCT ON (person_id) person_id, generation, relation_subtype
        FROM ancestors
        WHERE generation > 0
        ORDER BY person_id, generation ASC
        """
    )
    result = await db.execute(
        query, {"person_id": str(person_id), "tree_id": str(tree_id), "max_depth": MAX_DEPTH}
    )
    rows = result.mappings().all()

    ids = [row["person_id"] for row in rows]
    if not ids:
        return []

    people = await db.execute(text("SELECT * FROM persons WHERE id = ANY(:ids)"), {"ids": ids})
    people_by_id = {row["id"]: row for row in people.mappings().all()}

    return [
        AncestryPathNode(
            person=PersonRead.model_validate(dict(people_by_id[row["person_id"]])),
            generation=row["generation"],
            relation_subtype=row["relation_subtype"],
        )
        for row in rows
        if row["person_id"] in people_by_id
    ]


async def get_descendants(db: AsyncSession, person_id: uuid.UUID, tree_id: uuid.UUID) -> list[AncestryPathNode]:
    """Walk PARENT_CHILD edges downward (parent -> child) using a recursive CTE."""
    query = text(
        """
        WITH RECURSIVE descendants AS (
            SELECT
                p.id AS person_id,
                0 AS generation,
                ARRAY[p.id] AS visited,
                NULL::text AS relation_subtype
            FROM persons p
            WHERE p.id = :person_id

            UNION ALL

            SELECT
                r.person_b_id AS person_id,          -- child
                d.generation + 1,
                d.visited || r.person_b_id,
                r.parent_child_subtype::text
            FROM descendants d
            JOIN relationships r
                ON r.person_a_id = d.person_id       -- r.person_a_id = parent
                AND r.relationship_type = 'parent_child'
                AND r.tree_id = :tree_id
            WHERE NOT (r.person_b_id = ANY(d.visited))
              AND d.generation < :max_depth
        )
        SELECT DISTINCT ON (person_id) person_id, generation, relation_subtype
        FROM descendants
        WHERE generation > 0
        ORDER BY person_id, generation ASC
        """
    )
    result = await db.execute(
        query, {"person_id": str(person_id), "tree_id": str(tree_id), "max_depth": MAX_DEPTH}
    )
    rows = result.mappings().all()

    ids = [row["person_id"] for row in rows]
    if not ids:
        return []

    people = await db.execute(text("SELECT * FROM persons WHERE id = ANY(:ids)"), {"ids": ids})
    people_by_id = {row["id"]: row for row in people.mappings().all()}

    return [
        AncestryPathNode(
            person=PersonRead.model_validate(dict(people_by_id[row["person_id"]])),
            generation=row["generation"],
            relation_subtype=row["relation_subtype"],
        )
        for row in rows
        if row["person_id"] in people_by_id
    ]


async def build_nested_tree(db: AsyncSession, root_person_id: uuid.UUID, tree_id: uuid.UUID) -> TreeNode | None:
    """
    Builds a nested TreeNode (root + descendants + attached spouses) suitable
    for react-d3-tree. For very large trees prefer get_descendants() (flat list)
    and let the frontend lazily expand nodes instead of nesting everything.
    """
    root_row = await db.execute(text("SELECT * FROM persons WHERE id = :id"), {"id": str(root_person_id)})
    root = root_row.mappings().first()
    if not root:
        return None

    descendants = await get_descendants(db, root_person_id, tree_id)

    # Fetch all parent_child edges within this tree once, then build children map in memory.
    edges_result = await db.execute(
        text(
            """
            SELECT person_a_id AS parent_id, person_b_id AS child_id
            FROM relationships
            WHERE relationship_type = 'parent_child' AND tree_id = :tree_id
            """
        ),
        {"tree_id": str(tree_id)},
    )
    children_map: dict[str, list[str]] = {}
    for row in edges_result.mappings().all():
        children_map.setdefault(str(row["parent_id"]), []).append(str(row["child_id"]))

    spouse_result = await db.execute(
        text(
            """
            SELECT person_a_id, person_b_id
            FROM relationships
            WHERE relationship_type = 'spouse' AND tree_id = :tree_id
            """
        ),
        {"tree_id": str(tree_id)},
    )
    spouse_map: dict[str, list[str]] = {}
    for row in spouse_result.mappings().all():
        a, b = str(row["person_a_id"]), str(row["person_b_id"])
        spouse_map.setdefault(a, []).append(b)
        spouse_map.setdefault(b, []).append(a)

    people_by_id = {str(node.person.id): node.person for node in descendants}
    people_by_id[str(root_person_id)] = PersonRead.model_validate(dict(root))

    def build(node_id: str, visited: set[str]) -> TreeNode:
        person = people_by_id[node_id]
        spouses = [people_by_id[sid] for sid in spouse_map.get(node_id, []) if sid in people_by_id]

        child_nodes = []
        for child_id in children_map.get(node_id, []):
            if child_id in visited or child_id not in people_by_id:
                continue  # cycle guard
            child_nodes.append(build(child_id, visited | {child_id}))

        return TreeNode(person=person, children=child_nodes, spouses=spouses)

    return build(str(root_person_id), {str(root_person_id)})
