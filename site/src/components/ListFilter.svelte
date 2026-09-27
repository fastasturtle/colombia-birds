<script lang="ts">
  /** Site-wide species filter controls (see lib/filter.ts). Mount once per page, above the list. */
  import { filter, LEVEL_LABEL, TAG_LABEL, TAGS, type Level } from '../lib/filter';
  const levels: Level[] = ['sure', 'maybe', 'all'];
</script>

<div class="lf" role="group" aria-label="Фильтр видов">
  <div class="seg" role="radiogroup" aria-label="Насколько вероятно">
    {#each levels as l}
      <button type="button" role="radio" aria-checked={$filter.level === l} onclick={() => filter.update((f) => ({ ...f, level: l }))}>{LEVEL_LABEL[l]}</button>
    {/each}
  </div>
  <div class="seg tag" role="radiogroup" aria-label="Какие виды">
    {#each TAGS as t}
      <button type="button" role="radio" class={t} aria-checked={$filter.tag === t} onclick={() => filter.update((f) => ({ ...f, tag: t }))}>{#if t === 'int'}<span class="star" aria-hidden="true">★&nbsp;</span>{/if}{TAG_LABEL[t]}</button>
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
  /* 4 segments of «Все · ★ Интересные · Почти-эндемики · Эндемики» must fit a 360 px phone: shrink, keep 40 px height */
  @media (max-width: 440px) { .seg.tag button { padding: 0 6px; font-size: .78rem; } }
  @media (max-width: 380px) { .seg button { padding: 0 8px; font-size: .8rem; } .seg.tag button { padding: 0 4px; font-size: .74rem; } }
</style>
