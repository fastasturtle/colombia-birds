<script lang="ts">
  /**
   * «Место» of FilterBar: a button with the current selection («Все места» / «Чикаке» / «3 места») that opens a
   * dropdown with a search box and one checkbox row per site (OR between the checked ones). Counts as on the facet
   * chips (lib/facets.ts): absolute, or «+N» once something is checked (species the row would add); zero rows dimmed.
   * Order as the chips had: when the list is long (> fold), rows with a count (and checked ones) first, then the rest.
   * Closes on outside click, Escape (focus back to the button) and Tab out; opening focuses the search, ↓ / ↑ move
   * between the search and the rows, Enter or Space toggles a row.
   */
  import { onMount } from 'svelte';
  import { normQ, type SiteOpt } from '../lib/filter';
  import { plural } from '../lib/facets';

  interface Props { sites: SiteOpt[]; sel: string[]; counts: Record<string, number> | null; fold: number; onpick: (id: string) => void; onclear: () => void }
  const { sites, sel, counts, fold, onpick, onclear }: Props = $props();

  const uid = Math.random().toString(36).slice(2, 8);
  let open = $state(false);
  let q = $state('');
  let root = $state<HTMLElement | null>(null);
  let btn = $state<HTMLButtonElement | null>(null);
  let qEl = $state<HTMLInputElement | null>(null);
  let listEl = $state<HTMLElement | null>(null);

  const nameOf = $derived(new Map(sites.map((s) => [s.id, s.name])));
  let label = $derived(sel.length === 0 ? 'Все места' : sel.length === 1 ? (nameOf.get(sel[0]) ?? sel[0]) : `${sel.length} ${plural(sel.length, 'место', 'места', 'мест')}`);
  /** lower case, ё -> е, no accents (Spanish names) */
  const key = (s: string) => normQ(s).normalize('NFD').replace(/\p{M}/gu, '');
  let ordered = $derived.by(() => {
    if (!counts || sites.length <= fold) return sites;
    const main: SiteOpt[] = [], rest: SiteOpt[] = [];
    for (const s of sites) (sel.includes(s.id) || (counts[s.id] ?? 0) > 0 ? main : rest).push(s);
    return [...main, ...rest];
  });
  let shown = $derived.by(() => {
    const t = key(q.trim());
    return t ? ordered.filter((s) => key(s.name).includes(t)) : ordered;
  });
  const delta = $derived(sel.length > 0);
  const how = (n: number) => `${delta ? 'добавит' : plural(n, 'подойдёт', 'подойдут', 'подойдут')} ${n} ${plural(n, 'вид', 'вида', 'видов')}`;

  function setOpen(v: boolean, refocus = false) {
    open = v;
    if (v) { q = ''; queueMicrotask(() => qEl?.focus()); }
    else if (refocus) btn?.focus();
  }
  onMount(() => {
    const down = (e: PointerEvent) => { if (open && root && !root.contains(e.target as Node)) setOpen(false); };
    document.addEventListener('pointerdown', down);
    return () => document.removeEventListener('pointerdown', down);
  });
  const boxes = () => Array.from(listEl?.querySelectorAll<HTMLInputElement>('input[type="checkbox"]') ?? []);
  function onKey(e: KeyboardEvent) {
    if (e.key === 'Escape') { e.preventDefault(); e.stopPropagation(); setOpen(false, true); return; }
    if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
    const bs = boxes();
    if (!bs.length) return;
    e.preventDefault();
    const i = bs.indexOf(document.activeElement as HTMLInputElement);
    if (e.key === 'ArrowDown') bs[i < 0 ? 0 : Math.min(i + 1, bs.length - 1)].focus();
    else if (i <= 0) qEl?.focus();
    else bs[i - 1].focus();
  }
  function onRowKey(e: KeyboardEvent, id: string) {
    if (e.key === 'Enter') { e.preventDefault(); onpick(id); }
  }
  function onQKey(e: KeyboardEvent) {
    // Enter in the search: with one match, toggle it
    if (e.key === 'Enter') { e.preventDefault(); if (shown.length === 1) onpick(shown[0].id); }
  }
  function onFocusOut(e: FocusEvent) {
    const to = e.relatedTarget as Node | null;
    if (open && to && root && !root.contains(to)) setOpen(false);
  }
</script>

