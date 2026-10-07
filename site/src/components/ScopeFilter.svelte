<script lang="ts">
  /**
   * FilterBar for a static list: mount inside a FilterScope.astro (client:load). Reads the row descriptors from the
   * scope's DOM (lib/filter rowOf), keeps search / families / sites / traits in the URL (key = the scope's data-lf-key)
   * and re-applies applyFilterDom on every change. fams / sites: the list's facet options (lib/data facetOptions); the
   * trait vocabulary comes from the scope's ctx (tv), so it is in the page once.
   */
  import { onMount } from 'svelte';
  import FilterBar from './FilterBar.svelte';
  import { filter, applyFilterDom, readNarrow, writeNarrow, rowOf, makePass, scopeCtx, cleanTr, EMPTY_NARROW, type Narrow, type Row, type ScopeCtx, type FamOpt, type SiteOpt, type TraitOpt } from '../lib/filter';
  interface Props { fams: FamOpt[]; sites: SiteOpt[]; total: number }
  const { fams, sites, total }: Props = $props();

  let el: HTMLElement;
  let scope: HTMLElement | null = null;
  let key = '';
  let ctx: ScopeCtx = { f: [], s: [] };
  let byEl = new Map<HTMLElement, Row>();
  /** rowOf, cached: the rows do not change after load */
  const rowFor = (x: HTMLElement) => byEl.get(x) ?? rowOf(x, ctx);
  /** raw: the descriptors are read-only, a deep proxy would slow every sweep over them */
  let rows = $state.raw<Row[] | null>(null);
  let u = $state<Narrow>({ ...EMPTY_NARROW });
  let traits = $state<TraitOpt[]>([]);

  onMount(() => {
    // the island can hydrate while a long page is still parsing: read the rows once all of them are there
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
    else init();
  });
  function init() {
    scope = el.closest<HTMLElement>('[data-lf-scope]');
    if (!scope) return;
    key = scope.dataset.lfKey || '';
    ctx = scopeCtx(scope);
    const els = Array.from(scope.querySelectorAll<HTMLElement>('[data-st]'));
    const rs = els.map((x) => rowOf(x, ctx));
    byEl = new Map(els.map((x, i) => [x, rs[i]]));
    rows = rs;
    // this scope is applied here from now on (lib/filter applyAllScopes skips it)
    scope.dataset.lfLive = '';
    const r = readNarrow(key);
    // codes not on this page (stale link) would hide everything: drop them
    const fk = new Set(fams.map((f) => f.code)), sk = new Set(sites.map((s) => s.id));
    traits = ctx.tv ?? [];
    u = { ...r, fam: r.fam.filter((c) => fk.has(c)), site: r.site.filter((s) => sk.has(s)), tr: cleanTr(r.tr, traits) };
  }

  let timer: ReturnType<typeof setTimeout> | undefined;
  $effect(() => {
    if (!rows || !scope) return; // rows first: it is the reactive one
    const snap = $state.snapshot(u) as Narrow;
    applyFilterDom(scope, $filter, snap, rowFor, makePass, ctx);
    clearTimeout(timer);
    // debounced: Safari throttles replaceState (about 100 calls per 30 s)
    timer = setTimeout(() => writeNarrow(key, snap), 300);
  });
</script>

<div bind:this={el}><FilterBar {rows} {total} {fams} {sites} {traits} bind:u /></div>
