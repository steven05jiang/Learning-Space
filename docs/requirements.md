# Product Requirements for Learning Space

## Product Requirements

## 1. Overview

This system allows users to collect, organize, and explore learning resources through an automatically generated **knowledge graph**.

Users can upload learning materials such as links or text content. An LLM will summarize the content and generate tags to categorize it. These tags will be used to automatically construct and update a **personal knowledge graph**.

Users can browse their knowledge graph visually, explore related topics, and interact with an AI chatbot to discover and discuss their resources.

---

# Functional Requirements

## 1. Resource Management

Users can manage their learning resources within the system.

**Adding a resource requires the user to be logged in.** If the user is not logged in when they try to add a resource (e.g. submit a link or paste text), the app must prompt them to log in and only allow submission after they have logged in.

Supported actions include:

- Add a resource by submitting:
  - a URL (article, blog post, documentation, etc.)
  - pasted text content

- Edit an existing resource (title, tags, top-level categories). When editing tags or categories, at least one top-level category must remain associated — the system rejects edits that would leave a resource with no top-level category.
- Delete a resource
- View all previously uploaded resources

Each piece of user-submitted content is referred to as a **Resource**.

Each Resource should include the following fields:

- Resource ID
- Original content (URL or pasted text)
- Title
- LLM-generated summary
- LLM-generated tags
- Creation timestamp
- Last updated timestamp
- Owner (user)
- Top-level categories (one or more; assigned by LLM; see §2.1 Category System)
- Optional: preferred provider (for URL resources; hints which linked account to use when fetching, e.g. Twitter)

---

## 2. Automatic Resource Processing

After a Resource is submitted:

1. **Fetching URL content**: For URL resources, the system fetches content using a tiered strategy. Full specification: `docs/design-resource-fetching.md`.

   - **Tier 1 — API-integrated domains**: A system-maintained blocklist of domains that require official API access (e.g. `twitter.com`, `x.com`). For these URLs, the system uses the user's linked account for that provider. If the user has no linked account, the resource fails with a clear user-facing message and an actionable prompt (e.g. "Link your Twitter account in Settings"). If no API integration exists yet for that domain, the resource fails with "not yet supported".

   - **Tier 2 — General HTTP with Playwright fallback**: For all other URLs, the system first attempts a direct HTTP fetch. If that is blocked (e.g. HTTP 403, bot detection), it falls back to a Playwright headless browser fetch.

   - **Error classification**: If all tiers fail, the resource enters `FAILED` state with a classified error type (`API_REQUIRED`, `NOT_SUPPORTED`, `BOT_BLOCKED`, `FETCH_ERROR`) and a user-facing message explaining the issue.

2. The system sends the (fetched or pasted) content to an LLM.
3. The LLM performs:
   - Content summarization
   - Top-level category assignment (selects from the known category list; at least one required)
   - Tag generation (topics, concepts, technologies; reuses existing tags where applicable)

4. The system stores the generated metadata.

Example output:

Resource:

```
URL: https://example.com/ai-coding-agents
```

Generated metadata:

```
Summary: Overview of AI coding agents and how they assist developers.
Tags:
- AI
- Coding Agents
- LLM Tools
- Developer Productivity
```

---

## 2.1 Category System

The knowledge graph is organized under a two-level taxonomy of **top-level categories** and **topic nodes**. Full specification: `docs/design-category-taxonomy.md`.

**System-seeded categories** (predefined, cannot be deleted):

Science & Technology · Business & Economics · Politics & Government · Society & Culture · Education & Knowledge · Health & Medicine · Environment & Sustainability · Arts & Entertainment · Sports & Recreation · Lifestyle & Personal Life

**User-created categories**: Users may add custom top-level categories from the settings or graph view.

**Rules:**
- Every resource must be associated with at least one top-level category (assigned by LLM on processing).
- When a user manually edits tags on a resource, at least one top-level category must remain.
- LLM tag generation must include the current category list so it can select from known values.
- LLM tag generation must include the user's existing tags so it can reuse them instead of creating near-duplicates.

---

## 3. Knowledge Graph Generation

The system maintains a **knowledge graph for each user** with a three-level hierarchy:

- **Root node**: "My Learning Space" — single root per user, always present
- **Category nodes** (level 1): top-level categories — always shown in the graph
- **Topic nodes** (level 2+): LLM-generated tags — only shown when at least one resource is associated

**Edges:**
- Category nodes connect upward to the root node
- Topic nodes connect upward to one or more category nodes
- Topic nodes connect laterally to related topic nodes (co-occurrence based on shared resources)

When a resource is created, updated, or deleted:
- The knowledge graph is updated accordingly (asynchronously)
- Topic nodes with no associated resources are hidden from the graph (not deleted)

Graph updates should occur asynchronously.

---

## 4. Knowledge Graph Exploration

Users can visually explore their personal knowledge graph.

Features:

- The graph supports **multi-level navigation**
- Only the following nodes are shown at a time:
  - Parent level
  - Current level
  - Immediate child level

User interactions:

1. Clicking a node expands the next level of related nodes.
2. Users can navigate deeper into the graph hierarchy.
3. The UI should maintain context so users know their current position.

