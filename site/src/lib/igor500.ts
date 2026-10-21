/**
 * Hidden page /igor-500/ (not linked anywhere, noindex, outside the offline pack): derived data for Igor's push to 500
 * species, data/igor500.json (pipeline step `igor500`, refreshed every 2 hours by the observations workflow from the
 * eBird trip report: counts and candidate species per remaining site; no personal species list).
 * Build time only. Every species id must exist in data/species_index.json, otherwise `npm run build` fails.
 */
import { readJson, speciesIndex, type IndexEntry } from './data';

const FILE = 'igor500.json';

export type Tier = 'sure' | 'likely' | 'chance';
export interface Candidate {
  id: string; sci: string; en: string; ru: string | null; n_aut: number; n: number; family: string; tier: Tier;
  /** someone else in the group already saw it on this trip */
  group: boolean;
}
export interface ReachableMissed { id: string; sci: string; en: string; ru: string | null; sites: Record<string, number> }
export interface Igor500 {
  person: string; person_ru: string; species: number; checklists: number;
  /** latest checklist of the person in the trip report, "YYYY-MM-DD HH:MM" (local time of the checklist) */
  as_of: string; goal: number; group_species: number; missed_in_group: number;
  sure_total: number; likely_total: number;
  /** UTC ISO time of the last pipeline run that changed the file */
  fetched: string;
  sites: Record<string, Candidate[]>;
  reachable_missed: ReachableMissed[];
}

let _d: Igor500 | null = null;
export function igor500(): Igor500 {
  if (_d) return _d;
  const d = readJson<Igor500>(FILE);
  const idx = new Set(speciesIndex().map((s) => s.id));
  const ids = [...Object.values(d.sites).flat(), ...d.reachable_missed].map((x) => x.id);
  const bad = ids.filter((id) => !idx.has(id));
  if (bad.length) throw new Error(`data/igor500.json: unknown species ids ${[...new Set(bad)].join(', ')}`);
  return (_d = d);
}

/** Index entry by id; throws on an unknown id (a typo in the page's hand-written target lists). */
export function sp(id: string): IndexEntry {
  const s = speciesIndex().find((x) => x.id === id);
  if (!s) throw new Error(`igor-500: unknown species id "${id}"`);
  return s;
}
