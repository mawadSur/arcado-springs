// api/comments.js
// Pre-moderated public comment board — public endpoint.
//
// Required environment variables (set in the Vercel project):
//   BLOB_READ_WRITE_TOKEN  — read/write token for the linked Vercel Blob store.
//                            Auto-read by the @vercel/blob SDK; never hard-code it.
//   MODERATION_TOKEN       — admin secret used by api/moderate.js (not used here,
//                            documented for completeness of the feature).
//
// Storage model (two stable public JSON blobs, overwritten in place):
//   comments/approved.json — JSON array of approved comments (public)
//   comments/pending.json  — JSON array of pending comments (moderation queue)
// Comment shape: { id, name, role, comment, ts }  (ts = new Date().toISOString())

import { put, list } from '@vercel/blob';

const APPROVED = 'comments/approved.json';
const PENDING = 'comments/pending.json';

const MAX_PENDING = 1000;
const ROLES = ['resident', 'business', 'planner'];

// Read a JSON-array blob by exact pathname. Returns [] when it does not exist
// yet (first run) or on any read/parse error.
async function readList(pathname) {
  try {
    const { blobs } = await list({ prefix: pathname, limit: 1 });
    if (!blobs || blobs.length === 0) return [];
    // Blob public URLs are CDN-cached (default 30 days) at a STABLE pathname, so
    // a plain re-fetch after an overwrite returns stale content. Bust the CDN
    // cache key with a unique query param so every read gets the latest version.
    const fresh = blobs[0].url + (blobs[0].url.includes('?') ? '&' : '?') + '_ts=' + Date.now();
    const r = await fetch(fresh, { cache: 'no-store' });
    if (!r.ok) return [];
    const data = await r.json();
    return Array.isArray(data) ? data : [];
  } catch (e) {
    console.error('readList error', pathname, e);
    return [];
  }
}

// Overwrite a JSON-array blob at a stable pathname (no random suffix).
async function writeList(pathname, arr) {
  await put(pathname, JSON.stringify(arr), {
    access: 'public',
    addRandomSuffix: false,
    contentType: 'application/json',
    allowOverwrite: true,
    cacheControlMaxAge: 0, // minimize CDN caching of this mutable list
  });
}

// Normalize a stored record to the public comment shape.
function toPublic(c) {
  return {
    id: c.id,
    name: c.name,
    role: c.role,
    comment: c.comment,
    ts: c.ts,
  };
}

// Robustly obtain a parsed JSON body from a Vercel Node request.
async function readBody(req) {
  if (req.body && typeof req.body === 'object') return req.body;
  if (typeof req.body === 'string' && req.body.length) {
    try {
      return JSON.parse(req.body);
    } catch {
      return {};
    }
  }
  // Fall back to reading the raw request stream.
  const chunks = [];
  for await (const chunk of req) {
    chunks.push(typeof chunk === 'string' ? Buffer.from(chunk) : chunk);
  }
  const raw = Buffer.concat(chunks).toString('utf8').trim();
  if (!raw) return {};
  try {
    return JSON.parse(raw);
  } catch {
    return {};
  }
}

function newId() {
  return (
    globalThis.crypto?.randomUUID?.() ??
    String(Date.now()) + Math.random().toString(16).slice(2)
  );
}

export default async function handler(req, res) {
  try {
    if (req.method === 'GET') {
      const approved = await readList(APPROVED);
      // Stored newest-first; expose mapped to the public shape, newest first.
      const comments = approved.map(toPublic);
      res.setHeader('Cache-Control', 'public, s-maxage=30, max-age=30');
      res.status(200).json({ comments });
      return;
    }

    if (req.method === 'POST') {
      const body = await readBody(req);

      // Honeypot: any non-empty website field means a bot. Silently drop.
      if (typeof body.website === 'string' && body.website.trim().length > 0) {
        res.status(200).json({ ok: true, pending: true });
        return;
      }

      // Validate comment (required, 4..2000 after trim).
      const rawComment = typeof body.comment === 'string' ? body.comment.trim() : '';
      if (rawComment.length < 4 || rawComment.length > 2000) {
        res.status(400).json({ error: 'comment must be between 4 and 2000 characters' });
        return;
      }

      // name optional, trimmed, capped at 80 chars.
      let name = typeof body.name === 'string' ? body.name.trim().slice(0, 80) : '';

      // role must be one of the allowed values; default 'resident'.
      let role = typeof body.role === 'string' ? body.role : '';
      if (!ROLES.includes(role)) role = 'resident';

      // Defense-in-depth: strip angle brackets from user-rendered text.
      const strip = (s) => s.replace(/[<>]/g, '');
      name = strip(name);
      const comment = strip(rawComment);

      const record = {
        id: newId(),
        name,
        role,
        comment,
        ts: new Date().toISOString(),
      };

      const pending = await readList(PENDING);
      if (pending.length >= MAX_PENDING) {
        res.status(429).json({ error: 'queue full' });
        return;
      }
      pending.unshift(record); // newest first
      await writeList(PENDING, pending);

      res.status(200).json({ ok: true, pending: true });
      return;
    }

    res.setHeader('Allow', 'GET, POST');
    res.status(405).json({ error: 'method not allowed' });
  } catch (e) {
    console.error('comments handler error', e);
    res.status(500).json({ error: 'server error' });
  }
}
