/*
 * Service worker of «Птицы Колумбии» (hand-written, no Workbox).
 * Template: site/integrations/sw.template.js; the build (integrations/offline.mjs) writes dist/sw.js with
 * __VERSION__, __BASE__ and __MEDIA_ORIGIN__ replaced, so every deploy is a byte-different worker.
 *
 * The worker only SERVES. It never downloads the offline pack by itself: the /offline/ page does that
 * (OfflinePack.svelte) straight into the same two caches. On a normal visit the worker caches only what the
 * user actually opens (pages, assets, photos) plus the /offline/ page itself.
 *
 *   pages-v1  same-origin HTML and assets (keys: absolute URL without ?query)
 *   media-v1  photos from R2 (keys: absolute URL)
 * Cache names are NOT versioned per build: the pack diff on /offline/ handles updates. Changing a constant
 * below is the escape hatch that drops everything (old caches are deleted on activate).
 */
const VERSION = '__VERSION__';
const BASE = '__BASE__'; // "/colombia-birds/"
const MEDIA_ORIGIN = '__MEDIA_ORIGIN__';
const PAGES = 'pages-v1';
const MEDIA = 'media-v1';
const HTML_TIMEOUT_MS = 3000;
const OFFLINE_URL = new URL(BASE + 'offline/', self.location.origin).href;
/** Must always come from the network (never cached, never answered from cache). */
const PASSTHROUGH = new Set(['sw.js', 'version.json', 'offline-manifest.json'].map((f) => BASE + f));

// ---------- lifecycle ----------

self.addEventListener('install', (event) => {
  self.skipWaiting();
  // Best effort: keep the offline page (and the assets it references) so a later offline visit to an
  // unknown page can show it. A failure here must not block the install.
  event.waitUntil(precacheOfflinePage().catch(() => {}));
});

self.addEventListener('activate', (event) => {
  event.waitUntil((async () => {
    const keep = new Set([PAGES, MEDIA]);
    for (const name of await caches.keys()) if (!keep.has(name)) await caches.delete(name);
    await self.clients.claim();
  })());
});

self.addEventListener('message', (event) => {
  const data = event.data || {};
  if (data.type === 'GET_VERSION') {
    const reply = { type: 'VERSION', version: VERSION };
    if (event.ports && event.ports[0]) event.ports[0].postMessage(reply);
    else if (event.source) event.source.postMessage(reply);
  }
});

async function precacheOfflinePage() {
  const cache = await caches.open(PAGES);
  const res = await fetch(OFFLINE_URL, { cache: 'no-cache' });
  if (!res.ok) return;
  const html = await res.clone().text();
  await cache.put(OFFLINE_URL, res);
  // its CSS/JS (content-hashed, tiny): /colombia-birds/_astro/…
  const assets = new Set(html.match(new RegExp(escapeRe(BASE) + '_astro/[^"\'\\s)]+', 'g')) || []);
  await Promise.all([...assets].map(async (path) => {
    const url = new URL(path, self.location.origin).href;
    if (await cache.match(url)) return;
    const r = await fetch(url);
    if (r.ok) await cache.put(url, r);
  }));
}

// ---------- routing ----------

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return; // the report form POSTs go straight to the network
  // Requests that explicitly bypass the HTTP cache (the pack downloader on /offline/ uses cache: 'no-cache')
  // want the network, so the worker stays out of their way. Navigations are excluded: a user's reload
  // is also 'no-cache' and must still work offline.
  if (req.mode !== 'navigate' && (req.cache === 'no-cache' || req.cache === 'reload' || req.cache === 'no-store')) return;
  const url = new URL(req.url);

  if (url.origin === self.location.origin) {
    if (!url.pathname.startsWith(BASE) || PASSTHROUGH.has(url.pathname)) return;
    const accept = req.headers.get('accept') || '';
    if (req.mode === 'navigate' || accept.includes('text/html')) {
      event.respondWith(handleHtml(event));
    } else {
      event.respondWith(handleStatic(event, url));
    }
    return;
  }
  if (url.origin === MEDIA_ORIGIN && url.pathname.startsWith('/photos/')) {
    event.respondWith(handlePhoto(event));
  }
  // any other origin: not intercepted
});

// ---------- HTML: network first (bypassing the HTTP cache), cache on failure/timeout ----------

