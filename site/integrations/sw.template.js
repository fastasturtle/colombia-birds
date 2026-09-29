/*
 * Service worker of «Птицы Колумбии» (hand-written, no Workbox).
 * Template: site/integrations/sw.template.js; the build (integrations/offline.mjs) writes dist/sw.js with
 * __VERSION__, __BASE__ and __MEDIA_ORIGIN__ replaced, so every deploy is a byte-different worker.
 *
 * The worker only SERVES. It never downloads the offline pack by itself: the /offline/ page does that
 * (OfflinePack.svelte) straight into the same two caches. On a normal visit the worker caches only what the
 * user actually opens (pages, assets, photos) plus the /offline/ page itself.
 *
 * HTML is stale-while-revalidate: a cached page is shown at once (no waiting for the network, so the
 * home-screen app does not open on a black screen) and refreshed in the background. Once the fresh copy is
 * stored, the worker posts PAGE_REFRESHED with its build id to the page (notifyRefreshed); if it differs from
 * the page's own, Base.astro reloads the page once while the user has not started reading, otherwise shows the
 * «Есть новая версия» toast (which also has its own fallback check: version.json vs
 * <meta name="build-version">). Whenever a
 * fresh page is stored, the _astro files it references are stored too, so it also works offline right away.
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
  await cacheAssetsOf(html);
}

/** Stores the CSS/JS a page references (content-hashed, small: BASE + '_astro/…') that are not cached yet. */
async function cacheAssetsOf(html) {
  const cache = await caches.open(PAGES);
  const assets = new Set(html.match(new RegExp(escapeRe(BASE) + '_astro/[^"\'\\s)]+', 'g')) || []);
  await Promise.all([...assets].map(async (path) => {
    try {
      const url = new URL(path, self.location.origin).href;
      if (await cache.match(url)) return;
      const r = await fetch(url);
      if (r.ok && r.type === 'basic') await cache.put(url, r);
    } catch (e) { /* best effort: one missing file must not stop the others */ }
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

// ---------- HTML: stale-while-revalidate ----------
// Cached: answer from the cache immediately and fetch a fresh copy in the background (event.waitUntil) for
// the next visit. Not cached: the network (and store the page); network error: the offline page, else an
// inline 503 stub.
// A user reload (navigate with cache 'reload') also gets the cached copy first. That is intended: the
// toast's «Обновить» is pressed after the background refresh started by this very page load has normally
// completed, so the reload shows the fresh page. Freshness is the job of PAGE_REFRESHED (a one-time silent
// reload or the toast) and of the toast's own check, not a network wait.

async function handleHtml(event) {
  const req = event.request;
  const key = stripQuery(req.url);
  const hit = await matchPage(key);
  if (hit) {
    // revalidate the URL the copy is stored under (matchPage may have found the trailing-slash form)
    event.waitUntil(fetchPage(event, hit.key, hit.key).catch(() => {}));
    return hit.res;
  }
  try {
    return await fetchPage(event, req.url, key);
  } catch (e) {
    // network error (offline, DNS, …) and nothing cached
    const offline = await caches.match(OFFLINE_URL, { cacheName: PAGES });
    if (offline) return clean(offline);
    return new Response(
      '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
      + '<title>Нет сети</title><body style="font:16px/1.5 system-ui,sans-serif;padding:24px">'
      + '<h1>Нет сети и страница не скачана</h1><p>Откройте эту страницу, когда появится связь.</p></body>',
      { status: 503, headers: { 'Content-Type': 'text/html; charset=utf-8' } });
  }
}

/**
 * Fetches a page from the network; a plain 200 is stored under `key` and then (in event.waitUntil, never
 * delaying the response) the _astro files it references are stored too, so the page also works offline
 * right after a background refresh brought new hashed JS/CSS. Rejects on a network error.
 * `cache: 'no-cache'` revalidates with the server, skipping GitHub Pages' 10-minute max-age.
 * A fresh request from the URL (a navigate Request cannot be re-used with an init in every browser);
 * redirect: 'manual' hands a redirect (e.g. missing trailing slash) back as an opaqueredirect, which a
 * navigation accepts and follows itself. Such responses (and 404s, errors) are returned, never cached.
 */
async function fetchPage(event, url, key) {
  const res = await fetch(url, { cache: 'no-cache', credentials: 'same-origin', redirect: 'manual' });
  if (res.ok && res.type === 'basic' && !res.redirected) {
    const copy = res.clone();
    event.waitUntil((async () => {
      const html = await copy.clone().text();
      await (await caches.open(PAGES)).put(key, copy);
      await cacheAssetsOf(html);
      try { await notifyRefreshed(event, key, html); } catch (e) { /* never affects the response */ }
    })().catch(() => {}));
  }
  return res;
}

/**
 * Tells the page that made the request which build its URL now has in the cache:
 * { type: 'PAGE_REFRESHED', url: key, version }. It matters after a stale answer: Base.astro reloads the page
 * once (or shows the toast) when the version differs from the one the page was rendered with. Sent after a
 * first (uncached) fetch too, where the versions match and nothing happens. For a navigation the page is
 * event.resultingClientId: clientId is empty there, or (Chrome) the page the navigation started from, so
 * resultingClientId wins whenever it is set (it is empty for subresource requests). clients.get waits for
 * such a reserved client to be ready; the short retry covers a browser that resolves undefined meanwhile.
 */
async function notifyRefreshed(event, key, html) {
  const m = html.match(/<meta name="build-version" content="([^"]*)"/);
  const id = event.resultingClientId || event.clientId;
  if (!m || !id) return;
  for (let i = 0; i < 10; i++) {
    const client = await self.clients.get(id);
    if (client) { client.postMessage({ type: 'PAGE_REFRESHED', url: key, version: m[1] }); return; }
    await new Promise((ok) => setTimeout(ok, 300));
  }
}

/**
 * Cached page by URL without query; also tries the trailing-slash form of directory URLs.
 * Returns { res, key } (key: the URL the copy is stored under) or undefined.
 */
async function matchPage(key) {
  const cache = await caches.open(PAGES);
  let res = await cache.match(key, { ignoreSearch: true });
  if (!res) {
    const u = new URL(key);
    if (!u.pathname.endsWith('/') && !/\.[a-z0-9]+$/i.test(u.pathname)) {
      key += '/';
      res = await cache.match(key);
    }
  }
  return res ? { res: await clean(res), key } : undefined;
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
