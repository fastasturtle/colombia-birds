/**
 * Hand-written content from ../content (see content/README.md, content/families/README.md);
 * family portraits in content/families/, group portraits in content/groups/ (same schema).
 * Build time only. Bodies are plain paragraphs separated by blank lines; the English
 * version follows a "## English" heading.
 */
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import matter from 'gray-matter';
import { validateTraits, type Traits } from './traits';
import { speciesIndex } from './data';
import { linkify } from './linkify';

const CONTENT = join(process.cwd(), '..', 'content');

export interface FamilyContent {
  family: string;
  recognize: string[];
  confusable: { family: string; how: string }[];
  route_note: string | null;
  fact: string | null;
  body: string[]; // Russian paragraphs
  en: { recognize: string[]; route_note: string | null; fact: string | null; body: string[] } | null;
}

const paragraphs = (s: string) => s.split(/\n\s*\n/).map((p) => p.replace(/\s+/g, ' ').trim()).filter(Boolean);

export interface GroupContent extends Omit<FamilyContent, 'family' | 'confusable'> {
  group: string;
  confusable: { group: string; how: string }[];
}

/** Parse every portrait in content/<sub>/ (frontmatter + Russian body + "## English" body), keyed by `key`. */
function loadDir<T>(sub: string, key: string): Map<string, T> {
  const dir = join(CONTENT, sub);
  const out = new Map<string, T>();
  if (!existsSync(dir)) return out;
  for (const f of readdirSync(dir)) {
    if (!f.endsWith('.md') || f === 'README.md') continue;
    const { data, content } = matter(readFileSync(join(dir, f), 'utf8'));
    if (!data[key]) throw new Error(`content/${sub}/${f}: missing "${key}" in frontmatter`);
    const [ru, en = ''] = content.split(/^## English\s*$/m);
    const e = data.en ?? null;
    out.set(data[key], {
      [key]: data[key],
      recognize: data.recognize ?? [],
      confusable: data.confusable ?? [],
      route_note: data.route_note ?? null,
      fact: data.fact ?? null,
      body: paragraphs(ru),
      en: e || en.trim()
        ? { recognize: e?.recognize ?? [], route_note: e?.route_note ?? null, fact: e?.fact ?? null, body: paragraphs(en) }
        : null,
    } as T);
  }
  return out;
}

let _families: Map<string, FamilyContent> | null = null;
let _groups: Map<string, GroupContent> | null = null;

/** Portrait for a family code (e.g. "gralla2"), or null if none written yet. */
export function familyContent(code: string): FamilyContent | null {
  return (_families ??= loadDir<FamilyContent>('families', 'family')).get(code) ?? null;
}

/** Portrait for a group id from data/groups.json (content/groups/<id>.md), or null if none written yet. */
export function groupContent(id: string): GroupContent | null {
  return (_groups ??= loadDir<GroupContent>('groups', 'group')).get(id) ?? null;
}

/* ---- Species cards: content/species/<slug>.md (schema in content/README.md) ---- */

export type Difficulty = 'easy' | 'medium' | 'hard';
export const DIFFICULTY_RU: Record<Difficulty, string> = { easy: 'легко узнать', medium: 'средне', hard: 'трудно узнать' };
export interface CardText {
  key_features: string[];
  similar: { id: string; how: string }[];
  behavior: string;
  voice: string;
  body: string[];
}
export interface SpeciesCard extends CardText {
  id: string;
  difficulty: Difficulty;
  lynx_page: number | null;
  /** Date of the last fact-check pass (YYYY-MM-DD); bookkeeping only, not rendered. */
  checked: string | null;
  traits: Traits;
  sources: string[];
  en: CardText;
}

/** `checked:` → "YYYY-MM-DD", null if absent, undefined if invalid. YAML turns an unquoted date into a Date and
 *  silently rolls 2026-13-40 over, so for a Date the raw frontmatter text is validated instead. */
function parseChecked(v: unknown, rawFrontmatter: string): string | null | undefined {
  if (v == null) return null;
  const raw = /^checked:\s*['"]?([^'"#\s]*)/m.exec(rawFrontmatter)?.[1] ?? '';
  const s = v instanceof Date ? raw : typeof v === 'string' ? v.trim() : '';
  if (!/^\d{4}-\d{2}-\d{2}$/.test(s)) return undefined;
  const d = new Date(`${s}T00:00:00Z`);
  return !isNaN(d.getTime()) && d.toISOString().slice(0, 10) === s ? s : undefined;
}

/** Validate one card's frontmatter + body; throws with the file name on any schema error. */
function parseCard(file: string, data: Record<string, any>, content: string, known: Set<string>, rawFrontmatter = ''): SpeciesCard {
  const where = `content/species/${file}`;
  const fail = (m: string) => new Error(`${where}: ${m} (schema: content/README.md)`);
  const slug = file.replace(/\.md$/, '');
  if (data.id !== slug) throw fail(`id "${data.id}" must equal the file name "${slug}"`);
  if (!known.has(slug)) throw fail(`id "${slug}" is not in data/species_index.json`);
  if (!['easy', 'medium', 'hard'].includes(data.difficulty)) throw fail('difficulty must be easy | medium | hard');
  if (data.lynx_page != null && !Number.isInteger(data.lynx_page)) throw fail('lynx_page must be an integer or null');
  const checked = parseChecked(data.checked, rawFrontmatter);
  if (checked === undefined) throw fail('checked must be a date YYYY-MM-DD or absent');
  const str = (v: unknown, k: string) => {
    if (typeof v !== 'string' || !v.trim()) throw fail(`${k} must be a non-empty string`);
    return v.trim();
  };
  const text = (o: Record<string, any>, body: string, pre: string): CardText => {
    if ('beginner_note' in o) throw fail(`${pre}beginner_note was removed (27.09): put beginner tips into the body text`);
    const kf = o.key_features;
    if (!Array.isArray(kf) || kf.length < 3 || kf.length > 5) throw fail(`${pre}key_features must list 3–5 strings`);
    const sim = o.similar ?? [];
    if (!Array.isArray(sim)) throw fail(`${pre}similar must be a list of {id, how}`);
    return {
      key_features: kf.map((x: unknown, i: number) => str(x, `${pre}key_features[${i}]`)),
      similar: sim.map((x: any, i: number) => {
        const id = str(x?.id, `${pre}similar[${i}].id`);
        if (!known.has(id)) throw fail(`${pre}similar[${i}].id "${id}" is not in data/species_index.json`);
        if (id === slug) throw fail(`${pre}similar[${i}] points to the card itself`);
        return { id, how: str(x?.how, `${pre}similar[${i}].how`) };
      }),
      behavior: str(o.behavior, `${pre}behavior`),
      voice: str(o.voice, `${pre}voice`),
      body: paragraphs(body),
    };
  };
  const [ru, en = ''] = content.split(/^## English\s*$/m);
  if (!data.en || typeof data.en !== 'object') throw fail('en: English mirror is required');
  if (!en.trim()) throw fail('body needs a "## English" section');
  const card: SpeciesCard = {
    id: slug,
    difficulty: data.difficulty,
    lynx_page: data.lynx_page ?? null,
    checked,
    traits: validateTraits(data.traits, where),
    sources: Array.isArray(data.sources) ? data.sources.map((x: unknown, i: number) => str(x, `sources[${i}]`)) : [],
    ...text(data, ru, ''),
    en: text(data.en, en, 'en.'),
  };
  if (!card.sources.length) throw fail('sources must list at least one source');
  const ruIds = card.similar.map((x) => x.id).join(), enIds = card.en.similar.map((x) => x.id).join();
  if (ruIds !== enIds) throw fail('similar and en.similar must list the same ids in the same order');
  return card;
}

let _cards: Map<string, SpeciesCard> | null = null;
/** All species cards, validated (a bad card fails the build), keyed by species id. */
export function speciesCards(): Map<string, SpeciesCard> {
  if (_cards) return _cards;
  const dir = join(CONTENT, 'species');
  const out = new Map<string, SpeciesCard>();
  if (existsSync(dir)) {
    const known = new Set(speciesIndex().map((s) => s.id));
    for (const f of readdirSync(dir).sort()) {
      if (!f.endsWith('.md') || f === 'README.md') continue;
      const { data, content, matter: raw } = matter(readFileSync(join(dir, f), 'utf8'));
      const c = parseCard(f, data, content, known, raw);
      out.set(c.id, c);
    }
  }
  return (_cards = out);
}
/** Card for a species id, or null if none written yet. */
export function speciesCard(id: string): SpeciesCard | null {
  return speciesCards().get(id) ?? null;
}

/* ---- Standalone reference pages: content/history.md ---- */

/** One block of a reference page body. Inline text is already HTML (escaped, linkified). */
export type PageBlock =
  | { kind: 'h2'; id: string; html: string }
  | { kind: 'h3'; id: string; html: string }
  | { kind: 'p'; html: string }
  | { kind: 'ul'; items: string[] }
  | { kind: 'table'; head: string[]; rows: string[][] };

export interface ReferencePage {
  title: string;
  lead: string | null;
  updated: string | null;
  sources: string[];
  blocks: PageBlock[];
}

const escHtml = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

/** Inline markdown subset: **bold**, *italic*, [text](https://…); plain text goes through linkify (site and species names). */
function inline(text: string, base: string): string {
  const re = /\*\*(.+?)\*\*|\*(.+?)\*|\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g;
  let out = '';
  let pos = 0;
  for (let m = re.exec(text); m; m = re.exec(text)) {
    out += linkify(text.slice(pos, m.index), base);
    if (m[1] != null) out += `<strong>${linkify(m[1], base)}</strong>`;
    else if (m[2] != null) out += `<em>${linkify(m[2], base)}</em>`;
    else out += `<a href="${escHtml(m[4])}" rel="noopener">${escHtml(m[3])}</a>`;
    pos = re.lastIndex;
  }
  return out + linkify(text.slice(pos), base);
}

/** Bare URLs in a source line become links; the rest is escaped. */
function sourceHtml(s: string): string {
  return s.split(/(https?:\/\/\S+)/)
    .map((part, i) => (i % 2 ? `<a href="${escHtml(part)}" rel="noopener">${escHtml(part)}</a>` : escHtml(part)))
    .join('');
}

/**
 * Parse a reference page (content/<name>.md): frontmatter `title`, `lead`, `updated`, `sources`, then a body of
 * `## Heading` sections (with `### Subheading` inside them), paragraphs (blank-line separated, like the portraits),
 * `- ` lists and `| a | b |` tables (header + `|---|` row). A deliberately small markdown subset, no extra dependency.
 */
export function referencePage(name: string, base: string): ReferencePage {
  const { data, content } = matter(readFileSync(join(CONTENT, `${name}.md`), 'utf8'));
  if (typeof data.title !== 'string' || !data.title.trim()) throw new Error(`content/${name}.md: missing "title" in frontmatter`);
  const updated = data.updated instanceof Date ? data.updated.toISOString().slice(0, 10) : data.updated ? String(data.updated) : null;
  const cells = (row: string) => row.trim().replace(/^\||\|$/g, '').split('|').map((c) => inline(c.trim(), base));
  const blocks: PageBlock[] = [];
  for (const chunk of content.split(/\n\s*\n/)) {
    const lines = chunk.split('\n').map((l) => l.trimEnd()).filter((l) => l.trim());
    if (!lines.length) continue;
    const first = lines[0].trim();
    const h = /^(##|###)\s+(.+)$/.exec(first);
    if (h) {
      const id = h[2].toLowerCase().replace(/[^\p{L}\p{N}]+/gu, '-').replace(/^-|-$/g, '');
      blocks.push(h[1] === '##' ? { kind: 'h2', id, html: inline(h[2], base) } : { kind: 'h3', id, html: inline(h[2], base) });
      if (lines.length > 1) blocks.push({ kind: 'p', html: inline(lines.slice(1).join(' '), base) });
    } else if (first.startsWith('|')) {
      const [head, sep, ...rows] = lines;
      if (!sep || !/^\|?[\s:|-]+\|?$/.test(sep.trim())) throw new Error(`content/${name}.md: a table needs a |---| row after the header`);
      blocks.push({ kind: 'table', head: cells(head), rows: rows.map(cells) });
    } else if (/^[-*]\s/.test(first)) {
      const items: string[] = [];
      for (const l of lines) {
        if (/^\s*[-*]\s/.test(l)) items.push(l.replace(/^\s*[-*]\s+/, ''));
        else items[items.length - 1] += ' ' + l.trim();
      }
      blocks.push({ kind: 'ul', items: items.map((i) => inline(i, base)) });
    } else {
      blocks.push({ kind: 'p', html: inline(lines.map((l) => l.trim()).join(' '), base) });
    }
  }
  return {
    title: data.title.trim(),
    lead: typeof data.lead === 'string' ? data.lead.trim() : null,
    updated,
    sources: (Array.isArray(data.sources) ? data.sources : []).map((s: unknown) => sourceHtml(String(s))),
    blocks,
  };
}
