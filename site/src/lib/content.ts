/**
 * Hand-written content from ../content (see content/README.md, content/families/README.md);
 * family portraits in content/families/, group portraits in content/groups/ (same schema).
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
