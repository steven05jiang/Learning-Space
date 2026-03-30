"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { ArrowLeft, Edit2, Save, X, Trash2, ExternalLink, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/components/ui/use-toast";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Spinner } from "@/components/ui/spinner";
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

interface Category {
  id: number;
  name: string;
  is_system: boolean;
  user_id?: number;
  created_at: string;
}

type EmbeddingStatus = "none" | "processing" | "ready";

interface Resource {
  id: string;
  url?: string;
  title?: string;
  summary?: string;
  tags: string[];
  top_level_categories: string[];
  status: "PENDING" | "PROCESSING" | "READY" | "FAILED";
  processing_status: "pending" | "processing" | "success" | "failed";
  embedding_status: EmbeddingStatus;
  content_type: string;
  original_content: string;
  created_at: string;
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
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// Convert mock Resource to API Resource shape
function toApiResource(r: (typeof mockResources)[0]): Resource {
  return {
    id: r.id,
    url: r.url,
    title: r.title,
    summary: r.summary,
    tags: r.tags,
    top_level_categories: [],
    status:
      r.status === "processed"
        ? "READY"
        : r.status === "pending"
          ? "PENDING"
          : "FAILED",
    processing_status:
      r.status === "processed"
        ? "success"
        : r.status === "pending"
          ? "pending"
          : "failed",
    embedding_status: r.status === "processed" ? "ready" : "none",
    content_type: "url",
    original_content: r.url,
    created_at: r.createdAt,
  };
}

export default function ResourceDetailPage() {
  const router = useRouter();
  const params = useParams();
  const id = params.id as string;
  const isMock = useMock();
  const { toast } = useToast();

  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [resource, setResource] = useState<Resource | null>(null);
  const [isLoadingResource, setIsLoadingResource] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);

  // Reprocess state
  const [isReprocessing, setIsReprocessing] = useState(false);

  // Edit state
  const [isEditing, setIsEditing] = useState(false);
  const [editTitle, setEditTitle] = useState("");
  const [isUpdating, setIsUpdating] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Tag editing state
  const [editTags, setEditTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState("");
  const [isEditingTags, setIsEditingTags] = useState(false);
  const [isUpdatingTags, setIsUpdatingTags] = useState(false);

  // Category editing state
  const [editCategories, setEditCategories] = useState<string[]>([]);
  const [isEditingCategories, setIsEditingCategories] = useState(false);
  const [isUpdatingCategories, setIsUpdatingCategories] = useState(false);

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
      const parsedUser = JSON.parse(userInfo);
      if (!parsedUser.id || !parsedUser.email) {
        throw new Error("Invalid user data");
      }
      setUser(parsedUser);
    } catch {
      localStorage.removeItem("user_info");
      localStorage.removeItem("auth_token");
      router.push("/login");
      return;
    }

