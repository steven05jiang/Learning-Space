# Learning Space

A personal knowledge management app where you collect learning resources (URLs, text snippets), which are automatically summarized and tagged by an LLM, forming a personal knowledge graph you can explore visually and query via an AI chatbot.

## Local Dev

**Prerequisites:** Docker, Node 20+, Python 3.12+, `uv`

```bash
# Start infrastructure
docker compose up -d

# Run backend
cd apps/api
uv sync
uv run uvicorn main:app --reload

# Run frontend (new terminal)
cd apps/web
npm install
npm run dev
```