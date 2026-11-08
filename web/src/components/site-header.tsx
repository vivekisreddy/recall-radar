import Link from "next/link";
import { Radar } from "lucide-react";

const NAV = [
  { href: "/recalls", label: "Recalls" },
  { href: "/scan", label: "Scan" },
  { href: "/inventory", label: "My items" },
];

export function SiteHeader() {
  return (
    <header className="border-b border-border bg-background/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <Radar aria-hidden className="size-5 text-primary" />
          Recall Radar
        </Link>
        <nav className="flex items-center gap-1 text-sm">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-md px-3 py-2 text-muted-foreground hover:bg-muted hover:text-foreground"
            >
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
