/**
 * Read-only access to the generated database in ../data (built by pipeline/).
 * Everything here runs at build time only.
 */
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { searchKey } from './filter';
// content.ts imports this module too; the cycle is safe, both only call each other inside functions
import { speciesCards } from './content';
import { traitOpts, traitToken } from './traits';

const DATA = join(process.cwd(), '..', 'data');
/** Optional directory whose files shadow ../data (local testing only, e.g. stub files). */
const DATA_OVERRIDE = process.env.CB_DATA_OVERRIDE ?? '';

function readJson<T>(rel: string, fallback?: T): T {
  const o = DATA_OVERRIDE && join(DATA_OVERRIDE, rel);
  const p = o && existsSync(o) ? o : join(DATA, rel);
  if (!existsSync(p)) {
    if (fallback !== undefined) return fallback;
    throw new Error(`missing data file: ${p}`);
  }
  return JSON.parse(readFileSync(p, 'utf8')) as T;
}

export interface IndexEntry {
  id: string; sci: string; en: string; ru: string | null; family: string; order: string;
  taxon_order: number; status: string[]; endemic: boolean; iucn: string;
  /** near-endemic of Colombia (pipeline field; missing in older data = false) */
  near_endemic: boolean;
  elev: [number | null, number | null] | null; habitat: string | null; photo: string | null;
  /** page in Hilty (2021) «Birds of Colombia», Lynx Edicions; null = not found */
  lynx_page: number | null;
}
export interface Family {
  code: string; sci: string; order: string; names: Record<string, string>; species_count: number; slug: string;
  /** first page of the family in Hilty (2021) «Birds of Colombia», Lynx; null = not found */
  lynx_page: number | null;
}
export interface Photo {
  key_base: string; sizes: { thumb: string; medium: string; large: string };
  width?: number; height?: number; author: string; license: string; license_url?: string; source_url: string; credit?: string;
}
export interface Species {
  id: string; sci_name: string; sci_name_aco: string | null; authorship: string; taxonomy_note: string | null;
  /** aco2022 = ACO 2022 checklist taxon; clements2025 = eBird/Clements 2025 species absent from ACO (docs/DECISIONS.md row 19) */
  source?: 'aco2022' | 'clements2025';
  names: { en: string; ru: string | null; es: string | null; en_aco: string }; name_ru_source: string | null;
  ebird_code: string; taxon_order: number; order: string; family: { code: string; sci: string; en: string | null }; genus: string;
  colombia: { status: string[]; status_uncertain: boolean; status_raw: string; endemic: boolean; introduced: boolean;
    migration_note: string; libro_rojo: string; habitat_aco: string };
  iucn: { aco_2022: string; birdbase_2024: string | null; wikidata: string | null };
  traits: { elevation_m: { min: number | null; max: number | null; min_extreme: number | null; max_extreme: number | null } | null;
    mass_g: number | null; primary_habitat: string | null; habitats: string[]; habitat_breadth: number | null;
    primary_diet: string | null; diet_desc: string | null; mobility: Record<string, number | null> | null; range_restricted: number | null };
  ids: Record<string, string | number | null>;
  links: { ebird: string; wikipedia: Record<string, string | null>; commons_category: string | null; xeno_canto: string; inaturalist: string | null };
  wikidata_images: string[]; photos: Photo[]; texts: Record<string, unknown>; sounds: unknown[]; difficulty: string | null;
  /** field guide reference: Hilty (2021) «Birds of Colombia», Lynx Edicions */
  book: { lynx_page: number | null };
}
export interface WikiText {
  title: string; url: string; revision: number | null; retrieved: string; license: string; license_url: string;
  intro: string; sections: Record<string, string>;
}
export interface Texts { id: string; wikipedia: Record<string, WikiText> }

export interface Site {
  id: string; name: string; name_ru: string; region: string; department: string; lat: number; lon: number;
  coords_approx: boolean; elev_min: number | null; elev_max: number | null; habitat_ru: string;
  ebird_hotspots: { id: string; name: string }[]; sources: string[]; notes_ru: string;
  target_species?: string[]; target_species_raw?: { en: string; sci: string | null }[];
  /** not part of the group tour: a possible own trip from Bogotá on a free day (hand-authored in data/sites.json) */
  optional?: boolean;
}
export interface Day {
  date: string; day: number | string; title_ru: string; sites: string[]; overnight: string; overnight_site: string | null;
  guide: string | null; region: string; travel_ru: string; elev_sleep: number | null;
}
export interface Region { id: string; name_ru: string; name_en: string; description_ru: string; color: string; order: number }

