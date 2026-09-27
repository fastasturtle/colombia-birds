<script lang="ts">
  /**
   * Identifier by traits (/identify/). Chip groups come from content/traits.yaml: OR within a group, AND across groups.
   * The place (whole route / a day / a site) gives each species its likelihood state there (best over the place's
   * sites, as in lib/data), and the site-wide filter (lib/filter.ts, ListFilter.svelte) hides states as everywhere.
   * Species data is read from the page's <script id="identify-data"> JSON (see pages/identify/index.astro).
   * Facet counts: every unselected chip shows how many species would match with it added (same place + filter).
   */
  import { onMount } from 'svelte';
  import ListFilter from './ListFilter.svelte';
  import { filter, passes, tierOf } from '../lib/filter';
  type State = 'sure' | 'maybe' | 'unlikely';
  interface Item { id: string; en: string; ru: string | null; photo: string | null; t: Record<string, string[]>; st: Record<string, 's' | 'm'>; hl: string[]; x: boolean; e: boolean; n?: boolean }
  interface Group { key: string; label: string; values: { key: string; label: string; hint: string | null }[] }
  interface Place { key: string; label: string; group: string; sites: string[] }
  let { vocab, places, mediaBase, total, marked }: { vocab: Group[]; places: Place[]; mediaBase: string; total: number; marked: number } = $props();

  const base = import.meta.env.BASE_URL;
  const KEY = 'cb.identify';
  const STATE_RU: Record<State, string> = { sure: 'точно', maybe: 'возможно', unlikely: 'вряд ли' };
  const RANK: Record<State, number> = { sure: 2, maybe: 1, unlikely: 0 };

  let items = $state<Item[] | null>(null);
  /** Per-species trait sets, built once per parse: sets[i][group] for items[i]. */
  let sets = $derived(items ? items.map((it) => Object.fromEntries(Object.entries(it.t).map(([g, vs]) => [g, new Set(vs)])) as Record<string, Set<string>>) : []);
  let sel = $state<Record<string, string[]>>({});
  let place = $state('any');

  onMount(() => {
    try { items = JSON.parse(document.getElementById('identify-data')?.textContent || '[]'); } catch { items = []; }
    try {
      const v = JSON.parse(localStorage.getItem(KEY) || 'null');
      if (v && places.some((p) => p.key === v.place)) place = v.place;
      if (v?.sel && typeof v.sel === 'object') {
        const ok: Record<string, string[]> = {};
        for (const g of vocab) {
          const allowed = new Set(g.values.map((x) => x.key));
          const xs = Array.isArray(v.sel[g.key]) ? v.sel[g.key].filter((k: unknown) => typeof k === 'string' && allowed.has(k)) : [];
          if (xs.length) ok[g.key] = xs;
        }
        sel = ok;
      }
    } catch { /* private mode, bad JSON */ }
  });
  $effect(() => {
    const v = JSON.stringify({ place, sel });
    try { localStorage.setItem(KEY, v); } catch { /* ignore */ }
  });

  const toggle = (g: string, v: string) => {
    const cur = sel[g] ?? [];
    const next = cur.includes(v) ? cur.filter((x) => x !== v) : [...cur, v];
    const copy = { ...sel };
    if (next.length) copy[g] = next; else delete copy[g];
    sel = copy;
  };
  const reset = () => { sel = {}; };
  let nSel = $derived(Object.values(sel).reduce((a, b) => a + b.length, 0));

  let placeSites = $derived(places.find((p) => p.key === place)?.sites ?? []);
  const stateAt = (it: Item, sites: string[]): State => {
    let best: State = 'unlikely';
    for (const s of sites) {
      const v = it.st[s];
      if (v === 's') return 'sure';
      if (v === 'm') best = 'maybe';
    }
    return best;
  };
  let rows = $derived.by(() => {
    if (!items) return [];
    const groups = Object.entries(sel).filter(([, v]) => v.length);
    return items
      .filter((it) => groups.every(([g, vs]) => (it.t[g] ?? []).some((x) => vs.includes(x))))
      .map((it) => {
        const state = stateAt(it, placeSites);
        const int = it.x || it.hl.some((s) => placeSites.includes(s));
        return { it, state, int };
      })
      .sort((a, b) => Number(b.int) - Number(a.int) || RANK[b.state] - RANK[a.state] || a.it.en.localeCompare(b.it.en));
  });
  let shown = $derived(rows.filter((r) => passes($filter, r.state, tierOf(r.int, !!r.it.n, r.it.e))));
  /**
   * counts[group][value] = species shown (place + filter) if that chip were added to the selection:
   * OR within the chip's group (union with what is already selected there), AND with every other group.
   * One pass over species: a species matching all groups adds to every chip it has, plus to every chip of a
   * selected group; a species failing exactly one group adds only to that group's chips it has.
   */
  let counts = $derived.by(() => {
    const out: Record<string, Record<string, number>> = {};
    for (const g of vocab) out[g.key] = Object.fromEntries(g.values.map((v) => [v.key, 0]));
    if (!items) return out;
    const f = $filter;
    const selG = vocab.filter((g) => sel[g.key]?.length).map((g) => ({ key: g.key, vs: sel[g.key] }));
    items.forEach((it, i) => {
      const int = it.x || it.hl.some((s) => placeSites.includes(s));
      if (!passes(f, stateAt(it, placeSites), tierOf(int, !!it.n, it.e))) return;
      const ts = sets[i];
      let fail: string | null = null;
      for (const { key, vs } of selG) {
        const t = ts[key];
        if (!t || !vs.some((v) => t.has(v))) { if (fail) return; fail = key; }
      }
      for (const g of vocab) {
        if (fail && g.key !== fail) continue;
        const c = out[g.key], t = ts[g.key];
        if (!fail && sel[g.key]?.length) { for (const k in c) c[k]++; continue; }
        if (t) for (const v of t) if (v in c) c[v]++;
      }
    });
    return out;
  });
  let hidden = $derived(rows.length - shown.length);
  const plural = (n: number, a: string, b: string, c: string) => {
    const m10 = n % 10, m100 = n % 100;
    return m10 === 1 && m100 !== 11 ? a : m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14) ? b : c;
  };
  const dayPlaces = places.filter((p) => p.group === 'День');
  const sitePlaces = places.filter((p) => p.group === 'Место');
