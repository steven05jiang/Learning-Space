"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { Search, X, ExternalLink, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useMock } from "@/lib/mock/hooks";
import { mockResources } from "@/lib/mock";

interface User {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string;
}

interface SearchResource {
  id: string;
  title?: string;
  summary?: string;
  tags: string[];
  top_level_categories: string[];
  original_content: string;
  content_type: "url" | "text";
  status: "READY";
  created_at: string;
  updated_at: string;
  rank: number;
}

interface SearchResponse {
  resources: SearchResource[];
  total: number;
}

interface Resource {
  id: string;
  url?: string;
  title?: string;
  summary?: string;
  tags: string[];
  status: "PENDING" | "PROCESSING" | "READY" | "FAILED";
  created_at: string;
}

function getSafeUrl(url: string): string | undefined {
  try {
    const parsed = new URL(url);
    return ["http:", "https:"].includes(parsed.protocol) ? url : undefined;
  } catch {
    return undefined;
  }
}

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
    created_at: r.createdAt,
  };
}

export default function SearchPage() {
  const router = useRouter();
  const isMock = useMock();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [query, setQuery] = useState("");
  const [selectedTag, setSelectedTag] = useState<string>("");
  const [searchResults, setSearchResults] = useState<SearchResource[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [totalResults, setTotalResults] = useState(0);
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [hasSearched, setHasSearched] = useState(false);

  // Refs for debouncing
  const searchTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const searchInputRef = useRef<HTMLInputElement>(null);

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

  // Auto-focus search input on page load
  useEffect(() => {
    if (!isLoading && searchInputRef.current) {
      searchInputRef.current.focus();
    }
  }, [isLoading]);

  // Fetch available tags from user's resources
  const fetchAvailableTags = useCallback(async () => {
    if (!user) return;

    if (isMock) {
      const allTags = new Set<string>();
      mockResources.forEach((resource) => {
        resource.tags.forEach((tag) => allTags.add(tag));
      });
      setAvailableTags(Array.from(allTags).sort());
      return;
    }

    const token = localStorage.getItem("auth_token");
    if (!token) return;

    const apiBase =
      process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

    try {
      const response = await fetch(`${apiBase}/resources?limit=1000&offset=0`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const data: { items: Resource[] } = await response.json();
        const allTags = new Set<string>();
        data.items.forEach((resource) => {
          resource.tags.forEach((tag) => allTags.add(tag));
        });
        setAvailableTags(Array.from(allTags).sort());
      }
    } catch (err) {
      console.error("Failed to fetch tags:", err);
    }
  }, [user, isMock]);

  // Fetch tags when user is available
  useEffect(() => {
    if (user) fetchAvailableTags();
  }, [user, fetchAvailableTags]);

  // Search function
  const performSearch = useCallback(
    async (searchQuery: string, tagFilter?: string) => {
      if (!user || !searchQuery.trim()) return;

      setIsSearching(true);
      setSearchError(null);
      setHasSearched(true);

      if (isMock) {
        // Mock search - filter mockResources by query and tag
        await new Promise((r) => setTimeout(r, 300)); // Simulate API delay
        const filteredResults = mockResources
          .filter((r) => {
            const matchesQuery =
              r.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
              r.summary?.toLowerCase().includes(searchQuery.toLowerCase()) ||
              r.tags.some((tag) =>
                tag.toLowerCase().includes(searchQuery.toLowerCase()),
              );
            const matchesTag = !tagFilter || r.tags.includes(tagFilter);
            return matchesQuery && matchesTag;
          })
          .map((r, index) => ({
            id: r.id,
            title: r.title,
            summary: r.summary,
            tags: r.tags,
            top_level_categories: [],
            original_content: r.url || "Text content",
            content_type: r.url ? ("url" as const) : ("text" as const),
            status: "READY" as const,
            created_at: r.createdAt,
            updated_at: r.createdAt,
            rank: 1.0 - index * 0.1, // Mock ranking
          }));

        setSearchResults(filteredResults);
        setTotalResults(filteredResults.length);
        setIsSearching(false);
        return;
      }

      const token = localStorage.getItem("auth_token");
      if (!token) return;

      const apiBase =
        process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

      try {
        const params = new URLSearchParams({
          q: searchQuery,
          limit: "20",
          offset: "0",
        });
        if (tagFilter) {
          params.append("tag", tagFilter);
        }

        const response = await fetch(
          `${apiBase}/resources/search?${params.toString()}`,
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
          throw new Error(`Search failed: ${response.statusText}`);
        }

        const data: SearchResponse = await response.json();
        setSearchResults(data.resources);
        setTotalResults(data.total);
      } catch (err) {
        setSearchError(
          err instanceof Error ? err.message : "Search failed",
        );
        setSearchResults([]);
        setTotalResults(0);
      } finally {
        setIsSearching(false);
      }
    },
    [user, isMock, router],
  );

  // Debounced search effect
  useEffect(() => {
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (query.trim()) {
      searchTimeoutRef.current = setTimeout(() => {
        performSearch(query, selectedTag);
      }, 500);
    } else {
      setSearchResults([]);
      setTotalResults(0);
      setHasSearched(false);
    }

    return () => {
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
    };
  }, [query, selectedTag, performSearch]);

  const clearSearch = () => {
    setQuery("");
    setSelectedTag("");
    setSearchResults([]);
    setTotalResults(0);
    setHasSearched(false);
    if (searchInputRef.current) {
      searchInputRef.current.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && query.trim()) {
      // Clear timeout and search immediately
      if (searchTimeoutRef.current) {
        clearTimeout(searchTimeoutRef.current);
      }
      performSearch(query, selectedTag);
    }
  };

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
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">
          Search
        </h2>
        <p className="text-muted-foreground">
          Search through your learning resources
        </p>
      </div>

      {/* Search input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          ref={searchInputRef}
          type="text"
          placeholder="Search your resources..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          className="pl-9 pr-10"
        />
        {query && (
          <Button
            variant="ghost"
            size="sm"
            onClick={clearSearch}
            className="absolute right-1 top-1/2 h-7 w-7 -translate-y-1/2 p-0"
          >
            <X className="h-4 w-4" />
          </Button>
        )}
        {isSearching && (
          <Loader2 className="absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 animate-spin text-muted-foreground" />
        )}
      </div>

      {/* Tag filter */}
      {availableTags.length > 0 && (
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted-foreground">Filter by tag:</span>
          <Select value={selectedTag} onValueChange={setSelectedTag}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="All tags" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="">All tags</SelectItem>
              {availableTags.map((tag) => (
                <SelectItem key={tag} value={tag}>
                  {tag}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {/* Error */}
      {searchError && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {searchError}
        </div>
      )}

      {/* Blank state */}
      {!hasSearched && !query.trim() && (
        <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-dashed border-border py-16">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
            <Search className="h-6 w-6 text-muted-foreground" />
          </div>
          <div className="text-center">
            <p className="font-medium text-foreground">
              Type to search your resources
            </p>
            <p className="text-sm text-muted-foreground">
              Find learning materials by keywords, tags, or content
            </p>
          </div>
        </div>
      )}

      {/* Loading skeleton */}
      {isSearching && (
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
      {!isSearching &&
        hasSearched &&
        searchResults.length === 0 &&
        !searchError && (
          <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-dashed border-border py-16">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted">
              <Search className="h-6 w-6 text-muted-foreground" />
            </div>
            <div className="text-center">
              <p className="font-medium text-foreground">
                No results for &apos;{query}&apos;
              </p>
              <p className="text-sm text-muted-foreground">
                Try a broader search or check your spelling
              </p>
            </div>
          </div>
        )}

      {/* Results */}
      {searchResults.length > 0 && (
        <>
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              {totalResults} result{totalResults !== 1 ? "s" : ""} found
              {selectedTag && (
                <>
                  {" "}
                  with tag{" "}
                  <Badge variant="secondary" className="ml-1">
                    {selectedTag}
                  </Badge>
                </>
              )}
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {searchResults.map((resource) => {
              const isUrl = resource.content_type === "url";
              const safeUrl = isUrl
                ? getSafeUrl(resource.original_content)
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
                        {resource.title ||
                          resource.original_content ||
                          "Untitled Resource"}
                      </p>
                    </div>
                    {isUrl && resource.title && safeUrl && (
                      <a
                        href={safeUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="truncate text-xs text-muted-foreground hover:text-foreground transition-colors"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {resource.original_content}
                      </a>
                    )}
                  </CardHeader>
                  <CardContent className="flex flex-1 flex-col gap-3">
                    {resource.summary && (
                      <p className="text-xs text-muted-foreground line-clamp-3">
                        {resource.summary}
                      </p>
                    )}

                    {/* Tags */}
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

                    {/* Categories */}
                    {resource.top_level_categories.length > 0 && (
                      <div className="flex flex-wrap gap-1">
                        {resource.top_level_categories.map((category) => (
                          <Badge
                            key={category}
                            variant="outline"
                            className="text-xs"
                          >
                            {category}
                          </Badge>
                        ))}
                      </div>
                    )}

                    <div className="mt-auto flex items-center justify-between pt-2">
                      <span className="text-xs text-muted-foreground">
                        {new Date(resource.created_at).toLocaleDateString(
                          "en-US",
                          {
                            year: "numeric",
                            month: "short",
                            day: "numeric",
                          },
                        )}
                      </span>
                      {safeUrl && (
                        <a
                          href={safeUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          onClick={(e) => e.stopPropagation()}
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
        </>
      )}
    </div>
  );
}