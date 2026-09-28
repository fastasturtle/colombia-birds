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
  build: { format: 'directory' },
});
