/**
 * Shared species filter: «Точно · Точно и возможно · Все» + «Все · Интересные · Почти-эндемики · Эндемики».
 * One choice for the whole site, persisted in localStorage `cb.filter` and applied identically on every page.
 *
 * Static lists opt in with FilterScope.astro: items carry data-st="sure|maybe|unlikely" (+ data-int when
 * «интересная», data-nend when a Colombian near-endemic or endemic, data-end when an endemic, data-new when new
 * for the route). The tag levels are nested: Эндемики ⊂ Почти-эндемики ⊂ Интересные ⊂ Все; groups carry data-lf-group; counters data-lf-summary /
 * data-lf-gcount / data-lf-new; the «ещё N вряд ли · показать» line is data-lf-more. `applyFilterDom` does the
 * rest; it is also inlined into the page (FilterScope) so the first paint already matches the saved choice.
 * Svelte lists (SpeciesList.svelte) read the `filter` store and `passes()` directly.
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
export const FILTER_KEY = 'cb.filter';
export const DEFAULT_FILTER: Filter = { level: 'maybe', tag: 'all' };
export const LEVEL_LABEL: Record<Level, string> = { sure: 'Точно', maybe: 'Точно и возможно', all: 'Все' };
export const TAG_LABEL: Record<Tag, string> = { all: 'Все', int: 'Интересные', near: 'Почти-эндемики', end: 'Эндемики' };

/** Saved filter or the default; migrates the old `interesting: true` to «Интересные».
 * Self-contained: inlined into pages via toString(). */
export function readFilter(): { level: 'sure' | 'maybe' | 'all'; tag: 'all' | 'int' | 'near' | 'end' } {
  let level: 'sure' | 'maybe' | 'all' = 'maybe', tag: 'all' | 'int' | 'near' | 'end' = 'all';
  try {
    const v = JSON.parse(localStorage.getItem('cb.filter') || 'null');
    if (v && (v.level === 'sure' || v.level === 'maybe' || v.level === 'all')) level = v.level;
    if (v && (v.tag === 'all' || v.tag === 'int' || v.tag === 'near' || v.tag === 'end')) tag = v.tag;
    else if (v && v.interesting === true) tag = 'int';
  } catch { /* private mode, bad JSON */ }
  return { level, tag };
}

/** Does a species of this tier pass the tag part (used alone for the «ещё N … · показать» line)? */
export function passesTag(f: Filter, tier: Tier): boolean {
  return tier >= TAGS.indexOf(f.tag);
}
/** Is a species with this state and tier (tierOf) shown under the filter? */
export function passes(f: Filter, state: string, tier: Tier): boolean {
  if (!passesTag(f, tier)) return false;
  return f.level === 'all' || state === 'sure' || (f.level === 'maybe' && state === 'maybe');
}

/** Apply the filter to one static list (see the header). Self-contained: inlined into pages via toString(). */
export function applyFilterDom(scope: HTMLElement, f: { level: string; tag: string }): void {
  const need = { int: 'int', near: 'nend', end: 'end' }[f.tag as 'int' | 'near' | 'end'];
  const tagOk = (el: HTMLElement) => !need || need in el.dataset;
  const pass = (el: HTMLElement) => {
    if (!tagOk(el)) return false;
    const st = el.dataset.st;
    return f.level === 'all' || st === 'sure' || (f.level === 'maybe' && st === 'maybe');
  };
  const pl = (n: number, a: string, b: string, c: string) => {
    const m10 = n % 10, m100 = n % 100;
    return m10 === 1 && m100 !== 11 ? a : m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14) ? b : c;
  };
  scope.dataset.lv = f.level;
  scope.dataset.tag = f.tag;
  const items = Array.from(scope.querySelectorAll<HTMLElement>('[data-st]'));
  const vis = items.filter(pass);
  scope.querySelectorAll<HTMLElement>('[data-lf-group]').forEach((g) => {
    const gv = Array.from(g.querySelectorAll<HTMLElement>('[data-st]')).filter(pass);
    g.hidden = gv.length === 0;
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
  const more = items.filter((x) => !pass(x) && tagOk(x));
  const nu = more.filter((x) => x.dataset.st === 'unlikely').length;
  scope.querySelectorAll<HTMLElement>('[data-lf-more]').forEach((m) => {
    m.hidden = more.length === 0;
    const t = m.querySelector('[data-lf-more-text]');
    if (t) t.textContent = nu === more.length ? `ещё ${nu} вряд ли` : nu === 0 ? `ещё ${more.length} возможно`
      : `ещё ${more.length}: ${more.length - nu} возможно, ${nu} вряд ли`;
  });
}

function createStore() {
  const s = writable<Filter>(DEFAULT_FILTER);
  if (typeof window !== 'undefined') {
    s.set(readFilter());
    s.subscribe((f) => {
      try { localStorage.setItem(FILTER_KEY, JSON.stringify(f)); } catch { /* ignore */ }
      document.querySelectorAll<HTMLElement>('[data-lf-scope]').forEach((sc) => applyFilterDom(sc, f));
    });
    window.addEventListener('storage', (e) => { if (e.key === FILTER_KEY) s.set(readFilter()); });
    document.addEventListener('click', (e) => {
      if ((e.target as HTMLElement | null)?.closest?.('[data-lf-show-all]')) s.update((f) => ({ ...f, level: 'all' }));
    });
  }
  return s;
}
/** The site-wide filter (client: initialised from localStorage and saved on every change). */
export const filter = createStore();
