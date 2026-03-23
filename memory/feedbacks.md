# Product Feedback Log

Each feedback entry uses the structure below. AI agents should read all `status: open` items before planning work. Entries are never deleted — set `status: resolved` and add a `resolved_by` reference when addressed.

---

## Entry Format

```
### FB-NNN | YYYY-MM-DD | <area> | <short title>
status: open | in-progress | resolved
resolved_by: <task-id or PR number> (if resolved)
source: demo | user | internal

**Problem:** <what is wrong or missing — observable, specific>
**Expected:** <what correct behavior looks like>
**Proposed solution:** <recommended implementation approach>
**Scope:** <files, components, or systems likely affected>
**Priority:** P0 (blocking) / P1 (before release) / P2 (nice to have)
```

---

## Feedback Entries

### FB-001 | 2026-03-22 | resource-fetching | URL content fetch fails due to bot blocking
status: open
source: demo

**Problem:** The current URL fetch strategy is a plain HTTP request, which is blocked by bot-detection on many sites, causing resource processing to fail silently or return incomplete content.
**Expected:** Content is reliably fetched for the majority of URLs, including those protected by bot-detection.
**Proposed solution:** Implement a tiered fetch strategy: (1) direct HTTP fetch as the default fast path, (2) Playwright headless browser fetch as a fallback for bot-blocked pages, (3) official publisher/platform API fetch where available (e.g. YouTube, Twitter). The fetcher should try each tier in order and record which tier succeeded.
**Scope:** resource fetching service / worker pipeline
**Priority:** P1

---

### FB-002 | 2026-03-22 | resource-processing | No processing state tracked — duplicate processing possible
status: open
source: demo

**Problem:** The system does not track whether a resource has already been processed. Workers may re-process resources redundantly, and failed processing is silently retried, wasting compute and producing inconsistent results.
**Expected:** Each resource has a persistent processing state (e.g. `pending`, `processing`, `success`, `failed`). Workers skip any resource already in `success` or `failed` state. Neither success nor failure triggers automatic re-processing.
**Proposed solution:** Add a `processing_status` field to the resource model. Workers set it to `processing` on start, `success` or `failed` on completion. Expose a manual "Re-process" action per resource in the UI so users can trigger reprocessing on demand (e.g. to recover from stale or failed results).
**Scope:** resource data model, worker pipeline, resource detail UI
**Priority:** P1

---

### FB-003 | 2026-03-22 | graph-view | Graph is disorganized due to unbounded LLM-generated tags
status: open
source: demo

**Problem:** Tags/nodes are generated freely by the LLM without reference to existing taxonomy, resulting in a fragmented graph with poor connectivity between resources and no consistent top-level structure.
**Expected:** The graph is organized under a coherent set of root-level categories, with reuse of existing tags wherever applicable.
**Proposed solution:** (1) Define a set of system-level root categories (e.g. Technology, Science, Business, Arts). (2) Allow users to create custom root categories. (3) When generating tags, include the current tag list in the LLM prompt so it can reuse existing tags. (4) Enforce that every resource is assigned at least one root-level category. LLM output schema should require a `root_categories` field with one or more valid values.
**Scope:** tag generation prompt, tag schema, graph data model, category management UI
**Priority:** P1

---

### FB-004 | 2026-03-22 | resource-management | Users cannot manually edit tags on a resource
status: open
source: demo

**Problem:** After a resource is added and processed, there is no way for users to add or remove tags. Users are locked into whatever the LLM assigned.
**Expected:** Users can add and delete tags on any resource from the resource detail view. Saving the update triggers a worker job to resync the graph (update edges/nodes to reflect the changed tag set).
**Proposed solution:** Add a tag editor component to the resource detail page (add tag input + removable tag chips). On save, persist the updated tags and enqueue a graph resync job for that resource.
**Scope:** resource detail UI, tag editor component, graph resync worker
**Priority:** P2

---

### FB-005 | 2026-03-22 | graph-view | Node popup overflows — too much content shown
status: open
source: demo

**Problem:** Clicking a node in the graph view opens a popup that overflows its container, with summary detail text making it unreadable.
**Expected:** The popup is compact and shows only: resource title, URL (as a link), and associated tags. No summary text.
**Proposed solution:** Constrain the popup to a fixed max-width/max-height with overflow hidden. Remove the summary field from the popup template. Ensure title truncates with ellipsis if too long.
**Scope:** graph view node popup component
**Priority:** P2
