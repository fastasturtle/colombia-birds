<script lang="ts">
  /**
   * The one filter control of every species list (/species/, day, site and family pages).
   * Collapsed: search + «Фильтры» (badge = active non-default filters) + «показано N из M» + removable chips of the
   * active filters. Expanded (remembered in localStorage `cb.filter.open`): the site-wide ListFilter (likelihood, tag),
   * families and sites as facet chips with counts (lib/facets.ts, as in the identifier), elevation where `elev` is set.
   * Families / sites only show when the list has more than one. State: level + tag in the global `filter` store;
   * search, families, sites, elevation in `u` (bound; the parent keeps it in the URL and applies it).
   * Rows: one descriptor per list row (lib/filter Row); null while the parent is still reading them.
   */
  import { onMount } from 'svelte';
  import ListFilter from './ListFilter.svelte';
  import FacetChip from './FacetChip.svelte';
  import { filter, rowPasses, normQ, DEFAULT_FILTER, TAG_LABEL, type Narrow, type Row, type FamOpt, type SiteOpt } from '../lib/filter';
  import { facetCounts } from '../lib/facets';

  interface Props { rows: Row[] | null; total: number; fams: FamOpt[]; sites: SiteOpt[]; u: Narrow; elev?: boolean }
  let { rows, total, fams, sites, u = $bindable(), elev = false }: Props = $props();

  const OPEN_KEY = 'cb.filter.open';
  let open = $state(false);
  onMount(() => { try { open = localStorage.getItem(OPEN_KEY) === '1'; } catch { /* private mode */ } });
  const toggleOpen = () => {
    open = !open;
    try { localStorage.setItem(OPEN_KEY, open ? '1' : '0'); } catch { /* ignore */ }
  };
  const uid = Math.random().toString(36).slice(2, 8);

  const famName = (f: FamOpt) => f.ru ?? f.en ?? f.sci;
  const famOf = $derived(new Map(fams.map((f) => [f.code, f])));
  const siteOf = $derived(new Map(sites.map((s) => [s.id, s])));

  let famSets = $derived((rows ?? []).map((r) => new Set([r.fam])));
  let siteSets = $derived((rows ?? []).map((r) => new Set(r.sites)));
  let shown = $derived(rows ? rows.filter((r) => rowPasses(r, $filter, u)).length : null);
  let counts = $derived.by(() => {
    const rs = rows ?? [];
    const f = $filter, rest = { ...u, fam: [], site: [] };
    const groups = [{ key: 'fam', values: fams.map((x) => x.code) }, { key: 'site', values: sites.map((x) => x.id) }];
    return facetCounts(rs.length, groups, { fam: u.fam, site: u.site }, (i) => rowPasses(rs[i], f, rest),
      (i, g) => (g === 'fam' ? famSets[i] : siteSets[i]));
  });

  const toggle = (g: 'fam' | 'site', v: string) => {
    const cur = u[g];
    u[g] = cur.includes(v) ? cur.filter((x) => x !== v) : [...cur, v];
  };

  type Active = { key: string; label: string; drop: () => void };
  let active = $derived.by<Active[]>(() => {
    const out: Active[] = [];
    const f = $filter;
    if (f.level !== DEFAULT_FILTER.level) out.push({ key: 'lv', label: f.level === 'sure' ? 'Только «точно»' : 'Включая «вряд ли»', drop: () => filter.update((x) => ({ ...x, level: DEFAULT_FILTER.level })) });
    if (f.tag !== DEFAULT_FILTER.tag) out.push({ key: 'tag', label: `${f.tag === 'end' ? '◆' : f.tag === 'near' ? '◇' : '★'} ${TAG_LABEL[f.tag]}`, drop: () => filter.update((x) => ({ ...x, tag: DEFAULT_FILTER.tag })) });
    for (const c of u.fam) { const fo = famOf.get(c); out.push({ key: `f:${c}`, label: fo ? famName(fo) : c, drop: () => toggle('fam', c) }); }
    for (const s of u.site) out.push({ key: `s:${s}`, label: siteOf.get(s)?.name ?? s, drop: () => toggle('site', s) });
    if (u.elev != null) out.push({ key: 'elev', label: `высота ${u.elev} м`, drop: () => (u.elev = null) });
    return out;
  });
  const reset = () => {
    filter.set({ ...DEFAULT_FILTER });
    u.q = ''; u.fam = []; u.site = []; u.elev = null;
  };

  let famQ = $state('');
  const FAM_SEARCH_FROM = 15;
  let famsShown = $derived.by(() => {
    const t = normQ(famQ.trim());
    if (!t) return fams;
    return fams.filter((f) => u.fam.includes(f.code) || [f.ru, f.en, f.sci].some((x) => x && normQ(x).includes(t)));
  });
