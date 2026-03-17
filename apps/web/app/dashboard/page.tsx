"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { BookOpen, Plus, Network, TrendingUp } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useMock } from "@/lib/mock/hooks";
import { mockUser, mockResources } from "@/lib/mock";

interface User {
  id: string;
  email: string;
  display_name: string;
  avatar_url?: string;
}

const quickActions = [
  {
    title: "Add Resource",
    description: "Submit a URL to start learning from web content",
    icon: Plus,
    href: "/resources/new",
  },
  {
    title: "My Resources",
    description: "Browse your learning collection and track progress",
    icon: BookOpen,
    href: "/resources",
  },
  {
    title: "Knowledge Graph",
    description: "Visualize connections between your resources",
    icon: Network,
    href: "/knowledge-graph",
  },
  {
    title: "Analytics",
    description: "Track your learning progress and insights",
    icon: TrendingUp,
    href: "/analytics",
    comingSoon: true,
  },
];

export default function DashboardPage() {
  const router = useRouter();
  const isMock = useMock();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (isMock) {
      setUser({
        id: mockUser.id,
        email: mockUser.email,
        display_name: mockUser.displayName,
        avatar_url: mockUser.avatarUrl ?? undefined,
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

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-56px)] items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-border border-t-foreground" />
      </div>
    );
  }

  const resourceCount = isMock ? mockResources.length : null;
  const processedCount = isMock
    ? mockResources.filter((r) => r.status === "processed").length
    : null;

  return (
    <div className="flex flex-col gap-6 p-6">
      {/* Welcome */}
      <div>
        <h2 className="text-2xl font-semibold tracking-tight text-foreground">
          Welcome back{user?.display_name ? `, ${user.display_name}` : ""}
        </h2>
        <p className="text-muted-foreground">
          Here&apos;s what&apos;s happening with your learning space today.
        </p>
      </div>

      {/* Stats row (mock only) */}
      {isMock && resourceCount !== null && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Resources
              </CardTitle>
              <BookOpen className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{resourceCount}</div>
              <p className="text-xs text-muted-foreground">
                in your collection
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Processed
              </CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{processedCount}</div>
              <p className="text-xs text-muted-foreground">ready to explore</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Quick Actions */}
      <div>
        <h3 className="mb-4 text-sm font-medium text-muted-foreground uppercase tracking-wider">
          Quick Actions
        </h3>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {quickActions.map((action) => (
            <Card
              key={action.title}
              className={`cursor-pointer transition-shadow hover:shadow-md ${
                action.comingSoon ? "cursor-default opacity-60" : ""
              }`}
              onClick={() => !action.comingSoon && router.push(action.href)}
            >
              <CardHeader className="pb-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-muted">
                  <action.icon className="h-5 w-5 text-foreground" />
                </div>
              </CardHeader>
              <CardContent>
                <CardTitle className="mb-1 text-sm font-semibold">
                  {action.title}
                </CardTitle>
                <CardDescription className="text-xs">
                  {action.description}
                </CardDescription>
                {action.comingSoon && (
                  <span className="mt-2 inline-flex items-center rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                    Coming Soon
                  </span>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      {/* Recent Resources (mock) */}
      {isMock && (
        <div>
          <div className="mb-4 flex items-center justify-between">
            <h3 className="text-sm font-medium text-muted-foreground uppercase tracking-wider">
              Recent Resources
            </h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => router.push("/resources")}
            >
              View all
            </Button>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {mockResources.slice(0, 3).map((resource) => (
              <Card
                key={resource.id}
                className="hover:shadow-sm transition-shadow"
              >
                <CardContent className="pt-4">
                  <p className="font-medium text-sm text-foreground line-clamp-1">
                    {resource.title}
                  </p>
                  <p className="mt-1 text-xs text-muted-foreground line-clamp-2">
                    {resource.summary}
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {resource.tags.slice(0, 2).map((tag) => (
                      <span
                        key={tag}
                        className="inline-flex items-center rounded-md bg-muted px-2 py-0.5 text-xs text-muted-foreground"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
