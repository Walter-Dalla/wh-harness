# Pending

Open tasks of the repo's owner. Delete an item when it is done.

## Interactive flow page on GitHub Pages

The "How wh works" page (step-by-step of the agents and the files each one reads, writes, runs or deletes; today a claude.ai artifact, with a copy styled like the portfolio in `Walter-Dalla/portfolio` at `public/wh-harness/flow.html`) becomes a static file of this repo, published on GitHub Pages and embedded by `walterdalla.uk/projects/wh-harness` through an `<iframe>`. Updating the flow = a commit here; the portfolio does not redeploy. The portfolio side is the item "Fluxo do wh-harness embutido por iframe" of its `docs/PENDENCIAS.md`.

- Source: `site/flow.html`, one self-contained file (HTML + CSS + JS, no build), starting from the portfolio copy (portfolio tokens: IBM Plex Sans/Mono, dark `--bg #0b0d10`, light `#f7f6f2`, accent `#f5a524`); compare it with the artifact and keep the newer content. `site/index.html` redirects to `flow.html`; `site/.nojekyll`.
- Deploy: `.github/workflows/pages.yml`, on push to `main` with `paths: [site/**]` plus `workflow_dispatch`: `actions/upload-pages-artifact@v3` (`path: site`) and `actions/deploy-pages@v4` (`permissions: pages: write, id-token: write`). Owner action: Settings → Pages → Source = GitHub Actions. URL: `https://walter-dalla.github.io/wh-harness/flow.html`.
- Embed mode (`?embed=1`): hides the page's own header, theme toggle and outer padding. `?theme=dark|light` wins over `localStorage` and `prefers-color-scheme`. Listens to `message` `{type: "wh-flow:theme", theme}` only from `https://walterdalla.uk` (and `http://localhost:3000` for the portfolio's dev server). Posts `{type: "wh-flow:height", height}` to `parent` from a `ResizeObserver` on `document.body`. Opened directly, the page keeps working on its own.
- Language: the content is Portuguese only; `?lang=en` is ignored until an English copy of the strings exists (owner decision: translate or keep PT).
- Facts in sync: `tests/test_site_refs.py` checks that every repo path the page cites (`plugins/wh/...`, skills, agents, scripts) exists, like the section-reference tests, in the current CI. A PR that changes a skill, agent or script the page describes updates `site/flow.html` too (line in `CLAUDE.md`).
- Docs: `CLAUDE.md` and `README.md` point at `site/` and the Pages URL; `docs/MANUAL.md` links it. No plugin version bump (the plugin does not change).
- Acceptance: `python3 -m unittest discover -s tests`; after the merge, the URL answers 200 and the page renders inside an iframe on `walterdalla.uk` (GitHub Pages sends no `X-Frame-Options`).
