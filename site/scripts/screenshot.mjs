#!/usr/bin/env node
/**
 * Screenshot built pages at phone size. Usage (from site/):
 *   npm run build && npm run shots -- / /species/grallaria-milleri/ /route/
 * Options: --dark (dark color scheme), --out DIR (default ../.screenshots), --width N (default 390), --full (full page).
 * Paths are relative to the site base (/colombia-birds/). Serves ./dist on a free port; needs Chromium
 * (pre-installed in Claude Code cloud sessions at $PLAYWRIGHT_BROWSERS_PATH, otherwise `npx playwright install chromium`).
 */
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import { readFileSync, existsSync, statSync, mkdirSync } from 'node:fs';
import { join, resolve } from 'node:path';

const args = process.argv.slice(2);
const flag = (n) => { const i = args.indexOf(n); if (i >= 0) { args.splice(i, 1); return true; } return false; };
const opt = (n, d) => { const i = args.indexOf(n); if (i >= 0) { const v = args[i + 1]; args.splice(i, 2); return v; } return d; };
const dark = flag('--dark');
const full = flag('--full');
const out = resolve(opt('--out', '../.screenshots'));
const width = Number(opt('--width', '390'));
const paths = args.length ? args : ['/', '/species/', '/route/'];
const BASE = '/colombia-birds';
const dist = resolve('dist');
if (!existsSync(dist)) { console.error('dist/ not found: run `npm run build` first'); process.exit(1); }
mkdirSync(out, { recursive: true });

const types = { html: 'text/html; charset=utf-8', js: 'text/javascript', css: 'text/css', svg: 'image/svg+xml', json: 'application/json', png: 'image/png', webmanifest: 'application/manifest+json' };
const srv = createServer((req, res) => {
  let p = decodeURIComponent(req.url.split('?')[0]);
  if (!p.startsWith(BASE)) { res.statusCode = 404; return res.end(); }
  let f = join(dist, p.slice(BASE.length));
  if (existsSync(f) && statSync(f).isDirectory()) f = join(f, 'index.html');
  if (!existsSync(f)) { res.statusCode = 404; return res.end('not found'); }
  res.setHeader('content-type', types[f.split('.').pop()] ?? 'application/octet-stream');
  res.end(readFileSync(f));
}).listen(0);
const port = srv.address().port;

// Claude Code cloud sessions ship Chromium at /opt/pw-browsers/chromium; a newer Playwright than that build
// refuses its default path, so fall back to the explicit executable (see PLAYWRIGHT_CHROMIUM_EXECUTABLE too).
const explicit = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE ?? '/opt/pw-browsers/chromium';
const browser = await chromium.launch().catch(async (e) => {
  if (existsSync(explicit)) return chromium.launch({ executablePath: explicit });
  throw e;
});
const ctx = await browser.newContext({ viewport: { width, height: 844 }, deviceScaleFactor: 2, colorScheme: dark ? 'dark' : 'light' });
for (const p of paths) {
  const page = await ctx.newPage();
  const name = (p === '/' ? 'home' : p.replace(/^\/|\/$/g, '').replace(/\//g, '_')) + (dark ? '-dark' : '') + '.png';
  try {
    await page.goto(`http://localhost:${port}${BASE}${p}`, { waitUntil: 'networkidle', timeout: 60000 });
  } catch (e) { console.warn(`${p}: ${e.message.split('\n')[0]}`); }
  await page.waitForTimeout(1000);
  await page.screenshot({ path: join(out, name), fullPage: full });
  console.log(`${p} -> ${join(out, name)}`);
  await page.close();
}
await browser.close();
srv.close();