---

## 5. Resource Discovery from Graph Nodes

When a user clicks on a node in the knowledge graph:

The system should display the associated resources.

Displayed information:

- Resource title
- LLM summary
- Link to full content

Example:

Node: **AI Coding**

Displayed resources:

```
1. "How AI Coding Agents Work"
   Summary: Explanation of how LLM-powered agents generate code.

2. "Best Tools for AI-Assisted Development"
   Summary: Overview of tools like Copilot and code assistants.
```

---

## 6. AI Chatbot for Resource Discovery

The system provides a chatbot that allows users to query and discuss their resources.

Example interactions:

User questions:

- "What resources do I have about AI coding?"
- "Summarize what I learned about Kubernetes."
- "Show me related topics to LangGraph."

The AI Agent should be able to:

- Search resources
- Retrieve summaries
- Navigate the knowledge graph
- Suggest related topics

The agent will use internal system APIs as tools. The agent's resource search capability uses the same underlying retrieval service as the user-facing search (§7) — no duplicate retrieval logic.

---

## 7. Resource Search

Users can search their resources by keyword directly from the search page.

- Search accepts one or more keywords and matches across resource title, summary, and tags.
- Results are ranked by relevance (most relevant first).
- An optional tag filter narrows results to resources associated with that tag.
- Only successfully processed resources (`status = READY`) appear in search results.
- Both the user-facing search and the AI agent's `search_resources` tool use the same underlying search service, ensuring consistent retrieval behavior.

Search is implemented in two phases. Full specification: `docs/design-search.md`.

- **Phase 1** — PostgreSQL full-text search (tsvector + GIN index): multi-keyword, stemming, relevance ranking. Zero new infrastructure.
- **Phase 2** — Hybrid retrieval (full-text + pgvector embeddings + RRF merge): adds semantic matching so natural language queries like "what do I know about distributed systems?" surface conceptually relevant resources even when exact keywords don't match.

---

# Technical Choices

The system will use the following technologies:

### Frontend

- **Next.js**
- Graph visualization library (e.g., Cytoscape.js, React Flow, or D3)

### Backend

- **Python backend service**

Recommended frameworks:

- FastAPI (preferred)
- or Flask

### AI / Agent Framework

- **LangGraph** for agent workflow
- **LangSmith** for tracing, monitoring, and debugging

### Databases

**Graph Database**

- Neo4j
- Stores knowledge graph nodes and relationships

**Relational Database**

- PostgreSQL
- Stores:
  - Users
  - Resources
  - Metadata
  - Processing status

### Authentication

- **OAuth login** with support for multiple providers:
  - X / Twitter (initial)
  - Google
  - GitHub
- **Multiple social accounts per user**: A single user can link more than one social account (e.g. Twitter and Google). Logging in with any linked account authenticates as the same user. Users can:
  - Link additional accounts from settings (e.g. "Add Google account").
  - Unlink an account from settings, but must keep at least one account linked (the app must not allow unlinking the last account).

---

# Asynchronous Processing

Resource processing may involve expensive operations:

- fetching URL content (including, when needed, using the user's linked account to access login-required content)
- LLM summarization
- tag generation
- graph updates

Therefore:

- Resource creation, update, and deletion should be **handled asynchronously**.

Recommended architecture:

1. User submits resource
2. API stores resource with status `PROCESSING`
3. Background worker processes resource
4. Status updated to `READY`

The UI should clearly reflect processing states.

Example:

```
Processing resource...
Generating summary...
Updating knowledge graph...
```

---

# Technical Components

The codebase should be divided into the following major components.

---

## 1. UI Component

Responsibilities:

- Resource submission
- Resource browsing
- Knowledge graph visualization
- Chatbot interface

Technology:

- Next.js
- Graph visualization library

---

## 2. API Layer

Responsibilities:

- Handle all client requests
- Route requests to appropriate services
- Authentication and authorization
- Rate limiting

Possible implementation:

- FastAPI gateway service

---

## 3. Resource Update Component

Handles all operations related to resource lifecycle:

- Resource creation
- Resource updates
- Resource deletion
- LLM summarization
- Tag extraction
- Graph updates

This component will operate asynchronously.

---

## 4. Resource Viewer Component

Handles all read operations:

- Fetch resources
- Search by tag
- Retrieve resources linked to graph nodes
- Provide graph traversal APIs

---

## 5. AI Agent Component

Handles chatbot functionality.

Responsibilities:

- Interpret user questions
- Retrieve relevant resources
- Query the knowledge graph
- Generate conversational answers

Tools available to the agent:

- Resource search
- Graph traversal
- Resource summarization
- Resource update operations

Framework:

- LangGraph

Monitoring:

- LangSmith

---

## 6. Data Layer

Defines shared data models and data access logic.

Responsibilities:

- Define consistent schemas for:
  - Resources
  - Graph nodes
  - Graph edges

- Provide data access interfaces
- Maintain consistency between:
  - PostgreSQL
  - Neo4j

# Deployment Requirements

1. Create docker images for the deployment
2. Use helm chart to deploy the app to kubernetes
3. Use ArgoCD to automte the deployment
