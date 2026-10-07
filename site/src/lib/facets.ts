import { makePass, type Filter, type Narrow, type Row } from './filter';

/**
 * Facet chips with counts for FilterBar (families, sites, trait groups).
 * Selection: OR within a group, AND across groups. Counts, over the items that pass `base` (everything outside the facets):
 * - group without a selection: items that would match if the chip were selected (AND with all other groups);
 * - group with a selection: delta, items that selecting the chip too would ADD (match all other groups, have the chip,
 *   match none of the group's selected chips). Selected chips need no count.
 * One pass: an item matching all groups adds to the chips it has in unselected groups; an item failing exactly one
 * (selected) group adds only to that group's chips it has. Failing two or more adds nothing. So a pass costs one
 * predicate call and a few small integer loops per row, however many chips there are.
 */
export type Sel = Record<string, string[]>;
type Groups = { key: string; values: string[] }[];

/** Facet group key of a trait group in listCounts. */
export const trGroup = (g: string) => `t.${g}`;

/**
 * The rows' facet values as small integers, built once per list (FilterBar, when the rows arrive): for every group, per
 * row the indices (into the group's `values`) of the values it has. Groups: `fam`, `site`, `t.<trait group>` (trGroup).
 */
export interface FacetIndex { groups: Groups; pos: Map<string, number>[]; vals: Int32Array[][] }
export function facetIndex(rows: Row[], groups: Groups): FacetIndex {
  const pos = groups.map((g) => new Map(g.values.map((v, i) => [v, i])));
  const gi = new Map(groups.map((g, i) => [g.key, i]));
  const tmp: number[][][] = groups.map(() => rows.map(() => []));
  rows.forEach((r, ri) => {
    const add = (g: string, v: string) => {
      const k = gi.get(g);
      if (k == null) return;
      const j = pos[k].get(v);
      if (j != null && !tmp[k][ri].includes(j)) tmp[k][ri].push(j);
    };
    add('fam', r.fam);
    for (const x of r.sites) add('site', x);
    for (const x of r.tr ?? []) { const i = x.indexOf(':'); add(trGroup(x.slice(0, i)), x.slice(i + 1)); }
  });
  return { groups, pos, vals: tmp.map((g) => g.map((a) => Int32Array.from(a))) };
}

/** Does row i have one of the values marked in m? */
const hasAny = (a: Int32Array, m: Uint8Array) => {
  for (let j = 0; j < a.length; j++) if (m[a[j]]) return true;
  return false;
};
const addAll = (a: Int32Array, c: Int32Array) => { for (let j = 0; j < a.length; j++) c[a[j]]++; };

export function facetCounts(n: number, ix: FacetIndex, sel: Sel, base: (i: number) => boolean): Record<string, Record<string, number>> {
  const { groups, pos, vals } = ix, G = groups.length;
  const cnt = groups.map((g) => new Int32Array(g.values.length));
  /** per group: mask of the selected values, null when the group has no selection */
  const mask = groups.map((g, k) => {
    const vs = sel[g.key];
    if (!vs?.length) return null;
    const m = new Uint8Array(g.values.length);
    for (const v of vs) { const j = pos[k].get(v); if (j != null) m[j] = 1; }
    return m;
  });
  const selG: number[] = [];
  for (let k = 0; k < G; k++) if (mask[k]) selG.push(k);
  for (let i = 0; i < n; i++) {
    if (!base(i)) continue;
    let fail = -1, out = false;
    for (const k of selG) {
      if (hasAny(vals[k][i], mask[k]!)) continue;
      if (fail >= 0) { out = true; break; }
      fail = k;
    }
    if (out) continue;
    if (fail >= 0) { addAll(vals[fail][i], cnt[fail]); continue; }
    // a row in the results adds nothing to the deltas of a group with a selection
    for (let k = 0; k < G; k++) if (!mask[k]) addAll(vals[k][i], cnt[k]);
  }
  const res: Record<string, Record<string, number>> = {};
  groups.forEach((g, k) => {
    const o: Record<string, number> = (res[g.key] = {});
    g.values.forEach((v, j) => (o[v] = cnt[k][j]));
  });
  return res;
}

/**
 * Counts of the facet chips of a list (FilterBar) over its facetIndex. Everything else in `u` (search, elevation) and
 * the filter `f` (lv, tag) is the base every count respects: makePass + facetCounts.
 */
export function listCounts(rows: Row[], ix: FacetIndex, f: Filter, u: Narrow) {
  const sel: Sel = { fam: u.fam, site: u.site };
  for (const [g, vs] of Object.entries(u.tr)) sel[trGroup(g)] = vs;
  const base = makePass(f, { ...u, fam: [], site: [], tr: {} });
  return facetCounts(rows.length, ix, sel, (i) => base(rows[i]));
}
/** Rows that pass everything but the trait selection and have no traits: hidden only because they have no card. */
export function noTraitsHidden(rows: Row[], f: Filter, u: Narrow): number {
  if (!Object.values(u.tr).some((v) => v.length)) return 0;
  const pass = makePass(f, { ...u, tr: {} });
  return rows.filter((r) => !r.tr && pass(r)).length;
}

/** Russian plural (1 вид, 2 вида, 5 видов). */
export const plural = (n: number, a: string, b: string, c: string) => {
  const m10 = n % 10, m100 = n % 100;
  return m10 === 1 && m100 !== 11 ? a : m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14) ? b : c;
};
