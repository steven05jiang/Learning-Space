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

* Add a resource by submitting:

  * a URL (article, blog post, documentation, etc.)
  * pasted text content
* Edit an existing resource
* Delete a resource
* View all previously uploaded resources

Each piece of user-submitted content is referred to as a **Resource**.

Each Resource should include the following fields:

* Resource ID
* Original content (URL or pasted text)
* Title
* LLM-generated summary
* LLM-generated tags
* Creation timestamp
* Last updated timestamp
* Owner (user)
* Optional: preferred provider (for URL resources that require login; hints which linked account to use when fetching, e.g. Twitter)

---

## 2. Automatic Resource Processing

After a Resource is submitted:

1. **Fetching URL content**: For URL resources, the system fetches the content from the target site. If the content is **only accessible with login** (e.g. a paywalled article or a post on a social platform that requires authentication):
   * The system uses the **user's linked account** for that provider (e.g. Twitter) to log in and access the content, when the user has linked such an account.
   * If the user has **no linked account** for that provider, the system cannot fetch the content. The app must inform the user clearly (e.g. "This link requires login. Link your Twitter account in Settings to save content from this site.") and allow them to link the account in settings, then retry or re-add the resource.
2. The system sends the (fetched or pasted) content to an LLM.
3. The LLM performs:

   * Content summarization
   * Tag generation (topics, concepts, technologies, etc.)
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

## 3. Knowledge Graph Generation

The system maintains a **knowledge graph for each user**.

The graph structure:

* **Nodes** represent tags or topics
* **Edges** represent relationships between tags based on shared resources

When a resource is created, updated, or deleted:

* The knowledge graph should be updated accordingly.

For example:

If a resource has tags:

```
AI
Coding Agents
Developer Tools
```

Edges may be created:

```
AI -> Coding Agents
Coding Agents -> Developer Tools
```

Graph updates should occur asynchronously.

---

## 4. Knowledge Graph Exploration

Users can visually explore their personal knowledge graph.

Features:

* The graph supports **multi-level navigation**
* Only the following nodes are shown at a time:

  * Parent level
  * Current level
  * Immediate child level

User interactions:

1. Clicking a node expands the next level of related nodes.
2. Users can navigate deeper into the graph hierarchy.
3. The UI should maintain context so users know their current position.

---

## 5. Resource Discovery from Graph Nodes

When a user clicks on a node in the knowledge graph:

The system should display the associated resources.

Displayed information:

* Resource title
* LLM summary
* Link to full content

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

* "What resources do I have about AI coding?"
* "Summarize what I learned about Kubernetes."
* "Show me related topics to LangGraph."

The AI Agent should be able to:

* Search resources
* Retrieve summaries
* Navigate the knowledge graph
* Suggest related topics

The agent will use internal system APIs as tools.

---

# Technical Choices

The system will use the following technologies:

### Frontend

* **Next.js**
* Graph visualization library (e.g., Cytoscape.js, React Flow, or D3)

### Backend

* **Python backend service**

Recommended frameworks:

* FastAPI (preferred)
* or Flask

### AI / Agent Framework

* **LangGraph** for agent workflow
* **LangSmith** for tracing, monitoring, and debugging

### Databases

**Graph Database**

* Neo4j
* Stores knowledge graph nodes and relationships

**Relational Database**

* PostgreSQL
* Stores:

  * Users
  * Resources
  * Metadata
  * Processing status

### Authentication

* **OAuth login** with support for multiple providers:
  * X / Twitter (initial)
  * Google
  * GitHub
* **Multiple social accounts per user**: A single user can link more than one social account (e.g. Twitter and Google). Logging in with any linked account authenticates as the same user. Users can:
  * Link additional accounts from settings (e.g. "Add Google account").
  * Unlink an account from settings, but must keep at least one account linked (the app must not allow unlinking the last account).

---

# Asynchronous Processing

Resource processing may involve expensive operations:

* fetching URL content (including, when needed, using the user's linked account to access login-required content)
* LLM summarization
* tag generation
* graph updates

Therefore:

* Resource creation, update, and deletion should be **handled asynchronously**.

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

* Resource submission
* Resource browsing
* Knowledge graph visualization
* Chatbot interface

Technology:

* Next.js
* Graph visualization library

---

## 2. API Layer

Responsibilities:

* Handle all client requests
* Route requests to appropriate services
* Authentication and authorization
* Rate limiting

Possible implementation:

* FastAPI gateway service

---

## 3. Resource Update Component

Handles all operations related to resource lifecycle:

* Resource creation
* Resource updates
* Resource deletion
* LLM summarization
* Tag extraction
* Graph updates

This component will operate asynchronously.

---

## 4. Resource Viewer Component

Handles all read operations:

* Fetch resources
* Search by tag
* Retrieve resources linked to graph nodes
* Provide graph traversal APIs

---

## 5. AI Agent Component

Handles chatbot functionality.

Responsibilities:

* Interpret user questions
* Retrieve relevant resources
* Query the knowledge graph
* Generate conversational answers

Tools available to the agent:

* Resource search
* Graph traversal
* Resource summarization
* Resource update operations

Framework:

* LangGraph

Monitoring:

* LangSmith

---

## 6. Data Layer

Defines shared data models and data access logic.

Responsibilities:

* Define consistent schemas for:

  * Resources
  * Graph nodes
  * Graph edges
* Provide data access interfaces
* Maintain consistency between:

  * PostgreSQL
  * Neo4j

# Deployment Requirements

1. Create docker images for the deployment
2. Use helm chart to deploy the app to kubernetes
3. Use ArgoCD to automte the deployment
