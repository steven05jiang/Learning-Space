import { Suspense } from "react";
import { Loader2 } from "lucide-react";
import OAuthCallbackContent from "./OAuthCallbackContent";

export default async function OAuthCallbackPage({
  params,
}: {
  params: Promise<{ provider: string }>;
}) {
  const { provider } = await params;

  return (
    <Suspense
      fallback={
        <div className="flex min-h-svh items-center justify-center bg-background">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      }
    >
      <OAuthCallbackContent provider={provider} />
    </Suspense>
  );
}
