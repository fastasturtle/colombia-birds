<script lang="ts" module>
  /** label: row text, and the button text when it is the only one checked; sub: shown after it in muted italics (latin
   * name), or upright with `plain` (a site's route days; then it is not searched either); hint: tooltip prefix;
   * terms: extra search strings; dates: a site's route dates (with `byRoute`) */
  export interface PickOpt { key: string; label: string; sub?: string | null; plain?: boolean; hint?: string | null; terms?: (string | null | undefined)[]; dates?: string[] }
  /** the close function of the picker that is open now: opening another one closes it (one dropdown at a time) */
  let closeOpen: (() => void) | null = null;
</script>

<script lang="ts">
  /**
   * Searchable checkbox dropdown of a FilterBar facet («Семейство», «Место»): a button with the current selection
   * («Все места» / «Чикаке» / «3 места») that opens a dropdown with a search box and one checkbox row per option
   * (OR between the checked ones). Counts as lib/facets.ts gives them: absolute, or «+N» once something is checked
   * (species the row would add); zero rows dimmed. Options come in their given order (taxonomic for families, route
   * for sites); when the list is long (> fold), rows with a count (and checked ones) first, then the rest. With `byRoute`
   * (places) the rows go by route day against the viewer's clock instead (lib/dates sortByRoute: today, upcoming, past
   * most recent first, no days last), checked ones included, so a row never jumps when it is toggled.
   * Search: the option's label, sub and terms, ignoring case, ё/е and accents.
   * Closes on outside click, Escape (focus back to the button), Tab out and when another picker opens; opening focuses
   * the search, ↓ / ↑ move between the search and the rows, Enter or Space toggles a row.
   */
  import { onMount } from 'svelte';
  import { normQ, afterPaint } from '../lib/filter';
  import { plural } from '../lib/facets';
  import { sortByRoute, bogotaToday } from '../lib/dates';

  interface Props {
    /** group name for screen readers («Выбор мест») */
    name: string;
    options: PickOpt[]; sel: string[]; counts: Record<string, number> | null; fold: number;
    /** order rows by route day (options carry `dates`) instead of «with a count first» */
    byRoute?: boolean;
    /** button text with nothing checked («Все места») */
    allLabel: string;
    /** noun after a number of checked options: 1 / 2–4 / 5+ («место», «места», «мест») */
    forms: [string, string, string];
    placeholder: string; searchLabel: string; noneText: string;
    onpick: (key: string) => void; onclear: () => void;
  }
  const { name, options, sel, counts, fold, byRoute = false, allLabel, forms, placeholder, searchLabel, noneText, onpick, onclear }: Props = $props();

  const uid = Math.random().toString(36).slice(2, 8);
  let open = $state(false);
  let q = $state('');
  let root = $state<HTMLElement | null>(null);
  let btn = $state<HTMLButtonElement | null>(null);
  let qEl = $state<HTMLInputElement | null>(null);
  let listEl = $state<HTMLElement | null>(null);

  const labelOf = $derived(new Map(options.map((o) => [o.key, o.label])));
  let label = $derived(sel.length === 0 ? allLabel : sel.length === 1 ? (labelOf.get(sel[0]) ?? sel[0]) : `${sel.length} ${plural(sel.length, ...forms)}`);
  /** lower case, ё -> е, no accents (Spanish names) */
  const key = (s: string) => normQ(s).normalize('NFD').replace(/\p{M}/gu, '');
  const keys = $derived(new Map(options.map((o) => [o.key, [o.label, o.plain ? null : o.sub, ...(o.terms ?? [])].filter((x): x is string => !!x).map(key)])));
  let ordered = $derived.by(() => {
    // the clock is read when the list is (re)built, i.e. in the browser once the dropdown opens
    if (byRoute) return sortByRoute(options, (o) => o.dates ?? [], bogotaToday());
    if (!counts || options.length <= fold) return options;
    const main: PickOpt[] = [], rest: PickOpt[] = [];
    for (const o of options) (sel.includes(o.key) || (counts[o.key] ?? 0) > 0 ? main : rest).push(o);
    return [...main, ...rest];
  });
  let shown = $derived.by(() => {
    const t = key(q.trim());
    return t ? ordered.filter((o) => keys.get(o.key)?.some((k) => k.includes(t))) : ordered;
  });
  /** rows built when the dropdown opens: the first FIRST (more than fit on screen) at once, the rest in the next frame */
  const FIRST = 24;
  let limit = $state(Infinity);
  const delta = $derived(sel.length > 0);
  const how = (n: number) => `${delta ? 'добавит' : plural(n, 'подойдёт', 'подойдут', 'подойдут')} ${n} ${plural(n, 'вид', 'вида', 'видов')}`;
  const cap = (s: string) => s[0].toUpperCase() + s.slice(1);

  const close = () => { open = false; };
  function setOpen(v: boolean, refocus = false) {
    open = v;
    if (v) {
      if (closeOpen && closeOpen !== close) closeOpen();
      closeOpen = close;
      q = ''; queueMicrotask(() => qEl?.focus());
      if (options.length > FIRST) { limit = FIRST; afterPaint(() => { limit = Infinity; }); }
    } else {
      if (closeOpen === close) closeOpen = null;
      if (refocus) btn?.focus();
    }
  }
  onMount(() => {
    const down = (e: PointerEvent) => { if (open && root && !root.contains(e.target as Node)) setOpen(false); };
    document.addEventListener('pointerdown', down);
    return () => { document.removeEventListener('pointerdown', down); if (closeOpen === close) closeOpen = null; };
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
  function onRowKey(e: KeyboardEvent, k: string) {
    if (e.key === 'Enter') { e.preventDefault(); onpick(k); }
  }
  function onQKey(e: KeyboardEvent) {
    // Enter in the search: with one match, toggle it
    if (e.key === 'Enter') { e.preventDefault(); if (shown.length === 1) onpick(shown[0].key); }
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
    <div class="dd" id={`pp-${uid}`} role="group" aria-label={name}>
      <div class="pp-top">
        <input type="search" class="ppq" bind:this={qEl} bind:value={q} onkeydown={onQKey}
          {placeholder} aria-label={searchLabel} autocomplete="off" />
      </div>
      <ul class="pp-list" bind:this={listEl}>
        {#each shown.length > limit ? shown.slice(0, limit) : shown as o (o.key)}
          {@const on = sel.includes(o.key)}
          {@const n = counts ? (counts[o.key] ?? 0) : null}
          {@const tip = [o.hint, n != null && !on ? cap(how(n)) : null].filter(Boolean).join('. ')}
          <li>
            <label class="pp-row" class:zero={n === 0 && !on} title={tip || undefined}>
              <input type="checkbox" checked={on} onchange={() => onpick(o.key)} onkeydown={(e) => onRowKey(e, o.key)}
                aria-label={n != null && !on ? `${o.label}: ${how(n)}` : o.label} />
              <span class="pp-nm">{o.label}{#if o.sub}<span class="pp-sub" class:plain={o.plain}>{o.sub}</span>{/if}</span>
              {#if n != null && !on}<span class="pp-cnt" aria-hidden="true">{delta ? `+${n}` : n}</span>{/if}
            </label>
          </li>
        {/each}
        {#if shown.length === 0}<li class="pp-none">{noneText}</li>{/if}
      </ul>
      <div class="pp-foot">
        {#if sel.length}<button type="button" class="pp-lnk" onclick={() => { onclear(); qEl?.focus(); }}>Снять все</button>{/if}
        <button type="button" class="pp-ok" onclick={() => setOpen(false, true)}>Готово</button>
      </div>
    </div>
  {/if}
</div>

<style>
  .pp { position: relative; min-width: 0; }
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
  .pp-sub { margin-left: 6px; font-style: italic; color: var(--muted); font-size: .78rem; }
  .pp-sub.plain { font-style: normal; }
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
