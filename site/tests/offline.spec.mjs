#!/usr/bin/env node
/**
 * Offline smoke test (plain Node + Playwright, no test runner). Usage (from site/):
 *   npm run build && npm run test:offline
 *
 * 1. Serves ./dist under /colombia-birds/ on port 4321 (the R2 bucket's CORS allows http://localhost:4321;
 *    if the port is busy a random one is used and the photo checks are skipped).
 * 2. Opens /offline/ and waits for the service worker to control the page.
 * 3. Instead of the full ~440 MB pack, points the downloader at a small manifest (window.__OFFLINE_MANIFEST_URL__,
 *    see OfflinePack.svelte): a few pages + all _astro assets + 2 photos of Spatula discors, served from memory.
 * 4. Clicks «Скачать пакет», waits for «Пакет скачан». Online, checks stale-while-revalidate: a cached page
 *    comes from the cache although the server is slow, and the server is asked for it in the background; a page
 *    changed on the server shows up on the next visit and its new _astro file is already cached.
 * 5. Goes offline (context.setOffline + the server is closed)
 *    and checks: a cached species page renders its H1 and its cached medium photo; a cached day page shows the
 *    cached thumb; a page that was never cached gets the offline page with «эта страница не скачана».
 * Photo checks are skipped when R2 is unreachable from the browser (e.g. no network in CI).
 */
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import { readFileSync, existsSync, statSync } from 'node:fs';
import { join, resolve } from 'node:path';
import assert from 'node:assert/strict';

const BASE = '/colombia-birds';
const dist = resolve('dist');
if (!existsSync(join(dist, 'offline-manifest.json'))) { console.error('dist/ not built: run `npm run build` first'); process.exit(1); }

const full = JSON.parse(readFileSync(join(dist, 'offline-manifest.json'), 'utf8'));
const SPECIES = `${BASE}/species/spatula-discors/`;
const DAY = `${BASE}/days/2026-10-03/`;
const UNCACHED = `${BASE}/species/saltator-maximus/`;
const WORDS = `${BASE}/words/`; // cached; its content is changed on the server to test the background refresh
const pages = [`${BASE}/offline/`, `${BASE}/`, SPECIES, DAY, WORDS];
const photoKeys = ['photos/spatula-discors/1-thumb.jpg', 'photos/spatula-discors/1-medium.jpg'];
const files = full.files.filter((e) =>
  pages.includes(e[0]) || e[0].startsWith(`${BASE}/_astro/`) || photoKeys.some((k) => e[0].endsWith('/' + k)));
assert.equal(files.filter((e) => e[1] === 'key').length, 2, 'test photos present in the manifest');
assert.equal(files.filter((e) => pages.includes(e[0])).length, pages.length, 'test pages present in the manifest');
const testManifest = JSON.stringify({ ...full, version: 'test', hash: 'test-' + full.hash, files });
const TEST_MANIFEST = `${BASE}/__test-manifest.json`;

const types = { html: 'text/html; charset=utf-8', js: 'text/javascript', css: 'text/css', svg: 'image/svg+xml', json: 'application/json', webmanifest: 'application/manifest+json' };
const hits = []; // paths the server was asked for
const delays = new Map(); // path → ms before answering (to tell a cache answer from a network one)
const overrides = new Map(); // path → [content-type, body] served instead of dist
const failures = new Map(); // path → how many more times to answer 503 (a flaky CDN) before serving it
const srv = createServer(async (req, res) => {
  const p = decodeURIComponent(req.url.split('?')[0]);
  hits.push(p);
  if (delays.has(p)) await new Promise((ok) => setTimeout(ok, delays.get(p)));
  if (failures.get(p) > 0) { failures.set(p, failures.get(p) - 1); res.statusCode = 503; return res.end('busy'); }
  if (overrides.has(p)) { const [t, body] = overrides.get(p); res.setHeader('content-type', t); return res.end(body); }
  if (p === TEST_MANIFEST) { res.setHeader('content-type', types.json); return res.end(testManifest); }
  if (!p.startsWith(BASE)) { res.statusCode = 404; return res.end(); }
  let f = join(dist, p.slice(BASE.length));
  if (existsSync(f) && statSync(f).isDirectory()) f = join(f, 'index.html');
  if (!existsSync(f)) { res.statusCode = 404; return res.end('not found'); }
  res.setHeader('content-type', types[f.split('.').pop()] ?? 'application/octet-stream');
  res.setHeader('cache-control', 'max-age=600'); // like GitHub Pages
  res.end(readFileSync(f));
});
const port = await new Promise((ok) => {
  srv.once('error', () => srv.listen(0, () => ok(srv.address().port)));
  srv.listen(4321, () => ok(4321));
});
const origin = `http://localhost:${port}`;

