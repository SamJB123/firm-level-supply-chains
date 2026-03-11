# AGENTS.md

## Cursor Cloud specific instructions

This is a **TanStack Start** app targeting **Cloudflare Workers**, scaffolded from `TanStack/router/examples/react/start-basic-cloudflare`.

### Key commands

See `package.json` scripts. Key ones:

- **Dev server:** `pnpm dev` (runs on port 3000)
- **Build:** `pnpm build` (vite build + tsc --noEmit)
- **Type-check:** `npx tsc --noEmit`
- **Preview:** `pnpm preview`

### Caveats

- The `postinstall` script runs `wrangler types` to generate `worker-configuration.d.ts`. If you see missing Cloudflare type errors after install, re-run `pnpm run cf-typegen`.
- `pnpm.onlyBuiltDependencies` in `package.json` allows `esbuild`, `sharp`, and `workerd` to run their build scripts. Without this, the dev server will fail because `workerd` (the Cloudflare Workers runtime) won't be built.
- The dev server uses the Cloudflare Vite plugin which runs a local `workerd` instance — no Cloudflare account is needed for local development.
- No ESLint or Prettier scripts are configured in `package.json`; type-checking via `tsc --noEmit` is the primary lint-equivalent check.
- No automated test framework is configured in this project.