let _focus: Set<string> | null = null;
/** Target species of the route (pipeline step `sites`, data/focus_species.json). */
export function focusSpecies(): Set<string> {
  return (_focus ??= new Set(readJson<string[]>('focus_species.json', [])));
}

let _index: IndexEntry[] | null = null;
/**
 * Display names of a species: Russian is the primary name, English the secondary one.
 * Without a Russian name English becomes primary and there is no secondary (never print it twice).
 * Takes an IndexEntry ({ ru, en }) or Species.names.
 */
export function speciesNames(s: { ru: string | null; en: string }): { main: string; alt: string | null } {
  return s.ru ? { main: s.ru, alt: s.en && s.en !== s.ru ? s.en : null } : { main: s.en, alt: null };
}
export function speciesIndex(): IndexEntry[] {
  return (_index ??= readJson<IndexEntry[]>('species_index.json').map((s) => ({ ...s, near_endemic: s.near_endemic === true })));
}
export function families(): Family[] {
  return readJson<Family[]>('families.json');
}
/* ---- Informal field-guide groups above families (hand-authored data/groups.json) ---- */
export interface Group {
  id: string; name_ru: string; name_en: string; blurb_ru: string; blurb_en: string;
  /** family codes (Family.code), in display order */
  families: string[];
}
let _groups: Group[] | null = null;
/** Bird groups in field-guide order; every family belongs to exactly one. */
export function groups(): Group[] {
  if (_groups) return _groups;
  const gs = readJson<Group[]>('groups.json');
  const seen = new Map<string, string>();
  for (const g of gs) for (const c of g.families) {
    if (seen.has(c)) throw new Error(`groups.json: family ${c} in both ${seen.get(c)} and ${g.id}`);
    seen.set(c, g.id);
  }
  const missing = families().filter((f) => !seen.has(f.code)).map((f) => f.code);
  if (missing.length) throw new Error(`groups.json: families without a group: ${missing.join(', ')}`);
  return (_groups = gs);
}
let _groupOf: Map<string, Group> | null = null;
/** The group a family code belongs to. */
export function groupOfFamily(code: string): Group | null {
  _groupOf ??= new Map(groups().flatMap((g) => g.families.map((c) => [c, g] as const)));
  return _groupOf.get(code) ?? null;
}
let _ordersRu: Record<string, string> | null = null;
/** Russian name of an order ('Passeriformes' -> 'Воробьинообразные'), null if unknown. */
export function orderRu(order: string): string | null {
  return (_ordersRu ??= readJson<Record<string, string>>('orders_ru.json', {}))[order] ?? null;
}
export function species(id: string): Species {
  return readJson<Species>(`species/${id}.json`);
}
export function allSpecies(): Species[] {
  return readdirSync(join(DATA, 'species')).filter((f) => f.endsWith('.json')).map((f) => species(f.replace(/\.json$/, '')));
}
export function texts(id: string): Texts | null {
  return readJson<Texts | null>(`texts/${id}.json`, null);
}
let _sites: Site[] | null = null;
/** All sites, tour sites first, then optional ones (each group in data/sites.json order). */
export function sites(): Site[] {
  if (_sites) return _sites;
  const authored = readJson<Site[]>('sites.json', []);
  const resolved = readJson<Site[] | null>('sites_resolved.json', null);
  // `optional` is authored in sites.json; take it from there so a stale sites_resolved.json cannot lose it
  const opt = new Set(authored.filter((s) => s.optional === true).map((s) => s.id));
  const all = (resolved ?? authored).map((s) => ({ ...s, optional: opt.has(s.id) }));
  return (_sites = [...all.filter((s) => !s.optional), ...all.filter((s) => s.optional)]);
}
/** Group title for optional sites (not in the tour programme). */
export const OPTIONAL_SITES_RU = 'Возможные выезды из Боготы';
export const OPTIONAL_SITE_TAG_RU = 'не в программе тура';
/** True for a site that is not part of the group tour (`optional: true` in data/sites.json). */
export function isOptionalSite(id: string): boolean {
  return sitesById().get(id)?.optional === true;
}
export interface HotspotCheck { id: string; name_api: string | null; numSpeciesAllTime: number | null; status: string }
let _hsCheck: Record<string, HotspotCheck> | null = null;
/** Listed eBird hotspots verified by pipeline step `hotspots` (data/sources/hotspots_check.json), keyed by locId. */
export function hotspotCheck(id: string): HotspotCheck | null {
  if (!_hsCheck) {
    _hsCheck = {};
    const r = readJson<{ sites: Record<string, { listed: HotspotCheck[] }> } | null>('sources/hotspots_check.json', null);
    for (const s of Object.values(r?.sites ?? {})) for (const h of s.listed) _hsCheck[h.id] = h;
  }
  return _hsCheck[id] ?? null;
}
export function itinerary(): Day[] {
  return readJson<Day[]>('itinerary.json', []);
}
export function regions(): Region[] {
  return readJson<Region[]>('regions.json', []).sort((a, b) => a.order - b.order);
}

