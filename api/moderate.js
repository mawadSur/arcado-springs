// api/moderate.js
// Pre-moderated public comment board — token-gated admin endpoint.
//
// Required environment variables (set in the Vercel project):
//   BLOB_READ_WRITE_TOKEN  — read/write token for the linked Vercel Blob store.
//                            Auto-read by the @vercel/blob SDK; never hard-code it.
//   MODERATION_TOKEN       — admin secret. Requests must present it via the
//                            `token` query param OR the `x-moderation-token`
//                            header. If this env var is unset, all access is denied.
//
// GET  /api/moderate?token=... -> HTML moderation queue (approve/reject buttons)
// POST /api/moderate           -> action=approve|reject, id=<id>, token=<token>
//
// Storage model matches api/comments.js:
//   comments/approved.json — JSON array of approved comments
//   comments/pending.json  — JSON array of pending comments
// Comment shape: { id, name, role, comment, ts }

import { put, list } from '@vercel/blob';

const APPROVED = 'comments/approved.json';
const PENDING = 'comments/pending.json';

// --- Blob helpers (kept self-contained; mirror api/comments.js) ---

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

async function writeList(pathname, arr) {
  await put(pathname, JSON.stringify(arr), {
    access: 'public',
    addRandomSuffix: false,
    contentType: 'application/json',
    allowOverwrite: true,
    cacheControlMaxAge: 0, // minimize CDN caching of this mutable list
  });
}

// --- Auth ---

// Constant-time-ish comparison that does not short-circuit on length.
function safeEqual(a, b) {
  const sa = typeof a === 'string' ? a : '';
  const sb = typeof b === 'string' ? b : '';
  if (sa.length !== sb.length) return false;
  let diff = 0;
  for (let i = 0; i < sa.length; i++) {
    diff |= sa.charCodeAt(i) ^ sb.charCodeAt(i);
  }
  return diff === 0;
}

function tokenFrom(req, body) {
  return (
    (req.query && req.query.token) ||
    (req.headers && req.headers['x-moderation-token']) ||
    (body && body.token) ||
    ''
  );
}

function authorized(token) {
  const expected = process.env.MODERATION_TOKEN;
  if (!expected) return false; // env unset -> deny everything
  return safeEqual(String(token), expected);
}

// --- Body parsing (handle form-encoded and JSON) ---

async function readBody(req) {
  if (req.body && typeof req.body === 'object' && !Buffer.isBuffer(req.body)) {
    return req.body;
  }

  let raw;
  if (typeof req.body === 'string') {
    raw = req.body;
  } else if (Buffer.isBuffer(req.body)) {
    raw = req.body.toString('utf8');
  } else {
    const chunks = [];
    for await (const chunk of req) {
      chunks.push(typeof chunk === 'string' ? Buffer.from(chunk) : chunk);
    }
    raw = Buffer.concat(chunks).toString('utf8');
  }

  raw = (raw || '').trim();
  if (!raw) return {};

  const ctype = (req.headers && req.headers['content-type']) || '';
  if (ctype.includes('application/json')) {
    try {
      return JSON.parse(raw);
    } catch {
      return {};
    }
  }
  if (ctype.includes('application/x-www-form-urlencoded')) {
    return Object.fromEntries(new URLSearchParams(raw));
  }

  // Unknown content type: try JSON, then fall back to form-encoded parsing.
  try {
    return JSON.parse(raw);
  } catch {
    return Object.fromEntries(new URLSearchParams(raw));
  }
}

// --- HTML rendering ---

