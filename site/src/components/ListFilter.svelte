<script lang="ts">
  /** Site-wide species filter controls (see lib/filter.ts). Mount once per page, above the list. */
  import { filter, LEVEL_LABEL, type Level } from '../lib/filter';
  const levels: Level[] = ['sure', 'maybe', 'all'];
</script>

<div class="lf" role="group" aria-label="Фильтр видов">
  <div class="seg" role="radiogroup" aria-label="Насколько вероятно">
    {#each levels as l}
      <button type="button" role="radio" aria-checked={$filter.level === l} onclick={() => filter.update((f) => ({ ...f, level: l }))}>{LEVEL_LABEL[l]}</button>
    {/each}
  </div>
  <button type="button" class="tg" aria-pressed={$filter.interesting} onclick={() => filter.update((f) => ({ ...f, interesting: !f.interesting }))}>
    <span class="star" aria-hidden="true">★</span> Только интересные
  </button>
</div>

<style>
  .lf { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin: 8px 0 12px; }
  .seg { display: inline-flex; border: 1px solid var(--line); border-radius: 999px; overflow: hidden; background: var(--card); max-width: 100%; }
  .seg button, .tg {
    min-height: 40px; padding: 0 12px; border: 0; background: transparent; color: var(--fg); font: inherit; font-size: .88rem;
    cursor: pointer; white-space: nowrap;
  }
  .seg button + button { border-left: 1px solid var(--line); }
  .seg button[aria-checked="true"] { background: var(--accent); color: #fff; }
  .tg { border: 1px solid var(--line); border-radius: 999px; background: var(--card); }
  .tg .star { color: var(--accent-2); }
  .tg[aria-pressed="true"] { background: var(--accent-2); border-color: var(--accent-2); color: #fff; }
  .tg[aria-pressed="true"] .star { color: #fff; }
  @media (max-width: 380px) { .seg button, .tg { padding: 0 9px; font-size: .82rem; } }
</style>
