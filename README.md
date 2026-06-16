# Arcado Springs — Land Development Demo

A static showcase site for the **Arcado Springs** master-planned mixed-use development on Arcado Road.

This is the public-facing concept demo (a shareable stakeholder preview). The full interactive
3D visualization is built in Unity 6 (HDRP) and is **not** part of this repo — HDRP cannot build
to WebGL, so the development is presented here through renders, a walkthrough video, and the site plan.

## Structure
- `index.html` — single-page showcase
- `styles.css` — styling
- `public/site-plan.jpg` — master site plan (Conception 1 & 2)

## To update
Swap the hero/gallery placeholders for real HDRP screenshots (put images in `public/`, point the
`<figure>`/`.hero-media` at them), embed a trimmed walkthrough MP4 in the `.video-slot`, and fill in
the real figures in the "At a glance" section.

## Deploy
Auto-deploys to Vercel on push to `main`.
