import type { Metadata } from "next";
import Link from "next/link";
import { Suspense } from "react";

import { RecallCard, RecallCardSkeleton } from "@/components/recall-card";
import { buttonVariants } from "@/components/ui/button";
import { getRecalls, type RecallSource } from "@/lib/api";
import { SOURCE_SHORT } from "@/lib/labels";
import { cn } from "@/lib/utils";

export const metadata: Metadata = { title: "Recalls" };

const PAGE_SIZE = 20;
const SOURCES = Object.keys(SOURCE_SHORT) as RecallSource[];

export default function RecallsPage({ searchParams }: PageProps<"/recalls">) {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-semibold">Recalls</h1>
      {/* searchParams are request-time data, so everything that reads them streams in. */}
      <Suspense fallback={<ListSkeleton />}>
        <RecallList searchParams={searchParams} />
      </Suspense>
    </div>
  );
}

async function RecallList({ searchParams }: Pick<PageProps<"/recalls">, "searchParams">) {
  const params = await searchParams;
  const source = SOURCES.find((s) => s === params.source);
  const offset = Math.max(0, Number(params.offset) || 0);
  const page = await getRecalls({ source, limit: PAGE_SIZE, offset });

  const href = (next: { source?: RecallSource; offset?: number }) => {
    const qs = new URLSearchParams();
    if (next.source) qs.set("source", next.source);
    if (next.offset) qs.set("offset", String(next.offset));
    return qs.size ? `/recalls?${qs}` : "/recalls";
  };

  return (
    <div className="space-y-4">
      <nav aria-label="Filter by agency" className="flex flex-wrap gap-2">
        {[undefined, ...SOURCES].map((s) => (
          <Link
            key={s ?? "all"}
            href={href({ source: s })}
            aria-current={s === source ? "page" : undefined}
            className={cn(
              buttonVariants({ size: "sm", variant: s === source ? "default" : "outline" }),
            )}
          >
            {s ? SOURCE_SHORT[s] : "All"}
          </Link>
        ))}
      </nav>

      <p className="text-sm text-muted-foreground">
        {page.total.toLocaleString("en-US")} recalls
        {page.total > 0 &&
          ` · showing ${offset + 1}–${Math.min(offset + PAGE_SIZE, page.total)}`}
      </p>

      <div className="grid gap-3 md:grid-cols-2">
        {page.items.map((r) => (
          <RecallCard key={r.id} recall={r} />
        ))}
      </div>

      <div className="flex justify-between">
        {offset > 0 ? (
          <Link
            href={href({ source, offset: Math.max(0, offset - PAGE_SIZE) })}
            className={buttonVariants({ variant: "outline", size: "sm" })}
          >
            ← Newer
          </Link>
        ) : (
          <span />
        )}
        {offset + PAGE_SIZE < page.total && (
          <Link
            href={href({ source, offset: offset + PAGE_SIZE })}
            className={buttonVariants({ variant: "outline", size: "sm" })}
          >
            Older →
          </Link>
        )}
      </div>
    </div>
  );
}

function ListSkeleton() {
  return (
    <div className="grid gap-3 md:grid-cols-2">
      {Array.from({ length: 6 }, (_, i) => (
        <RecallCardSkeleton key={i} />
      ))}
    </div>
  );
}
