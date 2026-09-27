<script lang="ts">
  /** Site-wide species filter controls (see lib/filter.ts). Mount once per page, above the list. */
  import { filter, LEVEL_LABEL, TAG_LABEL, TAGS, type Level } from '../lib/filter';
  import EndemicMark from './EndemicMark.svelte';
  const levels: Level[] = ['sure', 'maybe', 'all'];
  /* Shown narrowest-first so «Все» sits on the right in both rows; TAGS itself stays widest-first (passesTag relies on it). */
  const tagsShown = [...TAGS].reverse();
</script>

<div class="lf" role="group" aria-label="Фильтр видов">
  <div class="seg" role="radiogroup" aria-label="Насколько вероятно">
    {#each levels as l}
      <button type="button" role="radio" aria-checked={$filter.level === l} onclick={() => filter.update((f) => ({ ...f, level: l }))}>{LEVEL_LABEL[l]}</button>
    {/each}
  </div>
  <div class="seg tag" role="radiogroup" aria-label="Какие виды">
    {#each tagsShown as t}
      <button type="button" role="radio" class={t} aria-checked={$filter.tag === t} onclick={() => filter.update((f) => ({ ...f, tag: t }))}>{#if t === 'int'}<span class="star" aria-hidden="true">★&nbsp;</span>{:else if t === 'end' || t === 'near'}<span class="ic" aria-hidden="true"><EndemicMark kind={t} variant="icon" /></span>{/if}{TAG_LABEL[t]}</button>
    {/each}
  </div>
</div>

<style>
  .lf { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 8px 0 12px; }
  .seg { display: inline-flex; border: 1px solid var(--line); border-radius: 999px; overflow: hidden; background: var(--card); max-width: 100%; }
  .seg button {
    min-height: 40px; padding: 0 12px; border: 0; background: transparent; color: var(--fg); font: inherit; font-size: .88rem;
    cursor: pointer; white-space: nowrap;
  }
  .seg button + button { border-left: 1px solid var(--line); }
  .seg button[aria-checked="true"] { background: var(--accent); color: #fff; }
  .star { color: var(--accent-2); }
  .seg button.int[aria-checked="true"] { background: var(--accent-2); }
  .seg button.near[aria-checked="true"] { background: #3f6212; }
  .seg button.end[aria-checked="true"] { background: #14532d; }
  .seg button[aria-checked="true"] .star { color: #fff; }
  /* ◆ / ◇ (EndemicMark) in the badge colours; lighter tints in dark mode, where #14532d / #3f6212 vanish on the dark card */
  .ic { display: inline-block; margin-right: .3em; vertical-align: -.1em; line-height: 0; }
  .end .ic { color: #14532d; }
  .near .ic { color: #3f6212; }
  @media (prefers-color-scheme: dark) {
    :global(:root:not([data-theme="light"])) .end .ic { color: #7bd389; }
    :global(:root:not([data-theme="light"])) .near .ic { color: #b5d86a; }
  }
  :global(:root[data-theme="dark"]) .end .ic { color: #7bd389; }
  :global(:root[data-theme="dark"]) .near .ic { color: #b5d86a; }
  .seg button[aria-checked="true"] .ic { color: #fff; }
  /* 4 segments of «◆ Эндемики · ◇ Почти-эндемики · ★ Интересные · Все» must fit a 360 px phone: shrink, keep 40 px height */
  @media (max-width: 440px) { .seg.tag button { padding: 0 5px; font-size: .74rem; } .ic { margin-right: .25em; } }
  @media (max-width: 380px) { .seg button { padding: 0 8px; font-size: .8rem; } .seg.tag button { padding: 0 3px; font-size: .7rem; } }
  @media (max-width: 340px) { .seg.tag button { padding: 0 2px; font-size: .64rem; } }
</style>
