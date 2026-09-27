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
  beginner_note: string;
  body: string[];
}
export interface SpeciesCard extends CardText {
  id: string;
  difficulty: Difficulty;
  lynx_page: number | null;
  traits: Traits;
  sources: string[];
  en: CardText;
}

/** Validate one card's frontmatter + body; throws with the file name on any schema error. */
function parseCard(file: string, data: Record<string, any>, content: string, known: Set<string>): SpeciesCard {
  const where = `content/species/${file}`;
  const fail = (m: string) => new Error(`${where}: ${m} (schema: content/README.md)`);
  const slug = file.replace(/\.md$/, '');
  if (data.id !== slug) throw fail(`id "${data.id}" must equal the file name "${slug}"`);
  if (!known.has(slug)) throw fail(`id "${slug}" is not in data/species_index.json`);
  if (!['easy', 'medium', 'hard'].includes(data.difficulty)) throw fail('difficulty must be easy | medium | hard');
  if (data.lynx_page != null && !Number.isInteger(data.lynx_page)) throw fail('lynx_page must be an integer or null');
  const str = (v: unknown, k: string) => {
    if (typeof v !== 'string' || !v.trim()) throw fail(`${k} must be a non-empty string`);
    return v.trim();
  };
  const text = (o: Record<string, any>, body: string, pre: string): CardText => {
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
      beginner_note: str(o.beginner_note, `${pre}beginner_note`),
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
      const { data, content } = matter(readFileSync(join(dir, f), 'utf8'));
      const c = parseCard(f, data, content, known);
      out.set(c.id, c);
    }
  }
  return (_cards = out);
}
/** Card for a species id, or null if none written yet. */
export function speciesCard(id: string): SpeciesCard | null {
  return speciesCards().get(id) ?? null;
}
