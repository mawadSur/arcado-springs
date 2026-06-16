# Arcado Springs — Land Development Preview

The public-facing concept site for the **Arcado Springs** master-planned mixed-use development
on Arcado Road (shops, dining, and walkable streets, beside the Legends of Parkview subdivision).
It's a shareable preview for residents, local businesses, and planning stakeholders.

The full interactive 3D walkthrough is built in **Unity 6 (HDRP)**. HDRP cannot build to WebGL,
so the playable in-browser build is a separate effort (see **`WEBGL_BUILD_GUIDE.md`**); this site
auto-detects that build when it's dropped in and otherwise shows the plan-based preview honestly.

## Structure
- `public/index.html` — single-page site (hero, walkthrough player, gallery, master plan, two
  conceptions, specs, "why it helps the community", feedback form)
- `public/styles.css` — styling (Fraunces / Inter / IBM Plex Mono; warm civic palette)
- `public/main.js` — nav, reveal animations, lightbox, site-plan pan/zoom, and the WebGL build
  auto-loader (probes `public/unity-build/Build/`, falls back to the plan preview if absent)
- `public/site-plan.jpg` — colored master site plan (Conception 1 & 2)
- `public/screenshots/` — dimensioned CAD plan drawings
- `public/unity-build/` — drop the exported Unity WebGL build here (auto-detected; see its README)
- `public/vercel.json` — static config + WASM/Brotli MIME headers for the future WebGL build
- `WEBGL_BUILD_GUIDE.md` — honest, step-by-step path to a real browser build (HDRP → URP → WebGL)

## To add the real 3D experience
1. Capture a few in-engine frames from the Unity scene and drop them in `public/screenshots/`,
   then point the hero / gallery `<img src>` at them for a stronger first impression.
2. Produce the WebGL build per `WEBGL_BUILD_GUIDE.md` and place the output in
   `public/unity-build/`. The player upgrades itself — no HTML edits needed.

## Deploy
Production branch is **`master`**.
- **Git:** `git push origin master` (if the Vercel project is connected to the GitHub repo, this
  auto-deploys).
- **Vercel CLI:** from the repo root, `vercel login` then `vercel --prod` (the project is already
  linked via `.vercel/project.json`).

Live at **https://arcado-springs.vercel.app**.
