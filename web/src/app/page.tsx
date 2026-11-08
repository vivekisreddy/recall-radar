import Link from "next/link";
import { Suspense } from "react";
import { BellRing, Camera, ScanSearch } from "lucide-react";

import { RecallCard, RecallCardSkeleton } from "@/components/recall-card";
import { buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { getRecalls, getStats } from "@/lib/api";
import { SOURCE_LABEL } from "@/lib/labels";

const STEPS = [
  { icon: Camera, title: "Snap a label", body: "Photograph a label, box or receipt." },
  { icon: ScanSearch, title: "We match it", body: "Model, lot and UPC checked against every federal recall." },
  { icon: BellRing, title: "Get alerted", body: "Saved items are re-checked daily, for as long as you own them." },
];

export default function HomePage() {
  return (
    <div className="space-y-12">
      <section className="space-y-5 pt-6">
        <h1 className="max-w-2xl text-4xl font-semibold tracking-tight text-balance sm:text-5xl">
          Is anything you own recalled?
        </h1>
        <p className="max-w-2xl text-lg text-muted-foreground text-pretty">
          Recall data is public, but finding out your car seat or space heater was recalled
          still depends on luck. Recall Radar matches the things you own against every federal
          recall, and keeps watching.
        </p>
        <div className="flex flex-wrap gap-3">
          <Link href="/scan" className={buttonVariants({ size: "lg" })}>
            <Camera aria-hidden className="size-4" /> Scan a label
          </Link>
          <Link href="/recalls" className={buttonVariants({ size: "lg", variant: "outline" })}>
            Browse recalls
          </Link>
        </div>
      </section>

      <Suspense fallback={<div className="h-20 animate-pulse rounded-lg bg-muted" />}>
        <StatsStrip />
      </Suspense>

      <section className="grid gap-4 sm:grid-cols-3">
        {STEPS.map(({ icon: Icon, title, body }) => (
          <Card key={title} className="space-y-2 p-5">
            <Icon aria-hidden className="size-5 text-primary" />
            <h2 className="font-medium">{title}</h2>
            <p className="text-sm text-muted-foreground">{body}</p>
          </Card>
        ))}
      </section>

      <section className="space-y-4">
        <div className="flex items-baseline justify-between">
          <h2 className="text-xl font-semibold">Latest recalls</h2>
          <Link href="/recalls" className="text-sm text-muted-foreground hover:text-foreground">
            See all →
          </Link>
        </div>
        <Suspense
          fallback={
            <div className="grid gap-3 md:grid-cols-2">
              {Array.from({ length: 4 }, (_, i) => (
                <RecallCardSkeleton key={i} />
              ))}
            </div>
          }
        >
          <LatestRecalls />
        </Suspense>
      </section>
    </div>
  );
}

async function StatsStrip() {
  const stats = await getStats();
  return (
    <Card className="grid grid-cols-2 divide-border p-5 sm:grid-cols-4 sm:divide-x">
      <Stat value={stats.total} label="Recalls tracked" />
      {stats.by_source.map((s) => (
        <Stat key={s.source} value={s.recalls} label={SOURCE_LABEL[s.source]} />
      ))}
    </Card>
  );
}

function Stat({ value, label }: { value: number; label: string }) {
  return (
    <div className="px-4 py-2">
      <div className="text-2xl font-semibold tabular-nums">{value.toLocaleString("en-US")}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  );
}

async function LatestRecalls() {
  const { items } = await getRecalls({ limit: 6 });
  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground">No recalls yet. Run `make seed`.</p>;
  }
  return (
    <div className="grid gap-3 md:grid-cols-2">
      {items.map((r) => (
        <RecallCard key={r.id} recall={r} />
      ))}
    </div>
  );
}
