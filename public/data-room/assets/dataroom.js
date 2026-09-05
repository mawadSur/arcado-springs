/* Arcado Springs data room.
   Client-side filtering over the index, a lightbox for drawings and renderings, and
   AES-256-GCM unlocking of the owner-only shelf. The key never touches the server: it
   travels in the URL fragment (or is pasted) and decrypts ciphertext shipped with the page.
   Confidential files are separate .bin blobs decrypted on demand and opened as blob: URLs. */
(function () {
  'use strict';

  var $ = function (s, r) { return (r || document).querySelector(s); };
  var $$ = function (s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); };

  /* ------------------------------------------------------------------ filtering */
  var q = '', cats = new Set();

  function haystack(el) {
    if (!el._hay) el._hay = (el.getAttribute('data-search') || el.textContent).toLowerCase();
    return el._hay;
  }

  function apply() {
    var shown = 0;
    $$('[data-item]').forEach(function (el) {
      var okQ = !q || haystack(el).indexOf(q) !== -1;
      var okC = !cats.size || cats.has(el.getAttribute('data-cat'));
      var hide = !(okQ && okC);
      el.classList.toggle('is-hidden', hide);
      if (!hide) shown++;
    });
    $$('[data-sec]').forEach(function (sec) {
      var any = $$('[data-item]', sec).some(function (el) { return !el.classList.contains('is-hidden'); });
      sec.classList.toggle('is-empty', !any);
      var n = $('[data-secn]', sec);
      if (n) n.textContent = $$('[data-item]', sec).filter(function (el) {
        return !el.classList.contains('is-hidden');
      }).length + ' items';
    });
    var c = $('#count');
    if (c) c.textContent = (q || cats.size) ? shown + ' of ' + $$('[data-item]').length + ' shown' : $$('[data-item]').length + ' items';
    var e = $('#empty');
    if (e) e.hidden = shown > 0;
  }

  var search = $('#q');
  if (search) {
    var t;
    search.addEventListener('input', function () {
      clearTimeout(t);
      t = setTimeout(function () { q = search.value.trim().toLowerCase(); apply(); }, 90);
    });
    search.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { search.value = ''; q = ''; apply(); }
    });
  }
  var clear = $('#q-clear');
  if (clear) clear.addEventListener('click', function () {
    search.value = ''; q = ''; apply(); search.focus();
  });

  document.addEventListener('click', function (e) {
    var chip = e.target.closest('.chip[data-cat]');
    if (!chip) return;
    var c = chip.getAttribute('data-cat');
    if (c === '*') { cats.clear(); $$('.chip[data-cat]').forEach(function (x) { x.setAttribute('aria-pressed', x === chip); }); }
    else {
      var on = chip.getAttribute('aria-pressed') === 'true';
      if (on) cats.delete(c); else cats.add(c);
      chip.setAttribute('aria-pressed', String(!on));
      var all = $('.chip[data-cat="*"]');
      if (all) all.setAttribute('aria-pressed', String(cats.size === 0));
    }
    apply();
  });

  // "/" focuses search
  document.addEventListener('keydown', function (e) {
    if (e.key === '/' && !/^(INPUT|TEXTAREA)$/.test(document.activeElement.tagName)) {
      e.preventDefault(); search && search.focus();
    }
  });

  /* ------------------------------------------------------------------ lightbox */
  var lb = $('#lb'), lbImg = $('#lb-img'), lbCap = $('#lb-cap'), lastFocus = null;

  function openLb(src, cap) {
    if (!lb) return;
    lastFocus = document.activeElement;
    lbImg.src = src; lbImg.alt = cap || '';
    lbCap.innerHTML = (cap || '') + ' <a href="' + src + '" target="_blank" rel="noopener">open full size &rarr;</a>';
    lb.hidden = false;
    document.body.style.overflow = 'hidden';
    $('.lb-x', lb).focus();
  }
  function closeLb() {
    if (!lb || lb.hidden) return;
    lb.hidden = true; lbImg.src = ''; document.body.style.overflow = '';
    lastFocus && lastFocus.focus();
  }
  document.addEventListener('click', function (e) {
    var trig = e.target.closest('[data-lb]');
    if (trig) { e.preventDefault(); openLb(trig.getAttribute('data-lb'), trig.getAttribute('data-cap')); return; }
    if (e.target.closest('[data-lb-close]')) closeLb();
  });
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeLb(); });

  /* ------------------------------------------------------------------ vault */
  var KEY = null;                 // CryptoKey once unlocked
  var blobCache = Object.create(null);

  function b64ToBytes(b64) {
    var bin = atob(b64), u = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i);
    return u;
  }
  function b64urlToBytes(s) {
    s = s.replace(/-/g, '+').replace(/_/g, '/');
    while (s.length % 4) s += '=';
    return b64ToBytes(s);
  }

  function msg(text, cls) {
    var m = $('#vault-msg');
    if (m) { m.textContent = text; m.className = 'vault-msg ' + (cls || ''); }
  }

  async function unlock(rawKey) {
    var payload = $('#vault-payload');
    if (!payload) return false;
    var data = JSON.parse(payload.textContent);
    var key;
    try {
      key = await crypto.subtle.importKey('raw', rawKey, 'AES-GCM', false, ['decrypt']);
    } catch (err) { msg('That key is not a valid 256-bit AES key.', 'err'); return false; }
    var plain;
    try {
      plain = await crypto.subtle.decrypt(
        { name: 'AES-GCM', iv: b64ToBytes(data.iv) }, key, b64ToBytes(data.ct));
    } catch (err) { msg('Wrong key — nothing decrypted.', 'err'); return false; }

    KEY = key;
    var body = $('#vault-body');
    body.innerHTML = new TextDecoder().decode(plain);
    $('#vault-gate').hidden = true;
    $('#vault-open').hidden = false;
    msg('', '');
    apply();
    return true;
  }

  var form = $('#vault-form');
  if (form) form.addEventListener('submit', async function (e) {
    e.preventDefault();
    var btn = $('#vault-go'), val = $('#vault-key').value.trim();
    var m = val.match(/#?k=([A-Za-z0-9_-]+)/);
    if (m) val = m[1];
    if (!val) { msg('Paste the key, or the whole owner link.', 'err'); return; }
    btn.disabled = true; msg('Decrypting…');
    var bytes;
    try { bytes = b64urlToBytes(val); } catch (err) { msg('That does not look like a key.', 'err'); btn.disabled = false; return; }
    if (bytes.length !== 32) { msg('A key is 32 bytes (43 characters); that one is ' + bytes.length + '.', 'err'); btn.disabled = false; return; }
    await unlock(bytes);
    btn.disabled = false;
  });

  /* confidential file link -> fetch ciphertext, decrypt, open as a blob */
  document.addEventListener('click', async function (e) {
    var a = e.target.closest('[data-enc]');
    if (!a) return;
    e.preventDefault();
    if (!KEY) { msg('Unlock the shelf first.', 'err'); return; }
    var path = a.getAttribute('data-enc'), mime = a.getAttribute('data-mime') || 'text/html';
    if (blobCache[path]) { window.open(blobCache[path], '_blank', 'noopener'); return; }

    // open the tab synchronously — popup blockers reject a window.open after an await
    var win = window.open('', '_blank');
    if (win) win.document.write('<title>Decrypting…</title><body style="font:15px system-ui;padding:40px;color:#5C6355">Decrypting…</body>');
    var label = a.textContent;
    a.textContent = 'Decrypting…';
    try {
      var res = await fetch(path);
      if (!res.ok) throw new Error(res.status);
      var buf = new Uint8Array(await res.arrayBuffer());
      var plain = await crypto.subtle.decrypt(
        { name: 'AES-GCM', iv: buf.slice(0, 12) }, KEY, buf.slice(12));
      var url = URL.createObjectURL(new Blob([plain], { type: mime }));
      blobCache[path] = url;
      if (win) win.location = url; else window.open(url, '_blank', 'noopener');
    } catch (err) {
      if (win) win.close();
      msg('Could not decrypt ' + path + ' (' + err.message + ').', 'err');
    } finally {
      a.textContent = label;
    }
  });

  /* auto-unlock from the fragment, then scrub it from the address bar */
  (async function () {
    var m = (location.hash || '').match(/k=([A-Za-z0-9_-]+)/);
    if (!m) return;
    var bytes;
    try { bytes = b64urlToBytes(m[1]); } catch (err) { return; }
    if (bytes.length !== 32) return;
    var ok = await unlock(bytes);
    if (ok) history.replaceState(null, '', location.pathname + location.search);
  })();

  apply();
})();