// Cloud sessions reach the internet only through an HTTPS proxy with its own CA.
const proxyUrl = process.env.HTTPS_PROXY || process.env.https_proxy;
const launchOpts = proxyUrl ? { proxy: { server: proxyUrl, bypass: 'localhost,127.0.0.1' } } : {};
const explicit = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ?? '/opt/pw-browsers/chromium';
const browser = await chromium.launch(launchOpts).catch(async (e) => {
  if (existsSync(explicit)) return chromium.launch({ ...launchOpts, executablePath: explicit });
  throw e;
});
const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, ignoreHTTPSErrors: !!proxyUrl });
await ctx.addInitScript((u) => { window.__OFFLINE_MANIFEST_URL__ = u; }, TEST_MANIFEST);
const page = await ctx.newPage();
const logs = [];
page.on('console', (m) => logs.push(`[${m.type()}] ${m.text()} ${m.location().url ?? ''}`));
page.on('requestfailed', (r) => logs.push(`[requestfailed] ${r.url()} ${r.failure()?.errorText}`));

let failed = false;
const step = async (name, fn) => {
  try { await fn(); console.log(`ok   ${name}`); }
  catch (e) { failed = true; console.log(`FAIL ${name}\n     ${e.message.split('\n').join('\n     ')}`); }
};

