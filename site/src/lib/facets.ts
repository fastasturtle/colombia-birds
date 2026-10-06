/**
 * Facet chips with counts, shared by the identifier (trait groups) and FilterBar (families, sites).
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

/** Russian plural (1 вид, 2 вида, 5 видов). */
export const plural = (n: number, a: string, b: string, c: string) => {
  const m10 = n % 10, m100 = n % 100;
  return m10 === 1 && m100 !== 11 ? a : m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14) ? b : c;
};
