"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function ComingSoonPage() {
  return (
    <div className="relative flex min-h-svh items-center justify-center overflow-hidden bg-background p-4">
      {/* Gradient background elements - same as login page */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden">
        <div className="absolute -left-1/4 -top-1/4 h-[600px] w-[600px] rounded-full bg-gradient-to-br from-primary/10 via-primary/5 to-transparent blur-3xl" />
        <div className="absolute -bottom-1/4 -right-1/4 h-[500px] w-[500px] rounded-full bg-gradient-to-tl from-muted/60 via-muted/30 to-transparent blur-3xl" />
        <div className="absolute left-1/2 top-1/2 h-[300px] w-[300px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-gradient-to-r from-primary/5 to-muted/20 blur-3xl" />
      </div>

      <div className="relative z-10 w-full max-w-sm">
        <div className="rounded-2xl border border-border/50 bg-card/80 p-8 shadow-xl backdrop-blur-xl">
          {/* Logo / Brand - same as login */}
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
              Private Beta
            </p>
          </div>

          {/* Coming soon message */}
          <div className="mb-6 text-center">
            <h2 className="mb-3 text-lg font-medium text-foreground">
              We&apos;re in private beta
            </h2>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Learning Space is currently available to a limited group of users.
              We&apos;ll be opening up to everyone soon!
            </p>
          </div>

          {/* Back to login button */}
          <Button
            variant="outline"
            className="h-11 w-full bg-background/50 backdrop-blur-sm"
            asChild
          >
            <Link href="/login">
              Back to login
            </Link>
          </Button>
        </div>
      </div>
    </div>
  );
}