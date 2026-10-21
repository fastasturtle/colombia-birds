/**
 * Hidden page /igor-500/ (not linked anywhere, noindex, outside the offline pack): derived data for Igor's push to 500
 * species, content/igor-500/data.json (counts and candidate species per remaining site; no personal species list).
 * Build time only. Every species id must exist in data/species_index.json, otherwise `npm run build` fails.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { speciesIndex, type IndexEntry } from './data';

const FILE = join(process.cwd(), '..', 'content', 'igor-500', 'data.json');

export type Tier = 'sure' | 'likely' | 'chance';
export interface Candidate {
  id: string; sci: string; en: string; ru: string | null; n_aut: number; n: number; family: string; tier: Tier;
  /** someone else in the group already saw it on this trip */
  group: boolean;
}
export interface ReachableMissed { id: string; sci: string; en: string; ru: string | null; sites: Record<string, number> }
export interface Igor500 {
  person_ru: string; species: number; checklists: number; as_of: string; goal: number; group_species: number;
  sure_total: number; likely_total: number;
  sites: Record<string, Candidate[]>;
  reachable_missed: ReachableMissed[];
}

let _d: Igor500 | null = null;
export function igor500(): Igor500 {
  if (_d) return _d;
  const d = JSON.parse(readFileSync(FILE, 'utf8')) as Igor500;
  const idx = new Set(speciesIndex().map((s) => s.id));
  const ids = [...Object.values(d.sites).flat(), ...d.reachable_missed].map((x) => x.id);
  const bad = ids.filter((id) => !idx.has(id));
  if (bad.length) throw new Error(`content/igor-500/data.json: unknown species ids ${[...new Set(bad)].join(', ')}`);
  return (_d = d);
}

/** Index entry by id; throws on an unknown id (a typo in the page's hand-written target lists). */
export function sp(id: string): IndexEntry {
  const s = speciesIndex().find((x) => x.id === id);
  if (!s) throw new Error(`igor-500: unknown species id "${id}"`);
  return s;
}