<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="pp" bind:this={root} onkeydown={onKey} onfocusout={onFocusOut}>
  <button type="button" class="pb" class:on={sel.length > 0} bind:this={btn} aria-haspopup="true" aria-expanded={open}
    aria-controls={`pp-${uid}`} onclick={() => setOpen(!open)}>
    <span class="pl">{label}</span><span class="car" aria-hidden="true">▾</span>
  </button>
  {#if open}
    <div class="dd" id={`pp-${uid}`} role="group" aria-label="Выбор мест">
      <div class="pp-top">
        <input type="search" class="ppq" bind:this={qEl} bind:value={q} onkeydown={onQKey}
          placeholder={`Найти среди ${sites.length} ${plural(sites.length, 'места', 'мест', 'мест')}`} aria-label="Найти место" autocomplete="off" />
      </div>
      <ul class="pp-list" bind:this={listEl}>
        {#each shown as s (s.id)}
          {@const on = sel.includes(s.id)}
          {@const n = counts ? (counts[s.id] ?? 0) : null}
          <li>
            <label class="pp-row" class:zero={n === 0 && !on} title={n != null && !on ? how(n)[0].toUpperCase() + how(n).slice(1) : undefined}>
              <input type="checkbox" checked={on} onchange={() => onpick(s.id)} onkeydown={(e) => onRowKey(e, s.id)}
                aria-label={n != null && !on ? `${s.name}: ${how(n)}` : s.name} />
              <span class="pp-nm">{s.name}</span>
              {#if n != null && !on}<span class="pp-cnt" aria-hidden="true">{delta ? `+${n}` : n}</span>{/if}
            </label>
          </li>
        {/each}
        {#if shown.length === 0}<li class="pp-none">Нет такого места</li>{/if}
      </ul>
      <div class="pp-foot">
        {#if sel.length}<button type="button" class="pp-lnk" onclick={() => { onclear(); qEl?.focus(); }}>Снять все</button>{/if}
        <button type="button" class="pp-ok" onclick={() => setOpen(false, true)}>Готово</button>
      </div>
    </div>
  {/if}
</div>

<style>
  .pp { position: relative; max-width: 360px; }
  .pb {
    display: flex; align-items: center; justify-content: space-between; gap: 8px; width: 100%; min-height: 40px; padding: 0 12px;
    border: 1px solid var(--line); border-radius: 8px; background: var(--bg); color: var(--fg); font: inherit; font-size: .9rem;
    cursor: pointer; text-align: left;
  }
  .pb.on { border-color: var(--accent); }
  .pb[aria-expanded="true"] { border-color: var(--accent); }
  .pb[aria-expanded="true"] .car { transform: rotate(180deg); }
  .pl { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; min-width: 0; }
  .car { flex: none; color: var(--muted); font-size: .8rem; transition: transform .15s; }
  .dd {
    position: absolute; z-index: 15; top: calc(100% + 4px); left: 0; right: 0; display: flex; flex-direction: column;
    max-height: min(60vh, 420px); border: 1px solid var(--line); border-radius: 10px; background: var(--card);
    box-shadow: 0 6px 24px rgba(0, 0, 0, .14); overflow: hidden;
  }
  .pp-top { flex: none; padding: 8px; border-bottom: 1px solid var(--line); }
  .ppq { width: 100%; min-height: 36px; padding: 0 10px; border: 1px solid var(--line); border-radius: 8px; background: var(--bg); color: var(--fg); font: inherit; font-size: .9rem; }
  .pp-list { flex: 1 1 auto; min-height: 0; overflow-y: auto; overscroll-behavior: contain; list-style: none; margin: 0; padding: 4px 0; }
  .pp-row { display: flex; align-items: center; gap: 10px; min-height: 40px; padding: 0 12px; cursor: pointer; font-size: .9rem; }
  .pp-row:hover, .pp-row:focus-within { background: var(--chip); }
  .pp-row input { flex: none; width: 18px; height: 18px; margin: 0; accent-color: var(--accent); }
  .pp-nm { flex: 1 1 auto; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .pp-cnt { flex: none; font-size: .75rem; line-height: 1; padding: 2px 6px; border-radius: 999px; background: var(--chip); color: var(--muted); font-variant-numeric: tabular-nums; }
  .pp-row:hover .pp-cnt, .pp-row:focus-within .pp-cnt { background: var(--bg); }
  .pp-row.zero { color: var(--muted); }
  .pp-row.zero .pp-cnt { opacity: .7; }
  .pp-none { padding: 10px 12px; color: var(--muted); font-size: .85rem; }
  .pp-foot { flex: none; display: flex; align-items: center; justify-content: flex-end; gap: 8px; padding: 4px 8px; border-top: 1px solid var(--line); }
  .pp-lnk { margin-right: auto; font: inherit; font-size: .85rem; color: var(--accent); background: none; border: 0; padding: 6px 4px; cursor: pointer; text-decoration: underline; }
  .pp-ok { min-height: 36px; padding: 0 14px; border: 0; border-radius: 8px; background: var(--accent); color: #fff; font: inherit; font-size: .85rem; font-weight: 600; cursor: pointer; }
  @media (prefers-color-scheme: dark) { :global(:root:not([data-theme="light"])) .pp-ok { color: #10150f; } }
  :global(:root[data-theme="dark"]) .pp-ok { color: #10150f; }
</style>
