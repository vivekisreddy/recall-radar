import type { Metadata } from "next";
import { Package } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

export const metadata: Metadata = { title: "My items" };

// TODO(week 5): sign-in, then list the user's items with any active matches (GET /api/v1/items).
export default function InventoryPage() {
  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <Badge variant="outline">Coming soon</Badge>
        <h1 className="text-2xl font-semibold">My items</h1>
        <p className="text-muted-foreground">
          Everything you&apos;ve saved, re-checked against new recalls every day.
        </p>
      </div>
      <Card className="flex flex-col items-center gap-3 border-dashed p-10 text-center">
        <Package aria-hidden className="size-8 text-muted-foreground" />
        <p className="text-sm text-muted-foreground">No items yet.</p>
      </Card>
    </div>
  );
}
