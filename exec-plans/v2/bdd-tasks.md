# BDD Tasks — Learning Space

_Version: v2 | Generated: 2026-03-17_

> **v2 Notes:** BDD scenarios are unchanged from v1. Three frontend scenarios (graph visualization,
> node click expand, node click resources, chat open, chat send) now have a working UI shell
> (built via UI-001/UI-002 with mock data). They will pass end-to-end once API wiring tasks
> DEV-052 and DEV-053 are complete.

---

## Feature: Authentication — OAuth Login

### Scenario: User logs in with Twitter for the first time

**Given** a user who has never used Learning Space before
**When** they click "Log in with Twitter" and authorize the app
**Then** a new user account is created, a `user_accounts` row is created linking Twitter, and the user is redirected to the app with a valid session
**Tags:** #auth, #backend, #frontend

### Scenario: User logs in with an existing linked account

**Given** a user who previously registered via Twitter
**When** they click "Log in with Twitter" and authorize
**Then** they are authenticated as the existing user, `last_login_at` is updated, and they are redirected with a valid session
**Tags:** #auth, #backend

### Scenario: User logs in with Google (second provider, same user)

**Given** a user who has linked both Twitter and Google accounts
**When** they log in via Google
**Then** they are authenticated as the same user identity
**Tags:** #auth, #backend

### Scenario: Unauthenticated user is redirected to login

**Given** a user who is not logged in
**When** they attempt to access a protected endpoint (e.g. `POST /resources`)
**Then** the API returns 401 Unauthorized and the frontend prompts them to log in
**Tags:** #auth, #backend, #frontend

### Scenario: Session/JWT is validated on each request

**Given** a user with an expired or invalid token
**When** they call any authenticated endpoint
**Then** the API returns 401 Unauthorized
**Tags:** #auth, #backend

---

## Feature: Authentication — Account Linking

### Scenario: User links an additional social account

**Given** a logged-in user who only has a Twitter account linked
**When** they navigate to Settings, click "Add Google account", and authorize
**Then** a new `user_accounts` row is created for Google under the same `user_id`, and Settings shows both accounts
**Tags:** #auth, #backend, #frontend

### Scenario: User attempts to link an account already linked to another user

**Given** a logged-in user attempting to link a Google account
**When** the Google account's `(provider, external_id)` is already linked to a different user
**Then** the API returns a 409 error and the account is not linked
**Tags:** #auth, #backend

### Scenario: User unlinks a social account

**Given** a logged-in user with two linked accounts (Twitter and Google)
**When** they click "Disconnect" on the Google account
**Then** the Google `user_accounts` row is deleted and only Twitter remains
**Tags:** #auth, #backend, #frontend

### Scenario: User cannot unlink their last account

**Given** a logged-in user with only one linked account
**When** they attempt to unlink that account
**Then** the API returns 400 with code `CANNOT_UNLINK_LAST_ACCOUNT` and the account remains
**Tags:** #auth, #backend, #frontend

---

## Feature: Authentication — Current User

### Scenario: User retrieves their profile and linked accounts

**Given** a logged-in user with Twitter and Google linked
**When** they call `GET /auth/me`
**Then** the response contains the user's `id`, `display_name`, `email`, and an `accounts` array with both providers (no tokens exposed)
**Tags:** #auth, #backend, #api

---

## Feature: Resource Management — Create

### Scenario: Authenticated user submits a URL resource

**Given** a logged-in user
**When** they submit `POST /resources` with `content_type: "url"` and a valid URL
**Then** the API returns 202 with the resource in `PENDING` or `PROCESSING` status and a background job is enqueued
**Tags:** #resources, #backend, #api

### Scenario: Authenticated user submits a text resource

**Given** a logged-in user
**When** they submit `POST /resources` with `content_type: "text"` and pasted text
**Then** the API returns 202 with the resource in `PENDING` or `PROCESSING` status
**Tags:** #resources, #backend, #api

### Scenario: Unauthenticated user attempts to create a resource

**Given** a user who is not logged in
**When** they submit `POST /resources`
**Then** the API returns 401 and the frontend shows a login prompt
**Tags:** #resources, #auth, #backend, #frontend

### Scenario: User submits a URL with prefer_provider hint

**Given** a logged-in user submitting a Twitter URL
**When** they include `prefer_provider: "twitter"` in the request
**Then** the resource is created with `prefer_provider` stored for the worker to use during fetching
**Tags:** #resources, #backend, #api

---

## Feature: Resource Management — Read / List

### Scenario: User lists their resources

