# Arcado Springs — WebGL Build Guide

How to produce an in-browser WebGL build of **this** Unity project and drop it into the
landing page so the player section goes from the screenshot-tour fallback to a real,
playable walkthrough.

---

## The honest constraint: this project is HDRP, and HDRP cannot build to WebGL

This project (`/mnt/c/Users/Mohammed Awad/Arcado Rd`) is:

- **Unity `6000.1.4f1`** (Unity 6)
- **High Definition Render Pipeline (HDRP) `17.1.0`** — see `Packages/manifest.json`:
  `com.unity.render-pipelines.high-definition` and `...high-definition-config`
- **Linear** color space (`ProjectSettings/ProjectSettings.asset` → `m_ActiveColorSpace: 1`)
- Main / walkthrough scene: **`Assets/withmap.unity`** (the one enabled in Build Settings today)

**HDRP does not support the WebGL build target.** HDRP targets compute-shader-capable
desktop/console GPU APIs (DX12, Vulkan, Metal). WebGL runs on WebGL 2.0 (GLES 3.0), which
HDRP's lighting/compute paths do not support. If you switch the platform to WebGL with HDRP
active, the build will either be disabled in the Build Profiles window or fail at build time.
There is no "just flip a switch" path — **you must move the scene onto URP first.**

You have two routes. Pick one before doing anything in the WebGL section below.

### Route A — Convert the whole project to URP (Render Pipeline Converter)

Best if you are OK with the desktop/HDRP look diverging from web, or you want a single
pipeline going forward. This rewrites materials project-wide.

1. **Back up the project first** (copy the folder, or commit). The converter edits materials
   in place and is not cleanly reversible.
2. Window ▸ Package Manager ▸ install **Universal RP**
   (`com.unity.render-pipelines.universal`). It is **not currently installed** — only HDRP
   is in `Packages/manifest.json`.
3. Create a URP asset: Assets ▸ Create ▸ Rendering ▸ **URP Asset (with Universal Renderer)**.
4. Edit ▸ Project Settings ▸ **Graphics** → set the Scriptable Render Pipeline Settings to
   the new URP asset. Also set it under **Quality** for each level you ship.
5. Window ▸ Rendering ▸ **Render Pipeline Converter**. Select **"Convert Built-in/HDRP to
   URP"** workflow → enable "Material Upgrade" (and the others it offers) → **Initialize and
   Convert**.
6. Expect manual cleanup: HDRP-only materials (Lit with HDRP features), volume overrides
   (HDRP `Volume` profiles, exponential fog, ray tracing, screen-space lighting), decals,
   and any HDRP-specific lighting will not survive 1:1. Re-light the scene for URP and
   replace anything pink/magenta (pink = unconverted material).
7. Remove the HDRP packages from `Packages/manifest.json` once converted, so the project
   stops pulling HDRP shaders.

### Route B — Dedicated URP/WebGL build variant of the walkthrough scene (recommended for the web demo)

Best if you want to **keep the HDRP desktop project intact** and only ship a trimmed,
web-friendly version of the walkthrough. This is the recommended route because the desktop
HDRP build (the realism work, the drivable car, NPCs) stays untouched.

1. **Back up / branch first.**
2. Make a copy of the scene: duplicate `Assets/withmap.unity` →
   `Assets/withmap_WebGL.unity`. Do all web work in the copy.
3. Install **Universal RP** (as in Route A, step 2) and create a URP asset + Universal
   Renderer. Assign it under Graphics + Quality.
4. Open `withmap_WebGL.unity` and strip / swap for the web target:
   - Replace HDRP materials with URP/Lit (run the Render Pipeline Converter scoped to the
     materials this scene uses, or swap by hand).
   - Remove HDRP `Volume` components, HDRP-only post, ray tracing, high-cost shadows.
   - Cut polygon/texture budget aggressively (WebGL ships everything to the browser):
     reduce tree/Nature Renderer density, bake lightmaps, drop 4K textures to 1–2K, disable
     realtime GI.
   - Decide what the web walkthrough is — e.g. a first-person walk camera. Keep the PROMETEO
     car only if it still drives cheaply on URP; otherwise ship the walk camera alone.
5. In Build Settings / Build Profiles, the **scene list for the WebGL profile** should be
   **`Assets/withmap_WebGL.unity`** only (not the HDRP `withmap.unity`).

> Either route ends at the same place: a project whose active render pipeline is **URP**,
> with a web-ready scene. Everything below assumes you are at that point.

---

## 1. Install the WebGL Build Support module (Unity Hub)

1. Open **Unity Hub** ▸ **Installs**.
2. Find **`6000.1.4f1`** ▸ gear / ⋮ ▸ **Add modules**.
3. Tick **WebGL Build Support** ▸ **Install**. (This is per-editor-version; it is not
   installed by default.)
4. Restart the editor if it was open.

---

## 2. Switch the active platform to WebGL

1. File ▸ **Build Settings** (or **Build Profiles** in Unity 6).
2. Select **Web / WebGL** in the platform list ▸ **Switch Platform**.
   - This re-imports assets for WebGL and can take a while on a project this size.
   - If WebGL is greyed out / "not supported" here, your active pipeline is still HDRP — go
     back and finish Route A or B.

