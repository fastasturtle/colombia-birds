<script lang="ts">
  /**
   * All-species list: the shared FilterBar (search, likelihood, tag, families, sites, elevation) over rows built from
   * the items JSON; the predicate is lib/filter makePass, as on the static lists. State = best across route sites
   * (lib/data routeState). Search / families / sites / elevation / traits live in the URL (writeNarrow).
   */
  import { onMount } from 'svelte';
  import FilterBar from './FilterBar.svelte';
  import EndemicMark from './EndemicMark.svelte';
  import { filter, makePass, afterPaint, searchKey, normQ, readNarrow, writeNarrow, traitFlat, decodeTr, cleanTr, EMPTY_NARROW, type Narrow, type Row, type FamOpt, type SiteOpt, type TraitOpt } from '../lib/filter';
  import { plural } from '../lib/facets';
  type State = 'sure' | 'maybe' | 'unlikely';
  /** ea: ACO English name when it differs (searchable); si: space-separated indices into `sites` that list the species;
   * trs: the items' trait tokens (lib/traits traitToken), space-separated in item order, empty for species without a card */
  interface Item { id: string; sci: string; en: string; ru: string | null; family: string; endemic: boolean; near: boolean; elev: [number|null, number|null] | null; photo: string | null; state: State; int: boolean; ea?: string; si?: string }
  let { items, fams, sites, traits, trs, base, mediaBase }: { items: Item[]; fams: FamOpt[]; sites: SiteOpt[]; traits: TraitOpt[]; trs: string; base: string; mediaBase: string } = $props();
  const trFlat = traitFlat(traits);
  const trTok = trs.split(' ');
  const STATE_RU: Record<State, string> = { sure: 'точно', maybe: 'возможно', unlikely: 'вряд ли' };
  const LIMIT = 300;
  const famOf = new Map(fams.map((f) => [f.code, f]));
  const famName = (code: string) => { const f = famOf.get(code); return f ? (f.ru ?? f.en ?? f.sci) : code; };
  const rows: Row[] = items.map((s, i) => {
    const f = famOf.get(s.family);
    return {
      st: s.state, int: s.int || s.near || s.endemic, nend: s.near || s.endemic, end: s.endemic, fam: s.family,
      sites: s.si ? s.si.split(' ').map((i) => sites[+i].id) : [], elev: s.elev, q: normQ(searchKey([s.ru, s.en, s.ea, s.sci, f?.ru, f?.en])),
      tr: trTok[i] ? decodeTr(trTok[i], trFlat) : null,
    };
  });

  let u = $state<Narrow>({ ...EMPTY_NARROW });
  let ready = $state(false);
  onMount(() => {
    const r = readNarrow('');
    const fk = new Set(fams.map((f) => f.code)), sk = new Set(sites.map((s) => s.id));
    u = { ...r, fam: r.fam.filter((c) => fk.has(c)), site: r.site.filter((s) => sk.has(s)), tr: cleanTr(r.tr, traits) };
    ready = true;
  });
  let timer: ReturnType<typeof setTimeout> | undefined;
  $effect(() => {
    const snap = $state.snapshot(u) as Narrow;
    if (!ready) return;
    clearTimeout(timer);
    timer = setTimeout(() => writeNarrow('', snap), 300);
  });

  /** indices of the items that pass, in list order */
  let shown = $derived.by(() => {
    const pass = makePass($filter, $state.snapshot(u) as Narrow), out: number[] = [];
    for (let i = 0; i < rows.length; i++) if (pass(rows[i])) out.push(i);
    return out;
  });
  /** the first LIMIT of them: the rows on screen */
  let vis = $derived(new Set(shown.slice(0, LIMIT)));
  /* Rendered rows: every item that has been on screen since load (at first the first LIMIT, as rendered on the server),
   * in list order; the ones not in `vis` are hidden. A filter change then only flips `hidden` on rows instead of
   * destroying and recreating up to LIMIT rows with their <img>. Rows never shown before are built GROW at a time, the
   * rest in the following frames, so one tap never builds hundreds of rows in one task. */
  const GROW = 40;
  const ever = new Uint8Array(items.length).fill(1, 0, LIMIT);
  let grow = $state(0);
  let growing = false;
  let pool = $derived.by(() => {
    void grow;
    let added = 0, more = false;
    for (const i of vis) if (!ever[i]) { if (added < GROW) { ever[i] = 1; added++; } else { more = true; break; } }
    if (more && !growing) { growing = true; afterPaint(() => { growing = false; grow++; }); }
    const out: number[] = [];
    for (let i = 0; i < ever.length; i++) if (ever[i]) out.push(i);
    return out;
  });
</script>

<FilterBar rows={rows} total={items.length} {fams} {sites} {traits} bind:u elev />
<p class="muted note">{shown.length > LIMIT ? `Показаны первые ${LIMIT}. ` : ''}«Точно», «возможно», «вряд ли» — лучшее по локациям маршрута.</p>
{#each pool as i (items[i].id)}
  {@const s = items[i]}
  <a class="row" href={`${base}species/${s.id}/`} hidden={!vis.has(i)}>
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
  /* rows off screen skip style, layout and paint (a filter change can show or hide hundreds); until laid out once a row
   * holds 107px, the height of one with two lines of names at phone width */
  .row { color: inherit; content-visibility: auto; contain-intrinsic-size: auto 107px; }
  .row[hidden] { display: none; }
  .row:hover { text-decoration: none; background: var(--chip); }
  .txt { min-width: 0; }
  .meta { display: flex; gap: 8px; align-items: center; }
  .stw { font-size: .75rem; font-weight: 600; }
  .stw.sure { color: var(--accent); }
  .stw.maybe { color: var(--muted); font-weight: 500; }
  .stw.unlikely { color: var(--muted); opacity: .6; font-weight: 400; }
  .star { color: var(--accent-2); margin-right: 4px; }
</style>
