/**
 * Birder's English vocabulary (content/vocabulary.yaml) for the /words/ page. Build time only. Entries are validated:
 * a missing en/ru, a duplicate word or an example id missing from data/species_index.json fails `npm run build`.
 * freq and examples are recomputed by scripts/vocab_freq.py --fill.
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import matter from 'gray-matter';
import { speciesIndex } from './data';

const FILE = join(process.cwd(), '..', 'content', 'vocabulary.yaml');

export interface VocabWord {
  en: string;
  ru: string;
  note: string | null;
  freq: number;
  /** example species: id + English name */
  examples: { id: string; en: string }[];
}

let _words: VocabWord[] | null = null;
/** Words in file order. */
export function vocabulary(): VocabWord[] {
  if (_words) return _words;
  // gray-matter's YAML engine, as in lib/traits.ts: wrap the file as front matter.
  const raw = matter(`---\n${readFileSync(FILE, 'utf8')}\n---\n`).data as unknown;
  const bad = (m: string) => new Error(`content/vocabulary.yaml: ${m}`);
  if (!Array.isArray(raw)) throw bad('must be a list of entries');
  const idx = new Map(speciesIndex().map((s) => [s.id, s]));
  const seen = new Set<string>();
  _words = raw.map((e: any, i: number) => {
    if (!e?.en || !e?.ru) throw bad(`entry ${i + 1} needs en and ru`);
    const en = String(e.en);
    if (seen.has(en)) throw bad(`duplicate word "${en}"`);
    seen.add(en);
    const examples = (Array.isArray(e.examples) ? e.examples : []).map((id: unknown) => {
      const s = idx.get(String(id));
      if (!s) throw bad(`"${en}": unknown species id "${id}"`);
      return { id: s.id, en: s.en };
    });
    return { en, ru: String(e.ru), note: e.note ? String(e.note) : null, freq: Number(e.freq) || 0, examples };
  });
  return _words;
}