    setIsLoading(false);
  }, [router, isMock]);

  // Fetch categories
  useEffect(() => {
    if (!user) return;

    const fetchCategories = async () => {
      if (isMock) {
        // Mock system categories for testing
        setCategories([
          { id: 1, name: "Technology", is_system: true, created_at: "2024-01-01T00:00:00Z" },
          { id: 2, name: "Science", is_system: true, created_at: "2024-01-01T00:00:00Z" },
          { id: 3, name: "Business", is_system: true, created_at: "2024-01-01T00:00:00Z" },
          { id: 4, name: "Arts", is_system: true, created_at: "2024-01-01T00:00:00Z" },
          { id: 5, name: "Health", is_system: true, created_at: "2024-01-01T00:00:00Z" },
          { id: 6, name: "Education", is_system: true, created_at: "2024-01-01T00:00:00Z" },
          { id: 7, name: "Politics", is_system: true, created_at: "2024-01-01T00:00:00Z" },
          { id: 8, name: "Entertainment", is_system: true, created_at: "2024-01-01T00:00:00Z" },
          { id: 9, name: "Sports", is_system: true, created_at: "2024-01-01T00:00:00Z" },
          { id: 10, name: "Philosophy", is_system: true, created_at: "2024-01-01T00:00:00Z" },
        ]);
        return;
      }

      const token = localStorage.getItem("auth_token");
      if (!token) return;

      const apiBase =
        process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

      try {
        const response = await fetch(`${apiBase}/categories`, {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });

        if (response.ok) {
          const data: Category[] = await response.json();
          setCategories(data);
        }
        // If categories fetch fails, continue without setting error
        // The validation will just check against an empty array
      } catch (err) {
        // Silent fail - categories are not critical for viewing
        console.warn("Failed to fetch categories:", err);
      }
    };

    fetchCategories();
  }, [user, isMock]);

  // Fetch resource
  useEffect(() => {
    if (!user || !id) return;

    const fetchResource = async () => {
      if (isMock) {
        setIsLoadingResource(true);
        await new Promise((r) => setTimeout(r, 300));

        const mockResource = mockResources.find((r) => r.id === id);
        if (mockResource) {
          const apiResource = toApiResource(mockResource);
          setResource(apiResource);
          setEditTitle(apiResource.title || "");
          setEditTags([...apiResource.tags]);
        } else {
          setError("Resource not found");
        }
        setIsLoadingResource(false);
        return;
      }

      const token = localStorage.getItem("auth_token");
      if (!token) return;

      setIsLoadingResource(true);
      setError(null);

      const apiBase =
        process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

      try {
        const response = await fetch(`${apiBase}/resources/${id}`, {
          method: "GET",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });

        if (response.status === 401) {
          localStorage.removeItem("auth_token");
          localStorage.removeItem("user_info");
          router.push("/login");
          return;
        }

        if (response.status === 404) {
          setError("Resource not found");
          return;
        }

        if (!response.ok) {
          throw new Error(`Failed to fetch resource: ${response.statusText}`);
        }

        const data: Resource = await response.json();
        setResource(data);
        setEditTitle(data.title || "");
        setEditTags([...data.tags]);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load resource"
        );
      } finally {
        setIsLoadingResource(false);
      }
    };

    fetchResource();
  }, [user, id, isMock, router]);

  const handleEdit = () => {
    setError(null);
    setIsEditing(true);
    setEditTitle(resource?.title || "");
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
    setEditTitle(resource?.title || "");
  };

  const handleEditTags = () => {
    setError(null);
    setIsEditingTags(true);
    setEditTags([...resource?.tags || []]);
    setNewTag("");
  };

  const handleCancelEditTags = () => {
    setIsEditingTags(false);
    setEditTags([...resource?.tags || []]);
    setNewTag("");
  };

  const handleAddTag = () => {
    const tag = newTag.trim();
    if (tag && !editTags.includes(tag)) {
      setEditTags([...editTags, tag]);
      setNewTag("");
    }
  };

  const handleRemoveTag = (tagToRemove: string) => {
    setEditTags(editTags.filter(tag => tag !== tagToRemove));
    setError(null);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      handleAddTag();
    }
  };

  const isTagsChanged = () => {
    const currentTags = [...(resource?.tags || [])].sort();
    const newTags = [...editTags].sort();
    return JSON.stringify(currentTags) !== JSON.stringify(newTags);
  };

  const handleSaveTags = async () => {
    if (!resource) return;

    setIsUpdatingTags(true);
    setError(null);

    try {
      if (isMock) {
        await new Promise((r) => setTimeout(r, 500));
        setResource({ ...resource, tags: [...editTags] });
        setIsEditingTags(false);
        toast({ title: "Tags updated successfully!" });
        setIsUpdatingTags(false);
        return;
      }

      const token = localStorage.getItem("auth_token");
      if (!token) {
        router.push("/login");
        return;
      }

      const apiBase =
        process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

      const response = await fetch(`${apiBase}/resources/${resource.id}`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          tags: editTags,
        }),
      });

      if (response.status === 401) {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("user_info");
        router.push("/login");
        return;
      }

      if (!response.ok) {
        throw new Error(`Failed to update tags: ${response.statusText}`);
      }

      const updatedResource: Resource = await response.json();
      setResource(updatedResource);
      setIsEditingTags(false);
      toast({ title: "Tags updated successfully!" });
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to update tags"
      );
    } finally {
      setIsUpdatingTags(false);
    }
  };

  const handleEditCategories = () => {
    setError(null);
    setIsEditingCategories(true);
    setEditCategories([...(resource?.top_level_categories || [])]);
  };

  const handleCancelEditCategories = () => {
    setIsEditingCategories(false);
    setEditCategories([...(resource?.top_level_categories || [])]);
  };

  const handleRemoveCategory = (cat: string) => {
    setEditCategories(editCategories.filter((c) => c !== cat));
    setError(null);
  };

  const handleAddCategory = (cat: string) => {
    if (cat && !editCategories.includes(cat)) {
      setEditCategories([...editCategories, cat]);
    }
  };

  const handleSaveCategories = async () => {
    if (!resource) return;
    setIsUpdatingCategories(true);
    setError(null);
    try {
      if (isMock) {
        await new Promise((r) => setTimeout(r, 500));
        setResource({ ...resource, top_level_categories: [...editCategories] });
        setIsEditingCategories(false);
        toast({ title: "Categories updated successfully!" });
        setIsUpdatingCategories(false);
        return;
      }

      const token = localStorage.getItem("auth_token");
      if (!token) { router.push("/login"); return; }

      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
      const response = await fetch(`${apiBase}/resources/${resource.id}`, {
        method: "PATCH",
        headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
        body: JSON.stringify({ top_level_categories: editCategories }),
      });

      if (response.status === 401) {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("user_info");
        router.push("/login");
        return;
      }
      if (!response.ok) throw new Error(`Failed to update categories: ${response.statusText}`);

      const updatedResource: Resource = await response.json();
      setResource(updatedResource);
      setIsEditingCategories(false);
      toast({ title: "Categories updated successfully!" });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to update categories");
    } finally {
      setIsUpdatingCategories(false);
    }
  };

  const handleSaveEdit = async () => {
    if (!resource) return;

    setIsUpdating(true);
    setError(null);

    try {
      if (isMock) {
        await new Promise((r) => setTimeout(r, 500));
        setResource({ ...resource, title: editTitle.trim() });
        setIsEditing(false);
        setIsUpdating(false);
        return;
      }

      const token = localStorage.getItem("auth_token");
      if (!token) {
        router.push("/login");
        return;
      }

      const apiBase =
        process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

      const response = await fetch(`${apiBase}/resources/${resource.id}`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: editTitle.trim(),
        }),
      });

      if (response.status === 401) {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("user_info");
        router.push("/login");
        return;
      }

      if (!response.ok) {
        throw new Error(`Failed to update resource: ${response.statusText}`);
      }

      const updatedResource: Resource = await response.json();
      setResource(updatedResource);
      setIsEditing(false);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to update resource"
      );
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDelete = async () => {
    if (!resource) return;

    setIsDeleting(true);
    setError(null);

    try {
      if (isMock) {
        await new Promise((r) => setTimeout(r, 500));
        router.push("/resources");
        return;
      }

      const token = localStorage.getItem("auth_token");
      if (!token) {
        router.push("/login");
        return;
      }

      const apiBase =
        process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

      const response = await fetch(`${apiBase}/resources/${resource.id}`, {
        method: "DELETE",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.status === 401) {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("user_info");
        router.push("/login");
        return;
      }

      if (!response.ok) {
        throw new Error(`Failed to delete resource: ${response.statusText}`);
      }

      router.push("/resources");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to delete resource"
      );
    } finally {
      setIsDeleting(false);
    }
  };

  const handleReprocess = async () => {
    if (!resource) return;

    setIsReprocessing(true);
    setError(null);

    try {
      if (isMock) {
        await new Promise((r) => setTimeout(r, 500));
        // Update resource with pending processing status
        setResource({ ...resource, processing_status: "pending" });
        // Show success message (could use a toast here in future)
        setIsReprocessing(false);
        return;
      }

      const token = localStorage.getItem("auth_token");
      if (!token) {
        router.push("/login");
        return;
      }

      const apiBase =
        process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

      const response = await fetch(`${apiBase}/resources/${resource.id}/reprocess`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (response.status === 401) {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("user_info");
        router.push("/login");
        return;
      }

      if (response.status === 404) {
        setError("Resource not found");
        return;
      }

      if (!response.ok) {
        throw new Error(`Failed to reprocess resource: ${response.statusText}`);
      }

      // On successful reprocess, refresh the resource data to get updated processing status
      const refreshResponse = await fetch(`${apiBase}/resources/${resource.id}`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (refreshResponse.ok) {
        const updatedResource: Resource = await refreshResponse.json();
        setResource(updatedResource);
      }

    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to reprocess resource"
      );
    } finally {
      setIsReprocessing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-56px)] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-border border-t-foreground" />
      </div>
    );
  }

  if (isLoadingResource) {
    return (
      <div className="flex flex-col gap-6 p-6">
        <Button
          variant="ghost"
          size="sm"
          className="-ml-2 w-fit"
          onClick={() => router.push("/resources")}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Resources
        </Button>

        <div className="animate-pulse space-y-6">
          <div className="h-8 w-3/4 rounded bg-muted"></div>
          <div className="space-y-4">
            <div className="h-4 w-full rounded bg-muted"></div>
            <div className="h-4 w-5/6 rounded bg-muted"></div>
            <div className="h-4 w-4/5 rounded bg-muted"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error && !resource) {
    return (
      <div className="flex flex-col gap-6 p-6">
        <Button
          variant="ghost"
          size="sm"
          className="-ml-2 w-fit"
          onClick={() => router.push("/resources")}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Resources
        </Button>

        <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-destructive">
          {error}
        </div>
      </div>
    );
  }

  if (!resource) {
    return null;
  }

  const statusConfig = STATUS_BADGE[resource.status];
  const safeUrl = resource.url ? getSafeUrl(resource.url) : undefined;

  return (
    <div className="flex flex-col gap-6 p-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button
          variant="ghost"
          size="sm"
          className="-ml-2 w-fit"
          onClick={() => router.push("/resources")}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Resources
        </Button>

        <div className="flex items-center gap-2">
          {!isEditing && (
            <>
              <Button
                variant="outline"
                size="sm"
                onClick={handleReprocess}
                disabled={resource.processing_status === "processing" || isReprocessing}
                className="gap-2"
              >
                {isReprocessing ? (
                  <>
                    <Spinner className="h-4 w-4" />
                    <span className="hidden sm:inline">Re-processing...</span>
                  </>
                ) : (
                  <>
                    <RefreshCw className="h-4 w-4" />
                    <span className="hidden sm:inline">Re-process</span>
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleEdit}
                className="gap-2"
              >
                <Edit2 className="h-4 w-4" />
                <span className="hidden sm:inline">Edit Title</span>
              </Button>
              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    className="gap-2 text-destructive hover:text-destructive"
                    disabled={isDeleting}
                  >
                    <Trash2 className="h-4 w-4" />
                    <span className="hidden sm:inline">Delete</span>
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Delete Resource</AlertDialogTitle>
                    <AlertDialogDescription>
                      Are you sure you want to delete this resource? This action
                      cannot be undone.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction
                      onClick={handleDelete}
                      className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                      disabled={isDeleting}
                    >
                      {isDeleting ? (
                        <>
                          <Spinner className="mr-2 h-4 w-4" />
                          Deleting...
                        </>
                      ) : (
                        "Delete"
                      )}
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </>
          )}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Resource Content */}
      <Card>
        <CardHeader className="pb-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 min-w-0">
              {isEditing ? (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="edit-title">Title</Label>
                    <Input
                      id="edit-title"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      placeholder="Enter resource title"
                      disabled={isUpdating}
                    />
                    {editTitle.trim() === "" && (
                      <div className="text-sm text-destructive">
                        Title cannot be empty
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      onClick={handleSaveEdit}
                      disabled={isUpdating || editTitle.trim() === ""}
                      className="gap-2"
                    >
                      {isUpdating ? (
                        <>
                          <Spinner className="h-4 w-4" />
                          Saving...
                        </>
                      ) : (
                        <>
                          <Save className="h-4 w-4" />
                          Save
                        </>
                      )}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleCancelEdit}
                      disabled={isUpdating}
                      className="gap-2"
                    >
                      <X className="h-4 w-4" />
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <CardTitle className="text-2xl leading-tight">
                  {resource.title || resource.url || "Untitled Resource"}
                </CardTitle>
              )}
            </div>
            <Badge
              variant={statusConfig.variant}
              className="shrink-0"
            >
              {statusConfig.label}
            </Badge>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* URL */}
          {resource.url && (
            <div className="space-y-2">
              <Label className="text-sm font-medium">Source URL</Label>
              <div className="flex items-center gap-2 min-w-0">
                {safeUrl ? (
                  <a
                    href={safeUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex-1 min-w-0 truncate rounded-md border border-input bg-muted px-3 py-2 text-sm text-blue-600 hover:underline dark:text-blue-400"
                  >
                    {resource.url}
                  </a>
                ) : (
                  <Input value={resource.url} readOnly className="bg-muted" />
                )}
                {safeUrl && (
                  <Button variant="outline" size="icon" className="shrink-0" asChild>
                    <a href={safeUrl} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="h-4 w-4" />
                      <span className="sr-only">Open</span>
                    </a>
                  </Button>
                )}
              </div>
            </div>
          )}

          {/* Summary */}
          {resource.summary && (
            <div className="space-y-2">
              <Label className="text-sm font-medium">Summary</Label>
              <Textarea
                value={resource.summary}
                readOnly
                rows={4}
                className="bg-muted resize-none"
              />
            </div>
          )}

          {/* Categories */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-sm font-medium">Categories</Label>
              {!isEditingCategories && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleEditCategories}
                  className="gap-1 h-7 px-2 text-xs"
                >
                  <Edit2 className="h-3 w-3" />
                  Edit
                </Button>
              )}
            </div>
            {isEditingCategories ? (
              <div className="space-y-3">
                <div className="flex flex-wrap gap-2">
                  {editCategories.map((cat) => (
                    <Badge
                      key={cat}
                      variant="outline"
                      className="text-xs flex items-center gap-1"
                    >
                      {cat}
                      <button
                        onClick={() => handleRemoveCategory(cat)}
                        className="ml-1 hover:bg-red-200 rounded-full p-0.5"
                        title={`Remove ${cat}`}
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
                <Select
                  onValueChange={handleAddCategory}
                  disabled={isUpdatingCategories}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Add a category..." />
                  </SelectTrigger>
                  <SelectContent>
                    {categories
                      .filter((c) => !editCategories.includes(c.name))
                      .map((c) => (
                        <SelectItem key={c.id} value={c.name}>
                          {c.name}
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
                <div className="flex items-center gap-2">
                  <Button
                    size="sm"
                    onClick={handleSaveCategories}
                    disabled={isUpdatingCategories || editCategories.length === 0}
                    className="gap-2"
                  >
                    {isUpdatingCategories ? (
                      <><Spinner className="h-4 w-4" />Saving...</>
                    ) : (
                      <><Save className="h-4 w-4" />Save</>
                    )}
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCancelEditCategories}
                    disabled={isUpdatingCategories}
                    className="gap-2"
                  >
                    <X className="h-4 w-4" />Cancel
                  </Button>
                </div>
              </div>
            ) : (
              <div className="flex flex-wrap gap-2">
                {(resource.top_level_categories || []).length > 0 ? (
                  resource.top_level_categories.map((cat) => (
                    <Badge key={cat} variant="outline" className="text-xs">
                      {cat}
                    </Badge>
                  ))
                ) : (
                  <span className="text-xs text-muted-foreground">No categories assigned</span>
                )}
              </div>
            )}
          </div>

          {/* Tags */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label className="text-sm font-medium">Tags</Label>
              {!isEditingTags && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleEditTags}
                  className="gap-1 h-7 px-2 text-xs"
                >
                  <Edit2 className="h-3 w-3" />
                  Edit
                </Button>
              )}
            </div>
              {isEditingTags ? (
                <div className="space-y-4">
                  {/* Current tags with remove buttons */}
                  <div className="flex flex-wrap gap-2">
                    {editTags.map((tag) => (
                      <Badge
                        key={tag}
                        variant="secondary"
                        className="text-xs flex items-center gap-1"
                      >
                        {tag}
                        <button
                          onClick={() => handleRemoveTag(tag)}
                          className="ml-1 hover:bg-red-200 rounded-full p-0.5"
                          title={`Remove ${tag}`}
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>

                  {/* Add new tag input */}
                  <div className="flex items-center gap-2">
                    <Input
                      value={newTag}
                      onChange={(e) => setNewTag(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Add new tag (press Enter or comma to add)"
                      className="flex-1"
                      disabled={isUpdatingTags}
                    />
                    <Button
                      size="sm"
                      onClick={handleAddTag}
                      disabled={!newTag.trim() || isUpdatingTags}
                      className="gap-2"
                    >
                      Add
                    </Button>
                  </div>

                  {/* Action buttons */}
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      onClick={handleSaveTags}
                      disabled={isUpdatingTags || !isTagsChanged() || editTags.length === 0}
                      className="gap-2"
                    >
                      {isUpdatingTags ? (
                        <>
                          <Spinner className="h-4 w-4" />
                          Saving...
                        </>
                      ) : (
                        <>
                          <Save className="h-4 w-4" />
                          Save Tags
                        </>
                      )}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={handleCancelEditTags}
                      disabled={isUpdatingTags}
                      className="gap-2"
                    >
                      <X className="h-4 w-4" />
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {resource.tags.length > 0 ? (
                    resource.tags.map((tag) => (
                      <Badge
                        key={tag}
                        variant="secondary"
                        className="text-xs"
                      >
                        {tag}
                      </Badge>
                    ))
                  ) : (
                    <span className="text-xs text-muted-foreground">No tags assigned</span>
                  )}
                </div>
              )}
          </div>

          {/* Metadata */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t">
            <div className="space-y-2">
              <Label className="text-sm font-medium">Content Type</Label>
              <div className="text-sm text-muted-foreground">
                {resource.content_type}
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-sm font-medium">Processing Status</Label>
              <div className="text-sm text-muted-foreground">
                {resource.processing_status === "pending" && "Pending"}
                {resource.processing_status === "processing" && "Processing"}
                {resource.processing_status === "success" && "Completed"}
                {resource.processing_status === "failed" && "Failed"}
              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-sm font-medium">Embedding Status</Label>
              <div className="text-sm">
                {resource.embedding_status === "ready" && (
                  <span className="text-muted-foreground">Ready</span>
                )}
                {resource.embedding_status === "none" && (
                  <span className="text-muted-foreground">Not embedded</span>
                )}
                {resource.embedding_status === "processing" && (
                  <span className="text-blue-600 dark:text-blue-400">Indexing…</span>
                )}

              </div>
            </div>

            <div className="space-y-2">
              <Label className="text-sm font-medium">Created</Label>
              <div className="text-sm text-muted-foreground">
                {formatDate(resource.created_at)}
              </div>
            </div>
          </div>

          {/* Original Content */}
          <div className="space-y-2">
            <Label className="text-sm font-medium">Original Content</Label>
            <Textarea
              value={resource.original_content}
              readOnly
              rows={3}
              className="bg-muted resize-none"
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}