import type { Metadata } from "next";
import { Camera } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

export const metadata: Metadata = { title: "Scan a label" };

// TODO(week 6): upload to object storage, POST /api/v1/scans, poll for extracted fields,
// let the user confirm or edit them (every correction becomes labeled data).
export default function ScanPage() {
  return (
    <div className="mx-auto max-w-lg space-y-6">
      <div className="space-y-2">
        <Badge variant="outline">Coming soon</Badge>
        <h1 className="text-2xl font-semibold">Scan a label</h1>
        <p className="text-muted-foreground">
          Photograph the label, box or receipt. We&apos;ll read the brand, model and lot number
          and check them against every federal recall.
        </p>
      </div>
      <Card className="flex flex-col items-center gap-3 border-dashed p-10 text-center">
        <Camera aria-hidden className="size-8 text-muted-foreground" />
        <label htmlFor="photo" className="font-medium">
          Take or choose a photo
        </label>
        {/* capture="environment" opens the rear camera on phones */}
        <input
          id="photo"
          type="file"
          accept="image/*"
          capture="environment"
          disabled
          className="text-sm text-muted-foreground"
        />
      </Card>
    </div>
  );
}
