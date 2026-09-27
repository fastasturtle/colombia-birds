/**
 * Read-only access to the generated database in ../data (built by pipeline/).
 * Everything here runs at build time only.
 */
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';

const DATA = join(process.cwd(), '..', 'data');

function readJson<T>(rel: string, fallback?: T): T {
  const p = join(DATA, rel);
  if (!existsSync(p)) {
    if (fallback !== undefined) return fallback;
    throw new Error(`missing data file: ${p}`);
  }
  return JSON.parse(readFileSync(p, 'utf8')) as T;
}

export interface IndexEntry {
  id: string; sci: string; en: string; ru: string | null; family: string; order: string;
  taxon_order: number; status: string[]; endemic: boolean; iucn: string;
  elev: [number | null, number | null] | null; habitat: string | null; photo: string | null;
}
export interface Family {
  code: string; sci: string; order: string; names: Record<string, string>; species_count: number; slug: string;
}
export interface Photo {
  key_base: string; sizes: { thumb: string; medium: string; large: string };
  width?: number; height?: number; author: string; license: string; license_url?: string; source_url: string; credit?: string;
}
export interface Species {
  id: string; sci_name: string; sci_name_aco: string; authorship: string; taxonomy_note: string | null;
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
}
export interface Day {
  date: string; day: number | string; title_ru: string; sites: string[]; overnight: string; overnight_site: string | null;
  guide: string | null; region: string; travel_ru: string; elev_sleep: number | null;
}
export interface Region { id: string; name_ru: string; name_en: string; description_ru: string; color: string; order: number }

let _index: IndexEntry[] | null = null;
export function speciesIndex(): IndexEntry[] {
  return (_index ??= readJson<IndexEntry[]>('species_index.json'));
}
export function families(): Family[] {
  return readJson<Family[]>('families.json');
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
export function sites(): Site[] {
  const resolved = readJson<Site[] | null>('sites_resolved.json', null);
  return resolved ?? readJson<Site[]>('sites.json', []);
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
