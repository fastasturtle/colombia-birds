<script lang="ts">
  /**
   * Endemic / near-endemic mark, shared by every species list, tile and the filter buttons, so they all look identical.
   * ◆ filled diamond = endemic of Colombia, ◇ hollow diamond = near-endemic (main range in Colombia).
   * Drawn as a tiny inline SVG rather than a text glyph: fonts place ◆/◇ at different heights and some fall back to emoji.
   * variant: 'tile' = chip over a photo, same box as the ★ chip (.b in StudyTile);
   *          'inline' = smaller chip inside a text row (does not grow the line box);
   *          'icon' = bare decorative diamond in currentColor (filter buttons; the parent sets the colour).
   * Usable from Astro without a client directive (renders to static HTML).
   */
  interface Props { kind: 'end' | 'near'; variant?: 'tile' | 'inline' | 'icon' }
  const { kind, variant = 'inline' }: Props = $props();
  const TITLE = { end: 'эндемик Колумбии', near: 'почти-эндемик Колумбии: основной ареал в Колумбии' } as const;
</script>

{#snippet diamond()}
  <svg viewBox="0 0 10 10" width="1em" height="1em" aria-hidden="true" focusable="false">
    {#if kind === 'end'}
      <path d="M5 .6 9.4 5 5 9.4 .6 5Z" fill="currentColor" />
    {:else}
      <path d="M5 1.35 8.65 5 5 8.65 1.35 5Z" fill="none" stroke="currentColor" stroke-width="1.5" />
    {/if}
  </svg>
{/snippet}

{#if variant === 'icon'}
  {@render diamond()}
{:else}
  <span class={`em ${kind} ${variant}`} role="img" title={TITLE[kind]} aria-label={TITLE[kind]}>{@render diamond()}</span>
{/if}

<style>
  .em { display: inline-flex; align-items: center; justify-content: center; line-height: 1; color: #fff; flex: none; }
  .em.end { background: #14532d; }
  .em.near { background: #3f6212; }
  /* Same box as the ★ chip: font-size .68rem, line-height 1, padding 3px 5px, radius 6px */
  .em.tile { font-size: .68rem; padding: 3px 5px; border-radius: 6px; }
  /* In text rows: a ~15 px chip, vertically centred, smaller than the row's line box */
  .em.inline { font-size: .68rem; padding: 2px 4px; border-radius: 5px; vertical-align: middle; }
  svg { display: block; }
</style>
