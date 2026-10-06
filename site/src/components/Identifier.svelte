<script lang="ts">
  /**
   * Identifier by traits (/identify/). Chip groups come from content/traits.yaml: OR within a group, AND across groups.
   * The place (whole route / a day / a site) gives each species its likelihood state there (best over the place's
   * sites, as in lib/data), and the site-wide filter (lib/filter.ts, ListFilter.svelte) hides states as everywhere.
   * Species data is read from the page's <script id="identify-data"> JSON (see pages/identify/index.astro).
   * Facet counts (same place + filter): in a group with no selection a chip shows the absolute count if selected;
   * in a group with a selection an unselected chip shows «+N», the species it would add; selected chips show none.
   * Matching and counting are the species lists' own (lib/filter rowPasses, lib/facets listCounts, FilterBar
   * «Признаки»): each species becomes a list Row with its state at the place and its traits.
   */
  import { onMount } from 'svelte';
  import ListFilter from './ListFilter.svelte';
  import EndemicMark from './EndemicMark.svelte';
  import FacetChip from './FacetChip.svelte';
  import { filter, rowPasses, EMPTY_NARROW, type Row, type Narrow } from '../lib/filter';
  import { listCounts, rowFacets, trGroup, plural } from '../lib/facets';
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
  /** Per-species traits as «group:value» (lib/filter Row.tr) and their facet sets, built once per parse. */
  let trs = $derived(items ? items.map((it) => Object.entries(it.t).flatMap(([g, vs]) => vs.map((v) => `${g}:${v}`))) : []);
  let sets = $derived(trs.map((tr) => rowFacets({ st: '', int: false, nend: false, end: false, fam: '', sites: [], q: '', tr })));
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
  /** Each species as a list Row at the place: state there, «интересная» (int: as the tiles show it) and its traits. */
  let placed = $derived((items ?? []).map((it, i) => {
    const state = stateAt(it, placeSites);
    const int = it.x || it.hl.some((s) => placeSites.includes(s));
    const row: Row = { st: state, int: int || !!it.n || it.e, nend: !!it.n || it.e, end: it.e, fam: '', sites: [], q: '', tr: trs[i] };
    return { it, state, int, row };
  }));
  let narrow = $derived<Narrow>({ ...EMPTY_NARROW, tr: sel });
  let shown = $derived(placed.filter((p) => rowPasses(p.row, $filter, narrow))
    .sort((a, b) => Number(b.int) - Number(a.int) || RANK[b.state] - RANK[a.state] || (a.it.ru ?? a.it.en).localeCompare(b.it.ru ?? b.it.en, 'ru')));
  /** counts[trGroup(group)][value] over species at the place under the filter (lib/facets listCounts, as FilterBar) */
  const facetGroups = vocab.map((g) => ({ key: trGroup(g.key), values: g.values.map((v) => v.key) }));
  let counts = $derived(listCounts(placed.map((p) => p.row), sets, $filter, narrow, facetGroups));
  const dayPlaces = places.filter((p) => p.group === 'День');
  const sitePlaces = places.filter((p) => p.group === 'Место');
  // any other group (e.g. «Возможные выезды из Боготы») gets its own <optgroup> after «Место», in input order
  const extraGroups = [...new Set(places.map((p) => p.group).filter((g) => g && g !== 'День' && g !== 'Место'))]
    .map((g) => ({ label: g, items: places.filter((p) => p.group === g) }));
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
      {#each extraGroups as g (g.label)}
        <optgroup label={g.label}>
          {#each g.items as p (p.key)}<option value={p.key}>{p.label}</option>{/each}
        </optgroup>
      {/each}
    </select>
  </label>
  <ListFilter />
  {#each vocab as g, gi (g.key)}
    <fieldset class="grp">
      <legend><span>{g.label}{#if sel[g.key]?.length}<span class="n"> · {sel[g.key].length}</span>{/if}</span>{#if gi === 0}<button type="button" class="lnk clr" style:visibility={nSel > 0 ? 'visible' : 'hidden'} onclick={reset}>Сбросить</button>{/if}</legend>
      <div class="chips">
        {#each g.values as v (v.key)}
          <FacetChip label={v.label} hint={v.hint} on={sel[g.key]?.includes(v.key) ?? false} n={items ? (counts[trGroup(g.key)]?.[v.key] ?? 0) : null}
            delta={(sel[g.key]?.length ?? 0) > 0} onclick={() => toggle(g.key, v.key)} />
        {/each}
      </div>
    </fieldset>
  {/each}


  <div class="sum">
    <strong>{#if items}Подходят {shown.length} {plural(shown.length, 'вид', 'вида', 'видов')}{:else}Загрузка…{/if}</strong>
    {#if nSel > 0}<button type="button" class="reset" onclick={reset}>Сбросить признаки ({nSel})</button>{/if}
  </div>

  <div class="tiles">
    {#each shown as r (r.it.id)}
      <a class="tile" href={`${base}species/${r.it.id}/`}>
        <span class="ph">
          {#if r.it.photo}<img src={`${mediaBase}/${r.it.photo}`} alt="" loading="lazy" />{:else}<span class="empty">🐦</span>{/if}
          {#if r.int || r.it.e || r.it.n}
            <span class="badges">
              {#if r.int && !r.it.e && !r.it.n}<span class="b hl" title="интересная">★</span>{/if}
              {#if r.it.e}<EndemicMark kind="end" variant="tile" />{:else if r.it.n}<EndemicMark kind="near" variant="tile" />{/if}
            </span>
          {/if}
        </span>
        <span class="nm">{r.it.ru ?? r.it.en}</span>
        {#if r.it.ru && r.it.en !== r.it.ru}<span class="sec">{r.it.en}</span>{/if}
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
  .nm { font-weight: 600; padding-top: 4px; overflow-wrap: anywhere; hyphens: auto; }
  .sec { color: var(--muted); overflow-wrap: anywhere; hyphens: auto; }
  .stw { font-size: .75rem; font-weight: 600; }
  .stw.sure { color: var(--accent); }
  .stw.maybe { color: var(--muted); font-weight: 500; }
  .stw.unlikely { color: var(--muted); opacity: .6; font-weight: 400; }
  .foot { font-size: .8rem; margin-top: 20px; }
</style>
