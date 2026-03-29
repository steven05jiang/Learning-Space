"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Plus, ExternalLink, RefreshCw } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useMock } from "@/lib/mock/hooks";
import { mockResources } from "@/lib/mock";

interface User {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string;
}

type EmbeddingStatus = "none" | "processing" | "ready";

interface Resource {
  id: string;
  url?: string;
  title?: string;
  summary?: string;
  tags: string[];
  status: "PENDING" | "PROCESSING" | "READY" | "FAILED";
  embedding_status: EmbeddingStatus;
  created_at: string;
}

interface ResourceListResponse {
  items: Resource[];
  total: number;
  limit: number;
  offset: number;
}

const STATUS_BADGE: Record<
  Resource["status"],
  {
    label: string;
    variant: "default" | "secondary" | "destructive" | "outline";
  }
> = {
  PENDING: { label: "Pending", variant: "outline" },
  PROCESSING: { label: "Processing", variant: "secondary" },
  READY: { label: "Ready", variant: "default" },
  FAILED: { label: "Failed", variant: "destructive" },
};

function getSafeUrl(url: string): string | undefined {
  try {
    const parsed = new URL(url);
    return ["http:", "https:"].includes(parsed.protocol) ? url : undefined;
  } catch {
    return undefined;
  }
}

function formatDate(dateString: string) {
  return new Date(dateString).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

const EMBEDDING_STATUS_CONFIG: Record<
  EmbeddingStatus,
  { label: string; className: string } | null
> = {
  ready: null,
  none: {
    label: "No embedding",
    className: "text-muted-foreground bg-muted border-transparent",
  },
  processing: {
    label: "Indexing",
    className: "text-blue-600 bg-blue-50 border-transparent dark:bg-blue-950 dark:text-blue-400",
  },
};

// Convert mock Resource to API Resource shape
function toApiResource(r: (typeof mockResources)[0]): Resource {
  return {
    id: r.id,
    url: r.url,
    title: r.title,
    summary: r.summary,
    tags: r.tags,
    status:
      r.status === "processed"
        ? "READY"
        : r.status === "pending"
          ? "PENDING"
          : "FAILED",
    embedding_status: r.status === "processed" ? "ready" : "none",
    created_at: r.createdAt,
  };
}

export default function ResourcesPage() {
  const router = useRouter();
  const isMock = useMock();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [resources, setResources] = useState<Resource[]>([]);
  const [isLoadingResources, setIsLoadingResources] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pagination, setPagination] = useState({
    total: 0,
    limit: 20,
    offset: 0,
  });

  // Auth check
  useEffect(() => {
    if (isMock) {
      setUser({
        id: "mock",
        email: "alex@learningspace.dev",
        display_name: "Alex Chen",
      });
      setIsLoading(false);
      return;
    }

    const token = localStorage.getItem("auth_token");
    const userInfo = localStorage.getItem("user_info");

    if (!token || !userInfo) {
      router.push("/login");
      return;
    }

    try {
      setUser(JSON.parse(userInfo));
    } catch {
      localStorage.removeItem("user_info");
      localStorage.removeItem("auth_token");
      router.push("/login");
      return;
    }

    setIsLoading(false);
  }, [router, isMock]);

  const fetchResources = useCallback(async () => {
    if (!user) return;

    if (isMock) {
      setIsLoadingResources(true);
      await new Promise((r) => setTimeout(r, 400));
      setResources(mockResources.map(toApiResource));
      setPagination({ total: mockResources.length, limit: 20, offset: 0 });
      setIsLoadingResources(false);
      return;
    }

    const token = localStorage.getItem("auth_token");
    if (!token) return;

    setIsLoadingResources(true);
    setError(null);

    const apiBase =
      process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

    try {
      const response = await fetch(
        `${apiBase}/resources?limit=${pagination.limit}&offset=${pagination.offset}`,
        {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        },
      );

      if (response.status === 401) {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("user_info");
        router.push("/login");
        return;
      }

      if (!response.ok) {
        throw new Error(`Failed to fetch resources: ${response.statusText}`);
      }

      const data: ResourceListResponse = await response.json();
      setResources(data.items);
      setPagination({
        total: data.total,
        limit: data.limit,
        offset: data.offset,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load resources");
    } finally {
      setIsLoadingResources(false);
    }
  }, [user, isMock, router, pagination.limit, pagination.offset]);

  useEffect(() => {
    if (user) fetchResources();
  }, [user]); // eslint-disable-line react-hooks/exhaustive-deps

  // Poll for status updates every 10 seconds (API mode only)
  useEffect(() => {
    if (!user || isMock) return;
    const interval = setInterval(() => fetchResources(), 10000);
    return () => clearInterval(interval);
  }, [user, isMock, fetchResources]);

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-56px)] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-border border-t-foreground" />
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-semibold tracking-tight text-foreground">
            My Resources
          </h2>
          <p className="text-muted-foreground">
            Manage and track your submitted learning resources
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={fetchResources}
            disabled={isLoadingResources}
          >
            <RefreshCw
              className={`h-4 w-4 ${isLoadingResources ? "animate-spin" : ""}`}
            />
            <span className="sr-only">Refresh</span>
          </Button>
          <Button onClick={() => router.push("/resources/new")}>
            <Plus className="mr-2 h-4 w-4" />
            Add Resource
          </Button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Loading skeleton */}
      {isLoadingResources && resources.length === 0 && (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i}>
              <CardHeader className="pb-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-3 w-full" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-3 w-full" />
                <Skeleton className="mt-1 h-3 w-2/3" />
                <div className="mt-3 flex gap-1">
                  <Skeleton className="h-5 w-12 rounded-full" />
                  <Skeleton className="h-5 w-16 rounded-full" />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!isLoadingResources && resources.length === 0 && !error && (
        <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-dashed border-border py-16">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
            <Plus className="h-6 w-6 text-muted-foreground" />
          </div>
          <div className="text-center">
            <p className="font-medium text-foreground">No resources yet</p>
            <p className="text-sm text-muted-foreground">
              Get started by submitting your first learning resource.
            </p>
          </div>
          <Button onClick={() => router.push("/resources/new")}>
            <Plus className="mr-2 h-4 w-4" />
            Add Resource
          </Button>
        </div>
      )}

      {/* Resource grid */}
      {resources.length > 0 && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {resources.map((resource) => {
              const statusConfig = STATUS_BADGE[resource.status];
              const embeddingConfig = EMBEDDING_STATUS_CONFIG[resource.embedding_status];
              const safeUrl = resource.url
                ? getSafeUrl(resource.url)
                : undefined;

              return (
                <Card
                  key={resource.id}
                  className="flex flex-col transition-shadow hover:shadow-md cursor-pointer"
                  onClick={() => router.push(`/resources/${resource.id}`)}
                >
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between gap-2">
                      <p className="font-semibold text-sm text-foreground line-clamp-2 leading-tight min-w-0 flex-1">
                        {resource.title || resource.url || "Untitled Resource"}
                      </p>
                      <Badge
                        variant={statusConfig.variant}
                        className="shrink-0 text-xs"
                      >
                        {statusConfig.label}
                      </Badge>
                    </div>
                    {resource.url && resource.title && safeUrl && (
                      <a
                        href={safeUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="truncate text-xs text-muted-foreground hover:text-foreground transition-colors"
                      >
                        {resource.url}
                      </a>
                    )}
                  </CardHeader>
                  <CardContent className="flex flex-1 flex-col gap-3">
                    {resource.summary && (
                      <p className="text-xs text-muted-foreground line-clamp-3">
                        {resource.summary}
                      </p>
                    )}
                    {resource.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {resource.tags.map((tag) => (
                          <span
                            key={tag}
                            className="inline-flex items-center rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground"
                          >
                            {tag}
                          </span>
                        ))}
                      </div>
                    )}
                    <div className="mt-auto flex items-center justify-between pt-2">
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-muted-foreground">
                          {formatDate(resource.created_at)}
                        </span>
                        {embeddingConfig && (
                          <span className={`inline-flex items-center rounded-md border px-1.5 py-0.5 text-xs font-medium ${embeddingConfig.className}`}>
                            {embeddingConfig.label}
                          </span>
                        )}
                      </div>
                      {safeUrl && (
                        <a
                          href={safeUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 gap-1 text-xs"
                          >
                            Open
                            <ExternalLink className="h-3 w-3" />
                          </Button>
                        </a>
                      )}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {/* Pagination info */}
          <p className="text-sm text-muted-foreground">
            Showing {pagination.offset + 1}–
            {Math.min(pagination.offset + pagination.limit, pagination.total)}{" "}
            of {pagination.total} resources
          </p>
        </>
      )}
    </div>
  );
}