async function handleHtml(event) {
  const req = event.request;
  const key = stripQuery(req.url);
  // `cache: 'no-cache'` revalidates with the server, skipping GitHub Pages' 10-minute max-age.
  // A fresh request from the URL (a navigate Request cannot be re-used with an init in every browser);
  // redirect: 'manual' hands a redirect (e.g. missing trailing slash) back as an opaqueredirect, which a
  // navigation accepts and follows itself. Such responses (and errors) are never cached.
  const network = fetch(req.url, { cache: 'no-cache', credentials: 'same-origin', redirect: 'manual' }).then(async (res) => {
    if (res.ok && res.type === 'basic' && !res.redirected) {
      const cache = await caches.open(PAGES);
      await cache.put(key, res.clone());
    }
    return res;
  });
  // keep the worker alive until the cache write finishes even when we answer from the cache first
  event.waitUntil(network.then(() => {}, () => {}));

  let timer;
  const timeout = new Promise((resolve) => { timer = setTimeout(() => resolve(null), HTML_TIMEOUT_MS); });
  try {
    const first = await Promise.race([network, timeout]);
    if (first) return first;
    // Slow network: a cached copy (possibly older) now beats waiting. Nothing cached: keep waiting,
    // because a slow page is better than the offline stub.
    const cached = await matchPage(key);
    if (cached) return cached;
    return await network;
  } catch (e) {
    // network error (offline, DNS, …)
    const cached = await matchPage(key);
    if (cached) return cached;
    const offline = await caches.match(OFFLINE_URL, { cacheName: PAGES });
    if (offline) return clean(offline);
    return new Response(
      '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
      + '<title>Нет сети</title><body style="font:16px/1.5 system-ui,sans-serif;padding:24px">'
      + '<h1>Нет сети и страница не скачана</h1><p>Откройте эту страницу, когда появится связь.</p></body>',
      { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } });
  } finally {
    clearTimeout(timer);
  }
}

/** Cached page by URL without query; also tries the trailing-slash form of directory URLs. */
async function matchPage(key) {
  const cache = await caches.open(PAGES);
  let res = await cache.match(key, { ignoreSearch: true });
  if (!res) {
    const u = new URL(key);
    if (!u.pathname.endsWith('/') && !/\.[a-z0-9]+$/i.test(u.pathname)) res = await cache.match(key + '/');
  }
  return res ? clean(res) : undefined;
}

/** A redirected response cannot answer a navigation; re-wrap it (body and headers stay the same). */
async function clean(res) {
  if (!res.redirected) return res;
  return new Response(await res.blob(), { status: res.status, statusText: res.statusText, headers: res.headers });
}

// ---------- other same-origin files ----------
// /_astro/* is content-hashed: cache first, forever. Other files (manifest, favicon) are not hashed:
// answer from the cache when present and refresh it in the background (fresh content wins next time).

async function handleStatic(event, url) {
  const key = stripQuery(event.request.url);
  const cache = await caches.open(PAGES);
  const hit = await cache.match(key);
  const hashed = url.pathname.startsWith(BASE + '_astro/');
  if (hit && hashed) return hit;
  const refresh = fetch(event.request).then(async (res) => {
    if (res.ok && res.type === 'basic') await cache.put(key, res.clone());
    return res;
  });
  if (hit) {
    event.waitUntil(refresh.then(() => {}, () => {}));
    return hit;
  }
  return refresh; // miss: network (a rejection shows as a normal network error)
}

// ---------- photos (R2): cache first; offline fallback large → medium → thumb ----------

async function handlePhoto(event) {
  const url = stripQuery(event.request.url);
  const cache = await caches.open(MEDIA);
  const hit = await cache.match(url);
  if (hit) return hit;
  try {
    // CORS so the stored response is not opaque (opaque entries are padded to megabytes in the quota)
    const res = await fetch(url, { mode: 'cors', credentials: 'omit' });
    if (res.status === 200) event.waitUntil(cache.put(url, res.clone()).catch(() => {}));
    return res;
  } catch (e) {
    for (const alt of smallerSizes(url)) {
      const r = await cache.match(alt);
      if (r) return r;
    }
    // Last resort: the browser's own no-cors request (e.g. an origin that is not in the bucket's CORS list,
    // or an HTTP-cached copy). Offline this fails too, and the <img> shows as broken.
    try { return await fetch(event.request); } catch (e2) { return Response.error(); }
  }
}

/** -large.jpg → [-medium.jpg, -thumb.jpg]; -medium.jpg → [-thumb.jpg]; otherwise []. */
function smallerSizes(url) {
  const m = url.match(/^(.*)-(large|medium)\.jpg$/);
  if (!m) return [];
  return m[2] === 'large' ? [m[1] + '-medium.jpg', m[1] + '-thumb.jpg'] : [m[1] + '-thumb.jpg'];
}

// ---------- helpers ----------

function stripQuery(u) {
  const url = new URL(u);
  url.search = '';
  url.hash = '';
  return url.href;
}

function escapeRe(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}
