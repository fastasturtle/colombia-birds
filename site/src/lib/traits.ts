/**
 * Closed trait vocabulary (content/traits.yaml; «Признаки» in FilterBar) and the validator for `traits` in species cards
 * (content/species/<slug>.md). Build time only. Any value outside the vocabulary, or a wrong number of values in a
 * group, throws with the file name, so `npm run build` fails instead of shipping a silently unmatched card.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import matter from 'gray-matter';

const FILE = join(process.cwd(), '..', 'content', 'traits.yaml');

export interface TraitValue { key: string; ru: string; en: string; hint: string | null }
export interface TraitGroup {
  key: string;
  label: { ru: string; en: string };
  /** how many values a card may carry; max 1 = a single string in the card */
  min: number;
  max: number;
  values: TraitValue[];
}
/** Normalised traits of one card: group key -> values (always an array, in vocabulary order). */
export type Traits = Record<string, string[]>;

let _vocab: TraitGroup[] | null = null;
/** Trait groups in display order (content/traits.yaml). */
export function traitVocabulary(): TraitGroup[] {
  if (_vocab) return _vocab;
  // gray-matter's YAML engine, so no extra dependency: wrap the file as front matter.
  const raw = matter(`---\n${readFileSync(FILE, 'utf8')}\n---\n`).data as Record<string, any>;
  const bad = (m: string) => new Error(`content/traits.yaml: ${m}`);
  const out: TraitGroup[] = [];
  for (const [key, g] of Object.entries(raw)) {
    if (!g || typeof g !== 'object' || !g.values || typeof g.values !== 'object') throw bad(`group "${key}" has no values`);
    if (!g.label?.ru || !g.label?.en) throw bad(`group "${key}" needs label.ru and label.en`);
    const min = Number(g.min ?? 0), max = Number(g.max ?? Object.keys(g.values).length);
    if (!Number.isInteger(min) || !Number.isInteger(max) || min < 0 || max < Math.max(1, min)) throw bad(`group "${key}": bad min/max`);
    const values = Object.entries(g.values as Record<string, any>).map(([k, v]) => {
      if (!v?.ru || !v?.en) throw bad(`${key}.${k} needs ru and en labels`);
      return { key: k, ru: String(v.ru), en: String(v.en), hint: v.hint ? String(v.hint) : null };
    });
    out.push({ key, label: { ru: String(g.label.ru), en: String(g.label.en) }, min, max, values });
  }
  return (_vocab = out);
}

/**
 * Check a card's `traits` against the vocabulary and normalise it (strings -> one-element arrays, vocabulary order).
 * Every group with min >= 1 is required. `file` is used in error messages (e.g. "content/species/x.md").
 */
export function validateTraits(raw: unknown, file: string): Traits {
  const fail = (m: string) => new Error(`${file}: traits: ${m} (vocabulary: content/traits.yaml)`);
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) throw fail('must be a mapping of group -> value(s)');
  const vocab = traitVocabulary();
  const groups = new Map(vocab.map((g) => [g.key, g]));
  const obj = raw as Record<string, unknown>;
  for (const k of Object.keys(obj)) if (!groups.has(k)) throw fail(`unknown group "${k}"; allowed: ${[...groups.keys()].join(', ')}`);
  const out: Traits = {};
  for (const g of vocab) {
    const v = obj[g.key];
    const list = v == null ? [] : Array.isArray(v) ? v : [v];
    if (list.some((x) => typeof x !== 'string')) throw fail(`${g.key}: values must be strings`);
    const allowed = new Set(g.values.map((x) => x.key));
    const badVals = (list as string[]).filter((x) => !allowed.has(x));
    if (badVals.length) throw fail(`${g.key}: unknown value${badVals.length > 1 ? 's' : ''} ${badVals.map((x) => `"${x}"`).join(', ')}; allowed: ${[...allowed].join(', ')}`);
    if (new Set(list).size !== list.length) throw fail(`${g.key}: duplicate value`);
    if (list.length < g.min || list.length > g.max)
      throw fail(`${g.key}: ${list.length} value(s), expected ${g.min === g.max ? g.min : `${g.min}–${g.max}`}`);
    if (list.length) out[g.key] = g.values.map((x) => x.key).filter((k) => list.includes(k));
  }
  return out;
}

/** The vocabulary for the client (lib/filter TraitOpt: FilterBar): Russian labels, hints only where set. */
export function traitOpts(): { key: string; label: string; values: { key: string; label: string; hint?: string }[] }[] {
  return traitVocabulary().map((g) => ({
    key: g.key, label: g.label.ru,
    values: g.values.map((v) => ({ key: v.key, label: v.ru, ...(v.hint ? { hint: v.hint } : {}) })),
  }));
}
let _flat: Map<string, number> | null = null;
/**
 * A card's traits as the compact row token of lib/filter (data-tr): one character per value, String.fromCharCode(65 + i),
 * i = the value's index in the flattened vocabulary. 62 values at most (65..126 is plain ASCII that needs no escaping).
 */
export function traitToken(t: Traits): string {
  if (!_flat) {
    const flat = traitVocabulary().flatMap((g) => g.values.map((v) => `${g.key}:${v.key}`));
    if (flat.length > 62) throw new Error('content/traits.yaml: more than 62 values, extend the row token encoding (lib/filter)');
    _flat = new Map(flat.map((k, i) => [k, i]));
  }
  return Object.entries(t).flatMap(([g, vs]) => vs.map((v) => String.fromCharCode(65 + _flat!.get(`${g}:${v}`)!))).join('');
}
