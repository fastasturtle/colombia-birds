/**
 * Hand-written content from ../content (see content/README.md, content/families/README.md).
 * Build time only. Bodies are plain paragraphs separated by blank lines; the English
 * version follows a "## English" heading.
 */
import { readFileSync, readdirSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import matter from 'gray-matter';

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

let _families: Map<string, FamilyContent> | null = null;
function loadFamilies(): Map<string, FamilyContent> {
  const dir = join(CONTENT, 'families');
  const out = new Map<string, FamilyContent>();
  if (!existsSync(dir)) return out;
  for (const f of readdirSync(dir)) {
    if (!f.endsWith('.md') || f === 'README.md') continue;
    const { data, content } = matter(readFileSync(join(dir, f), 'utf8'));
    if (!data.family) throw new Error(`content/families/${f}: missing "family" in frontmatter`);
    const [ru, en = ''] = content.split(/^## English\s*$/m);
    const e = data.en ?? null;
    out.set(data.family, {
      family: data.family,
      recognize: data.recognize ?? [],
      confusable: data.confusable ?? [],
      route_note: data.route_note ?? null,
      fact: data.fact ?? null,
      body: paragraphs(ru),
      en: e || en.trim()
        ? { recognize: e?.recognize ?? [], route_note: e?.route_note ?? null, fact: e?.fact ?? null, body: paragraphs(en) }
        : null,
    });
  }
  return out;
}

/** Portrait for a family code (e.g. "gralla2"), or null if none written yet. */
export function familyContent(code: string): FamilyContent | null {
  return (_families ??= loadFamilies()).get(code) ?? null;
}
