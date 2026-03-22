RESULT: PR_READY
TASK: DEV-028
PR: #99
BRANCH: feature/dev-028-get-graph
SUMMARY: Implemented three-level rooted subgraph fix for GET /graph endpoint. Updated the Cypher query to fetch root, children, and parent-level nodes (neighbors of neighbors), fixed response building logic to include all three levels with correct level labels (current, child, parent), added edge deduplication, updated endpoint docstring to document all three levels, and enhanced the test to validate the complete three-level structure. All unit tests pass and lint checks pass.