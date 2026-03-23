# Design: Category Taxonomy and Graph Hierarchy

**Extends:** `docs/technical-design.md` §2.1 (Data Models — PostgreSQL), §2.2 (Data Models — Neo4j), §3.1 (Resource API schemas), §3.2 (Graph API schemas), §4 (Endpoints), §5.4 (Graph exploration flow), §6.2 (Graph update sequence), §8.2 (Backend checklist), §8.3 (Frontend checklist)

This document specifies the two-level category taxonomy, the updated graph hierarchy, the LLM integration changes, and the validation rules for tag editing (FB-003, FB-004).

---

## 1. Overview

The knowledge graph is restructured from a flat tag network into a rooted hierarchy:

```
My Learning Space (root, per user)
  ├── Science & Technology      (category — always shown)
  │     ├── Machine Learning    (topic — shown only if has resources)
  │     └── Python              (topic — shown only if has resources)
  ├── Business & Economics      (category — always shown)
  │     └── Startup Strategy    (topic — shown only if has resources)
  └── ...
```

Every resource must be assigned at least one top-level category. Topic nodes (LLM-generated tags) are only visible when they have at least one associated resource.

---

## 2. Category Model

### 2.1 System-Seeded Categories

The following 10 categories are seeded at startup and cannot be deleted:

| Name |
|------|
| Science & Technology |
| Business & Economics |
| Politics & Government |
| Society & Culture |
| Education & Knowledge |
| Health & Medicine |
| Environment & Sustainability |
| Arts & Entertainment |
| Sports & Recreation |
| Lifestyle & Personal Life |

These are global (not per-user). Any user can associate their resources with any system category.

### 2.2 User-Created Categories

Users may create custom top-level categories (e.g. "My Research", "Work Projects"). These are scoped to the user (`user_id` is set).

Rules:
- Name must be unique per user (case-insensitive check against both system and user-created categories)
- No limit on number of user-created categories
- User-created categories can be deleted only if no resources are currently associated with them (enforce at API level)
- System categories cannot be deleted by any user

### 2.3 PostgreSQL Table: `categories`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, default gen_random_uuid() | Category ID |
| `user_id` | UUID | FK(users.id), nullable | NULL = system-seeded, non-null = user-created |
| `name` | VARCHAR(255) | NOT NULL | Display name |
| `is_system` | BOOLEAN | NOT NULL, default false | True for seeded categories |
| `created_at` | TIMESTAMPTZ | NOT NULL, default now() | |

**Unique constraint:** `(user_id, LOWER(name))` — case-insensitive uniqueness per user. System categories (user_id IS NULL) use a partial unique index on `LOWER(name) WHERE user_id IS NULL`.

**Indexes:** `user_id`, `is_system`.

---

## 3. Resource Model Addition

One new field on the `resources` table (see `docs/technical-design.md` §2.1.3):

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `top_level_categories` | JSONB | NOT NULL, default '[]' | Array of category names assigned to this resource. Min 1 entry after processing. |

The `top_level_categories` array stores category **names** (not IDs) for simplicity and query performance. Names are treated as stable identifiers; renaming a category requires a migration.

**Index:** GIN on `top_level_categories` for fast filtering.

---

## 4. Neo4j Schema Updates

### 4.1 New Node Types

**`Root` node (1 per user)**
- Label: `Root`
- Properties: `owner_id` (UUID string), `name` ("My Learning Space")
- Created automatically when a user's first resource is processed

**`Category` nodes**
- Label: `Category`
- Properties: `id` (category name), `owner_id` (UUID string), `is_system` (boolean)
- Created/merged when the graph is first built for a user
- System categories are merged for each user on their first graph interaction

### 4.2 Existing Node Type (unchanged)

**`Tag` nodes** (topic-level, LLM-generated)
- Label: `Tag` (unchanged)
- Properties: `id` (tag name), `owner_id`

### 4.3 New Relationship Types

**`Category -[:CHILD_OF]-> Root`**
- Created for each category node pointing to the user's root node
- No additional properties

**`Tag -[:BELONGS_TO]-> Category`**
- Links a topic tag to one or more categories
- Created/updated when a resource is processed or tags are edited
- A tag can belong to multiple categories (e.g. "AI Ethics" → both "Science & Technology" and "Society & Culture")
- Properties: `weight` (number of resources that link this tag to this category)

### 4.4 Existing Relationship Type (unchanged)

**`Tag -[:RELATED_TO]-> Tag`** — co-occurrence edges between topic tags (unchanged)

### 4.5 Visibility Rules

- `Root` node: always present (not filtered by resource count)
- `Category` nodes: always shown when graph is expanded (not filtered by resource count)
- `Tag` nodes: only shown when `resource_count >= 1` — enforced by graph query

### 4.6 Updated ER Diagram (Neo4j)

```
Root
  └─ CHILD_OF ← Category (system or user)
                   └─ BELONGS_TO ← Tag (LLM-generated)
                                     └─ RELATED_TO ── Tag
```

---

## 5. LLM Integration

### 5.1 Updated Output Schema

The LLM must return `top_level_categories` in addition to `title`, `summary`, and `tags`:

```json
{
  "title": "How Transformers Changed NLP",
  "summary": "Overview of the transformer architecture and its impact on NLP.",
  "top_level_categories": ["Science & Technology", "Education & Knowledge"],
  "tags": ["Transformers", "NLP", "Machine Learning", "Deep Learning"]
}
```

`top_level_categories` must contain one or more values from the current known category list. The LLM is constrained by a schema validator — if the returned categories don't match any known category, the worker falls back to "Science & Technology" (or the most semantically appropriate system category) and logs a warning.

### 5.2 Prompt Design

The LLM prompt for tag/category generation must include:

