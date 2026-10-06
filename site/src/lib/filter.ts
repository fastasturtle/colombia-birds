/**
 * Shared species filter: «Точно · Точно и возможно · Все» + «Все · Интересные · Почти-эндемики · Эндемики».
 * One choice for the whole site, persisted in localStorage `cb.filter2` and applied identically on every page.
 * Default: level «Все», tag «Все» (nothing hidden). Until 06.10 the default level was «Точно и возможно», saved under
 * `cb.filter`; readFilter migrates that key once (see there) and the store then drops it.
 * On top of it every list page has its own narrowing (search, families, sites, elevation; FilterBar.svelte), kept in the
 * page URL (readNarrow / writeNarrow). Both go through the one predicate rowPasses() over a plain Row descriptor.
 *
 * Static lists opt in with FilterScope.astro: items carry data-st="sure|maybe|unlikely" (+ data-int when
 * «интересная», data-nend when a Colombian near-endemic or endemic, data-end when an endemic, data-new when new
 * for the route) and data-fam / data-sites / data-q (listFacets().attrs in lib/data.ts). The tag levels are nested:
 * Эндемики ⊂ Почти-эндемики ⊂ Интересные ⊂ Все; groups carry data-lf-group; counters data-lf-summary /
 * data-lf-gcount / data-lf-new. `applyFilterDom` does the rest; it is also inlined into the page (FilterScope) so the
 * first paint already matches the saved choice and the URL.
 * Svelte lists (SpeciesList.svelte) build Rows from their JSON and call rowPasses() directly.
 */
import { writable } from 'svelte/store';

export type Level = 'sure' | 'maybe' | 'all';
/** «Все · Интересные · Почти-эндемики · Эндемики», nested: all / «интересная» (★) / near-endemic or endemic / endemic. */
export type Tag = 'all' | 'int' | 'near' | 'end';
/** How far down the nesting a species goes: 0 plain, 1 «интересная», 2 near-endemic, 3 endemic. */
export type Tier = 0 | 1 | 2 | 3;
export const TAGS: Tag[] = ['all', 'int', 'near', 'end'];
export const tierOf = (interesting: boolean, nearEndemic: boolean, endemic: boolean): Tier =>
  endemic ? 3 : nearEndemic ? 2 : interesting ? 1 : 0;
export interface Filter { level: Level; tag: Tag }
export const FILTER_KEY = 'cb.filter2';
/** The pre-06.10 key, whose level defaulted to «Точно и возможно» (readFilter migrates it). */
export const OLD_FILTER_KEY = 'cb.filter';
export const DEFAULT_FILTER: Filter = { level: 'all', tag: 'all' };
export const LEVEL_LABEL: Record<Level, string> = { sure: 'Точно', maybe: 'Точно и возможно', all: 'Все' };
export const TAG_LABEL: Record<Tag, string> = { all: 'Все', int: 'Интересные', near: 'Почти-эндемики', end: 'Эндемики' };

/** Saved filter or the default («Все» + «Все»). Migration: without `cb.filter2`, the old `cb.filter` is read, its
 * tag kept (and its older `interesting: true` read as «Интересные»), its level kept only when it is not the old
 * default `maybe`, which was rarely a choice: everyone lands on «Все» once. Self-contained: inlined into pages via toString(). */
export function readFilter(): { level: 'sure' | 'maybe' | 'all'; tag: 'all' | 'int' | 'near' | 'end' } {
  let level: 'sure' | 'maybe' | 'all' = 'all', tag: 'all' | 'int' | 'near' | 'end' = 'all';
  try {
    let v = JSON.parse(localStorage.getItem('cb.filter2') || 'null');
    if (!v) {
      v = JSON.parse(localStorage.getItem('cb.filter') || 'null');
      if (v && v.level === 'maybe') v.level = 'all';
    }
    if (v && (v.level === 'sure' || v.level === 'maybe' || v.level === 'all')) level = v.level;
    if (v && (v.tag === 'all' || v.tag === 'int' || v.tag === 'near' || v.tag === 'end')) tag = v.tag;
    else if (v && v.interesting === true) tag = 'int';
  } catch { /* private mode, bad JSON */ }
  return { level, tag };
}