export const MEDIA_BASE = (import.meta.env.PUBLIC_MEDIA_BASE_URL ?? 'https://pub-5e58909dbd0e457c85e4e36ef2cdc583.r2.dev').replace(/\/$/, '');
export function mediaUrl(key: string): string {
  return `${MEDIA_BASE}/${key}`;
}

export const STATUS_RU: Record<string, string> = {
  resident: 'оседлый',
  endemic: 'эндемик',
  boreal_migrant: 'северный мигрант',
  austral_migrant: 'южный мигрант',
  vagrant: 'залётный',
  hypothetical: 'гипотетический',
  introduced: 'интродуцирован',
  extinct: 'вымер',
};
export const IUCN_RU: Record<string, string> = {
  LC: 'не вызывает опасений', NT: 'близок к уязвимому', VU: 'уязвимый', EN: 'под угрозой', CR: 'на грани исчезновения', DD: 'данных недостаточно', EX: 'вымер',
};
export const HABITAT_RU: Record<string, string> = {
  Forest: 'лес', Shrubland: 'кустарники', Grassland: 'луга и саванны', Wetland: 'водно-болотные угодья', Woodland: 'редколесье',
  Marine: 'море', 'Human Modified': 'антропогенные ландшафты', Riverine: 'реки', Coastal: 'побережье', Rock: 'скалы',
  Savanna: 'саванна', Desert: 'пустыня', Agricultural: 'сельхозугодья', Shrub: 'кустарники', Bamboo: 'бамбук', Plantation: 'плантации', Riparian: 'приречные заросли', 'Rivers/Lakes': 'реки и озёра', Sea: 'море', Other: 'другое', Rocky: 'скалы', Artificial: 'антропогенные ландшафты', Plains: 'равнины',
};

/* ---- Likelihood per (species, place) and «интересная» (pipeline steps gbif_sites + study) ----
 * state: sure («точно», GBIF autumn freq >= 1% within the site radius), maybe («возможно», 0.1–1%),
 * unlikely («вряд ли», < 0.1%, < 3 autumn records, or not in the site's GBIF list). Thresholds: pipeline/common.py.
 * interesting: trip-report highlight at the place, Colombian endemic or near-endemic, or range-restricted; independent of state. */
export type State = 'sure' | 'maybe' | 'unlikely';
export const STATES: State[] = ['sure', 'maybe', 'unlikely'];
export const STATE_RU: Record<State, string> = { sure: 'точно', maybe: 'возможно', unlikely: 'вряд ли' };
export const STATE_RANK: Record<State, number> = { sure: 2, maybe: 1, unlikely: 0 };
export function asState(x: unknown): State {
  return x === 'sure' || x === 'maybe' ? x : 'unlikely';
}
export const bestState = (xs: State[]): State => xs.reduce<State>((a, b) => (STATE_RANK[b] > STATE_RANK[a] ? b : a), 'unlikely');
export type Why = 'highlight' | 'endemic' | 'near_endemic' | 'range_restricted';
export const WHY_RU: Record<Why, string> = { highlight: 'цель из отчётов о поездках', endemic: 'эндемик Колумбии', near_endemic: 'почти-эндемик Колумбии', range_restricted: 'узкий ареал' };