</script>

<div class="fb" role="search">
  <div class="bar">
    <input type="search" class="q" bind:value={u.q} placeholder="Поиск вида"
      aria-label="Поиск по названию: русскому, английскому, латинскому или семейства" autocomplete="off" />
    <button type="button" class="tg" aria-expanded={open} aria-controls={`fb-panel-${uid}`} onclick={toggleOpen}>
      Фильтры{#if active.length}<span class="badge" aria-label={`активно: ${active.length}`}>{active.length}</span>{/if}<span class="car" aria-hidden="true">▾</span>
    </button>
  </div>
  <div class="line">
    <span class="count" aria-live="polite">{#if shown != null}показано <b>{shown}</b> из {total}{/if}</span>
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
          <legend>Семейство{#if u.fam.length}<span class="n"> · {u.fam.length}</span>{/if}</legend>
          {#if fams.length > FAM_SEARCH_FROM}
            <input type="search" class="fq" bind:value={famQ} placeholder={`Найти среди ${fams.length} семейств`} aria-label="Найти семейство" autocomplete="off" />
          {/if}
          <div class="chips">
            {#each famsShown as f (f.code)}
              <FacetChip label={famName(f)} sub={f.sci} hint={f.ru && f.en ? `${f.en} · ${f.sci}` : f.sci} on={u.fam.includes(f.code)}
                n={rows ? (counts.fam?.[f.code] ?? 0) : null} delta={u.fam.length > 0} onclick={() => toggle('fam', f.code)} />
            {/each}
            {#if famsShown.length === 0}<span class="muted none">Нет такого семейства</span>{/if}
          </div>
        </fieldset>
      {/if}
      {#if sites.length > 1}
        <fieldset class="grp">
          <legend>Место{#if u.site.length}<span class="n"> · {u.site.length}</span>{/if}</legend>
          <div class="chips">
            {#each sites as s (s.id)}
              <FacetChip label={s.name} on={u.site.includes(s.id)} n={rows ? (counts.site?.[s.id] ?? 0) : null}
                delta={u.site.length > 0} onclick={() => toggle('site', s.id)} />
            {/each}
          </div>
        </fieldset>
      {/if}
      {#if elev}
        <label class="elev">Встречается на высоте <input type="number" min="0" max="5000" step="100" placeholder="напр. 2000" bind:value={u.elev} /> м</label>
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
  .tg[aria-expanded="true"] .car { transform: rotate(180deg); }
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
  .fq { width: 100%; max-width: 320px; min-height: 36px; margin-bottom: 6px; padding: 0 10px; border: 1px solid var(--line); border-radius: 8px; background: var(--bg); color: var(--fg); font: inherit; font-size: .9rem; }
  .none { font-size: .85rem; padding: 8px 0; }
  .elev { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; font-size: .9rem; margin: 0 0 10px; }
  .elev input { width: 110px; min-height: 36px; padding: 0 8px; border: 1px solid var(--line); border-radius: 8px; background: var(--bg); color: var(--fg); font: inherit; }
</style>
