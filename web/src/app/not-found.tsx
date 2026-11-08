import Link from "next/link";

import { buttonVariants } from "@/components/ui/button";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-md space-y-4 py-16 text-center">
      <h1 className="text-xl font-semibold">Not found</h1>
      <p className="text-sm text-muted-foreground">That page or recall doesn&apos;t exist.</p>
      <Link href="/recalls" className={buttonVariants({ variant: "outline" })}>
        Browse recalls
      </Link>
    </div>
  );
}