/** Does a species of this tier pass the tag part? */
export function passesTag(f: Filter, tier: Tier): boolean {
  return tier >= TAGS.indexOf(f.tag);
}

/* ---- Page-level narrowing (FilterBar.svelte): search, families, sites, elevation, traits ----
 * Lives in the page URL (`q`, `fam`, `site`, `elev`; lists comma-separated; traits as `t=size:small,medium;colors:red`;
 * a scope with data-lf-key="d" uses `d-q` etc.), so links are shareable and nothing leaks between pages. Filters only
 * narrow: EMPTY_NARROW passes every row. */
/** Selected traits (content/traits.yaml): group key -> value keys. OR within a group, AND across groups. */
export type TraitSel = Record<string, string[]>;
export interface Narrow { q: string; fam: string[]; site: string[]; elev: number | null; tr: TraitSel }
export const EMPTY_NARROW: Narrow = { q: '', fam: [], site: [], elev: null, tr: {} };
/** The trait vocabulary as the client sees it (lib/traits traitOpts): groups and values in display order. */
export interface TraitOpt { key: string; label: string; values: { key: string; label: string; hint?: string | null }[] }
/**
 * Row traits travel as one character per value: String.fromCharCode(65 + i), i = the value's index in the flattened
 * vocabulary (traitFlat; at most 62 values). rowOf decodes the same way inline.
 */
export const traitFlat = (tv: TraitOpt[]) => tv.flatMap((g) => g.values.map((v) => `${g.key}:${v.key}`));
export const decodeTr = (s: string, flat: string[]) => Array.from(s, (c) => flat[c.charCodeAt(0) - 65]).filter(Boolean);
/** A selection limited to the vocabulary (a stale link must not hide everything). */
export function cleanTr(sel: TraitSel, tv: TraitOpt[]): TraitSel {
  const out: TraitSel = {};
  for (const g of tv) {
    const ok = new Set(g.values.map((v) => v.key));
    const vs = (sel[g.key] ?? []).filter((v) => ok.has(v));
    if (vs.length) out[g.key] = vs;
  }
  return out;
}
export const trCount = (sel: TraitSel) => Object.values(sel).reduce((a, b) => a + b.length, 0);
/**
 * One list row, from a static row's dataset (rowOf) or built from JSON (SpeciesList). q: searchable names (species
 * Russian / English / ACO English / Latin, family Russian / English), normQ'd and joined with «|»; on static rows they
 * come from the row's [data-n] elements (printed names) + data-q (names not printed) + the family entry of the scope
 * ctx. sites: ids of this page's sites where the species is listed (GBIF list or trip-report target); elev: altitude
 * range, only on /species/. tr: the species' traits as «group:value» (species card), null when it has no card.
 */
export interface Row { st: string; int: boolean; nend: boolean; end: boolean; fam: string; sites: string[]; q: string; elev?: [number | null, number | null] | null; tr?: string[] | null }

/** FilterBar facet options (lib/data facetOptions). */
export interface FamOpt { code: string; ru: string | null; en: string | null; sci: string }
export interface SiteOpt { id: string; name: string }

/** Lower case, ё -> е: both the indexed names and the typed query go through it. */
export const normQ = (s: string) => s.toLowerCase().replace(/ё/g, 'е');
/** Names joined with «|» (data-q, ctx family names, SpeciesList); not normalised here, rowOf / SpeciesList normQ it. */
export const searchKey = (parts: (string | null | undefined)[]) => [...new Set(parts.filter(Boolean))].join('|');

