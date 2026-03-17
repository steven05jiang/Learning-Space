// Mock data for Storybook stories and development
// Use these instead of hardcoded strings in component stories

export interface Resource {
  id: string;
  title: string;
  summary: string;
  tags: string[];
  url: string;
  status: "pending" | "processed" | "failed";
  createdAt: string;
}

export interface User {
  id: string;
  email: string;
  displayName: string;
  avatarUrl: string | null;
}

export interface NavItem {
  id: string;
  label: string;
  href: string;
  icon: string; // lucide-react icon name
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
}

// ── Resources ────────────────────────────────────────────────────────────────

export const mockResource: Resource = {
  id: "res-001",
  title: "Introduction to Transformer Architecture",
  summary:
    "A deep dive into the transformer model that powers modern LLMs, covering attention mechanisms, positional encoding, and feed-forward layers.",
  tags: ["machine-learning", "transformers", "deep-learning"],
  url: "https://example.com/transformers",
  status: "processed",
  createdAt: "2026-03-15T10:30:00Z",
};

export const mockResources: Resource[] = [
  mockResource,
  {
    id: "res-002",
    title: "Building RAG Systems with LangChain",
    summary:
      "Step-by-step guide to building retrieval-augmented generation pipelines using LangChain, vector databases, and OpenAI embeddings.",
    tags: ["rag", "langchain", "vector-db"],
    url: "https://example.com/rag-langchain",
    status: "processed",
    createdAt: "2026-03-14T14:20:00Z",
  },
  {
    id: "res-003",
    title: "Graph Neural Networks for Knowledge Representation",
    summary:
      "How GNNs can represent and reason over structured knowledge, with practical examples in Neo4j and PyTorch Geometric.",
    tags: ["graph-ml", "knowledge-graph", "neo4j"],
    url: "https://example.com/gnn-knowledge",
    status: "pending",
    createdAt: "2026-03-13T09:00:00Z",
  },
  {
    id: "res-004",
    title: "Fine-Tuning LLMs with LoRA",
    summary:
      "Low-rank adaptation techniques for efficiently fine-tuning large language models on domain-specific data without full parameter updates.",
    tags: ["fine-tuning", "lora", "llm"],
    url: "https://example.com/lora-finetuning",
    status: "failed",
    createdAt: "2026-03-12T16:45:00Z",
  },
  {
    id: "res-005",
    title: "Prompt Engineering Best Practices",
    summary:
      "Practical techniques for crafting effective prompts including chain-of-thought, few-shot learning, and structured output formatting.",
    tags: ["prompting", "llm", "best-practices"],
    url: "https://example.com/prompt-engineering",
    status: "processed",
    createdAt: "2026-03-11T11:15:00Z",
  },
  {
    id: "res-006",
    title: "Vector Databases Compared: Pinecone vs Weaviate vs Qdrant",
    summary:
      "Comprehensive comparison of leading vector database solutions covering performance, scaling, cost, and developer experience.",
    tags: ["vector-db", "comparison", "infrastructure"],
    url: "https://example.com/vector-db-comparison",
    status: "processed",
    createdAt: "2026-03-10T08:30:00Z",
  },
];

// ── User ─────────────────────────────────────────────────────────────────────

export const mockUser: User = {
  id: "user-001",
  email: "alex@learningspace.dev",
  displayName: "Alex Chen",
  avatarUrl: null,
};

// ── Navigation ────────────────────────────────────────────────────────────────

export const mockNavItems: NavItem[] = [
  {
    id: "dashboard",
    label: "Dashboard",
    href: "/dashboard",
    icon: "LayoutDashboard",
  },
  { id: "resources", label: "Resources", href: "/resources", icon: "BookOpen" },
  {
    id: "knowledge-graph",
    label: "Knowledge Graph",
    href: "/knowledge-graph",
    icon: "Network",
  },
  { id: "search", label: "Search", href: "/search", icon: "Search" },
  { id: "settings", label: "Settings", href: "/settings", icon: "Settings" },
];

// ── Chat Messages ─────────────────────────────────────────────────────────────

export const mockMessages: ChatMessage[] = [
  {
    id: "msg-001",
    role: "assistant",
    content:
      "Hi! I can help you explore your learning resources. What would you like to know?",
    timestamp: "2026-03-15T10:00:00Z",
  },
  {
    id: "msg-002",
    role: "user",
    content: "Can you summarize the resources about transformers?",
    timestamp: "2026-03-15T10:01:00Z",
  },
  {
    id: "msg-003",
    role: "assistant",
    content:
      'You have 1 resource about transformer architecture: "Introduction to Transformer Architecture" which covers attention mechanisms, positional encoding, and feed-forward layers. Would you like me to generate a deeper summary or find related resources?',
    timestamp: "2026-03-15T10:01:15Z",
  },
];

export const mockEmptyMessages: ChatMessage[] = [];
