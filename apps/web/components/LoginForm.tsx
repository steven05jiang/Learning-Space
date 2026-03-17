"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { useMock } from "@/lib/mock/hooks";

export function LoginForm() {
  const router = useRouter();
  const isMock = useMock();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const [isXLoading, setIsXLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSignIn = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    if (isMock) {
      await new Promise((r) => setTimeout(r, 600));
      router.push("/dashboard");
      return;
    }

    try {
      const apiBase =
        process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
      const res = await fetch(`${apiBase}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) throw new Error("Invalid credentials");
      const data = await res.json();
      localStorage.setItem("auth_token", data.access_token);
      localStorage.setItem("user_info", JSON.stringify(data.user));
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sign in failed");
      setIsLoading(false);
    }
  };

  const handleXLogin = async () => {
    setError("");
    setIsXLoading(true);

    if (isMock) {
      await new Promise((r) => setTimeout(r, 600));
      router.push("/dashboard");
      return;
    }

    try {
      const apiBase =
        process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
      const res = await fetch(`${apiBase}/auth/login/x`);
      if (!res.ok) throw new Error("Failed to initiate X login");
      const data = await res.json();
      if (data.authorization_url) {
        if (data.state) localStorage.setItem("oauth_state_x", data.state);
        window.location.href = data.authorization_url;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "X login failed");
      setIsXLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setError("");
    setIsGoogleLoading(true);

    if (isMock) {
      await new Promise((r) => setTimeout(r, 600));
      router.push("/dashboard");
      return;
    }

    try {
      const apiBase =
        process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
      const res = await fetch(`${apiBase}/auth/login/google`);
      if (!res.ok) throw new Error("Failed to initiate Google login");
      const data = await res.json();
      if (data.authorization_url) {
        if (data.state) localStorage.setItem("oauth_state_google", data.state);
        window.location.href = data.authorization_url;
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Google login failed");
      setIsGoogleLoading(false);
    }
  };

  return (
    <div className="rounded-2xl border border-border/50 bg-card/80 p-8 shadow-xl backdrop-blur-xl">
      {/* Logo / Brand */}
      <div className="mb-8 text-center">
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary text-primary-foreground">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            className="h-6 w-6"
          >
            <path d="M12 2L2 7l10 5 10-5-10-5Z" />
            <path d="M2 17l10 5 10-5" />
            <path d="M2 12l10 5 10-5" />
          </svg>
        </div>
        <h1 className="text-2xl font-semibold tracking-tight text-foreground">
          Learning Space
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">
          Sign in to your account to continue
        </p>
      </div>

      {/* Mock mode badge */}
      {isMock && (
        <div className="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-4 py-2 text-center text-xs text-amber-700 dark:border-amber-800 dark:bg-amber-900/20 dark:text-amber-400">
          Mock mode — any credentials will work
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="mb-4 rounded-xl border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSignIn} className="space-y-5">
        <div className="space-y-2">
          <Label
            htmlFor="email"
            className="text-sm font-medium text-foreground"
          >
            Email
          </Label>
          <Input
            id="email"
            type="email"
            placeholder="name@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required={!isMock}
            className="h-11 bg-background/50 backdrop-blur-sm"
          />
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label
              htmlFor="password"
              className="text-sm font-medium text-foreground"
            >
              Password
            </Label>
            <Link
              href="#"
              className="text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              Forgot password?
            </Link>
          </div>
          <Input
            id="password"
            type="password"
            placeholder="Enter your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required={!isMock}
            className="h-11 bg-background/50 backdrop-blur-sm"
          />
        </div>

        <Button
          type="submit"
          className="h-11 w-full text-sm font-medium"
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <Spinner className="mr-2 h-4 w-4" />
              Signing in...
            </>
          ) : (
            "Sign in"
          )}
        </Button>
      </form>

      {/* Divider */}
      <div className="relative my-6">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-border" />
        </div>
        <div className="relative flex justify-center text-xs">
          <span className="bg-card/80 px-2 text-muted-foreground">
            or continue with
          </span>
        </div>
      </div>

      {/* Social login */}
      <div className="grid grid-cols-2 gap-3">
        <Button
          variant="outline"
          className="h-11 bg-background/50 backdrop-blur-sm"
          onClick={handleGoogleLogin}
          disabled={isGoogleLoading}
          type="button"
        >
          {isGoogleLoading ? (
            <Spinner className="mr-2 h-4 w-4" />
          ) : (
            <svg
              className="mr-2 h-4 w-4"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                fill="#4285F4"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="#34A853"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="#FBBC05"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="#EA4335"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
          )}
          Google
        </Button>
        <Button
          variant="outline"
          className="h-11 bg-background/50 backdrop-blur-sm"
          onClick={handleXLogin}
          disabled={isXLoading}
          type="button"
        >
          {isXLoading ? (
            <Spinner className="mr-2 h-4 w-4" />
          ) : (
            <svg
              className="mr-2 h-4 w-4"
              fill="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
            </svg>
          )}
          X
        </Button>
      </div>

      {/* Sign up link */}
      <p className="mt-6 text-center text-sm text-muted-foreground">
        {"Don't have an account? "}
        <Link
          href="/signup"
          className="font-medium text-foreground hover:underline"
        >
          Sign up
        </Link>
      </p>
    </div>
  );
}
