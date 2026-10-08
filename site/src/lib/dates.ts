/**
 * Pure date helpers (no node:fs), safe to import from Svelte islands as well as from build-time code.
 */
export const RU_MONTHS_SHORT = ['янв', 'фев', 'мар', 'апр', 'мая', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек'];

const parse = (date: string) => new Date(`${date}T12:00:00Z`);
const short = (d: Date, month = true) => (month ? `${d.getUTCDate()} ${RU_MONTHS_SHORT[d.getUTCMonth()]}` : `${d.getUTCDate()}`);

/**
 * ISO dates -> compact Russian list, runs of consecutive days collapsed:
 * ['2026-10-01'] -> '1 окт'; ['2026-10-01','2026-10-02','2026-10-03','2026-10-05'] -> '1–3 окт, 5 окт';
 * ['2026-09-30','2026-10-01'] -> '30 сен – 1 окт'. Duplicates and order do not matter; [] -> ''.
 */
export function fmtDaysShort(dates: string[]): string {
  const ds = [...new Set(dates)].sort().map(parse);
  const parts: string[] = [];
  for (let i = 0; i < ds.length; ) {
    let j = i;
    while (j + 1 < ds.length && ds[j + 1].getTime() - ds[j].getTime() === 864e5) j++;
    const a = ds[i], b = ds[j];
    if (j === i) parts.push(short(a));
    else if (a.getUTCMonth() === b.getUTCMonth()) parts.push(`${short(a, false)}–${short(b)}`);
    else parts.push(`${short(a)} – ${short(b)}`);
    i = j + 1;
  }
  return parts.join(', ');
}

/**
 * Short route days of a site from its visit dates. With `pageDate` (a day page): '' when the site is visited
 * only on that date (it would just repeat the page's own date), otherwise all its days.
 */
export function siteDaysFromDates(dates: string[], pageDate?: string): string {
  if (pageDate && dates.every((d) => d === pageDate)) return '';
  return fmtDaysShort(dates);
}

/** Today in Bogotá (the tour's clock) as yyyy-mm-dd. */
export function bogotaToday(now = new Date()): string {
  return new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Bogota' }).format(now);
}
/** routeRank of a place with no route days: after every dated one. */
export const NO_ROUTE_DAYS = 1e9;
/**
 * Sort key of a place by its route days relative to `today` (lower comes first): today 0, a day n days ahead n,
 * a day n days ago 1e5 + n (so past days follow the future ones, most recent first); a place visited on several
 * days takes its best one; NO_ROUTE_DAYS without days. The inline `routeSort` in Base.astro repeats this rule.
 */
export function routeRank(dates: string[], today: string): number {
  const t = Date.parse(today);
  let best = NO_ROUTE_DAYS;
  for (const d of dates) {
    const n = Math.round((Date.parse(d) - t) / 864e5);
    best = Math.min(best, n >= 0 ? n : 1e5 - n);
  }
  return best;
}
/** Stable sort by routeRank: ties (and places without days, at the end) keep their given order. */
export function sortByRoute<T>(xs: T[], datesOf: (x: T) => string[], today: string): T[] {
  return xs.map((x, i) => ({ x, i, r: routeRank(datesOf(x), today) })).sort((a, b) => a.r - b.r || a.i - b.i).map((o) => o.x);
}