try {
  let photosReachable = port === 4321;
  if (photosReachable) {
    photosReachable = await page.request.get(files.find((e) => e[1] === 'key')[0], { timeout: 15000 })
      .then((r) => r.ok(), () => false);
  }
  console.log(`serving dist on ${origin}; test manifest: ${files.length} files; R2 photos ${photosReachable ? 'reachable' : 'NOT reachable, photo checks skipped'}`);

  await step('service worker controls /offline/', async () => {
    await page.goto(`${origin}${BASE}/offline/`, { waitUntil: 'load' });
    await page.evaluate(() => navigator.serviceWorker.ready);
    if (!(await page.evaluate(() => !!navigator.serviceWorker.controller))) {
      await page.reload({ waitUntil: 'load' });
    }
    assert.ok(await page.evaluate(() => !!navigator.serviceWorker.controller), 'controller after reload');
    const v = await page.evaluate(() => new Promise((ok) => {
      const ch = new MessageChannel(); ch.port1.onmessage = (e) => ok(e.data.version);
      navigator.serviceWorker.controller.postMessage({ type: 'GET_VERSION' }, [ch.port2]);
    }));
    assert.equal(v, full.version, 'GET_VERSION returns the baked build id');
  });

  await step('download the test pack', async () => {
    const btn = page.getByRole('button', { name: /Скачать пакет/ });
    await btn.waitFor({ timeout: 15000 });
    await page.getByText('тестовый манифест').waitFor();
    hits.length = 0;
    failures.set(DAY, 2); // the CDN answers 503 twice: the downloader retries and gets it on the 3rd try
    try {
      await btn.click();
      await page.getByText('Пакет скачан: сайт работает без сети.').waitFor({ timeout: 60000 })
        .catch(async (e) => { console.log(await page.locator('main').innerText()); throw e; });
    } finally { failures.delete(DAY); }
    await page.getByText(`Скачано ${files.length} из ${files.length} файлов`).waitFor();
    assert.equal(await page.getByText(/Не скачалось/).count(), 0, 'no download errors');
    assert.equal(hits.filter((h) => h === DAY).length, 3, `${DAY} fetched 3 times (2 × 503, then 200)`);
    const keys = await page.evaluate(async () => {
      const out = [];
      for (const n of ['pages-v1', 'media-v1']) for (const r of await (await caches.open(n)).keys()) out.push(r.url);
      return out;
    });
    for (const e of files) {
      const u = e[0].startsWith('http') ? e[0] : origin + e[0];
      if (e[1] === 'key' && !photosReachable) continue;
      assert.ok(keys.includes(u), `cached: ${u}`);
    }
  }).then(() => { if (!photosReachable) console.log('     (photos not asserted)'); });

  const waitFor = async (cond, what, ms = 10000) => {
    for (const t0 = Date.now(); !(await cond());) {
      if (Date.now() - t0 > ms) throw new Error(`timed out waiting for ${what}`);
      await new Promise((ok) => setTimeout(ok, 100));
    }
  };

  await step('online navigation to a cached page is served from cache, then revalidated in the background', async () => {
    hits.length = 0;
    delays.set(SPECIES, 4000); // the server is slow: only a cache answer can be fast
    try {
      const t0 = Date.now();
      await page.goto(`${origin}${SPECIES}`, { waitUntil: 'load' });
      const ms = Date.now() - t0;
      assert.ok(ms < 2500, `page shown from cache without waiting for the server (took ${ms} ms)`);
      assert.ok((await page.locator('main h1').first().textContent())?.trim(), 'H1 has text');
      assert.ok(await page.evaluate(() => !!navigator.serviceWorker.controller), 'page is controlled');
      await waitFor(() => hits.includes(SPECIES), `a revalidation request for ${SPECIES}; got ${hits.join(', ')}`, 5000);
    } finally { delays.delete(SPECIES); }
  });

  await step('a page changed on the server shows up on the next visit, with its new _astro file cached', async () => {
    const oldHtml = readFileSync(join(dist, 'words/index.html'), 'utf8');
    const oldH1 = oldHtml.match(/<h1[^>]*>([^<]*)<\/h1>/)[1];
    const NEW_H1 = 'Обновлённый заголовок (тест)';
    const ASSET = `${BASE}/_astro/__test-refresh.js`;
    overrides.set(ASSET, [types.js, 'document.documentElement.dataset.testRefresh = "1";']);
    overrides.set(WORDS, [types.html, oldHtml
      .replace(/(<h1[^>]*>)[^<]*(<\/h1>)/, `$1${NEW_H1}$2`)
      .replace('</head>', `<script type="module" src="${ASSET}"></script></head>`)]);
    hits.length = 0;
    await page.goto(`${origin}${WORDS}`, { waitUntil: 'load' });
    assert.equal((await page.locator('main h1').first().textContent())?.trim(), oldH1, 'first visit: the cached (stale) page');
    await waitFor(() => hits.includes(WORDS), `a revalidation request for ${WORDS}`);
    await waitFor(() => page.evaluate((u) => caches.open('pages-v1').then((c) => c.match(u)).then((r) => !!r), origin + ASSET),
      'the refreshed page\'s new _astro file in pages-v1');
    await page.goto(`${origin}${WORDS}`, { waitUntil: 'load' });
    assert.equal((await page.locator('main h1').first().textContent())?.trim(), NEW_H1, 'second visit: the refreshed page');
    await page.waitForFunction(() => document.documentElement.dataset.testRefresh === '1', null, { timeout: 5000 });
  });

  // go offline: browser-level emulation + the server really stops answering
  await ctx.setOffline(true);
  srv.closeAllConnections();
  await new Promise((ok) => srv.close(ok));

  await step('cached species page renders offline', async () => {
    await page.goto(`${origin}${SPECIES}`, { waitUntil: 'load', timeout: 20000 });
    const h1 = await page.locator('main h1').first().textContent();
    assert.ok(h1 && h1.trim().length > 0, 'H1 has text');
    assert.ok(await page.locator('#offline-strip').isVisible(), 'offline strip visible');
    if (photosReachable) {
      const img = page.locator('img[src$="1-medium.jpg"]').first();
      await img.scrollIntoViewIfNeeded();
      await page.waitForFunction((el) => el.complete, await img.elementHandle(), { timeout: 10000 });
      assert.ok(await img.evaluate((el) => el.naturalWidth) > 0, 'medium photo from cache');
    }
  });

  await step('cached day page shows the cached thumb offline', async () => {
    await page.goto(`${origin}${DAY}`, { waitUntil: 'load', timeout: 20000 });
    assert.ok((await page.locator('main h1').first().textContent())?.trim(), 'H1 has text');
    if (photosReachable) {
      // the thumb may sit in a collapsed list: force the lazy image to load, then decode it
      const img = page.locator('img[src$="spatula-discors/1-thumb.jpg"]').first();
      const w = await img.evaluate(async (el) => { el.loading = 'eager'; await el.decode().catch(() => {}); return el.naturalWidth; });
      assert.ok(w > 0, 'thumb from cache');
    }
  });

  await step('non-cached page falls back to the offline page', async () => {
    await page.goto(`${origin}${UNCACHED}`, { waitUntil: 'load', timeout: 20000 });
    await page.getByText('Нет сети, и эта страница не скачана.').waitFor({ timeout: 10000 });
  });
} finally {
  await browser.close();
  srv.close();
}
if (failed) { console.log('--- browser console ---\n' + logs.slice(-30).join('\n')); process.exit(1); }
console.log('offline smoke test passed');
