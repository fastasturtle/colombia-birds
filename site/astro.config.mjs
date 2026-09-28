// @ts-check
import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';
import { loadEnv } from 'vite';
import { join } from 'node:path';
import offline from './integrations/offline.mjs';

const BASE = '/colombia-birds';
// same default as MEDIA_BASE in src/lib/data.ts (PUBLIC_MEDIA_BASE_URL from the environment or site/.env)
const env = loadEnv(process.env.NODE_ENV ?? 'production', process.cwd(), 'PUBLIC_');
const MEDIA_BASE = process.env.PUBLIC_MEDIA_BASE_URL ?? env.PUBLIC_MEDIA_BASE_URL ?? 'https://pub-5e58909dbd0e457c85e4e36ef2cdc583.r2.dev';

// GitHub Pages project site: https://fastasturtle.github.io/colombia-birds/
export default defineConfig({
  site: 'https://fastasturtle.github.io',
  base: BASE,
  trailingSlash: 'always',
  integrations: [svelte(), offline({ base: BASE, mediaBase: MEDIA_BASE, dataDir: join(process.cwd(), '..', 'data') })],
  // With 'auto' Base.astro's ~3 KB global CSS is inlined into all 2 150 pages unless the ReportButton island pushes the
  // chunk past the 4 KB limit, so builds with/without PUBLIC_REPORT_URL differed by 6 MB in the offline pack;
  // 'never' keeps it one shared file and the pack 6 MB smaller.
  build: { format: 'directory', inlineStylesheets: 'never' },
});
