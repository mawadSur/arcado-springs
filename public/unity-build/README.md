# unity-build/ — drop your Unity WebGL build output here

This folder is the **auto-detected mount point** for the in-browser walkthrough on the
Arcado Springs landing page.

## What goes here

Point Unity's WebGL **Build** output directory at this exact folder:

```
/mnt/c/Users/Mohammed Awad/Arcado Rd/web/unity-build/
```

After a successful build this folder should contain:

```
unity-build/
├── index.html          (Unity's own test page — not used by the landing page)
└── Build/
    ├── unity-build.loader.js      ← the landing page probes for this
    ├── unity-build.framework.js   (or .framework.js.br)
    ├── unity-build.wasm           (or .wasm.br)
    └── unity-build.data           (or .data.br)
```

## How detection works

On page load, the landing page's `loader.js` sends a `HEAD` request to
`unity-build/Build/unity-build.loader.js`:

- **Present** → the Unity instance loads into the 16:9 canvas with a **Launch** overlay.
- **Absent** (this folder still empty) → the page shows the **screenshot-tour fallback** with
  a *"live build deploying soon"* badge. No fake "playable" claim is made.

So while this folder is empty, the site is honest and still works. Drop a real build in,
redeploy, and the player upgrades itself — no edits to `index.html` required.

## Important

- This project is **HDRP**, which **cannot** build to WebGL. You must first move the
  walkthrough scene to **URP** (Render Pipeline Converter) or build a dedicated URP/WebGL
  scene variant. See **`../WEBGL_BUILD_GUIDE.md`** for the full, honest steps.
- Keep the `Build/` subfolder name exactly as Unity emits it.
- The `*.loader.js` filename can differ if you name the build folder differently — the page
  auto-discovers it, but `unity-build` is the simplest name to keep.