export interface SiteSpeciesEntry { id: string; n: number; n_aut: number; freq_aut: number; state: State }
export interface SiteSpecies {
  radius_km: number; total_records: number; total_records_aut?: number; retrieved: string; species: SiteSpeciesEntry[];
}
let _siteSpecies: Record<string, SiteSpecies> | null = null;
export function siteSpecies(): Record<string, SiteSpecies> {
  if (_siteSpecies) return _siteSpecies;
  const raw = readJson<Record<string, SiteSpecies>>('site_species.json', {});
  for (const v of Object.values(raw)) for (const x of v.species) x.state = asState(x.state);
  return (_siteSpecies = raw);
}
let _siteMap: Map<string, Map<string, SiteSpeciesEntry>> | null = null;
function siteEntry(siteId: string, spId: string): SiteSpeciesEntry | undefined {
  _siteMap ??= new Map(Object.entries(siteSpecies()).map(([k, v]) => [k, new Map(v.species.map((x) => [x.id, x]))]));
  return _siteMap.get(siteId)?.get(spId);
}
/** State of a species at a site; not in the site's GBIF list = unlikely. */
export function siteState(siteId: string, spId: string): State {
  return siteEntry(siteId, spId)?.state ?? 'unlikely';
}
let _rr: Set<string> | null = null;
/** Range-restricted species (data/species/<id>.json traits.range_restricted == 1). */
export function rangeRestricted(): Set<string> {
  return (_rr ??= new Set(allSpecies().filter((s) => s.traits?.range_restricted === 1).map((s) => s.id)));
}
let _endemic: Set<string> | null = null;
let _nearEndemic: Set<string> | null = null;
/** Near-endemics of Colombia that are not endemics (species_index `near_endemic`). */
export function nearEndemics(): Set<string> {
  return (_nearEndemic ??= new Set(speciesIndex().filter((s) => s.near_endemic && !s.endemic).map((s) => s.id)));
}
/** Reasons a species is «интересная» at the given sites (all route sites when omitted). */
export function whyInteresting(spId: string, siteIds?: string[]): Why[] {
  _endemic ??= new Set(speciesIndex().filter((s) => s.endemic).map((s) => s.id));
  const ids = siteIds ?? routeSiteIds();
  const siteOf = sitesById();
  const out: Why[] = [];
  if (ids.some((sid) => siteOf.get(sid)?.target_species?.includes(spId))) out.push('highlight');
  if (_endemic.has(spId)) out.push('endemic');
  if (nearEndemics().has(spId)) out.push('near_endemic');
  if (rangeRestricted().has(spId)) out.push('range_restricted');
  return out;
}
let _sitesById: Map<string, Site> | null = null;
function sitesById(): Map<string, Site> {
  return (_sitesById ??= new Map(sites().map((s) => [s.id, s])));
}
let _routeSites: string[] | null = null;
/** Sites visited on some itinerary day. */
export function routeSiteIds(): string[] {
  return (_routeSites ??= [...new Set(itinerary().flatMap((d) => d.sites))]);
}
let _routeState: Map<string, State> | null = null;
/** Best state of a species across all route sites (no place context); no route data = unlikely. */
export function routeState(spId: string): State {
  if (!_routeState) {
    _routeState = new Map();
    for (const sid of routeSiteIds()) for (const x of siteSpecies()[sid]?.species ?? []) {
      const cur = _routeState.get(x.id);
      if (!cur || STATE_RANK[x.state] > STATE_RANK[cur]) _routeState.set(x.id, x.state);
    }
  }
  return _routeState.get(spId) ?? 'unlikely';
}

