/**
 * Shared species filter: «Точно · Точно и возможно · Все» + «Только интересные».
 * One choice for the whole site, persisted in localStorage `cb.filter` and applied identically on every page.
 *
 * Static lists opt in with FilterScope.astro: items carry data-st="sure|maybe|unlikely" (+ data-int when
 * «интересная», data-new when new for the route); groups carry data-lf-group; counters data-lf-summary /
 * data-lf-gcount / data-lf-new; the «ещё N вряд ли · показать» line is data-lf-more. `applyFilterDom` does the
 * rest; it is also inlined into the page (FilterScope) so the first paint already matches the saved choice.
 * Svelte lists (SpeciesList.svelte) read the `filter` store and `passes()` directly.
 */
import { writable } from 'svelte/store';

export type Level = 'sure' | 'maybe' | 'all';
export interface Filter { level: Level; interesting: boolean }
export const FILTER_KEY = 'cb.filter';
export const DEFAULT_FILTER: Filter = { level: 'maybe', interesting: false };
export const LEVEL_LABEL: Record<Level, string> = { sure: 'Точно', maybe: 'Точно и возможно', all: 'Все' };

/** Saved filter or the default. Self-contained: inlined into pages via toString(). */
export function readFilter(): { level: 'sure' | 'maybe' | 'all'; interesting: boolean } {
  try {
    const v = JSON.parse(localStorage.getItem('cb.filter') || 'null');
    if (v && (v.level === 'sure' || v.level === 'maybe' || v.level === 'all')) return { level: v.level, interesting: !!v.interesting };
  } catch { /* private mode, bad JSON */ }
  return { level: 'maybe', interesting: false };
}

/** Is a species with this state / interesting flag shown under the filter? */
export function passes(f: Filter, state: string, interesting: boolean): boolean {
  if (f.interesting && !interesting) return false;
  return f.level === 'all' || state === 'sure' || (f.level === 'maybe' && state === 'maybe');
}

/** Apply the filter to one static list (see the header). Self-contained: inlined into pages via toString(). */
export function applyFilterDom(scope: HTMLElement, f: { level: string; interesting: boolean }): void {
  const pass = (el: HTMLElement) => {
    if (f.interesting && !('int' in el.dataset)) return false;
    const st = el.dataset.st;
    return f.level === 'all' || st === 'sure' || (f.level === 'maybe' && st === 'maybe');
  };
  const pl = (n: number, a: string, b: string, c: string) => {
    const m10 = n % 10, m100 = n % 100;
    return m10 === 1 && m100 !== 11 ? a : m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14) ? b : c;
  };
  scope.dataset.lv = f.level;
  scope.dataset.int = f.interesting ? '1' : '0';
  const items = Array.from(scope.querySelectorAll<HTMLElement>('[data-st]'));
  const vis = items.filter(pass);
  scope.querySelectorAll<HTMLElement>('[data-lf-group]').forEach((g) => {
    const gv = Array.from(g.querySelectorAll<HTMLElement>('[data-st]')).filter(pass);
    g.hidden = gv.length === 0;
    g.querySelectorAll('[data-lf-gcount]').forEach((c) => (c.textContent = String(gv.length)));
    g.querySelectorAll<HTMLElement>('[data-lf-gint]').forEach((c) => {
      const k = gv.filter((x) => 'int' in x.dataset).length;
      c.hidden = k === 0;
      c.textContent = ` · ${k}★`;
    });
  });
  const nInt = vis.filter((x) => 'int' in x.dataset).length;
  scope.querySelectorAll('[data-lf-summary]').forEach((e) => {
    e.textContent = `${vis.length} ${pl(vis.length, 'вид', 'вида', 'видов')}` +
      (nInt ? ` · ${nInt} ${pl(nInt, 'интересный', 'интересных', 'интересных')}` : '');
  });
  scope.querySelectorAll<HTMLElement>('[data-lf-new]').forEach((e) => {
    const k = vis.filter((x) => 'new' in x.dataset).length;
    e.hidden = k === 0;
    e.textContent = `из них ${k} впервые на маршруте`;
  });
  scope.querySelectorAll<HTMLElement>('[data-lf-empty]').forEach((e) => (e.hidden = vis.length > 0));
  const more = items.filter((x) => !pass(x) && (!f.interesting || 'int' in x.dataset));
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
