# Higgsfield AI image prompts — Arcado Springs lifestyle imagery

Generate these on **higgsfield.ai**, then save the results into **`public/lifestyle/`** with the
exact filenames below. The site auto-detects them — no code changes needed. Until a file exists,
the page shows a tasteful "AI preview coming soon" placeholder (and the hero falls back to the
site plan).

> Keep the look consistent: **photorealistic architectural visualization, warm golden-hour light,
> a walkable suburban town center, lush landscaping, a diverse and friendly community.** Add
> `no text, no watermark, no logos` to every prompt. Photoreal model, high detail.

| Save as | Aspect ratio | Use on page |
|---|---|---|
| `public/lifestyle/hero.jpg` | 16:9 (≈2400×1350) | Full-bleed hero |
| `public/lifestyle/walking.jpg` | 16:9 (≈1600×900) | Gallery — wide |
| `public/lifestyle/dining.jpg` | 4:3 (≈1200×900) | Gallery |
| `public/lifestyle/shopping.jpg` | 4:3 (≈1200×900) | Gallery |

---

## 1. `hero.jpg` — establishing street shot (16:9)
> Photorealistic architectural visualization, golden hour, a vibrant walkable suburban town-center
> main street, tree-lined sidewalks, modern low-rise brick-and-glass retail storefronts with awnings
> and outdoor café seating, warm string lights overhead, diverse families and young professionals
> strolling and chatting, lush green landscaping and planters, a central plaza in the distance, eye-level
> 35mm lens, soft warm sunlight, shallow depth of field, cinematic, inviting community atmosphere,
> ultra-detailed, no text, no watermark, no logos.

## 2. `walking.jpg` — people walking the main street (16:9)
> Photorealistic, late-afternoon golden light, neighbors of different ages and backgrounds walking and
> biking along a tree-lined main street of a new mixed-use town center, wide landscaped sidewalks, a
> marked bicycle lane, storefronts with greenery, relaxed pedestrians, a parent with a stroller, a couple
> holding hands, candid lifestyle photography, 35mm, warm tones, shallow depth of field, ultra-detailed,
> no text, no watermark, no logos.

## 3. `dining.jpg` — outdoor patio dining (4:3)
> Photorealistic, warm early evening, people dining at outdoor patio tables outside a cozy restaurant in
> a walkable town center, string lights and umbrellas, plants and wood-and-steel furniture, friends
> laughing over dinner, a server bringing food, soft bokeh background of lit storefronts, inviting and
> lively, 50mm lens, shallow depth of field, ultra-detailed, no text, no watermark, no logos.

## 4. `shopping.jpg` — shopping the retail frontage (4:3)
> Photorealistic, bright pleasant daytime, shoppers with bags browsing attractive boutique storefronts
> along the retail frontage of a new suburban town center, large clean shop windows, awnings, benches and
> planters, a family window-shopping, a young woman carrying shopping bags, welcoming and upscale-casual,
> 35mm lens, natural light, ultra-detailed, no text, no watermark, no logos.

---

### Tips
- Generate a few variations of each and pick the most natural; avoid frames with garbled text on signage
  (crop it out or choose another).
- Optimize before committing (aim < ~400 KB each; JPG quality ~80) so the page stays fast.
- Once `hero.jpg` exists, optionally update the social preview: set `og:image` / `twitter:image` in
  `public/index.html` to `https://arcado-springs.vercel.app/lifestyle/hero.jpg`.
