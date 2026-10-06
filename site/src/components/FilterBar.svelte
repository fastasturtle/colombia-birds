<script lang="ts">
  /**
   * The one filter control of every species list (/species/, day, site and family pages).
   * Collapsed: search + «Фильтры» (badge = active non-default filters) + «показано N из M» + removable chips of the
   * active filters. Expanded (remembered in localStorage `cb.filter.open`): the site-wide ListFilter (likelihood, tag),
   * families and sites as facet chips with counts (lib/facets.ts), elevation where `elev` is set, and «Признаки» (its
   * own fold, `cb.filter.traits`): trait groups of content/traits.yaml, OR within a group, AND across groups.
   * `?panel=traits` in the URL (the «Определить» nav item, the old /identify/ page) opens the panel and «Признаки» for
   * this visit and scrolls «Признаки» into view (`?panel=1`: the panel only); nothing is saved, and the flag is dropped
   * from the URL once read.
   * Families / sites only show when the list has more than one; «Признаки» when some row has traits (a species card).
   * Long chip groups (> FOLD_FROM chips) fold: chips with a non-zero count (and selected ones) first, «ещё N» reveals
   * the rest. State: level + tag in the global `filter` store; search, families, sites, elevation, traits in `u`
   * (bound; the parent keeps it in the URL and applies it).
   * Rows: one descriptor per list row (lib/filter Row); null while the parent is still reading them.
   */
  import { onMount } from 'svelte';
  import ListFilter from './ListFilter.svelte';
  import FacetChip from './FacetChip.svelte';
  import { filter, normQ, rowPasses, trCount, DEFAULT_FILTER, TAG_LABEL, type Narrow, type Row, type FamOpt, type SiteOpt, type TraitOpt } from '../lib/filter';
  import { listCounts, rowFacets, noTraitsHidden, trGroup, plural } from '../lib/facets';

  interface Props { rows: Row[] | null; total: number; fams: FamOpt[]; sites: SiteOpt[]; traits?: TraitOpt[]; u: Narrow; elev?: boolean }
  let { rows, total, fams, sites, traits = [], u = $bindable(), elev = false }: Props = $props();

  const OPEN_KEY = 'cb.filter.open', TR_KEY = 'cb.filter.traits';
  let open = $state(false);
  let trOpen = $state(false);
  /** `?panel=traits`: scroll «Признаки» into view once it is rendered (static lists read their rows after mount) */
  let toTraits = $state(false);
  let trsEl = $state<HTMLElement | null>(null);
  onMount(() => {
    try { open = localStorage.getItem(OPEN_KEY) === '1'; trOpen = localStorage.getItem(TR_KEY) === '1'; } catch { /* private mode */ }
    const url = new URL(location.href), panel = url.searchParams.get('panel');
    if (panel != null) {
      open = true;
      if (panel === 'traits') trOpen = toTraits = true;
      url.searchParams.delete('panel');
      history.replaceState(history.state, '', url.href);
    }
  });
  $effect(() => {
    if (!toTraits || !trsEl) return;
    toTraits = false;
    const head = document.querySelector<HTMLElement>('header.top');
    window.scrollTo({ top: trsEl.getBoundingClientRect().top + window.scrollY - (head?.offsetHeight ?? 0) - 8 });
  });
  const toggleOpen = () => {
    open = !open;
    try { localStorage.setItem(OPEN_KEY, open ? '1' : '0'); } catch { /* ignore */ }
  };
  const toggleTrOpen = () => {
    trOpen = !trOpen;
    try { localStorage.setItem(TR_KEY, trOpen ? '1' : '0'); } catch { /* ignore */ }
  };
  const uid = Math.random().toString(36).slice(2, 8);

  const famName = (f: FamOpt) => f.ru ?? f.en ?? f.sci;
  const famOf = $derived(new Map(fams.map((f) => [f.code, f])));
  const siteOf = $derived(new Map(sites.map((s) => [s.id, s])));
  const trLabel = $derived(new Map(traits.flatMap((g) => g.values.map((v) => [`${g.key}:${v.key}`, `${g.label}: ${v.label}`] as const))));

  let sets = $derived((rows ?? []).map(rowFacets));
  let nWithTr = $derived((rows ?? []).filter((r) => r.tr).length);
  let showTraits = $derived(traits.length > 0 && nWithTr > 0);
  let shown = $derived(rows ? rows.filter((r) => rowPasses(r, $filter, u)).length : null);
  let groups = $derived([
    { key: 'fam', values: fams.map((x) => x.code) },
    { key: 'site', values: sites.map((x) => x.id) },
    ...(showTraits ? traits.map((g) => ({ key: trGroup(g.key), values: g.values.map((v) => v.key) })) : []),
  ]);
  let counts = $derived(rows ? listCounts(rows, sets, $filter, u, groups) : {});
  /** rows hidden only because they have no traits (some trait is selected) */
  let noTr = $derived(rows ? noTraitsHidden(rows, $filter, u) : 0);
  let nTr = $derived(trCount(u.tr));

  const toggle = (g: 'fam' | 'site', v: string) => {
    const cur = u[g];
    u[g] = cur.includes(v) ? cur.filter((x) => x !== v) : [...cur, v];
  };
  const toggleTr = (g: string, v: string) => {
    const cur = u.tr[g] ?? [];
    const next = cur.includes(v) ? cur.filter((x) => x !== v) : [...cur, v];
    const copy = { ...u.tr };
    if (next.length) copy[g] = next; else delete copy[g];
    u.tr = copy;
  };

  type Active = { key: string; label: string; drop: () => void };
  let active = $derived.by<Active[]>(() => {
    const out: Active[] = [];
    const f = $filter;
    if (f.level !== DEFAULT_FILTER.level) out.push({ key: 'lv', label: f.level === 'sure' ? 'Только «точно»' : 'Включая «вряд ли»', drop: () => filter.update((x) => ({ ...x, level: DEFAULT_FILTER.level })) });
    if (f.tag !== DEFAULT_FILTER.tag) out.push({ key: 'tag', label: `${f.tag === 'end' ? '◆' : f.tag === 'near' ? '◇' : '★'} ${TAG_LABEL[f.tag]}`, drop: () => filter.update((x) => ({ ...x, tag: DEFAULT_FILTER.tag })) });
    for (const c of u.fam) { const fo = famOf.get(c); out.push({ key: `f:${c}`, label: fo ? famName(fo) : c, drop: () => toggle('fam', c) }); }
    for (const s of u.site) out.push({ key: `s:${s}`, label: siteOf.get(s)?.name ?? s, drop: () => toggle('site', s) });
    for (const [g, vs] of Object.entries(u.tr)) for (const v of vs) out.push({ key: `t:${g}:${v}`, label: trLabel.get(`${g}:${v}`) ?? v, drop: () => toggleTr(g, v) });
    if (u.elev != null) out.push({ key: 'elev', label: `высота ${u.elev} м`, drop: () => (u.elev = null) });
    return out;
  });
  const reset = () => {
    filter.set({ ...DEFAULT_FILTER });
    u.q = ''; u.fam = []; u.site = []; u.elev = null; u.tr = {};
  };

  let famQ = $state('');
  const FAM_SEARCH_FROM = 15;
  let famsShown = $derived.by(() => {
    const t = normQ(famQ.trim());
    if (!t) return fams;
    return fams.filter((f) => u.fam.includes(f.code) || [f.ru, f.en, f.sci].some((x) => x && normQ(x).includes(t)));
  });

  /* Fold of long chip groups: chips with a count (and selected ones) first, in their order; «ещё N» shows the rest. */
  const FOLD_FROM = 12;
  type Opt = { key: string; label: string; sub?: string | null; hint?: string | null };
  let unfolded = $state<Record<string, boolean>>({});
  function split(g: string, opts: Opt[], sel: string[], fold: boolean): { main: Opt[]; rest: Opt[] } {
    const c = counts[g];
    if (!fold || !rows || !c || opts.length <= FOLD_FROM) return { main: opts, rest: [] };
    const main: Opt[] = [], rest: Opt[] = [];
    for (const o of opts) (sel.includes(o.key) || (c[o.key] ?? 0) > 0 ? main : rest).push(o);
    return { main, rest };
  }
  let famOpts = $derived(famsShown.map((f) => ({ key: f.code, label: famName(f), sub: f.sci, hint: f.ru && f.en ? `${f.en} · ${f.sci}` : f.sci })));
  let siteOpts = $derived(sites.map((s) => ({ key: s.id, label: s.name })));
