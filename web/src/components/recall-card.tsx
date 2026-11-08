import Image from "next/image";
import Link from "next/link";
import { Car, Package, Pill } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import type { RecallSource, RecallSummary, Severity } from "@/lib/api";
import { SEVERITY_LABEL, SOURCE_SHORT, formatDate } from "@/lib/labels";

const SOURCE_ICON: Record<RecallSource, typeof Car> = { cpsc: Package, fda: Pill, nhtsa: Car };

export function SeverityBadge({ severity }: { severity: Severity | null }) {
  if (!severity) return null;
  const variant = severity === "critical" ? "critical" : severity === "high" ? "warning" : "default";
  return <Badge variant={variant}>{SEVERITY_LABEL[severity]}</Badge>;
}

export function RecallCard({ recall }: { recall: RecallSummary }) {
  const Icon = SOURCE_ICON[recall.source];
  return (
    <Link href={`/recalls/${recall.id}`} className="group block focus-visible:outline-none">
      <Card className="flex h-full gap-4 p-4 transition-colors group-hover:border-foreground/30 group-focus-visible:ring-2 group-focus-visible:ring-ring">
        <div className="relative size-16 shrink-0 overflow-hidden rounded-md bg-muted">
          {recall.image_url ? (
            <Image src={recall.image_url} alt="" fill sizes="64px" className="object-cover" />
          ) : (
            <Icon aria-hidden className="absolute inset-0 m-auto size-6 text-muted-foreground" />
          )}
        </div>
        <div className="min-w-0 flex-1 space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="outline">{SOURCE_SHORT[recall.source]}</Badge>
            <SeverityBadge severity={recall.severity} />
            <span className="text-xs text-muted-foreground">{formatDate(recall.recall_date)}</span>
          </div>
          <h3 className="line-clamp-2 text-sm font-medium leading-snug">{recall.title}</h3>
          {recall.hazard && (
            <p className="line-clamp-2 text-sm text-muted-foreground">{recall.hazard}</p>
          )}
        </div>
      </Card>
    </Link>
  );
}

export function RecallCardSkeleton() {
  return (
    <Card className="flex gap-4 p-4" aria-hidden>
      <div className="size-16 shrink-0 animate-pulse rounded-md bg-muted" />
      <div className="flex-1 space-y-2">
        <div className="h-4 w-24 animate-pulse rounded bg-muted" />
        <div className="h-4 w-full animate-pulse rounded bg-muted" />
        <div className="h-4 w-2/3 animate-pulse rounded bg-muted" />
      </div>
    </Card>
  );
}
