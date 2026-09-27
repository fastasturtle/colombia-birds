<script lang="ts">
  /** All-species list: search + elevation + the site-wide filter (state = best across route sites, see lib/data routeState). */
  import ListFilter from './ListFilter.svelte';
  import EndemicMark from './EndemicMark.svelte';
  import { filter, passes, tierOf } from '../lib/filter';
  type State = 'sure' | 'maybe' | 'unlikely';
  interface Item { id: string; sci: string; en: string; ru: string | null; family: string; endemic: boolean; near: boolean; elev: [number|null, number|null] | null; photo: string | null; state: State; int: boolean }
  let { items, families, base, mediaBase }: { items: Item[]; families: Record<string, string>; base: string; mediaBase: string } = $props();
  const STATE_RU: Record<State, string> = { sure: 'точно', maybe: 'возможно', unlikely: 'вряд ли' };
  const LIMIT = 300;
  let q = $state('');
  let elev = $state<number | null>(null);
  const norm = (s: string) => s.toLowerCase().replace(/ё/g, 'е');
  let matched = $derived.by(() => {
    const t = norm(q.trim());
    return items.filter((s) => {
      if (elev != null && s.elev && ((s.elev[0] ?? 0) > elev || (s.elev[1] ?? 9000) < elev)) return false;
      if (!t) return true;
      return norm(s.en).includes(t) || norm(s.sci).includes(t) || (s.ru ? norm(s.ru).includes(t) : false) || norm(families[s.family] ?? '').includes(t);
    });
  });
  let shown = $derived(matched.filter((s) => passes($filter, s.state, tierOf(s.int, s.near, s.endemic))));
  const plural = (n: number, a: string, b: string, c: string) => {
    const m10 = n % 10, m100 = n % 100;
    return m10 === 1 && m100 !== 11 ? a : m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14) ? b : c;
  };
</script>

<div class="filters">
  <input type="search" placeholder="Название: по-русски, по-английски или латынь" bind:value={q} />
  <label>высота, м <input type="number" min="0" max="5000" step="100" placeholder="напр. 2000" bind:value={elev} /></label>
</div>
<ListFilter />
<p class="muted">{shown.length} {plural(shown.length, 'вид', 'вида', 'видов')} из {items.length}{shown.length > LIMIT ? `, показаны первые ${LIMIT}` : ''} · «точно» и «возможно» — хотя бы на одной локации маршрута</p>
{#each shown.slice(0, LIMIT) as s (s.id)}
  <a class="row" href={`${base}species/${s.id}/`}>
    {#if s.photo}<img class="thumb" src={`${mediaBase}/${s.photo}`} alt="" loading="lazy" />{:else}<div class="thumb empty">🐦</div>{/if}
    <div class="txt">
      <div>{#if s.int && !s.endemic && !s.near}<b class="star" title="интересная">★</b>{/if}<strong>{s.ru ?? s.en}</strong></div>
      <div class="muted">{#if s.ru && s.en !== s.ru}{`${s.en} · `}{/if}<span class="sci">{s.sci}</span> · <span>{families[s.family]}</span></div>
      <div class="meta"><span class={`stw ${s.state}`}>{STATE_RU[s.state]}</span>{#if s.endemic}<EndemicMark kind="end" />{:else if s.near}<EndemicMark kind="near" />{/if}</div>
    </div>
  </a>
{/each}
{#if shown.length === 0}<p class="muted">Под этот фильтр видов нет.</p>{/if}

<style>
  .filters { display: flex; flex-wrap: wrap; gap: 10px 16px; align-items: center; margin: 8px 0; }
  input[type="search"] { flex: 1 1 260px; padding: 10px 12px; border: 1px solid var(--line); border-radius: 10px; background: var(--card); color: var(--fg); font-size: 1rem; }
  input[type="number"] { width: 110px; padding: 6px 8px; border: 1px solid var(--line); border-radius: 8px; background: var(--card); color: var(--fg); }
  .row { color: inherit; }
  .row:hover { text-decoration: none; background: var(--chip); }
  .txt { min-width: 0; }
  .meta { display: flex; gap: 8px; align-items: center; }
  .stw { font-size: .75rem; font-weight: 600; }
  .stw.sure { color: var(--accent); }
  .stw.maybe { color: var(--muted); font-weight: 500; }
  .stw.unlikely { color: var(--muted); opacity: .6; font-weight: 400; }
  .star { color: var(--accent-2); margin-right: 4px; }
</style>
