/**
 * Offline pack (PWA) build step.
 *
 * - `astro:config:setup`: defines `__BUILD_ID__` (one id per build) so every page carries it in
 *   `<meta name="build-version">` (Base.astro). The same id goes into version.json and sw.js below,
 *   so "is there a newer deploy?" is a plain string compare everywhere.
 * - `astro:build:done`: writes into dist/
 *     offline-manifest.json  { version, hash, built, photoEstimate, files: [[url, ver, size?], ...] }
 *         url  = site-relative with the base for dist files (/colombia-birds/species/x/, /colombia-birds/_astro/…),
 *                absolute R2 URL for photos;
 *         ver  = first 12 hex of sha256 of the file (HTML is hashed without the build-version meta, so an
 *                unchanged page keeps its ver across builds), or "key" for photos (immutable on R2: URL = version);
 *         size = bytes for dist files; photos have no size, the UI uses photoEstimate by suffix and shows «≈».
 *     version.json           { version, hash, built }  (hash = hash of the sorted file list: changes iff content changes)
 *     sw.js                  from integrations/sw.template.js with __VERSION__/__BASE__/__MEDIA_ORIGIN__ baked in
 *                            (a new build id makes the browser's byte-compare pick up the new worker).
 * The pack = all HTML pages + _astro assets + manifest/favicon + thumb and medium photos (large photos stay online-only).
 */
import { createHash } from 'node:crypto';
import { readFileSync, readdirSync, writeFileSync, existsSync, statSync } from 'node:fs';
import { join, relative, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

/** Measured average photo sizes on R2 (bytes); sizes are not recorded in data/. */
const PHOTO_ESTIMATE = { '-thumb.jpg': 23040, '-medium.jpg': 107520 };
/** Generated here or must always come from the network: never part of the pack. */
const EXCLUDE = new Set(['offline-manifest.json', 'version.json', 'sw.js']);
const META_RE = /<meta name="build-version" content="[^"]*"\s*\/?>/;

/** @param {Buffer | string} buf */
const sha = (buf) => createHash('sha256').update(buf).digest('hex').slice(0, 12);

/** @param {string} dir @param {string[]} [out] @returns {string[]} */
function walk(dir, out = []) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) walk(p, out); else out.push(p);
  }
  return out;
}

/**
 * @param {{ base: string, mediaBase: string, dataDir: string }} opts
 * @returns {import('astro').AstroIntegration}
 */
export default function offline({ base, mediaBase, dataDir }) {
  const buildId = process.env.CB_BUILD_ID || Date.now().toString(36);
  const b = base.replace(/\/$/, ''); // "/colombia-birds"
  const media = mediaBase.replace(/\/$/, '');
  return {
    name: 'cb-offline',
    hooks: {
      'astro:config:setup': ({ updateConfig }) => {
        updateConfig({ vite: { define: { __BUILD_ID__: JSON.stringify(buildId) } } });
      },
      'astro:build:done': ({ dir, logger }) => {
        const dist = fileURLToPath(dir);
        /** @type {Array<[string, string, number?]>} */
        const files = [];
        for (const f of walk(dist)) {
          const rel = relative(dist, f).split(sep).join('/');
          if (EXCLUDE.has(rel)) continue;
          let buf = readFileSync(f);
          const size = buf.length;
          const url = rel === 'index.html' || rel.endsWith('/index.html')
            ? `${b}/${rel.slice(0, -'index.html'.length)}`
            : `${b}/${rel}`;
          if (rel.endsWith('.html')) buf = Buffer.from(buf.toString('utf8').replace(META_RE, ''));
          files.push([url, sha(buf), size]);
        }
        // photos (thumb + medium) of species that have a page
        let photos = 0;
        const spDir = join(dataDir, 'species');
        for (const name of readdirSync(spDir).filter((n) => n.endsWith('.json')).sort()) {
          const slug = name.slice(0, -5);
          if (!existsSync(join(dist, 'species', slug, 'index.html'))) continue;
          const sp = JSON.parse(readFileSync(join(spDir, name), 'utf8'));
          for (const p of sp.photos ?? []) {
            for (const k of [p.sizes?.thumb, p.sizes?.medium]) if (k) { files.push([`${media}/${k}`, 'key']); photos++; }
          }
        }
        // dedupe (two species could share a photo key) and sort for a stable hash
        const uniq = [...new Map(files.map((e) => [e[0], e])).values()].sort((x, y) => (x[0] < y[0] ? -1 : 1));
        photos = uniq.filter((e) => e[1] === 'key').length;
        const hash = sha(JSON.stringify(uniq));
        const built = new Date().toISOString();
        writeFileSync(join(dist, 'offline-manifest.json'),
          JSON.stringify({ version: buildId, hash, built, photoEstimate: PHOTO_ESTIMATE, files: uniq }));
        writeFileSync(join(dist, 'version.json'), JSON.stringify({ version: buildId, hash, built }));
        const tpl = readFileSync(new URL('./sw.template.js', import.meta.url), 'utf8');
        writeFileSync(join(dist, 'sw.js'), tpl
          .replaceAll('__VERSION__', buildId)
          .replaceAll('__BASE__', `${b}/`)
          .replaceAll('__MEDIA_ORIGIN__', new URL(media).origin));
        const distBytes = uniq.reduce((s, e) => s + (e[2] ?? 0), 0);
        const est = uniq.reduce((s, e) => s + (e[2] ?? (e[0].endsWith('-thumb.jpg') ? PHOTO_ESTIMATE['-thumb.jpg'] : PHOTO_ESTIMATE['-medium.jpg'])), 0);
        logger.info(`offline pack: ${uniq.length} files (${uniq.length - photos} from dist, ${(distBytes / 1048576).toFixed(0)} MB; `
          + `${photos} photos), ≈ ${(est / 1048576).toFixed(0)} MB total; version ${buildId}, hash ${hash}`);
      },
    },
  };
}
