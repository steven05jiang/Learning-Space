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
  CheckCircle
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useMock } from "@/lib/mock/hooks";

interface Account {
  id: number;
  provider: string;
  provider_account_id: string;
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
}

const PROVIDERS: Provider[] = [
  { id: "github", name: "GitHub", icon: Github },
  { id: "google", name: "Google", icon: Mail },
  { id: "twitter", name: "X (Twitter)", icon: ({ className }) => (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
    </svg>
  ) },
];

export default function SettingsPage() {
  const router = useRouter();
  const isMock = useMock();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [unlinkingAccount, setUnlinkingAccount] = useState<number | null>(null);

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

        // Set user data - accounts may not be included in current API response
        setUser({
          ...userData,
          accounts: userData.accounts || [], // Default to empty array if not included
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load user data");
        // Fallback to localStorage data
        try {
          const parsedUser = JSON.parse(userInfo!);
          setUser({ ...parsedUser, accounts: [] });
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
                        Connected as {linkedAccount.provider_account_id}
                      </p>
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
    </div>
  );
}