/** Narrow state from the URL. Self-contained: inlined into pages via toString(). */
export function readNarrow(key: string): { q: string; fam: string[]; site: string[]; elev: number | null; tr: Record<string, string[]> } {
  const p = new URLSearchParams(location.search), k = key ? key + '-' : '';
  const list = (n: string) => (p.get(k + n) || '').split(',').filter(Boolean);
  const e = parseInt(p.get(k + 'elev') || '', 10);
  const tr: Record<string, string[]> = {};
  for (const part of (p.get(k + 't') || '').split(';')) {
    const i = part.indexOf(':'), vs = part.slice(i + 1).split(',').filter(Boolean);
    if (i > 0 && vs.length) tr[part.slice(0, i)] = vs;
  }
  return { q: p.get(k + 'q') || '', fam: list('fam'), site: list('site'), elev: Number.isFinite(e) ? e : null, tr };
}
/** Write the narrow state into the URL (replaceState; other params and the hash are kept). */
export function writeNarrow(key: string, u: Narrow): void {
  const url = new URL(location.href), k = key ? key + '-' : '';
  const set = (n: string, v: string) => { if (v) url.searchParams.set(k + n, v); else url.searchParams.delete(k + n); };
  set('q', u.q.trim()); set('fam', u.fam.join(',')); set('site', u.site.join(',')); set('elev', u.elev != null ? String(u.elev) : '');
  set('t', Object.entries(u.tr).filter(([, vs]) => vs.length).map(([g, vs]) => `${g}:${vs.join(',')}`).join(';'));
  if (url.href !== location.href) history.replaceState(history.state, '', url.href);
}
/** The scope's data-lf-ctx (lib/data listFacets): f = [family code, its searchable names], s = site ids; rows index both.
 * tv: the trait vocabulary, present when some row of the scope has traits (data-tr indexes its flattened values). */
export interface ScopeCtx { f: [string, string][]; s: string[]; tv?: TraitOpt[] }
/** Row descriptor of a static row. Self-contained: inlined into pages via toString(). */
export function rowOf(el: HTMLElement, ctx: { f: [string, string][]; s: string[]; tv?: { key: string; values: { key: string }[] }[]; _tf?: string[] }): { st: string; int: boolean; nend: boolean; end: boolean; fam: string; sites: string[]; q: string; tr: string[] | null } {
  const d = el.dataset, f = (d.fam ? ctx.f[+d.fam] : null) || ['', ''];
  // flattened trait vocabulary (as traitFlat), cached on the ctx object
  const tf = ctx._tf || (ctx._tf = (ctx.tv || []).flatMap((g) => g.values.map((v) => g.key + ':' + v.key)));
  return {
    st: d.st || '', int: 'int' in d, nend: 'nend' in d, end: 'end' in d, fam: f[0],
    sites: (d.sites || '').split(' ').filter(Boolean).map((i) => ctx.s[+i]),
    q: [d.q || '', f[1], ...Array.from(el.querySelectorAll('[data-n]'), (n) => n.textContent || '')].join('|').toLowerCase().replace(/ё/g, 'е'),
    tr: d.tr != null ? Array.from(d.tr, (c) => tf[c.charCodeAt(0) - 65]).filter(Boolean) : null,
  };
}
/** The scope's ctx. Self-contained: inlined into pages via toString(). */
export function scopeCtx(scope: HTMLElement): { f: [string, string][]; s: string[]; tv?: { key: string; label: string; values: { key: string; label: string; hint?: string | null }[] }[] } {
  try { return JSON.parse(scope.dataset.lfCtx || ''); } catch { return { f: [], s: [] }; }
}
/**
 * The one predicate: does a row pass the site-wide filter f and the page's narrow state u? Families OR, sites OR,
 * trait values OR within their group (rows without traits fail any trait selection), AND across everything.
 * Self-contained: inlined into pages via toString().
 */
export function rowPasses(
  r: { st: string; int: boolean; nend: boolean; end: boolean; fam: string; sites: string[]; q: string; elev?: [number | null, number | null] | null; tr?: string[] | null },
  f: { level: string; tag: string },
  u: { q: string; fam: string[]; site: string[]; elev: number | null; tr?: Record<string, string[]> },
): boolean {
  if (f.tag === 'int' ? !r.int : f.tag === 'near' ? !r.nend : f.tag === 'end' ? !r.end : false) return false;
  if (!(f.level === 'all' || r.st === 'sure' || (f.level === 'maybe' && r.st === 'maybe'))) return false;
  if (u.fam.length && !u.fam.includes(r.fam)) return false;
  if (u.site.length && !r.sites.some((s) => u.site.includes(s))) return false;
  if (u.elev != null && r.elev && ((r.elev[0] ?? 0) > u.elev || (r.elev[1] ?? 9000) < u.elev)) return false;
  for (const g in u.tr || {}) {
    const vs = u.tr![g];
    if (vs.length && !(r.tr && vs.some((v) => r.tr!.includes(g + ':' + v)))) return false;
  }
  const t = u.q.trim().toLowerCase().replace(/ё/g, 'е');
  return !t || r.q.includes(t);
}