</script>

{#snippet chipGroup(g: string, opts: Opt[], sel: string[], onpick: (v: string) => void, fold: boolean)}
  {@const sp = split(g, opts, sel, fold)}
  {#each [...sp.main, ...(unfolded[g] ? sp.rest : [])] as o (o.key)}
    <FacetChip label={o.label} sub={o.sub} hint={o.hint} on={sel.includes(o.key)} n={rows ? (counts[g]?.[o.key] ?? 0) : null}
      delta={sel.length > 0} onclick={() => onpick(o.key)} />
  {/each}
  {#if sp.rest.length}
    <button type="button" class="more" aria-expanded={!!unfolded[g]} onclick={() => (unfolded[g] = !unfolded[g])}>
{unfolded[g] ? 'свернуть' : `ещё ${sp.rest.length}`}</button>
  {/if}
{/snippet}

<div class="fb" role="search">
  <div class="bar">
    <input type="search" class="q" bind:value={u.q} placeholder="Поиск вида"
      aria-label="Поиск по названию: русскому, английскому, латинскому или семейства" autocomplete="off" />
    <button type="button" class="tg" aria-expanded={open} aria-controls={`fb-panel-${uid}`} onclick={toggleOpen}>
      Фильтры{#if active.length}<span class="badge" aria-label={`активно: ${active.length}`}>{active.length}</span>{/if}<span class="car" aria-hidden="true">▾</span>
    </button>
  </div>
  <div class="line">
    <span class="count" aria-live="polite">{#if shown != null}показано <b>{shown}</b> из {total}{#if noTr > 0}<span class="ntr">{' · '}ещё {noTr} {plural(noTr, 'вид', 'вида', 'видов')} без описания признаков {plural(noTr, 'скрыт', 'скрыты', 'скрыты')}</span>{/if}{/if}</span>
    {#each active as a (a.key)}
      <button type="button" class="ac" onclick={a.drop} aria-label={`Убрать фильтр: ${a.label}`}>{a.label}<span aria-hidden="true" class="x">✕</span></button>
    {/each}
    {#if active.length || u.q.trim()}<button type="button" class="lnk" onclick={reset}>Сбросить</button>{/if}
  </div>
  {#if open}
    <div class="panel" id={`fb-panel-${uid}`}>
      <ListFilter />
      {#if fams.length > 1}
        <fieldset class="grp">
          <legend>Семейство{#if u.fam.length}<span class="n">{" · "}{u.fam.length}</span>{/if}</legend>
          {#if fams.length > FAM_SEARCH_FROM}
            <input type="search" class="fq" bind:value={famQ} placeholder={`Найти среди ${fams.length} семейств`} aria-label="Найти семейство" autocomplete="off" />
          {/if}
          <div class="chips">
            {@render chipGroup('fam', famOpts, u.fam, (v) => toggle('fam', v), !famQ.trim())}
            {#if famsShown.length === 0}<span class="muted none">Нет такого семейства</span>{/if}
          </div>
        </fieldset>
      {/if}
      {#if sites.length > 1}
        <fieldset class="grp">
          <legend>Место{#if u.site.length}<span class="n">{" · "}{u.site.length}</span>{/if}</legend>
          <div class="chips">
            {@render chipGroup('site', siteOpts, u.site, (v) => toggle('site', v), true)}
          </div>
        </fieldset>
      {/if}
      {#if elev}
        <label class="elev">Встречается на высоте <input type="number" min="0" max="5000" step="100" placeholder="напр. 2000" bind:value={u.elev} /> м</label>
      {/if}
      {#if showTraits}
        <div class="trs" bind:this={trsEl}>
          <button type="button" class="trh" aria-expanded={trOpen} aria-controls={`fb-tr-${uid}`} onclick={toggleTrOpen}>
            <span>Признаки{#if nTr}<span class="n">{" · "}{nTr}</span>{/if}</span><span class="car" aria-hidden="true">▾</span>
          </button>
          {#if trOpen}
            <div id={`fb-tr-${uid}`}>
              <p class="muted trn">Отметь, что успел разглядеть: внутри группы подходит любой из отмеченных, между группами нужны все. Признаки описаны у {nWithTr} из {rows?.length ?? 0} {plural(rows?.length ?? 0, 'вида', 'видов', 'видов')} списка.</p>
              {#if noTr > 0}<p class="trw">Ещё {noTr} {plural(noTr, 'вид', 'вида', 'видов')} без описания признаков {plural(noTr, 'скрыт', 'скрыты', 'скрыты')}.</p>{/if}
              {#each traits as g (g.key)}
                <fieldset class="grp">
                  <legend>{g.label}{#if u.tr[g.key]?.length}<span class="n">{" · "}{u.tr[g.key].length}</span>{/if}</legend>
                  <div class="chips">
                    {@render chipGroup(trGroup(g.key), g.values, u.tr[g.key] ?? [], (v) => toggleTr(g.key, v), true)}
                  </div>
                </fieldset>
              {/each}
            </div>
          {/if}
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .fb { margin: 8px 0 12px; }
  .bar { display: flex; gap: 8px; align-items: stretch; }
  .q { flex: 1 1 auto; min-width: 0; min-height: 44px; padding: 0 12px; border: 1px solid var(--line); border-radius: 10px; background: var(--card); color: var(--fg); font: inherit; font-size: 1rem; }
  .tg {
    flex: none; display: inline-flex; align-items: center; gap: 6px; min-height: 44px; padding: 0 12px;
    border: 1px solid var(--line); border-radius: 10px; background: var(--card); color: var(--fg); font: inherit; font-size: .92rem; cursor: pointer;
  }
  .tg[aria-expanded="true"] { border-color: var(--accent); }
  .tg[aria-expanded="true"] .car, .trh[aria-expanded="true"] .car { transform: rotate(180deg); }
  .car { color: var(--muted); font-size: .8rem; transition: transform .15s; }
  .badge { min-width: 20px; height: 20px; padding: 0 6px; border-radius: 999px; background: var(--accent); color: #fff; font-size: .75rem; font-weight: 700; line-height: 20px; text-align: center; }
  @media (prefers-color-scheme: dark) { :global(:root:not([data-theme="light"])) .badge { color: #10150f; } }
  :global(:root[data-theme="dark"]) .badge { color: #10150f; }
  .line { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 6px; margin-top: 6px; min-height: 24px; }
  .count { color: var(--muted); font-size: .85rem; margin-right: 4px; font-variant-numeric: tabular-nums; }
  .count b { color: var(--fg); }
  .ac {
    display: inline-flex; align-items: center; gap: 6px; min-height: 32px; padding: 0 10px; border: 0; border-radius: 999px;
    background: var(--chip); color: var(--fg); font: inherit; font-size: .8rem; cursor: pointer; max-width: 100%;
  }
  .ac .x { color: var(--muted); font-size: .7rem; }
  .lnk { font: inherit; font-size: .85rem; color: var(--accent); background: none; border: 0; padding: 6px 2px; cursor: pointer; text-decoration: underline; }
  .panel { margin-top: 8px; padding: 10px 12px 4px; border: 1px solid var(--line); border-radius: 12px; background: var(--card); }
  .panel :global(.lf) { margin: 0 0 8px; }
  /* phones: no side padding, so the ListFilter segments keep the full width they are sized for */
  @media (max-width: 480px) { .panel { padding: 10px 0 2px; border-width: 1px 0; border-radius: 0; background: transparent; } }
  .grp { border: 0; margin: 0 0 10px; padding: 0; min-width: 0; }
  legend { font-weight: 600; font-size: .9rem; padding: 0; margin-bottom: 4px; }
  .n { color: var(--accent); }
  .chips { display: flex; flex-wrap: wrap; gap: 5px; }
  .more { min-height: 40px; padding: 0 10px; border: 0; background: none; color: var(--accent); font: inherit; font-size: .82rem; cursor: pointer; text-decoration: underline; }
  .fq { width: 100%; max-width: 320px; min-height: 36px; margin-bottom: 6px; padding: 0 10px; border: 1px solid var(--line); border-radius: 8px; background: var(--bg); color: var(--fg); font: inherit; font-size: .9rem; }
  .none { font-size: .85rem; padding: 8px 0; }
  .elev { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; font-size: .9rem; margin: 0 0 10px; }
  .elev input { width: 110px; min-height: 36px; padding: 0 8px; border: 1px solid var(--line); border-radius: 8px; background: var(--bg); color: var(--fg); font: inherit; }
  .trs { border-top: 1px solid var(--line); margin: 0 0 6px; padding-top: 4px; }
  .trh {
    display: flex; align-items: center; justify-content: space-between; width: 100%; min-height: 44px; padding: 0; border: 0;
    background: none; color: var(--fg); font: inherit; font-weight: 600; font-size: .95rem; cursor: pointer; text-align: left;
  }
  .trn { font-size: .82rem; margin: 0 0 8px; }
  .trw { font-size: .85rem; margin: 0 0 8px; padding: 6px 10px; border-radius: 8px; background: var(--chip); }
</style>
