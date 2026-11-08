import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { ExternalLink } from "lucide-react";

import { SeverityBadge } from "@/components/recall-card";
import { Badge } from "@/components/ui/badge";
import { buttonVariants } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ApiError, getRecall } from "@/lib/api";
import { SOURCE_LABEL, formatDate } from "@/lib/labels";

export default function RecallPage({ params }: PageProps<"/recalls/[id]">) {
  return (
    <div className="space-y-6">
      <Link href="/recalls" className="text-sm text-muted-foreground hover:text-foreground">
        ← All recalls
      </Link>
      <Suspense fallback={<div className="h-64 animate-pulse rounded-lg bg-muted" />}>
        <RecallDetail params={params} />
      </Suspense>
    </div>
  );
}

async function RecallDetail({ params }: Pick<PageProps<"/recalls/[id]">, "params">) {
  const { id } = await params;
  const recall = await getRecall(id).catch((err) => {
    if (err instanceof ApiError && (err.status === 404 || err.status === 422)) notFound();
    throw err;
  });

  return (
    <article className="space-y-6">
      <header className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="outline">{SOURCE_LABEL[recall.source]}</Badge>
          <SeverityBadge severity={recall.severity} />
          <span className="text-sm text-muted-foreground">
            #{recall.source_id} · {formatDate(recall.recall_date)}
          </span>
        </div>
        <h1 className="text-2xl font-semibold text-balance">{recall.title}</h1>
      </header>

      {recall.image_url && (
        <div className="relative aspect-video max-w-md overflow-hidden rounded-lg bg-muted">
          <Image
            src={recall.image_url}
            alt={`Photo of the recalled product: ${recall.title}`}
            fill
            sizes="(min-width: 768px) 448px, 100vw"
            className="object-contain"
          />
        </div>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {recall.hazard && <Section title="Hazard">{recall.hazard}</Section>}
        {recall.remedy && <Section title="What to do">{recall.remedy}</Section>}
      </div>

      {recall.vehicles.length > 0 && (
        <Section title="Vehicles covered">
          <ul className="flex flex-wrap gap-2">
            {recall.vehicles.map((v) => (
              <li key={`${v.make}-${v.model}-${v.model_year}`}>
                <Badge>
                  {v.model_year} {v.make} {v.model}
                </Badge>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-xs text-muted-foreground">
            A recall can cover only some trims of a model. Check your VIN on NHTSA.gov.
          </p>
        </Section>
      )}

      {recall.url && (
        <a href={recall.url} target="_blank" rel="noreferrer" className={buttonVariants({ variant: "outline" })}>
          Official notice <ExternalLink aria-hidden className="size-4" />
        </a>
      )}
    </article>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Card className="space-y-2 p-5">
      <h2 className="text-sm font-medium text-muted-foreground">{title}</h2>
      <div className="text-sm leading-relaxed">{children}</div>
    </Card>
  );
}
