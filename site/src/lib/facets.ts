import { rowPasses, type Filter, type Narrow, type Row } from './filter';

/**
 * Facet chips with counts for FilterBar (families, sites, trait groups).
 * Selection: OR within a group, AND across groups. Counts, over the items that pass `base` (everything outside the facets):
 * - group without a selection: items that would match if the chip were selected (AND with all other groups);
 * - group with a selection: delta, items that selecting the chip too would ADD (match all other groups, have the chip,
 *   match none of the group's selected chips). Selected chips need no count.
 * One pass: an item matching all groups adds to the chips it has in unselected groups; an item failing exactly one
 * (selected) group adds only to that group's chips it has. Failing two or more adds nothing.
 */
export type Sel = Record<string, string[]>;

/** Does item i match every group with a selection? */
export function matchesSel(i: number, sel: Sel, has: (i: number, g: string) => ReadonlySet<string> | undefined): boolean {
  for (const [g, vs] of Object.entries(sel)) {
    if (!vs.length) continue;
    const t = has(i, g);
    if (!t || !vs.some((v) => t.has(v))) return false;
  }
  return true;
}

export function facetCounts(
  n: number,
  groups: { key: string; values: string[] }[],
  sel: Sel,
  base: (i: number) => boolean,
  has: (i: number, g: string) => ReadonlySet<string> | undefined,
): Record<string, Record<string, number>> {
  const out: Record<string, Record<string, number>> = {};
  for (const g of groups) out[g.key] = Object.fromEntries(g.values.map((v) => [v, 0]));
  const selG = groups.filter((g) => sel[g.key]?.length).map((g) => ({ key: g.key, vs: sel[g.key] }));
  for (let i = 0; i < n; i++) {
    if (!base(i)) continue;
    let fail: string | null = null, out2 = false;
    for (const { key, vs } of selG) {
      const t = has(i, key);
      if (!t || !vs.some((v) => t.has(v))) { if (fail) { out2 = true; break; } fail = key; }
    }
    if (out2) continue;
    for (const g of groups) {
      if (fail && g.key !== fail) continue;
      if (!fail && sel[g.key]?.length) continue; // already in the results: adds nothing to this group's deltas
      const c = out[g.key], t = has(i, g.key);
      if (t) for (const v of t) if (v in c) c[v]++;
    }
  }
  return out;
}

/** Facet values of one list row: `fam`, `site` and `t.<trait group>` (see listCounts). Build once per row. */
export type RowFacets = Record<string, ReadonlySet<string>>;
export function rowFacets(r: Row): RowFacets {
  const o: Record<string, Set<string>> = { fam: new Set([r.fam]), site: new Set(r.sites) };
  for (const x of r.tr ?? []) {
    const i = x.indexOf(':'), k = `t.${x.slice(0, i)}`;
    (o[k] ??= new Set()).add(x.slice(i + 1));
  }
  return o;
}
/** Facet group key of a trait group in listCounts. */
export const trGroup = (g: string) => `t.${g}`;
/**
 * Counts of the facet chips of a list (FilterBar): `groups` are any of
 * `fam`, `site`, `t.<trait group>` (trGroup) with their values. Everything else in `u` (search, elevation) and the
 * site-wide filter `f` is the base every count respects: rowPasses + facetCounts.
 */
export function listCounts(rows: Row[], sets: RowFacets[], f: Filter, u: Narrow, groups: { key: string; values: string[] }[]) {
  const sel: Sel = { fam: u.fam, site: u.site };
  for (const [g, vs] of Object.entries(u.tr)) sel[trGroup(g)] = vs;
  const rest: Narrow = { ...u, fam: [], site: [], tr: {} };
  return facetCounts(rows.length, groups, sel, (i) => rowPasses(rows[i], f, rest), (i, g) => sets[i][g]);
}
/** Rows that pass everything but the trait selection and have no traits: hidden only because they have no card. */
export const noTraitsHidden = (rows: Row[], f: Filter, u: Narrow) =>
  Object.values(u.tr).some((v) => v.length) ? rows.filter((r) => !r.tr && rowPasses(r, f, { ...u, tr: {} })).length : 0;

/** Russian plural (1 вид, 2 вида, 5 видов). */
export const plural = (n: number, a: string, b: string, c: string) => {
  const m10 = n % 10, m100 = n % 100;
  return m10 === 1 && m100 !== 11 ? a : m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14) ? b : c;
};