---

## 3. Player Settings for the web build

Edit ▸ Project Settings ▸ **Player** ▸ (WebGL tab):

- **Publishing Settings ▸ Compression Format:**
  - **Brotli** — smallest payload, best for the deployed Vercel site. Requires the server to
    send `Content-Encoding: br` (Vercel does for `.br` assets, and Unity also ships a
    decompression fallback). **Use this for production.**
  - **Disabled** — use this for **quick local testing** (open via a simple static server
    with no special headers). Larger files, but zero server-config friction.
  - Avoid **Gzip** unless your host can't do Brotli.
  - Also enable **Decompression Fallback** if you serve from a host that can't set the
    `Content-Encoding` header — it makes the build self-decompress in JS.
- **Color Space:** this project is **Linear** (`m_ActiveColorSpace: 1`). WebGL 2.0 supports
  Linear, so you can keep it. If you ever target the old WebGL 1.0 path you'd be forced to
  Gamma — not relevant here, keep **Linear**.
- **Other Settings ▸ Rendering:** confirm **WebGL 2.0** is in the Graphics APIs list (drop
  WebGL 1.0). Disable features the scene doesn't need to shrink the build.
- Optional: set **Resolution and Presentation** to a default canvas, but the landing page
  controls sizing via CSS, so this is cosmetic.

---

## 4. Confirm the scene in Build Settings

In Build Settings / the WebGL Build Profile, **Scenes In Build** should contain exactly the
scene you want to ship:

- **Route A:** `Assets/withmap.unity` (now URP).
- **Route B:** `Assets/withmap_WebGL.unity` (the URP/web copy). Make sure the HDRP
  `withmap.unity` is **unchecked / removed** from the WebGL profile.

The scene at the top of the enabled list is the one that loads first.

---

## 5. Build — OUTPUT DIRECTORY MUST BE EXACTLY THIS

Click **Build** and choose this output folder:

```
/mnt/c/Users/Mohammed Awad/Arcado Rd/web/unity-build/
```

> The landing page auto-detects the build at `web/unity-build/Build/`. If you build anywhere
> else, the page stays on the screenshot-tour fallback. Do not rename the `Build/` subfolder.

Let it finish (WebGL builds are slow). **Do not** use "Build And Run" for the final artifact
— that drops it in a temp location; use plain **Build** pointed at the folder above.

---

## 6. Expected output

After a successful build, `web/unity-build/` should look like:

```
web/unity-build/
├── index.html              ← Unity's own test page (the landing page does NOT use this)
└── Build/
    ├── unity-build.loader.js      ← the loader the landing page looks for
    ├── unity-build.framework.js   (or .framework.js.br / .framework.js.unityweb)
    ├── unity-build.wasm           (or .wasm.br / .wasm.unityweb)
    └── unity-build.data           (or .data.br / .data.unityweb)
```

Notes:

- The **base filename** matches the build folder name. If your folder is `unity-build`, the
  loader is `unity-build.loader.js`. If you named it differently, the loader name changes to
  match — **the landing page's loader.js auto-discovers the `*.loader.js` regardless of its
  exact name**, so either works, but keeping it `unity-build` is simplest.
- With **Brotli** the heavy files gain a `.br` suffix (`*.wasm.br`, `*.data.br`,
  `*.framework.js.br`). With **Disabled** there is no suffix. The `*.loader.js` is always
  uncompressed plain JS — that's the file the page probes for.
- A `StreamingAssets/` or `TemplateData/` folder may also appear; harmless, leave them.

---

## 7. How the landing page picks it up (no code change needed)

The player section in `index.html` runs `loader.js` on load. It:

1. `fetch(..., { method: 'HEAD' })` probes `unity-build/Build/unity-build.loader.js`.
2. **If found** → injects that loader script, calls `createUnityInstance(...)` into the 16:9
   canvas, and shows the **Launch** overlay. The user clicks Launch to start the real build.
3. **If absent** (404 / network error) → leaves the **screenshot-tour fallback** visible with
   the *"Interactive walkthrough — live build deploying soon"* badge. No fake "playable"
   claim is shown when there is no build.

So the deploy flow is just: build into `web/unity-build/`, commit/upload that folder, redeploy.
Nothing in `index.html` has to change.

---

## 8. Local test before deploying

From the `web/` directory, serve over HTTP (WebGL will not run from a `file://` URL):

```bash
cd "/mnt/c/Users/Mohammed Awad/Arcado Rd/web"
python3 -m http.server 8080
# open http://localhost:8080/  → player section should now show Launch instead of the fallback
```

If you built with **Brotli** and the browser console complains about decompression / MIME
type on a plain `http.server`, either (a) rebuild with **Compression = Disabled** for local
testing, or (b) enable **Decompression Fallback** in Player Settings, or (c) test on Vercel
where the headers are set correctly.

---

## 9. Deploy

Copy / commit the populated `web/unity-build/` folder alongside `index.html` and redeploy the
static site (the showcase currently deploys via Vercel CLI). Once `unity-build/Build/` is live,
the player section upgrades itself to the real walkthrough automatically.
