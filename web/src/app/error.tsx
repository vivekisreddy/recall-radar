"use client";

import { useEffect } from "react";

import { Button } from "@/components/ui/button";

// Shown when a page throws, e.g. the API is down. `retry` re-fetches and re-renders the segment.
export default function ErrorPage({ error, retry }: { error: unknown; retry: () => void }) {
  useEffect(() => {
    console.error(error); // TODO(week 11): report to Sentry
  }, [error]);

  return (
    <div className="mx-auto max-w-md space-y-4 py-16 text-center">
      <h1 className="text-xl font-semibold">Something went wrong</h1>
      <p className="text-sm text-muted-foreground">
        We couldn&apos;t load this page. The recall service may be temporarily unavailable.
      </p>
      <Button variant="outline" onClick={() => retry()}>
        Try again
      </Button>
    </div>
  );
}