1. **Available categories list** — all system categories + user's custom categories. Passed as a JSON array in the prompt:
   ```
   Available top-level categories: ["Science & Technology", "Business & Economics", ...]
   ```

2. **Existing tags for this user** — passed as a JSON array so the LLM reuses existing tags rather than creating near-duplicates:
   ```
   Existing tags for this user (reuse these when applicable): ["Machine Learning", "Python", "Startup Strategy", ...]
   ```

3. **Instructions** — the LLM must:
   - Select 1–3 `top_level_categories` from the provided list (required)
   - Generate 3–10 topic `tags` (reuse existing tags when semantically equivalent)
   - Return valid JSON matching the output schema

### 5.3 Tag-Category Association

After LLM returns tags and categories, the worker builds the `Tag → Category` associations:

- For each tag in the LLM output, associate it with each category in `top_level_categories`.
- This creates/updates `Tag -[:BELONGS_TO]-> Category` edges in Neo4j with `weight += 1`.
- If a tag already exists in Neo4j for this user (from a prior resource), its category associations are expanded (not replaced).

---

## 6. API Changes

### 6.1 Resource Schema Updates

**Create resource (`POST /resources`) — no change to request.**

**Resource response** — add `top_level_categories` field:

```json
{
  "id": "...",
  "content_type": "url",
  "original_content": "https://example.com/article",
  "title": "...",
  "summary": "...",
  "tags": ["Machine Learning", "Python"],
  "top_level_categories": ["Science & Technology"],
  "status": "READY",
  "status_message": null,
  "fetch_tier": "http",
  "fetch_error_type": null,
  "created_at": "...",
  "updated_at": "..."
}
```

**Update resource (`PATCH /resources/{id}`) — add editable fields:**

```json
{
  "title": "Optional user override",
  "tags": ["Machine Learning", "Python", "Neural Networks"],
  "top_level_categories": ["Science & Technology", "Education & Knowledge"]
}
```

Validation: if `tags` or `top_level_categories` are provided, `top_level_categories` must contain at least one valid category name. Return `400 CATEGORY_REQUIRED` if violated.

### 6.2 Graph Node Schema Update

Add `node_type` field to graph node response (see `docs/technical-design.md` §3.2.1):

```json
{
  "id": "Science & Technology",
  "label": "Science & Technology",
  "node_type": "category",
  "level": "current",
  "resource_count": 12
}
```

| `node_type` | Value | Description |
|-------------|-------|-------------|
| `root` | "My Learning Space" node | Always present |
| `category` | System or user-created top-level category | Always shown |
| `topic` | LLM-generated tag node | Shown only if resource_count >= 1 |

### 6.3 New Category Endpoints

Base path: `/api/v1`. All category endpoints require authentication.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/categories` | List all categories visible to the current user (system + user-created). Returns array of category objects. |
| `POST` | `/categories` | Create a custom category. Body: `{"name": "My Research"}`. Returns 201 with new category. Returns 409 if name conflicts with existing category. |
| `DELETE` | `/categories/{id}` | Delete a user-created category. Returns 400 `CATEGORY_IN_USE` if any resources reference it. Returns 403 if trying to delete a system category. |

**Category object (response):**
```json
{
  "id": "550e8400-...",
  "name": "Science & Technology",
  "is_system": true,
  "user_id": null,
  "created_at": "2026-03-22T00:00:00Z"
}
```

---

## 7. Validation Rules

### 7.1 Resource Creation

When a resource is submitted and processed, the worker validates the LLM output:
- `top_level_categories` must be non-empty
- Each value must match a known category (system or user-created) — case-insensitive match
- If validation fails: fall back to most semantically appropriate system category; log warning

### 7.2 Resource Tag Update (PATCH /resources/{id})

When a user manually edits tags or categories:
- If `top_level_categories` is provided and is empty: return `400 CATEGORY_REQUIRED`
- If `top_level_categories` is provided and contains unknown category names: return `400 INVALID_CATEGORY`
- After a successful update, enqueue a graph resync job for this resource (re-merge Neo4j nodes/edges)

### 7.3 Category Deletion

When deleting a user-created category:
- Query `resources` where `top_level_categories @> '["category_name"]'` for the current user
- If any results exist: return `400 CATEGORY_IN_USE` with count of affected resources
- If no resources: delete the category from PostgreSQL and remove `Category` node from Neo4j

---

## 8. Graph Exploration Updates

The graph exploration flow (see `docs/technical-design.md` §5.4) is updated:

1. **Default view**: `GET /graph` with no `root` param returns the "My Learning Space" root node and all category-level children (always shown, regardless of resource count).
2. **Expanding a category**: `POST /graph/expand` with a category `node_id` returns topic-level tag nodes that `BELONGS_TO` that category and have `resource_count >= 1`.
3. **Expanding a topic**: Same as before — returns related topic tags via `RELATED_TO` edges.
4. **Resource list by node**: `GET /graph/nodes/{node_id}/resources` works for both category nodes (resources with that category in `top_level_categories`) and topic nodes (resources with that tag in `tags`).

---

## 9. Seeding and Migration

### 9.1 Category Seeding

System categories are seeded via a one-time migration script (Alembic migration). The seed is idempotent — it uses `INSERT ... ON CONFLICT DO NOTHING`.

System categories in Neo4j are created lazily: the first time a user processes a resource, the worker merges `Category` nodes for each of the 10 system categories into Neo4j with that user's `owner_id`, and links them to the user's `Root` node.

### 9.2 Existing Resources

Resources created before this feature was introduced will have `top_level_categories = []`. A backfill job should be run to re-process these resources through the updated LLM prompt to assign categories. Until backfilled, these resources will not appear under any category node in the graph.

The backfill is a one-time operational task (tracked separately as an OPS task).
