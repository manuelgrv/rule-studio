# Gestor de políticas · Sites demo

Single Sites application: React/Vinext/shadcn UI, authenticated per-viewer D1 workspaces, DuckDB-WASM synthetic data consolidation, and the existing Python compiler/interpreter through Pyodide.

`npm run dev` starts the local preview. Use the local sign-in link, then initialize your workspace. Run `npx wrangler d1 migrations apply DB --local --config wrangler.local.json` before saving drafts.

`node tests/wasm.mjs` tests actual WASM engines against 30,000 clients and 90,000 expected decisions. `node --experimental-strip-types tests/workflow.mts` tests workflow permissions and immutable versions. `node tests/api.mjs` tests the local API. `npx tsc --noEmit` and `npm run build` validate the application.

The role selector simulates personas within one real viewer's private workspace. It is not banking authorization. Semantic compilation happens client-side; production needs independent trusted validation. Runs are experimental and device-local; D1 persists authored documents and publication history. No FastAPI service is required.

Source assets are regenerated from the parent project's `scripts/prepare_web_demo.py`. Published archives contain only generated synthetic data. Python imports and arbitrary rule execution are rejected by the existing AST compiler.

WebMCP navigation is feature-detected; no supported live validation context was available during implementation. Browser UI interaction testing was not requested; engine, API, type and build checks were performed.
