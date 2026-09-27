/**
 * Build-time linkifier for hand-written family texts (route notes, bodies): English species names from
 * data/species_index.json become links to /species/<id>/, site names from data/sites.json (English or
 * Russian, Russian ones tolerant of case endings: «в Сибундое», «парамо Чингасы») link to /sites/<id>/.
 * Returns an HTML string (input is escaped), for `set:html`.
 *
 * Also handles the shared-group-noun shorthand «Hooded и White-bellied Antpitta»: both halves are linked
 * when both «Hooded Antpitta» and «White-bellied Antpitta» are species.
 *
 * Sanity check (by hand, with base '/b/'):
 *   linkify('Boyaca Antpitta на Чингасе', '/b/')
 *     -> '<a href="/b/species/grallaria-alticola/">Boyaca Antpitta</a> на <a href="/b/sites/chingaza/">Чингасе</a>'
 *   linkify('Hooded и White-bellied Antpitta в Ла-Дримофиле', '/b/')
 *     -> '<a …grallaricula-cucullata/>Hooded</a> и <a …grallaria-hypoleuca/>White-bellied Antpitta</a> в <a …sites/la-drymophila/>Ла-Дримофиле</a>'
 *   linkify('a ruff of feathers', '/b/') -> unchanged (one-word names must be capitalised)
 *   linkify('Merlin app', '/b/') -> unchanged (ambiguous with the Merlin app, never linked)
 */
import { speciesIndex, sites } from './data';

const esc = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const reEsc = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
const norm = (s: string) => s.toLowerCase().replace(/[’`]/g, "'").replace(/\s+/g, ' ');
const stripDiacritics = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').normalize('NFC');
const L = "[\\p{L}\\p{N}]";
const bounded = (p: string) => `(?<![\\p{L}\\p{N}-])(?:${p})(?![\\p{L}\\p{N}])`;

/** Never linked: ambiguous with ordinary words or product names. */
const SKIP_SPECIES = new Set(['merlin']);
/** Generic words dropped from site names to get the short name used in running text. */
const SITE_PREFIX = /^(?:PNN|RN|Parque Natural|Parque|Valle de|Reserva|Páramo|Laguna|Долина|Парамо|Лагуна)\s+/i;
const SITE_SUFFIX = /\s+(?:Nature Reserve|Reserva Natural|Bird Lodge|Lodge|Birding Center|Center)$/i;

/** Pattern for a site alias; Cyrillic words tolerate a changed/added case ending of up to 3 letters. */
function sitePattern(alias: string): string {
  return alias.split(/\s+/).map((w) => {
    if (!/[а-яё]/i.test(w)) return reEsc(w);
    const parts = w.split('-');
    const last = parts.pop()!;
    const stem = last.length > 4 ? last.replace(/[аяоеыйьи]$/i, '') : last;
    return [...parts.map(reEsc), `${reEsc(stem)}[а-яё]{0,3}`].join('-');
  }).join('\\s+');
}

function siteAliases(s: { name: string; name_ru: string }): string[] {
  const out = new Set<string>();
  const add = (a: string) => { a = a.trim(); if (a.length >= 4) { out.add(a); out.add(stripDiacritics(a)); } };
  for (const raw of [s.name, s.name_ru]) {
    const base = raw.replace(/\s*\([^)]*\)/g, '').replace(/\s*«[^»]*»/g, '');
    for (const part of base.split(/\s*\/\s*/)) {
      add(part);
      const short = part.replace(SITE_PREFIX, '').replace(SITE_SUFFIX, '');
      if (short !== part) add(short);
      add(part.replace(/\s+Bird\s+Lodge$/i, ' Lodge'));
      // «La Isla Escondida» -> «Isla Escondida», but never a one-word rest («La Drymophila» -> genus name)
      const noArticle = short.replace(/^La\s+/, '');
      if (noArticle !== short && /\s/.test(noArticle)) add(noArticle);
    }
  }
  return [...out];
}

interface Linker { re: RegExp; pair: RegExp; species: Map<string, string>; sites: { id: string; re: RegExp }[] }
let _linker: Linker | null = null;
function linker(): Linker {
  if (_linker) return _linker;
  const species = new Map<string, string>();
  for (const s of speciesIndex()) if (!SKIP_SPECIES.has(norm(s.en))) species.set(norm(s.en), s.id);
  const siteList = sites().map((s) => {
    const pats = siteAliases(s).sort((a, b) => b.length - a.length).map(sitePattern);
    return { id: s.id, pats, re: new RegExp(`^(?:${pats.join('|')})$`, 'iu') };
  });
  const alts: { len: number; p: string }[] = [];
  for (const name of species.keys()) alts.push({ len: name.length, p: reEsc(name).replace(/'/g, "['’]").replace(/ /g, '\\s+') });
  for (const s of siteList) for (const p of s.pats) alts.push({ len: p.length, p });
  alts.sort((a, b) => b.len - a.len); // longest first: «Chestnut-crowned Antpitta» before «Antpitta …»
  const W = `[A-Z][\\p{L}'’-]*`;
  _linker = {
    re: new RegExp(bounded(alts.map((a) => a.p).join('|')), 'giu'),
    pair: new RegExp(`(?<![\\p{L}-])(${W})(\\s+(?:и|или|and|or)\\s+)(${W}(?:\\s+${W})?)\\s+(${W})(?!${L})`, 'gu'),
    species,
    sites: siteList.map(({ id, re }) => ({ id, re })),
  };
  return _linker;
}

export function linkify(text: string | null | undefined, base: string): string {
  if (!text) return '';
  const b = base.endsWith('/') ? base : `${base}/`;
  const { re, pair, species, sites: siteRes } = linker();
  const a = (href: string, t: string) => `<a href="${b}${href}">${esc(t)}</a>`;
  let out = '';
  let pos = 0;
  while (pos < text.length) {
    re.lastIndex = pos; pair.lastIndex = pos;
    let m = re.exec(text);
    // shorthand pair «X и Y Group»: take it when it starts before the next plain match and both halves are species
    let p: RegExpExecArray | null;
    let pairHit: { idx: number; html: string; end: number } | null = null;
    while ((p = pair.exec(text)) && (!m || p.index <= m.index)) {
      const [, x, sep, y, group] = p;
      const ix = species.get(norm(`${x} ${group}`)), iy = species.get(norm(`${y} ${group}`));
      if (ix && iy) { pairHit = { idx: p.index, end: p.index + p[0].length, html: a(`species/${ix}/`, x) + esc(sep) + a(`species/${iy}/`, `${y} ${group}`) }; break; }
      pair.lastIndex = p.index + 1;
    }
    if (pairHit && (!m || pairHit.idx <= m.index)) {
      out += esc(text.slice(pos, pairHit.idx)) + pairHit.html;
      pos = pairHit.end;
      continue;
    }
    if (!m) break;
    const t = m[0];
    const sp = species.get(norm(t));
    let html: string | null = null;
    if (sp) html = /\s/.test(t) || /^\p{Lu}/u.test(t) ? a(`species/${sp}/`, t) : null;
    else {
      const site = siteRes.find((s) => s.re.test(t));
      if (site) html = a(`sites/${site.id}/`, t);
    }
    out += esc(text.slice(pos, m.index)) + (html ?? esc(t));
    pos = m.index + t.length;
  }
  return out + esc(text.slice(pos));
}
