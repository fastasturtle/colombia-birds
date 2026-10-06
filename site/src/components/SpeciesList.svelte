<script lang="ts">
  /**
   * All-species list: the shared FilterBar (search, likelihood, tag, families, sites, elevation) over rows built from
   * the items JSON; the predicate is lib/filter rowPasses, as on the static lists. State = best across route sites
   * (lib/data routeState). Search / families / sites / elevation live in the URL (writeNarrow).
   */
  import { onMount } from 'svelte';
  import FilterBar from './FilterBar.svelte';
  import EndemicMark from './EndemicMark.svelte';
  import { filter, rowPasses, searchKey, normQ, readNarrow, writeNarrow, EMPTY_NARROW, type Narrow, type Row, type FamOpt, type SiteOpt } from '../lib/filter';
  import { plural } from '../lib/facets';
  type State = 'sure' | 'maybe' | 'unlikely';
  /** ea: ACO English name when it differs (searchable); si: space-separated indices into `sites` that list the species */
  interface Item { id: string; sci: string; en: string; ru: string | null; family: string; endemic: boolean; near: boolean; elev: [number|null, number|null] | null; photo: string | null; state: State; int: boolean; ea?: string; si?: string }
  let { items, fams, sites, base, mediaBase }: { items: Item[]; fams: FamOpt[]; sites: SiteOpt[]; base: string; mediaBase: string } = $props();
  const STATE_RU: Record<State, string> = { sure: 'точно', maybe: 'возможно', unlikely: 'вряд ли' };
  const LIMIT = 300;
  const famOf = new Map(fams.map((f) => [f.code, f]));
  const famName = (code: string) => { const f = famOf.get(code); return f ? (f.ru ?? f.en ?? f.sci) : code; };
  const rows: Row[] = items.map((s) => {
    const f = famOf.get(s.family);
    return {
      st: s.state, int: s.int || s.near || s.endemic, nend: s.near || s.endemic, end: s.endemic, fam: s.family,
      sites: s.si ? s.si.split(' ').map((i) => sites[+i].id) : [], elev: s.elev, q: normQ(searchKey([s.ru, s.en, s.ea, s.sci, f?.ru, f?.en])),
    };
  });

  let u = $state<Narrow>({ ...EMPTY_NARROW });
  let ready = $state(false);
  onMount(() => {
    const r = readNarrow('');
    const fk = new Set(fams.map((f) => f.code)), sk = new Set(sites.map((s) => s.id));
    u = { ...r, fam: r.fam.filter((c) => fk.has(c)), site: r.site.filter((s) => sk.has(s)) };
    ready = true;
  });
  let timer: ReturnType<typeof setTimeout> | undefined;
  $effect(() => {
    const snap = $state.snapshot(u) as Narrow;
    if (!ready) return;
    clearTimeout(timer);
    timer = setTimeout(() => writeNarrow('', snap), 300);
  });

  let shown = $derived(items.filter((_, i) => rowPasses(rows[i], $filter, u)));
</script>

<FilterBar rows={rows} total={items.length} {fams} {sites} bind:u elev />
<p class="muted note">{shown.length > LIMIT ? `Показаны первые ${LIMIT}. ` : ''}«Точно» и «возможно» — хотя бы на одной локации маршрута.</p>
{#each shown.slice(0, LIMIT) as s (s.id)}
  <a class="row" href={`${base}species/${s.id}/`}>
    {#if s.photo}<img class="thumb" src={`${mediaBase}/${s.photo}`} alt="" loading="lazy" />{:else}<div class="thumb empty">🐦</div>{/if}
    <div class="txt">
      <div>{#if s.int && !s.endemic && !s.near}<b class="star" title="интересная">★</b>{/if}<strong>{s.ru ?? s.en}</strong></div>
      <div class="muted">{#if s.ru && s.en !== s.ru}{`${s.en} · `}{/if}<span class="sci">{s.sci}</span> · <span>{famName(s.family)}</span></div>
      <div class="meta"><span class={`stw ${s.state}`}>{STATE_RU[s.state]}</span>{#if s.endemic}<EndemicMark kind="end" />{:else if s.near}<EndemicMark kind="near" />{/if}</div>
    </div>
  </a>
{/each}
{#if shown.length === 0}<p class="muted">Ничего не найдено. Измени поиск или сбрось фильтры.</p>{/if}
{#if shown.length > LIMIT}<p class="muted note">Ещё {shown.length - LIMIT} {plural(shown.length - LIMIT, 'вид', 'вида', 'видов')}: уточни поиск или фильтры.</p>{/if}

<style>
  .note { font-size: .85rem; margin: 0 0 6px; }
  .row { color: inherit; }
  .row:hover { text-decoration: none; background: var(--chip); }
  .txt { min-width: 0; }
  .meta { display: flex; gap: 8px; align-items: center; }
  .stw { font-size: .75rem; font-weight: 600; }
  .stw.sure { color: var(--accent); }
  .stw.maybe { color: var(--muted); font-weight: 500; }
  .stw.unlikely { color: var(--muted); opacity: .6; font-weight: 400; }
  .star { color: var(--accent-2); margin-right: 4px; }
</style>