**Given** a logged-in user with 5 resources
**When** they call `GET /resources`
**Then** they receive a paginated list of their own resources (not other users')
**Tags:** #resources, #backend, #api

### Scenario: User filters resources by tag

**Given** a logged-in user with resources tagged "AI" and "Kubernetes"
**When** they call `GET /resources?tag=AI`
**Then** only resources with the "AI" tag are returned
**Tags:** #resources, #backend, #api

### Scenario: User filters resources by status

**Given** a logged-in user with resources in READY and PROCESSING states
**When** they call `GET /resources?status=READY`
**Then** only READY resources are returned
**Tags:** #resources, #backend, #api

### Scenario: User views a single resource

**Given** a logged-in user who owns a resource
**When** they call `GET /resources/{id}`
**Then** the full resource details are returned including title, summary, tags, and status
**Tags:** #resources, #backend, #api

---

## Feature: Resource Management — Update

### Scenario: User updates a resource title

**Given** a logged-in user who owns a resource
**When** they call `PATCH /resources/{id}` with a new title
**Then** the title is updated and the resource's `updated_at` changes
**Tags:** #resources, #backend, #api

### Scenario: User updates original_content triggering reprocessing

**Given** a logged-in user who owns a READY resource
**When** they call `PATCH /resources/{id}` with new `original_content`
**Then** the resource status changes to `PROCESSING` and a new background job is enqueued
**Tags:** #resources, #backend, #api

---

## Feature: Resource Management — Delete

### Scenario: User deletes a resource

**Given** a logged-in user who owns a resource
**When** they call `DELETE /resources/{id}`
**Then** the resource is removed and a graph sync job is enqueued to update Neo4j
**Tags:** #resources, #backend, #api, #graph

---

## Feature: Resource Processing — Async Worker

### Scenario: Worker processes a URL resource successfully

**Given** a resource with `content_type: "url"` and `status: PROCESSING`
**When** the worker fetches the URL content (unauthenticated) successfully
**Then** the worker calls the LLM for title/summary/tags, updates the resource to `READY`, and triggers a graph update
**Tags:** #worker, #backend, #llm

### Scenario: Worker processes a text resource successfully

**Given** a resource with `content_type: "text"` and `status: PROCESSING`
**When** the worker processes it
**Then** the LLM generates title/summary/tags from `original_content`, the resource status becomes `READY`, and the graph is updated
**Tags:** #worker, #backend, #llm

### Scenario: URL requires login and user has linked account

**Given** a URL resource from twitter.com and the owner has a linked Twitter account
**When** the unauthenticated fetch fails (401/403 or auth-required domain)
**Then** the worker uses the owner's Twitter `access_token` to fetch via provider API, then proceeds to LLM processing
**Tags:** #worker, #backend, #auth

### Scenario: URL requires login and user has no linked account

**Given** a URL resource from twitter.com and the owner has no linked Twitter account
**When** the unauthenticated fetch fails
**Then** the resource status is set to `FAILED` with `status_message` like "Link your Twitter account in Settings to save content from Twitter."
**Tags:** #worker, #backend, #auth

### Scenario: LLM processing fails

**Given** a resource being processed by the worker
**When** the LLM call fails (timeout, error, etc.)
**Then** the resource status is set to `FAILED` with an appropriate `status_message`
**Tags:** #worker, #backend, #llm

---

## Feature: Knowledge Graph — Update

### Scenario: Graph is updated after resource is processed

**Given** a resource that has just been processed with tags ["AI", "Coding Agents", "LLM Tools"]
**When** the graph update step runs
**Then** Tag nodes are merged in Neo4j (scoped by `owner_id`), and `RELATED_TO` edges are created/incremented for each tag pair
**Tags:** #graph, #backend, #neo4j

### Scenario: Graph is updated after resource deletion

**Given** a resource with tags ["AI", "Coding Agents"] is deleted
**When** the graph sync job runs
**Then** `RELATED_TO` edge weights are decremented, and Tag nodes with no remaining resources are optionally removed
**Tags:** #graph, #backend, #neo4j

### Scenario: Graph is updated after resource re-processing

**Given** a resource whose tags changed from ["AI", "Python"] to ["AI", "LangGraph"]
**When** the graph update runs
**Then** old tag associations are removed, new ones are applied, and edge weights are recalculated
**Tags:** #graph, #backend, #neo4j

---

## Feature: Knowledge Graph — Exploration

### Scenario: User views the root graph

**Given** a logged-in user with resources and tags in their graph
**When** they call `GET /graph`
**Then** they receive nodes (with levels: parent/current/child) and edges for their personal graph
**Tags:** #graph, #backend, #api, #frontend

### Scenario: User views graph centered on a specific tag

**Given** a logged-in user
**When** they call `GET /graph?root=AI`
**Then** nodes and edges are returned centered on the "AI" tag with parent/current/child levels
**Tags:** #graph, #backend, #api

### Scenario: User expands a graph node

**Given** a user viewing the graph
**When** they click a node and `POST /graph/expand` with `node_id`
**Then** the next level of nodes and edges is returned
**Tags:** #graph, #backend, #api, #frontend

### Scenario: User views resources for a graph node

**Given** a user viewing the graph with an "AI" node
**When** they click the "AI" node and `GET /graph/nodes/AI/resources`
**Then** a list of resources tagged with "AI" (owned by the user) is returned
**Tags:** #graph, #resources, #backend, #api, #frontend

---

## Feature: Chat — AI Agent

### Scenario: User sends a chat message

**Given** a logged-in user
**When** they send `POST /chat` with `message: "What resources do I have about AI coding?"`
**Then** the agent uses tools to search resources and returns a relevant answer with a `conversation_id`
**Tags:** #chat, #backend, #agent, #api

### Scenario: User continues a conversation

**Given** a user with an existing `conversation_id`
**When** they send `POST /chat` with the same `conversation_id` and a follow-up message
**Then** the agent responds in the context of the previous conversation
**Tags:** #chat, #backend, #agent, #api

### Scenario: Agent uses graph traversal tool

**Given** a user asking "Show me related topics to LangGraph"
**When** the agent processes the message
**Then** the agent calls `get_graph_neighbors("LangGraph")` and includes related topics in the response
**Tags:** #chat, #backend, #agent

### Scenario: User lists their conversations

**Given** a logged-in user with past conversations
**When** they call `GET /chat/conversations`
**Then** a list of their conversations is returned
**Tags:** #chat, #backend, #api

### Scenario: User retrieves messages in a conversation

**Given** a conversation with multiple messages
**When** the user calls `GET /chat/conversations/{id}/messages`
**Then** all messages in that conversation are returned in order
**Tags:** #chat, #backend, #api

---

## Feature: Frontend — Resource UI

### Scenario: User sees resource submission form

**Given** a logged-in user on the main page
**When** they view the resource submission area
**Then** they see a form to submit a URL or paste text
**Tags:** #frontend, #ui

### Scenario: Resource shows processing status

**Given** a user who just submitted a resource
**When** the resource is in PROCESSING state
**Then** the UI shows a processing indicator (e.g. "Processing resource...", "Generating summary...")
**Tags:** #frontend, #ui

### Scenario: Resource shows FAILED status with actionable message

**Given** a resource that failed because the user has no linked Twitter account
**When** the user views the resource
**Then** the UI shows the `status_message` and a link to Settings to add the account
**Tags:** #frontend, #ui

### Scenario: User browses their resource list

**Given** a logged-in user with multiple resources
**When** they navigate to the resources list
**Then** they see all their resources with titles, summaries, tags, and statuses
**Tags:** #frontend, #ui

---

## Feature: Frontend — Graph Visualization

### Scenario: User views the knowledge graph

**Given** a logged-in user with a populated graph
**When** they navigate to the graph view
**Then** a visual force-directed graph is rendered with nodes (tags) and edges
**Tags:** #frontend, #ui, #graph

### Scenario: User clicks a node to expand

**Given** a user viewing the graph
**When** they click a node
**Then** the graph expands to show the next level of connected nodes
**Tags:** #frontend, #ui, #graph

### Scenario: User clicks a node to see resources

**Given** a user viewing the graph
**When** they click a node
**Then** a panel or list shows resources associated with that tag
**Tags:** #frontend, #ui, #graph

---

## Feature: Frontend — Chat UI

### Scenario: User opens the chat interface

**Given** a logged-in user
**When** they click the Sparkles toggle button in the sidebar
**Then** the chat panel slides open showing a chat input and any previous conversations
**Tags:** #frontend, #ui, #chat

### Scenario: User sends a message and receives a response

**Given** a user in the chat interface
**When** they type a message and submit
**Then** the message is sent to the API, and the assistant's response is displayed in the panel
**Tags:** #frontend, #ui, #chat

---

## Feature: Frontend — Settings / Account Management

### Scenario: User views linked accounts in settings

**Given** a logged-in user with Twitter and Google linked
**When** they navigate to Settings
**Then** they see both linked accounts with options to disconnect each
**Tags:** #frontend, #ui, #auth

### Scenario: User adds a new linked account from settings

**Given** a logged-in user in Settings
**When** they click "Add GitHub account" and authorize
**Then** they are redirected back to Settings showing the new account
**Tags:** #frontend, #ui, #auth

### Scenario: User sees error when unlinking last account

**Given** a logged-in user with only one account
**When** they try to disconnect it
**Then** the UI shows an error message that they must keep at least one account
**Tags:** #frontend, #ui, #auth

---

## Feature: Deployment

### Scenario: Docker images build successfully

**Given** the source code for frontend and backend
**When** Docker build is run
**Then** `learning-space-frontend` and `learning-space-backend` images are produced without errors
**Tags:** #infra, #devops

### Scenario: Helm chart deploys to Kubernetes

**Given** valid Docker images and a Kubernetes cluster
**When** the Helm chart is applied with `helm install`
**Then** frontend, API, worker, and database pods are running and healthy
**Tags:** #infra, #devops, #k8s

### Scenario: ArgoCD syncs from Git

**Given** updated image tags committed to the deploy repo
**When** ArgoCD detects the change
**Then** it syncs the Kubernetes cluster to match the desired state
**Tags:** #infra, #devops, #gitops

---

## Feature: API — Health & Errors

### Scenario: Health check returns OK

**Given** the API is running
**When** `GET /health` is called
**Then** the response is 200 with service status
**Tags:** #api, #backend

### Scenario: API returns standard error format

**Given** any error condition (e.g. resource not found)
**When** the error response is returned
**Then** it follows the standard format: `{ "detail": "...", "code": "...", "status": 404 }`
**Tags:** #api, #backend
