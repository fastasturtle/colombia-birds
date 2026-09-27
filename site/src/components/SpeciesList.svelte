<script lang="ts">
  interface Item { id: string; sci: string; en: string; ru: string | null; family: string; status: string[]; endemic: boolean; elev: [number|null, number|null] | null; photo: string | null }
  let { items, families, base, mediaBase }: { items: Item[]; families: Record<string, string>; base: string; mediaBase: string } = $props();
  let q = $state('');
  let onlyEndemic = $state(false);
  let elev = $state<number | null>(null);
  const norm = (s: string) => s.toLowerCase().replace(/ё/g, 'е');
  let filtered = $derived.by(() => {
    const t = norm(q.trim());
    return items.filter((s) => {
      if (onlyEndemic && !s.endemic) return false;
      if (elev != null && s.elev && ((s.elev[0] ?? 0) > elev || (s.elev[1] ?? 9000) < elev)) return false;
      if (!t) return true;
      return norm(s.en).includes(t) || norm(s.sci).includes(t) || (s.ru ? norm(s.ru).includes(t) : false) || norm(families[s.family] ?? '').includes(t);
    }).slice(0, 300);
  });
</script>

<div class="filters">
  <input type="search" placeholder="Название: по-русски, по-английски или латынь" bind:value={q} />
  <label><input type="checkbox" bind:checked={onlyEndemic} /> только эндемики</label>
  <label>высота, м <input type="number" min="0" max="5000" step="100" placeholder="напр. 2000" bind:value={elev} /></label>
</div>
<p class="muted">{filtered.length === 300 ? 'показаны первые 300' : filtered.length} из {items.length}</p>
{#each filtered as s (s.id)}
  <a class="row" href={`${base}species/${s.id}/`}>
    {#if s.photo}<img class="thumb" src={`${mediaBase}/${s.photo}`} alt="" loading="lazy" />{:else}<div class="thumb empty">🐦</div>{/if}
    <div>
      <div><strong>{s.en}</strong>{#if s.endemic}<span class="chip endemic" style="margin-left:8px">эндемик</span>{/if}</div>
      <div class="muted"><span class="sci">{s.sci}</span>{#if s.ru} · {s.ru}{/if} · <span>{families[s.family]}</span></div>
    </div>
  </a>
{/each}

<style>
  .filters { display: flex; flex-wrap: wrap; gap: 10px 16px; align-items: center; margin: 8px 0; }
  input[type="search"] { flex: 1 1 260px; padding: 10px 12px; border: 1px solid var(--line); border-radius: 10px; background: var(--card); color: var(--fg); font-size: 1rem; }
  input[type="number"] { width: 110px; padding: 6px 8px; border: 1px solid var(--line); border-radius: 8px; background: var(--card); color: var(--fg); }
  .row { color: inherit; }
  .row:hover { text-decoration: none; background: var(--chip); }
</style>