export interface PlaceSpecies {
  id: string;
  /** GBIF records (all year) summed over the given sites (0 if only a highlight) */
  n: number;
  /** best state across the given sites */
  state: State;
  /** best autumn frequency across the given sites */
  freq_aut: number;
  why: Why[];
  interesting: boolean;
  /** ids of the sites that list it as a highlight (trip reports, `target_species`) */
  highlightAt: string[];
}
/** Merge GBIF species and trip-report highlights of several sites, deduped; sorted interesting, state, freq. */
export function speciesForSites(siteIds: string[]): PlaceSpecies[] {
  const ids = [...new Set(siteIds)];
  const siteOf = sitesById();
  const out = new Map<string, PlaceSpecies>();
  const at = (id: string) => out.get(id) ?? out.set(id, { id, n: 0, state: 'unlikely', freq_aut: 0, why: [], interesting: false, highlightAt: [] }).get(id)!;
  for (const sid of ids) {
    for (const x of siteSpecies()[sid]?.species ?? []) {
      const e = at(x.id);
      e.n += x.n;
      e.state = bestState([e.state, x.state]);
      e.freq_aut = Math.max(e.freq_aut, x.freq_aut ?? 0);
    }
    for (const id of siteOf.get(sid)?.target_species ?? []) at(id).highlightAt.push(sid);
  }
  const known = new Set(speciesIndex().map((s) => s.id));
  const res = [...out.values()].filter((e) => known.has(e.id));
  for (const e of res) { e.why = whyInteresting(e.id, ids); e.interesting = e.why.length > 0; }
  return res.sort(cmpPlace);
}
/** Of the given sites, those that list the species (GBIF list at any state, or a trip-report target): FilterBar's «Место». */
export function sitesListing(spId: string, siteIds: string[]): string[] {
  const siteOf = sitesById();
  return siteIds.filter((sid) => siteEntry(sid, spId) || siteOf.get(sid)?.target_species?.includes(spId));
}
let _enAlt: Map<string, string> | null = null;
/** ACO English name where it differs from the eBird/Clements one (older or alternative name; searchable). */
export function enAltName(spId: string): string | null {
  if (!_enAlt) {
    const idx = new Map(speciesIndex().map((s) => [s.id, s.en]));
    _enAlt = new Map(allSpecies().filter((s) => s.names.en_aco && s.names.en_aco !== idx.get(s.id)).map((s) => [s.id, s.names.en_aco]));
  }
  return _enAlt.get(spId) ?? null;
}
/**
 * Facet options of a list for FilterBar: the families present (taxonomic order) and the sites present (given order).
 * rows: family code and the row's site ids (sitesListing).
 */
export function facetOptions(rows: { family: string; sites: string[] }[], siteOrder: string[]) {
  const famSet = new Set(rows.map((r) => r.family));
  const siteSet = new Set(rows.flatMap((r) => r.sites));
  const siteOf = sitesById();
  return {
    fams: families().filter((f) => famSet.has(f.code)).map((f) => ({ code: f.code, ru: f.names.ru ?? null, en: f.names.en ?? null, sci: f.sci })),
    sites: siteOrder.filter((id) => siteSet.has(id)).map((id) => ({ id, name: siteOf.get(id)?.name_ru || siteOf.get(id)?.name || id })),
  };
}
/**
 * Everything a static list needs for FilterBar (FilterScope + ScopeFilter): the facet options, `ctx` for the scope
 * (data-lf-ctx: family codes with their searchable names, site ids; rows refer to both by index to keep pages small)
 * and `attrs(s, siteIds)`, the row's data-fam / data-sites / data-q / data-tr to spread next to data-st.
 * Traits: when a row has a species card, ctx.tv carries the trait vocabulary once (lib/traits traitOpts) and each
 * card row a data-tr token (traitToken, a few characters); rows without a card have no data-tr.
 */
export function listFacets(rows: { id: string; family: string; sites: string[] }[], siteOrder: string[]) {
  const { fams, sites: siteOpts } = facetOptions(rows, siteOrder);
  const fi = new Map(fams.map((f, i) => [f.code, i]));
  const si = new Map(siteOpts.map((s, i) => [s.id, i]));
  const cards = speciesCards();
  const tv = rows.some((r) => cards.has(r.id)) ? traitOpts() : undefined;
  return {
    fams, sites: siteOpts,
    ctx: JSON.stringify({ f: fams.map((f) => [f.code, searchKey([f.ru, f.en])]), s: siteOpts.map((s) => s.id), ...(tv ? { tv } : {}) }),
    /** shown: which names the row already prints inside [data-n] elements (rowOf reads them; the main name always is),
     * so data-q only carries the rest */
    attrs: (s: IndexEntry, siteIds: string[] = [], shown: { alt?: boolean; sci?: boolean } = {}): Record<string, string | undefined> => {
      const at = siteIds.filter((x) => si.has(x)).map((x) => si.get(x)).join(' ');
      const q = searchKey([!shown.alt ? speciesNames(s).alt : null, !shown.sci ? s.sci : null, enAltName(s.id)]);
      const card = cards.get(s.id);
      return { 'data-fam': String(fi.get(s.family) ?? ''), 'data-sites': at || undefined, 'data-q': q || undefined, 'data-tr': card ? traitToken(card.traits) : undefined };
    },
  };
}
export type RowAttrs = Record<string, string | undefined>;
export const cmpPlace = (a: { interesting: boolean; state: State; freq_aut: number; id: string }, b: typeof a) =>
  Number(b.interesting) - Number(a.interesting) || STATE_RANK[b.state] - STATE_RANK[a.state] || b.freq_aut - a.freq_aut || a.id.localeCompare(b.id);

