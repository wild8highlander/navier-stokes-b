# nextjs-source — React (Next.js 16) edition of the Fluid Lab

The same 2D Navier-Stokes simulator as the standalone `index.html`,
packaged as a React component (`src/lib/fluid-engine.ts` + `src/app/page.tsx`)
with a bilingual EN/RU interface.

## Run

```bash
npm install        # or: bun install
npm run dev        # http://localhost:3000
```

No database is required; the prisma folder is kept only so the scaffold
boots untouched. The simulator itself is client-side only.
