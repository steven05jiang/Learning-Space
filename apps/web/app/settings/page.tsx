"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import {
  Github,
  Mail,
  Plus,
  Unlink,
  Loader2,
  AlertCircle,
  CheckCircle,
  X,
  Lock
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Input } from "@/components/ui/input";
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
import { useMock } from "@/lib/mock/hooks";

interface Account {
  id: number;
  provider: string;
  provider_account_id: string;
  username: string | null;
  created_at: string;
  last_login_at?: string;
}

interface User {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string;
  accounts?: Account[];
}

interface Provider {
  id: string;
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  disabled?: boolean;
}

interface Category {
  id: number;
  name: string;
  is_system: boolean;
  user_id?: number;
  created_at: string;
}

const PROVIDERS: Provider[] = [
  { id: "github", name: "GitHub", icon: Github, disabled: true },
  { id: "google", name: "Google", icon: Mail },
  { id: "twitter", name: "X (Twitter)", icon: ({ className }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
    </svg>
  ), disabled: true },
];

export default function SettingsPage() {
  const router = useRouter();
  const isMock = useMock();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [unlinkingAccount, setUnlinkingAccount] = useState<number | null>(null);

  // Categories state
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoadingCategories, setIsLoadingCategories] = useState(false);
  const [newCategoryName, setNewCategoryName] = useState("");
  const [isAddingCategory, setIsAddingCategory] = useState(false);
  const [deletingCategory, setDeletingCategory] = useState<number | null>(null);
  const [categoryError, setCategoryError] = useState<string | null>(null);

  // Auth check and fetch user data
  useEffect(() => {
    const fetchUserData = async () => {
      if (isMock) {
        // Mock data - user with some linked accounts
        setUser({
          id: "mock",
          email: "alex@learningspace.dev",
          display_name: "Alex Chen",
          accounts: [
            {
              id: 1,
              provider: "github",
              provider_account_id: "alexchen",
              created_at: "2026-03-10T10:00:00Z",
              last_login_at: "2026-03-17T09:00:00Z",
            },
            {
              id: 2,
              provider: "google",
              provider_account_id: "alex@learningspace.dev",
              created_at: "2026-03-12T15:30:00Z",
            },
          ],
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

        // Fetch current user data from API (including accounts if supported)
        const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

        const response = await fetch(`${apiBase}/auth/me`, {
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

        if (!response.ok) {
          throw new Error(`Failed to fetch user data: ${response.statusText}`);
        }

        const userData = await response.json();

        // Fetch linked OAuth accounts from the dedicated endpoint
        let accounts: Account[] = [];
        try {
          const accountsResponse = await fetch(`${apiBase}/auth/accounts`, {
            headers: {
              Authorization: `Bearer ${token}`,
              "Content-Type": "application/json",
            },
          });
          if (accountsResponse.ok) {
            const accountsData = await accountsResponse.json();
            accounts = accountsData.accounts ?? [];
          }
        } catch {
          // Non-fatal: accounts section will show empty
        }

        setUser({ ...userData, accounts });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load user data");
        // Fallback to localStorage data
        try {
          const parsedUser = JSON.parse(userInfo!);
          setUser({ ...parsedUser, accounts: [] }); // accounts unknown without API
        } catch {
          localStorage.removeItem("user_info");
          localStorage.removeItem("auth_token");
          router.push("/login");
          return;
        }
      } finally {
        setIsLoading(false);
      }
    };

    fetchUserData();
  }, [router, isMock]);

  // Fetch categories when user is loaded
  const fetchCategories = useCallback(async () => {
    if (!user) return;

    setIsLoadingCategories(true);
    setCategoryError(null);

    if (isMock) {
      // Mock categories data
      setCategories([
        {
          id: 1,
          name: "Technology",
          is_system: true,
          user_id: undefined,
          created_at: "2026-03-10T10:00:00Z",
        },
        {
          id: 2,
          name: "Science",
          is_system: true,
          user_id: undefined,
          created_at: "2026-03-10T10:00:00Z",
        },
        {
          id: 3,
          name: "My Personal Research",
          is_system: false,
          user_id: 1,
          created_at: "2026-03-15T14:30:00Z",
        },
        {
          id: 4,
          name: "Learning Notes",
          is_system: false,
          user_id: 1,
          created_at: "2026-03-16T09:15:00Z",
        },
      ]);
      setIsLoadingCategories(false);
      return;
    }

    try {
      const token = localStorage.getItem("auth_token");
      if (!token) return;

      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

      const response = await fetch(`${apiBase}/categories`, {
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

      if (!response.ok) {
        throw new Error(`Failed to fetch categories: ${response.statusText}`);
      }

      const categoriesData = await response.json();
      setCategories(categoriesData);
    } catch (err) {
      setCategoryError(err instanceof Error ? err.message : "Failed to load categories");
    } finally {
      setIsLoadingCategories(false);
    }
  }, [user, isMock, router]);

  useEffect(() => {
    if (user && !isLoading) {
      fetchCategories();
    }
  }, [user, isLoading, fetchCategories]);

  const handleAddAccount = useCallback((provider: string) => {
    // Navigate to OAuth link flow
    const redirectUrl = `/auth/link/${provider}`;
    window.location.href = redirectUrl;
  }, []);

  const handleUnlinkAccount = useCallback(async (accountId: number, provider: string) => {
    if (!user || isMock) {
      if (isMock) {
        // Mock unlink - just show a temporary message
        alert(`Mock: Would unlink ${provider} account`);
        return;
      }
      return;
    }

    setUnlinkingAccount(accountId);
    setError(null);

    const token = localStorage.getItem("auth_token");
    if (!token) return;

    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

    try {
      const response = await fetch(`${apiBase}/auth/accounts/${accountId}`, {
        method: "DELETE",
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

      if (response.status === 400) {
        const errorData = await response.json().catch(() => null);
        if (errorData?.code === "CANNOT_UNLINK_LAST_ACCOUNT") {
          setError("Cannot disconnect your last account. Please connect another account first.");
          return;
        }
        throw new Error(errorData?.detail || "Failed to unlink account");
      }

      if (!response.ok) {
        throw new Error(`Failed to unlink account: ${response.statusText}`);
      }

      // Remove account from local state
      setUser(prev => prev ? {
        ...prev,
        accounts: prev.accounts?.filter(acc => acc.id !== accountId) || []
      } : null);

    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to unlink account");
    } finally {
      setUnlinkingAccount(null);
    }
  }, [user, isMock, router]);

  const getLinkedAccount = useCallback((providerId: string) => {
    return user?.accounts?.find(account => account.provider === providerId);
  }, [user?.accounts]);

  const handleAddCategory = useCallback(async () => {
    if (!user || !newCategoryName.trim()) return;

    setIsAddingCategory(true);
    setCategoryError(null);

    if (isMock) {
      // Mock add category - check for duplicate names (case-insensitive)
      const trimmedName = newCategoryName.trim();
      const isDuplicate = categories.some(c =>
        c.name.toLowerCase() === trimmedName.toLowerCase()
      );

      if (isDuplicate) {
        setCategoryError("Category name already exists");
        setIsAddingCategory(false);
        return;
      }

      const newCategory: Category = {
        id: Math.max(...categories.map(c => c.id)) + 1,
        name: trimmedName,
        is_system: false,
        user_id: 1,
        created_at: new Date().toISOString(),
      };
      setCategories(prev => [...prev, newCategory]);
      setNewCategoryName("");
      setIsAddingCategory(false);
      return;
    }

    try {
      const token = localStorage.getItem("auth_token");
      if (!token) return;

      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

      const response = await fetch(`${apiBase}/categories`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ name: newCategoryName.trim() }),
      });

      if (response.status === 401) {
        localStorage.removeItem("auth_token");
        localStorage.removeItem("user_info");
        router.push("/login");
        return;
      }

      if (response.status === 409) {
        const errorData = await response.json().catch(() => null);
        setCategoryError(errorData?.detail || "Category name already exists");
        return;
      }

      if (!response.ok) {
        throw new Error(`Failed to create category: ${response.statusText}`);
      }

      const newCategory = await response.json();
      setCategories(prev => [...prev, newCategory]);
      setNewCategoryName("");
    } catch (err) {
      setCategoryError(err instanceof Error ? err.message : "Failed to create category");
    } finally {
      setIsAddingCategory(false);
    }
  }, [user, newCategoryName, categories, isMock, router]);

  const handleDeleteCategory = useCallback(async (categoryId: number) => {
    if (!user || isMock) {
      if (isMock) {
        // Mock delete
        setCategories(prev => prev.filter(c => c.id !== categoryId));
        return;
      }
      return;
    }

    setDeletingCategory(categoryId);
    setCategoryError(null);

    try {
      const token = localStorage.getItem("auth_token");
      if (!token) return;

      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

      const response = await fetch(`${apiBase}/categories/${categoryId}`, {
        method: "DELETE",
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

      if (response.status === 403) {
        setCategoryError("Cannot delete system category");
        return;
      }

      if (response.status === 404) {
        setCategoryError("Category not found or access denied");
        return;
      }

      if (response.status === 409) {
        const errorData = await response.json().catch(() => null);
        const detail = errorData?.detail ?? "";
        const match = detail.match(/(\d+) resource/);
        const count = match ? match[1] : "some";
        setCategoryError(
          `This category is used by ${count} resource(s). Go to My Resources, remove this category from those resources, then try again.`
        );
        return;
      }

      if (!response.ok) {
        throw new Error(`Failed to delete category: ${response.statusText}`);
      }

      // Remove category from local state
      setCategories(prev => prev.filter(c => c.id !== categoryId));
    } catch (err) {
      setCategoryError(err instanceof Error ? err.message : "Failed to delete category");
    } finally {
      setDeletingCategory(null);
    }
  }, [user, isMock, router]);

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
          Account Settings
        </h2>
        <p className="text-muted-foreground">
          Manage your linked OAuth accounts and login methods
        </p>
      </div>

      {/* Error alert */}
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* User profile section */}
      <Card>
        <CardHeader>
          <CardTitle>Profile Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {user ? (
            <>
              <div>
                <label className="text-sm font-medium text-foreground">Email</label>
                <p className="text-sm text-muted-foreground">{user.email}</p>
              </div>
              <div>
                <label className="text-sm font-medium text-foreground">Display Name</label>
                <p className="text-sm text-muted-foreground">{user.display_name}</p>
              </div>
            </>
          ) : (
            <div className="space-y-3">
              <Skeleton className="h-4 w-48" />
              <Skeleton className="h-4 w-32" />
            </div>
          )}
        </CardContent>
      </Card>

      {/* Linked accounts section */}
      <Card>
        <CardHeader>
          <CardTitle>Linked Accounts</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {PROVIDERS.map(provider => {
            const linkedAccount = getLinkedAccount(provider.id);
            const isUnlinking = unlinkingAccount === linkedAccount?.id;

            return (
              <div
                key={provider.id}
                className="flex items-center justify-between p-4 border border-border rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <provider.icon className="h-6 w-6 text-muted-foreground" />
                  <div>
                    <p className="font-medium text-foreground">{provider.name}</p>
                    {linkedAccount ? (
                      <p className="text-sm text-muted-foreground">
                        Connected{linkedAccount.username ? ` as ${linkedAccount.username}` : ""}
                      </p>
                    ) : provider.disabled ? (
                      <p className="text-sm text-muted-foreground">Coming soon</p>
                    ) : (
                      <p className="text-sm text-muted-foreground">Not connected</p>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {linkedAccount ? (
                    <>
                      <CheckCircle className="h-4 w-4 text-green-500" />
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleUnlinkAccount(linkedAccount.id, provider.name)}
                        disabled={isUnlinking}
                      >
                        {isUnlinking ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Unlink className="h-4 w-4" />
                        )}
                        {isUnlinking ? "Disconnecting..." : "Disconnect"}
                      </Button>
                    </>
                  ) : provider.disabled ? (
                    <Button variant="outline" size="sm" disabled>
                      <Plus className="h-4 w-4" />
                      Connect
                    </Button>
                  ) : (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleAddAccount(provider.id)}
                    >
                      <Plus className="h-4 w-4" />
                      Connect
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </CardContent>
      </Card>

      {/* Categories section */}
      <Card>
        <CardHeader>
          <CardTitle>Categories</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Category error alert */}
          {categoryError && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{categoryError}</AlertDescription>
            </Alert>
          )}

          {/* Add category form */}
          <div className="flex gap-2">
            <Input
              placeholder="Category name"
              value={newCategoryName}
              onChange={(e) => setNewCategoryName(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !isAddingCategory && newCategoryName.trim()) {
                  handleAddCategory();
                }
              }}
              disabled={isAddingCategory}
            />
            <Button
              onClick={handleAddCategory}
              disabled={isAddingCategory || !newCategoryName.trim()}
              size="sm"
            >
              {isAddingCategory ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Plus className="h-4 w-4" />
              )}
              Add
            </Button>
          </div>

          {/* Categories list */}
          {isLoadingCategories ? (
            <div className="space-y-3">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : (
            <>
              {categories.length === 0 ? (
                <div className="text-center py-8">
                  <p className="text-muted-foreground">No categories found. Add your first category above.</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {categories.map((category) => {
                    const isDeleting = deletingCategory === category.id;
                    const isUserCategory = !category.is_system;

                    return (
                      <div
                        key={category.id}
                        className="flex items-center justify-between p-3 border border-border rounded-lg"
                        data-testid="category-row"
                      >
                        <div className="flex items-center gap-3">
                          {category.is_system ? (
                            <Lock className="h-4 w-4 text-muted-foreground" data-testid="lock-icon" />
                          ) : (
                            <div className="h-4 w-4" />
                          )}
                          <div>
                            <p className="font-medium text-foreground">{category.name}</p>
                            <p className="text-xs text-muted-foreground">
                              {category.is_system
                                ? "System category"
                                : `Created ${new Date(category.created_at).toLocaleDateString()}`
                              }
                            </p>
                          </div>
                        </div>

                        {isUserCategory && (
                          <AlertDialog>
                            <AlertDialogTrigger asChild>
                              <Button
                                variant="ghost"
                                size="sm"
                                disabled={isDeleting}
                              >
                                {isDeleting ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <X className="h-4 w-4" />
                                )}
                              </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                              <AlertDialogHeader>
                                <AlertDialogTitle>Delete Category</AlertDialogTitle>
                                <AlertDialogDescription>
                                  Are you sure you want to delete &quot;{category.name}&quot;?
                                  This action cannot be undone. If any resources are still
                                  assigned to this category, deletion will be blocked — remove
                                  the category from those resources first.
                                </AlertDialogDescription>
                              </AlertDialogHeader>
                              <AlertDialogFooter>
                                <AlertDialogCancel>Cancel</AlertDialogCancel>
                                <AlertDialogAction
                                  onClick={() => handleDeleteCategory(category.id)}
                                  className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                >
                                  Delete
                                </AlertDialogAction>
                              </AlertDialogFooter>
                            </AlertDialogContent>
                          </AlertDialog>
                        )}
                      </div>
                    );
                  })}

                  {/* Empty state for custom categories */}
                  {categories.filter(c => !c.is_system).length === 0 && (
                    <div className="text-center py-4 border border-dashed border-border rounded-lg">
                      <p className="text-sm text-muted-foreground">
                        No custom categories yet. Add one above to get started.
                      </p>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}