/* ---- Per-day species lists (pipeline step study, data/study_lists.json); optional ---- */
export interface StudyEntry { id: string; state: State; interesting: boolean; why: Why[]; freq_aut: number; new_for_route: boolean }
export interface StudyList { sites: string[]; species: StudyEntry[] }
let _study: Record<string, StudyList> | null = null;
/** Species list for a date, normalised; null when the file or the day's entry is missing. */
export function studyList(date: string): StudyList | null {
  if (!_study) {
    const raw = readJson<Record<string, Partial<StudyList>> | null>('study_lists.json', null) ?? {};
    const known = new Set(speciesIndex().map((s) => s.id));
    _study = {};
    for (const [d, v] of Object.entries(raw)) {
      if (!v || typeof v !== 'object') continue;
      _study[d] = {
        sites: Array.isArray(v.sites) ? v.sites : [],
        species: (Array.isArray(v.species) ? v.species : []).filter((f) => f && known.has(f.id)).map((f) => {
          const why = (Array.isArray(f.why) ? f.why : []).filter((w): w is Why => w in WHY_RU);
          // the site owns the near-endemic rule too: add it even when study_lists.json predates the flag
          if (nearEndemics().has(f.id) && !why.includes('near_endemic')) why.push('near_endemic');
          return { id: f.id, state: asState(f.state), why, interesting: why.length > 0,
            freq_aut: typeof f.freq_aut === 'number' ? f.freq_aut : 0, new_for_route: !!f.new_for_route };
        }),
      };
    }
  }
  return _study[date] ?? null;
}
/** Counts under the default filter (lib/filter DEFAULT_FILTER: level «Все», all species), for the server-rendered
 * counters (home day cards, which have no JS; first paint of the day / site list headers). total = every species;
 * sure / maybe / unlikely split it by likelihood; interesting over all of them. */
export function defaultCounts(list: { state: State; interesting: boolean }[]) {
  const n = (s: State) => list.filter((x) => x.state === s).length;
  return { total: list.length, sure: n('sure'), maybe: n('maybe'), unlikely: n('unlikely'),
    interesting: list.filter((x) => x.interesting).length };
}
/** Days (in itinerary order) that visit a site. */
export function daysForSite(siteId: string): Day[] {
  return itinerary().filter((d) => d.sites.includes(siteId));
}

