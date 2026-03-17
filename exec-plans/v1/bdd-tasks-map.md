# BDD Tasks Dependency Map — Learning Space

_Version: v1 | Generated: 2026-03-14_

---

## Dependency Tree

```
[Feature: API — Health & Errors]
├── Scenario: Health check returns OK                              ← No dependencies (infra only)
└── Scenario: API returns standard error format                    ← No dependencies

[Feature: Authentication — OAuth Login]
├── Scenario: User logs in with Twitter for the first time
│   ├── Scenario: User logs in with an existing linked account
│   └── Scenario: Session/JWT is validated on each request
│       └── Scenario: Unauthenticated user is redirected to login
├── Scenario: User logs in with Google (second provider)
│   └── [depends on] Scenario: User links an additional social account

[Feature: Authentication — Account Linking]
├── [depends on] Scenario: User logs in with Twitter for the first time
│   ├── Scenario: User links an additional social account
│   │   ├── Scenario: User unlinks a social account
│   │   │   └── Scenario: User cannot unlink their last account
│   │   └── Scenario: User attempts to link an account already linked to another user
│   └── Scenario: User retrieves their profile and linked accounts

[Feature: Authentication — Current User]
├── [depends on] Scenario: User logs in with Twitter for the first time
│   └── Scenario: User retrieves their profile and linked accounts

[Feature: Resource Management — Create]
├── [depends on] Scenario: Session/JWT is validated on each request
│   ├── Scenario: Authenticated user submits a URL resource
│   │   └── Scenario: User submits a URL with prefer_provider hint
│   ├── Scenario: Authenticated user submits a text resource
│   └── Scenario: Unauthenticated user attempts to create a resource
│       └── [depends on] Scenario: Unauthenticated user is redirected to login

[Feature: Resource Management — Read / List]
├── [depends on] Scenario: Authenticated user submits a URL resource
│   ├── Scenario: User lists their resources
│   ├── Scenario: User views a single resource
│   ├── Scenario: User filters resources by tag
│   │   └── [depends on] Scenario: Worker processes a URL resource successfully (tags must exist)
│   └── Scenario: User filters resources by status

[Feature: Resource Management — Update]
├── [depends on] Scenario: Authenticated user submits a URL resource
│   ├── Scenario: User updates a resource title
│   └── Scenario: User updates original_content triggering reprocessing

[Feature: Resource Management — Delete]
├── [depends on] Scenario: Authenticated user submits a URL resource
│   └── Scenario: User deletes a resource
│       └── Scenario: Graph is updated after resource deletion

[Feature: Resource Processing — Async Worker]
├── [depends on] Scenario: Authenticated user submits a URL resource
│   ├── Scenario: Worker processes a URL resource successfully
│   │   └── Scenario: Graph is updated after resource is processed
│   ├── Scenario: Worker processes a text resource successfully
│   │   └── [depends on] Scenario: Authenticated user submits a text resource
│   ├── Scenario: URL requires login and user has linked account
│   │   └── [depends on] Scenario: User links an additional social account
│   ├── Scenario: URL requires login and user has no linked account
│   └── Scenario: LLM processing fails

[Feature: Knowledge Graph — Update]
├── [depends on] Scenario: Worker processes a URL resource successfully
│   ├── Scenario: Graph is updated after resource is processed
│   ├── Scenario: Graph is updated after resource deletion
│   │   └── [depends on] Scenario: User deletes a resource
│   └── Scenario: Graph is updated after resource re-processing
│       └── [depends on] Scenario: User updates original_content triggering reprocessing

[Feature: Knowledge Graph — Exploration]
├── [depends on] Scenario: Graph is updated after resource is processed
│   ├── Scenario: User views the root graph
│   ├── Scenario: User views graph centered on a specific tag
│   ├── Scenario: User expands a graph node
│   └── Scenario: User views resources for a graph node

[Feature: Chat — AI Agent]
├── [depends on] Scenario: User views resources for a graph node (tools need working resource/graph APIs)
├── [depends on] Scenario: User lists their resources
│   ├── Scenario: User sends a chat message
│   │   └── Scenario: User continues a conversation
│   ├── Scenario: Agent uses graph traversal tool
│   ├── Scenario: User lists their conversations
│   └── Scenario: User retrieves messages in a conversation

[Feature: Frontend — Resource UI]
├── [depends on] Scenario: Authenticated user submits a URL resource (API must exist)
│   ├── Scenario: User sees resource submission form
│   ├── Scenario: Resource shows processing status
│   │   └── [depends on] Scenario: Worker processes a URL resource successfully
│   ├── Scenario: Resource shows FAILED status with actionable message
│   │   └── [depends on] Scenario: URL requires login and user has no linked account
│   └── Scenario: User browses their resource list
│       └── [depends on] Scenario: User lists their resources

[Feature: Frontend — Graph Visualization]
├── [depends on] Scenario: User views the root graph (API must exist)
│   ├── Scenario: User views the knowledge graph
│   ├── Scenario: User clicks a node to expand
│   └── Scenario: User clicks a node to see resources

[Feature: Frontend — Chat UI]
├── [depends on] Scenario: User sends a chat message (API must exist)
│   ├── Scenario: User opens the chat interface
│   └── Scenario: User sends a message and receives a response

[Feature: Frontend — Settings / Account Management]
├── [depends on] Scenario: User retrieves their profile and linked accounts
│   ├── Scenario: User views linked accounts in settings
│   ├── Scenario: User adds a new linked account from settings
│   │   └── [depends on] Scenario: User links an additional social account
│   └── Scenario: User sees error when unlinking last account
│       └── [depends on] Scenario: User cannot unlink their last account

[Feature: Deployment]
├── Scenario: Docker images build successfully                     ← Can start after any code exists
│   └── Scenario: Helm chart deploys to Kubernetes
│       └── Scenario: ArgoCD syncs from Git
```

---

## Parallel Execution Groups

These groups of scenarios have no interdependencies and can be developed/tested in parallel:

**Group A — Foundation (no dependencies):**

- Health check returns OK
- API returns standard error format
- Docker images build successfully

**Group B — Auth (depends only on Group A foundation):**

- User logs in with Twitter for the first time
- Session/JWT is validated on each request
- Unauthenticated user is redirected to login

**Group C — After Auth established (parallel within group):**

- User links an additional social account
- User retrieves their profile and linked accounts
- Authenticated user submits a URL resource
- Authenticated user submits a text resource

**Group D — After resources exist (parallel within group):**

- User lists their resources
- User views a single resource
- User filters resources by status
- User updates a resource title
- User deletes a resource
- Worker processes a URL resource successfully
- Worker processes a text resource successfully

**Group E — After graph populated (parallel within group):**

- User views the root graph
- User views graph centered on a specific tag
- User expands a graph node
- User views resources for a graph node

**Group F — Frontend (parallel with backend, after APIs exist):**

- Resource UI scenarios
- Graph visualization scenarios
- Chat UI scenarios
- Settings / Account management scenarios

---

## Dependency Notes

- **No circular dependencies** detected.
- Auth is the critical bottleneck — nearly all features depend on a working auth flow.
- Frontend features can be developed with mocked APIs and integrated later.
- The Chat feature has the deepest dependency chain (requires auth + resources + worker + graph + exploration APIs all working).
- Deployment scenarios are largely independent of feature development and can progress in parallel.