/**
 * Apply the filter to one static list (see the header): rows that fail get data-lf-out (hidden by FilterScope's CSS),
 * groups without visible rows are hidden, counters and «ничего не найдено» follow; a search opens the collapsed
 * <details> groups that have hits. Self-contained (helpers come in as arguments): inlined into pages via toString().
 */
export function applyFilterDom(
  scope: HTMLElement, f: { level: string; tag: string }, u: { q: string; fam: string[]; site: string[]; elev: number | null; tr: Record<string, string[]> },
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  rowOf: (el: HTMLElement, ctx: any) => any, rowPasses: (r: any, f: { level: string; tag: string }, u: any) => boolean, ctx: { f: [string, string][]; s: string[] },
): void {
  const pl = (n: number, a: string, b: string, c: string) => {
    const m10 = n % 10, m100 = n % 100;
    return m10 === 1 && m100 !== 11 ? a : m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14) ? b : c;
  };
  scope.dataset.lv = f.level;
  scope.dataset.tag = f.tag;
  const items = Array.from(scope.querySelectorAll<HTMLElement>('[data-st]'));
  const ok = new Set<HTMLElement>();
  for (const el of items) {
    if (rowPasses(rowOf(el, ctx), f, u)) { ok.add(el); el.removeAttribute('data-lf-out'); } else el.setAttribute('data-lf-out', '');
  }
  const vis = items.filter((x) => ok.has(x));
  const searching = u.q.trim() !== '';
  scope.querySelectorAll<HTMLElement>('[data-lf-group]').forEach((g) => {
    const gv = Array.from(g.querySelectorAll<HTMLElement>('[data-st]')).filter((x) => ok.has(x));
    g.hidden = gv.length === 0;
    if (searching && gv.length && g.tagName === 'DETAILS') (g as HTMLDetailsElement).open = true;
    g.querySelectorAll('[data-lf-gcount]').forEach((c) => (c.textContent = String(gv.length)));
    g.querySelectorAll<HTMLElement>('[data-lf-gint]').forEach((c) => {
      const k = gv.filter((x) => 'int' in x.dataset).length;
      c.hidden = k === 0 || f.tag !== 'all';
      c.textContent = ` · ${k}★`;
    });
  });
  const nInt = vis.filter((x) => 'int' in x.dataset).length;
  scope.querySelectorAll('[data-lf-summary]').forEach((e) => {
    e.textContent = f.tag === 'end' ? `${vis.length} ${pl(vis.length, 'эндемик', 'эндемика', 'эндемиков')}`
      : `${vis.length} ${pl(vis.length, 'вид', 'вида', 'видов')}` +
        (nInt && f.tag === 'all' ? ` · ${nInt} ${pl(nInt, 'интересный', 'интересных', 'интересных')}` : '');
  });
  scope.querySelectorAll<HTMLElement>('[data-lf-new]').forEach((e) => {
    const k = vis.filter((x) => 'new' in x.dataset).length;
    e.hidden = k === 0;
    e.textContent = `из них ${k} впервые на маршруте`;
  });
  scope.querySelectorAll<HTMLElement>('[data-lf-empty]').forEach((e) => (e.hidden = vis.length > 0));
}
/** Re-apply every static list on the page (the narrow state of each scope comes from the URL). */
export function applyAllScopes(f: Filter): void {
  document.querySelectorAll<HTMLElement>('[data-lf-scope]').forEach((sc) => applyFilterDom(sc, f, readNarrow(sc.dataset.lfKey || ''), rowOf, rowPasses, scopeCtx(sc)));
}

function createStore() {
  const s = writable<Filter>(DEFAULT_FILTER);
  if (typeof window !== 'undefined') {
    s.set(readFilter());
    s.subscribe((f) => {
      try { localStorage.setItem(FILTER_KEY, JSON.stringify(f)); localStorage.removeItem(OLD_FILTER_KEY); } catch { /* ignore */ }
      applyAllScopes(f);
    });
    window.addEventListener('storage', (e) => { if (e.key === FILTER_KEY) s.set(readFilter()); });
  }
  return s;
}
/** The site-wide filter (client: initialised from localStorage and saved on every change). */
export const filter = createStore();
