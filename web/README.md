# Recall Radar · web

Next.js 16 PWA (App Router, Cache Components, Tailwind CSS 4).

```bash
cp .env.example .env.local   # API_URL=http://localhost:8000
npm install
npm run dev                  # http://localhost:3000
```

- Pages fetch from the backend in Server Components via `src/lib/api.ts` (server-only). Live data is wrapped in `<Suspense>`, which Cache Components requires.
- UI components follow shadcn/ui conventions (`components.json`, `src/components/ui`, `cn()` in `src/lib/utils.ts`), so `npx shadcn add <component>` works.
- This Next.js version differs from older ones: check `node_modules/next/dist/docs/` before relying on memory (see `AGENTS.md`).
