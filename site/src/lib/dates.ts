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