/* ---- Weather forecast (pipeline step weather, data/weather.json from Open-Meteo); optional, refreshed daily by CI ---- */
export type WeatherPeriodName = 'morning' | 'day' | 'evening';
export interface WeatherPeriod {
  t_min: number; t_max: number;
  /** max precipitation probability over the period, % */
  precip_prob: number | null;
  /** precipitation sum, mm */
  precip: number | null;
  /** mean cloud cover, % */
  cloud_cover: number | null;
  /** most severe WMO weather code of the period's hours */
  weather_code: number | null;
}
export interface WeatherSite {
  id: string; name_ru: string; elevation: number | null; overnight: boolean;
  periods: Partial<Record<WeatherPeriodName, WeatherPeriod>>;
}
export interface Weather { fetched_at: string; source: string; days: Record<string, { sites: WeatherSite[] }> }
export const WEATHER_PERIODS: { id: WeatherPeriodName; ru: string }[] = [
  { id: 'morning', ru: 'Утро' }, { id: 'day', ru: 'День' }, { id: 'evening', ru: 'Вечер' },
];
let _weather: Weather | null | undefined;
/** The whole forecast file, or null when data/weather.json is missing or malformed. */
export function weather(): Weather | null {
  if (_weather === undefined) {
    const w = readJson<Weather | null>('weather.json', null);
    _weather = w && typeof w === 'object' && w.days && typeof w.days === 'object' ? w : null;
  }
  return _weather;
}
/** Forecast rows of a date (day sites first, overnight last), or null when there is none. */
export function weatherDay(date: string): WeatherSite[] | null {
  const rows = weather()?.days[date]?.sites;
  return Array.isArray(rows) && rows.length ? rows : null;
}
/** WMO weather code -> Unicode icon + short Russian label. */
export function wmo(code: number | null | undefined): { icon: string; ru: string } {
  if (code == null) return { icon: '·', ru: '' };
  if (code === 0) return { icon: '☀️', ru: 'ясно' };
  if (code === 1) return { icon: '🌤️', ru: 'малооблачно' };
  if (code === 2) return { icon: '⛅', ru: 'облачно' };
  if (code === 3) return { icon: '☁️', ru: 'пасмурно' };
  if (code === 45 || code === 48) return { icon: '🌫️', ru: 'туман' };
  if (code >= 51 && code <= 57) return { icon: '🌦️', ru: 'морось' };
  if (code >= 61 && code <= 67) return { icon: '🌧️', ru: 'дождь' };
  if (code >= 71 && code <= 77) return { icon: '🌨️', ru: 'снег' };
  if (code >= 80 && code <= 82) return { icon: '🌧️', ru: 'ливень' };
  if (code >= 85 && code <= 86) return { icon: '🌨️', ru: 'снегопад' };
  if (code >= 95) return { icon: '⛈️', ru: 'гроза' };
  return { icon: '·', ru: '' };
}
/** '29 сентября, 05:12' in Bogotá time (UTC-5, no DST) from an ISO UTC timestamp. */
export function fmtBogota(iso: string): string {
  const t = new Date(new Date(iso).getTime() - 5 * 3600e3);
  if (Number.isNaN(t.getTime())) return iso;
  const hm = `${String(t.getUTCHours()).padStart(2, '0')}:${String(t.getUTCMinutes()).padStart(2, '0')}`;
  return `${t.getUTCDate()} ${RU_MONTHS_GEN[t.getUTCMonth()]}, ${hm}`;
}
export const RU_MONTHS_GEN = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня', 'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря'];
export const RU_WEEKDAYS = ['воскресенье', 'понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота'];
/** '2026-10-05' -> '5 октября, понедельник' */
export function fmtDateRu(date: string, weekday = true): string {
  const d = new Date(`${date}T12:00:00Z`);
  const s = `${d.getUTCDate()} ${RU_MONTHS_GEN[d.getUTCMonth()]}`;
  return weekday ? `${s}, ${RU_WEEKDAYS[d.getUTCDay()]}` : s;
}
/** Day label: 'день 3' or 'до тура' for the pre-trip days ('pre-2'). */
export function dayLabel(d: Day): string {
  return typeof d.day === 'number' ? `день ${d.day}` : 'до тура';
}
/** Russian plural: plural(5, 'вид', 'вида', 'видов') */
export function plural(n: number, one: string, few: string, many: string): string {
  const m10 = n % 10, m100 = n % 100;
  return m10 === 1 && m100 !== 11 ? one : m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14) ? few : many;
}

export interface DayWithSpecies { day: Day; species: PlaceSpecies[] }
let _dws: DayWithSpecies[] | null = null;
/** Every itinerary day with its merged species list (GBIF + highlights of the day's sites). */
export function itineraryWithSpecies(): DayWithSpecies[] {
  return (_dws ??= itinerary().map((day) => ({ day, species: speciesForSites(day.sites) })));
}

/** Up to n representative species of a family: route targets with photos, then any with a photo, then route targets without. */
export function representativeSpecies(code: string, n = 3): IndexEntry[] {
  const focus = focusSpecies();
  const all = speciesIndex().filter((s) => s.family === code).sort((a, b) => a.taxon_order - b.taxon_order);
  const tiers = [
    all.filter((s) => focus.has(s.id) && s.photo),
    all.filter((s) => !focus.has(s.id) && s.photo),
    all.filter((s) => focus.has(s.id) && !s.photo),
  ];
  return [...new Set(tiers.flat())].slice(0, n);
}