</script>

<div class="idf">
  <label class="place">
    <span>Где</span>
    <select bind:value={place}>
      <option value="any">Весь маршрут</option>
      <optgroup label="День">
        {#each dayPlaces as p (p.key)}<option value={p.key}>{p.label}</option>{/each}
      </optgroup>
      <optgroup label="Место">
        {#each sitePlaces as p (p.key)}<option value={p.key}>{p.label}</option>{/each}
      </optgroup>
    </select>
  </label>
  <ListFilter />
  {#each vocab as g, gi (g.key)}
    <fieldset class="grp">
      <legend><span>{g.label}{#if sel[g.key]?.length}<span class="n"> · {sel[g.key].length}</span>{/if}</span>{#if gi === 0}<button type="button" class="lnk clr" style:visibility={nSel > 0 ? 'visible' : 'hidden'} onclick={reset}>Сбросить</button>{/if}</legend>
      <div class="chips">
        {#each g.values as v (v.key)}
          {@const on = sel[g.key]?.includes(v.key) ?? false}
          {@const n = counts[g.key]?.[v.key] ?? 0}
          <button type="button" class="chip-b" class:zero={items !== null && !on && n === 0} aria-pressed={on} title={v.hint ?? undefined} onclick={() => toggle(g.key, v.key)}>{v.label}{#if items && !on}<span class="cnt">{n}</span>{/if}</button>
        {/each}
      </div>
    </fieldset>
  {/each}


  <div class="sum">
    <strong>{#if items}Подходят {shown.length} {plural(shown.length, 'вид', 'вида', 'видов')}{:else}Загрузка…{/if}</strong>
    {#if hidden > 0}<span class="muted"> · ещё {hidden} скрыто фильтром · <button type="button" class="lnk" onclick={() => filter.update((f) => ({ ...f, level: 'all', tag: 'all' }))}>показать</button></span>{/if}
    {#if nSel > 0}<button type="button" class="reset" onclick={reset}>Сбросить признаки ({nSel})</button>{/if}
  </div>

  <div class="tiles">
    {#each shown as r (r.it.id)}
      <a class="tile" href={`${base}species/${r.it.id}/`}>
        <span class="ph">
          {#if r.it.photo}<img src={`${mediaBase}/${r.it.photo}`} alt="" loading="lazy" />{:else}<span class="empty">🐦</span>{/if}
          {#if r.int || r.it.e || r.it.n}
            <span class="badges">
              {#if r.int}<span class="b hl" title="интересная">★</span>{/if}
              {#if r.it.e}<span class="b en" title="эндемик Колумбии">энд.</span>{:else if r.it.n}<span class="b ne" title="почти-эндемик Колумбии">п.-энд.</span>{/if}
            </span>
          {/if}
        </span>
        <span class="nm">{r.it.en}</span>
        {#if r.it.ru}<span class="ru">{r.it.ru}</span>{/if}
        <span class={`stw ${r.state}`}>{STATE_RU[r.state]}</span>
      </a>
    {/each}
  </div>
  {#if items && shown.length === 0}<p class="muted">Под эти признаки и фильтр видов нет. Сними часть признаков или расширь фильтр.</p>{/if}
  <p class="foot muted">Размечено {marked} из {total} {plural(total, 'вида', 'видов', 'видов')}: виды без разметки определитель не показывает. Размер, цвета и приметы — со слов карточек вида; «точно/возможно» — по осенним записям GBIF.</p>
</div>

<style>
  .grp { border: 0; margin: 0 0 6px; padding: 0; min-width: 0; }
  legend { font-weight: 600; font-size: .9rem; padding: 0; margin-bottom: 4px; }
  .n { color: var(--accent); }
  .chips { display: flex; flex-wrap: wrap; gap: 5px; }
  legend { display: flex; align-items: center; width: 100%; }
  .lnk.clr { margin: -10px 0 -10px auto; font-size: .85rem; font-weight: 400; padding: 10px 2px; }
  .chip-b {
    display: inline-flex; align-items: center; gap: 6px;
    min-height: 40px; padding: 0 10px; border: 1px solid var(--line); border-radius: 999px; background: var(--card);
    color: var(--fg); font: inherit; font-size: .82rem; cursor: pointer; white-space: nowrap;
  }
  .cnt { font-size: .75rem; line-height: 1; padding: 2px 6px; border-radius: 999px; background: var(--chip); color: var(--muted); font-variant-numeric: tabular-nums; }
  .chip-b.zero { color: var(--muted); border-style: dashed; background: transparent; }
  .chip-b.zero .cnt { opacity: .7; }
  .chip-b[aria-pressed="true"] { background: var(--accent); border-color: var(--accent); color: #fff; }
  @media (prefers-color-scheme: dark) { .chip-b[aria-pressed="true"] { color: #10150f; } }
  .place { display: flex; align-items: center; gap: 8px; margin: 4px 0 0; font-weight: 600; font-size: .9rem; }
  .place select {
    flex: 1; min-width: 0; min-height: 40px; padding: 0 10px; border: 1px solid var(--line); border-radius: 10px;
    background: var(--card); color: var(--fg); font: inherit; font-weight: 400;
  }
  .sum { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 10px; margin: 8px -16px 10px; padding: 8px 16px;
    position: sticky; bottom: 0; z-index: 5; background: var(--bg); border-top: 1px solid var(--line); }
  .lnk { font: inherit; color: var(--accent); background: none; border: 0; padding: 6px 2px; cursor: pointer; text-decoration: underline; }
  .reset { margin-left: auto; font: inherit; font-size: .85rem; min-height: 36px; padding: 0 12px; border: 1px solid var(--line); border-radius: 999px; background: var(--card); color: var(--fg); cursor: pointer; }
  .tiles { display: grid; gap: 12px 10px; grid-template-columns: repeat(auto-fill, minmax(104px, 1fr)); }
  .tile { color: inherit; display: flex; flex-direction: column; min-width: 0; font-size: .78rem; line-height: 1.25; }
  .tile:hover { text-decoration: none; }
  .tile:hover .nm { text-decoration: underline; }
  .ph { position: relative; display: block; width: 100%; aspect-ratio: 1; border-radius: 10px; overflow: hidden; background: var(--chip); }
  .ph img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .empty { display: grid; place-items: center; height: 100%; color: var(--muted); font-size: 1.6rem; }
  .badges { position: absolute; top: 4px; left: 4px; display: flex; gap: 3px; }
  .b { font-size: .68rem; font-weight: 700; line-height: 1; padding: 3px 5px; border-radius: 6px; color: #fff; background: rgba(0,0,0,.6); }
  .b.hl { background: var(--accent-2); }
  .b.en { background: #14532d; }
  .b.ne { background: #3f6212; }
  .nm { font-weight: 600; padding-top: 4px; overflow-wrap: anywhere; hyphens: auto; }
  .ru { color: var(--muted); overflow-wrap: anywhere; hyphens: auto; }
  .stw { font-size: .75rem; font-weight: 600; }
  .stw.sure { color: var(--accent); }
  .stw.maybe { color: var(--muted); font-weight: 500; }
  .stw.unlikely { color: var(--muted); opacity: .6; font-weight: 400; }
  .foot { font-size: .8rem; margin-top: 20px; }
</style>
