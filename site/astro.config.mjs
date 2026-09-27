// @ts-check
import { defineConfig } from 'astro/config';
import svelte from '@astrojs/svelte';

// GitHub Pages project site: https://fastasturtle.github.io/colombia-birds/
export default defineConfig({
  site: 'https://fastasturtle.github.io',
  base: '/colombia-birds',
  trailingSlash: 'always',
  integrations: [svelte()],
  build: { format: 'directory' },
});