function escapeHtml(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function renderPage(pending, approvedCount, token) {
  const tokenAttr = escapeHtml(token);
  const actionUrl = '/api/moderate?token=' + encodeURIComponent(token);
  const cards = pending
    .map((c) => {
      const name = escapeHtml(c.name) || '<em>(no name)</em>';
      const role = escapeHtml(c.role);
      const ts = escapeHtml(c.ts);
      const comment = escapeHtml(c.comment);
      const id = escapeHtml(c.id);
      return `
      <div class="card">
        <div class="meta"><strong>${name}</strong> &middot; <span class="role">${role}</span> &middot; <span class="ts">${ts}</span></div>
        <div class="comment">${comment}</div>
        <div class="actions">
          <form method="POST" action="${escapeHtml(actionUrl)}">
            <input type="hidden" name="action" value="approve">
            <input type="hidden" name="id" value="${id}">
            <input type="hidden" name="token" value="${tokenAttr}">
            <button class="approve" type="submit">Approve</button>
          </form>
          <form method="POST" action="${escapeHtml(actionUrl)}">
            <input type="hidden" name="action" value="reject">
            <input type="hidden" name="id" value="${id}">
            <input type="hidden" name="token" value="${tokenAttr}">
            <button class="reject" type="submit">Reject</button>
          </form>
        </div>
      </div>`;
    })
    .join('\n');

  return `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Comment Moderation</title>
<style>
  body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; padding: 1.5rem; background: #f5f5f4; color: #1c1917; }
  h1 { font-size: 1.4rem; margin: 0 0 .25rem; }
  .counts { color: #57534e; margin-bottom: 1.5rem; font-size: .95rem; }
  .empty { color: #78716c; font-style: italic; }
  .card { background: #fff; border: 1px solid #e7e5e4; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; max-width: 720px; }
  .meta { font-size: .85rem; color: #57534e; margin-bottom: .5rem; }
  .role { text-transform: capitalize; }
  .comment { white-space: pre-wrap; word-break: break-word; margin-bottom: .75rem; line-height: 1.45; }
  .actions { display: flex; gap: .5rem; }
  .actions form { margin: 0; }
  button { border: 0; border-radius: 6px; padding: .45rem .9rem; font-size: .9rem; cursor: pointer; color: #fff; }
  button.approve { background: #15803d; }
  button.reject { background: #b91c1c; }
</style>
</head>
<body>
  <h1>Comment Moderation</h1>
  <div class="counts">${pending.length} pending &middot; ${approvedCount} approved</div>
  ${pending.length ? cards : '<p class="empty">No pending comments.</p>'}
</body>
</html>`;
}

export default async function handler(req, res) {
  try {
    if (req.method === 'GET') {
      const token = tokenFrom(req, {});
      if (!authorized(token)) {
        res.status(401).setHeader('Content-Type', 'text/plain');
        res.send('Unauthorized');
        return;
      }
      const [pending, approved] = await Promise.all([
        readList(PENDING),
        readList(APPROVED),
      ]);
      res.status(200).setHeader('Content-Type', 'text/html; charset=utf-8');
      res.send(renderPage(pending, approved.length, token));
      return;
    }

    if (req.method === 'POST') {
      const body = await readBody(req);
      const token = tokenFrom(req, body);
      if (!authorized(token)) {
        res.status(401).setHeader('Content-Type', 'text/plain');
        res.send('Unauthorized');
        return;
      }

      const action = body.action;
      const id = body.id;

      if ((action === 'approve' || action === 'reject') && id) {
        if (action === 'approve') {
          const [pending, approved] = await Promise.all([
            readList(PENDING),
            readList(APPROVED),
          ]);
          const idx = pending.findIndex((c) => c.id === id);
          if (idx !== -1) {
            const [item] = pending.splice(idx, 1);
            approved.unshift(item);
            await Promise.all([
              writeList(PENDING, pending),
              writeList(APPROVED, approved),
            ]);
          }
        } else {
          const pending = await readList(PENDING);
          const next = pending.filter((c) => c.id !== id);
          if (next.length !== pending.length) {
            await writeList(PENDING, next);
          }
        }
      }

      res.status(302).setHeader(
        'Location',
        '/api/moderate?token=' + encodeURIComponent(token)
      );
      res.end();
      return;
    }

    res.setHeader('Allow', 'GET, POST');
    res.status(405).setHeader('Content-Type', 'text/plain');
    res.send('Method Not Allowed');
  } catch (e) {
    console.error('moderate handler error', e);
    res.status(500).setHeader('Content-Type', 'text/plain');
    res.send('server error');
  }
}
