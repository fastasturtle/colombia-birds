<script lang="ts">
  /**
   * Toggle chip with a facet count (lib/facets.ts), shared by the identifier and FilterBar.
   * n = null while the data is loading (no count); delta = the chip's group already has a selection, so the count is
   * «+N» (species it would add) instead of the absolute number. Zero-count chips are dimmed but stay clickable.
   */
  import { plural } from '../lib/facets';
  interface Props { label: string; sub?: string | null; on: boolean; n: number | null; delta: boolean; hint?: string | null; onclick: () => void }
  const { label, sub = null, on, n, delta, hint = null, onclick }: Props = $props();
  let how = $derived(n != null && !on ? `${delta ? 'добавит' : plural(n, 'подойдёт', 'подойдут', 'подойдут')} ${n} ${plural(n, 'вид', 'вида', 'видов')}` : null);
</script>

<button type="button" class="chip-b" class:zero={n === 0 && !on} aria-pressed={on}
  aria-label={how ? `${label}: ${how}` : undefined}
  title={[hint, how && how[0].toUpperCase() + how.slice(1)].filter(Boolean).join('. ') || undefined}
  {onclick}>{label}{#if sub}<span class="sub">{sub}</span>{/if}{#if how}<span class="cnt" aria-hidden="true">{delta ? `+${n}` : n}</span>{/if}</button>

<style>
  .chip-b {
    display: inline-flex; align-items: center; gap: 6px;
    min-height: 40px; padding: 0 10px; border: 1px solid var(--line); border-radius: 999px; background: var(--card);
    color: var(--fg); font: inherit; font-size: .82rem; cursor: pointer; white-space: nowrap; max-width: 100%;
  }
  .sub { font-style: italic; color: var(--muted); font-size: .74rem; overflow: hidden; text-overflow: ellipsis; min-width: 0; }
  .cnt { font-size: .75rem; line-height: 1; padding: 2px 6px; border-radius: 999px; background: var(--chip); color: var(--muted); font-variant-numeric: tabular-nums; }
  .chip-b.zero { color: var(--muted); border-style: dashed; background: transparent; }
  .chip-b.zero .cnt { opacity: .7; }
  .chip-b[aria-pressed="true"] { background: var(--accent); border-color: var(--accent); color: #fff; }
  .chip-b[aria-pressed="true"] .sub { color: inherit; opacity: .8; }
  @media (prefers-color-scheme: dark) { .chip-b[aria-pressed="true"] { color: #10150f; } }
</style>
