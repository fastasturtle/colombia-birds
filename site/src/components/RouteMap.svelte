<script lang="ts">
  import basemap from '../generated/basemap.json';
  interface Site { id: string; name: string; name_ru: string; region: string; lat: number; lon: number; elev_min: number | null; elev_max: number | null }
  interface Day { date: string; day: number | string; title_ru: string; sites: string[]; overnight_site: string | null; travel_ru?: string; region: string; elev_sleep: number | null }
  interface Region { id: string; name_ru: string; color: string }
  let { days, sites, regions }: { days: Day[]; sites: Site[]; regions: Region[] } = $props();

  const base = import.meta.env.BASE_URL;
  const color = Object.fromEntries(regions.map((r) => [r.id, r.color]));
  const siteOf = Object.fromEntries(sites.map((s) => [s.id, s]));
  const todayIdx = (() => { const t = new Date().toISOString().slice(0, 10); return days.findIndex((d) => d.date === t); })();

  // same projection as pipeline/steps/build_basemap.py
  const { lon0, lat1, kx, scale } = basemap.projection;
  const W = basemap.viewBox[2], H = basemap.viewBox[3];
  const P = (lon: number, lat: number) => ({ x: (lon - lon0) * kx * scale, y: (lat1 - lat) * scale });

  // route: overnight sites in day order, falling back to first site of the day
  const stopDays = days.map((d) => ({ d, s: siteOf[d.overnight_site ?? d.sites[0]] })).filter((x) => x.s);
  // consecutive stops joined by segments; a day whose travel mentions a flight draws a dotted "flight" segment
  const segs = stopDays.slice(1).map(({ d, s }, i) => ({ a: P(stopDays[i].s.lon, stopDays[i].s.lat), b: P(s.lon, s.lat), flight: /рейс|перел[её]т/i.test(d.travel_ru ?? '') }))
    .filter(({ a, b }) => a.x !== b.x || a.y !== b.y);
  const dayNums = new Map<string, number[]>();
  for (const { d, s } of stopDays) if (typeof d.day === 'number') dayNums.set(s.id, [...(dayNums.get(s.id) ?? []), d.day]);
  const fmtDays = (ns: number[]) => {
    const u = [...new Set(ns)].sort((a, b) => a - b), parts: string[] = [];
    for (let i = 0; i < u.length; ) { let j = i; while (j + 1 < u.length && u[j + 1] === u[j] + 1) j++; parts.push(j > i ? `${u[i]}–${u[j]}` : `${u[i]}`); i = j + 1; }
    return parts.join(', ');
  };

  const R_STOP = 11, R_SITE = 7.5;
  const markers = sites.map((s) => ({ s, ...P(s.lon, s.lat), stop: dayNums.has(s.id) }))
    .sort((a, b) => Number(a.stop) - Number(b.stop));

  // greedy label placement (sized for the phone font, the largest in viewBox units)
  type Box = { x0: number; y0: number; x1: number; y1: number };
  const boxes: Box[] = markers.map((m) => { const r = (m.stop ? R_STOP : R_SITE) + 2; return { x0: m.x - r, y0: m.y - r, x1: m.x + r, y1: m.y + r }; });
  const hit = (b: Box) => b.x0 < 2 || b.y0 < 2 || b.x1 > W - 2 || b.y1 > H - 2 || boxes.some((o) => b.x0 < o.x1 && b.x1 > o.x0 && b.y0 < o.y1 && b.y1 > o.y0);
  function place(x: number, y: number, text: string, fs: number, gap: number) {
    const w = text.length * fs * 0.58, h = fs * 0.95;
    const cands: [number, number, 'start' | 'middle' | 'end'][] = [
      [gap, 0, 'start'], [-gap, 0, 'end'], [0, -gap - h / 2, 'middle'], [0, gap + h / 2, 'middle'],
      [gap * 0.8, -gap * 0.8 - h / 3, 'start'], [-gap * 0.8, -gap * 0.8 - h / 3, 'end'],
      [gap * 0.8, gap * 0.8 + h / 3, 'start'], [-gap * 0.8, gap * 0.8 + h / 3, 'end'],
    ];
    for (const [dx, dy, anchor] of [...cands, ...cands.map(([dx, dy, a]) => [dx * 2, dy * 1.8, a] as typeof cands[0])]) {
      const tx = x + dx, ty = y + dy;
      const x0 = anchor === 'start' ? tx : anchor === 'end' ? tx - w : tx - w / 2;
      const b = { x0, y0: ty - h / 2, x1: x0 + w, y1: ty + h / 2 };
      if (!hit(b)) { boxes.push(b); return { x: tx, y: ty, anchor, text }; }
    }
    return null;
  }
  const numLabels = markers.filter((m) => m.stop).sort((a, b) => Math.min(...dayNums.get(a.s.id)!) - Math.min(...dayNums.get(b.s.id)!))
    .map((m) => place(m.x, m.y, fmtDays(dayNums.get(m.s.id)!), 28, R_STOP + 3)).filter((l) => l !== null);
  const nearSite = (x: number, y: number) => markers.some((m) => Math.hypot(m.x - x, m.y - y) < 16);
  const places = basemap.places.map((p) => {
    const dot = !nearSite(p.x, p.y);
    if (dot) boxes.push({ x0: p.x - 4, y0: p.y - 4, x1: p.x + 4, y1: p.y + 4 });
    return { ...p, dot };
  }).map((p) => ({ ...p, label: place(p.x, p.y, p.name_ru, 26, p.dot ? 8 : R_STOP + 3) }));

  let sel = $state<string | null>(null);
  const selM = $derived(markers.find((m) => m.s.id === sel));
  const toggle = (id: string) => (e: Event) => { e.stopPropagation(); sel = sel === id ? null : id; };
  const key = (id: string) => (e: KeyboardEvent) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); toggle(id)(e); } if (e.key === 'Escape') sel = null; };

  const profile = days.map((d) => ({ d, e: d.elev_sleep ?? siteOf[d.sites[0]]?.elev_min ?? 0 }));
  const maxE = Math.max(3000, ...profile.map((p) => p.e));
</script>

<div class="wrap" style={`--ar:${W / H}`}>
  <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_noninteractive_element_interactions -->
  <svg viewBox={basemap.viewBox.join(' ')} role="img" aria-label="Карта маршрута: места ночёвок и локации по регионам" onclick={() => (sel = null)}>
    <rect class="sea" width={W} height={H} />
    <path class="nb" d={basemap.neighbors} />
    <path class="co" d={basemap.colombia} />
    <path class="dept" d={basemap.departments} />
    <path class="riv" d={basemap.rivers} />
    {#if basemap.lakes}<path class="lake" d={basemap.lakes} />{/if}
    <path class="co-line" d={basemap.colombia} />
    <text class="ocean" x={basemap.oceanLabel.x} y={basemap.oceanLabel.y} transform={`rotate(-90 ${basemap.oceanLabel.x} ${basemap.oceanLabel.y})`} text-anchor="middle">{basemap.oceanLabel.name}</text>
    {#each basemap.countries as c}<text class="country" x={c.x} y={c.y} text-anchor="middle">{c.name}</text>{/each}
    {#each basemap.riverLabels as r}<text class="rivlbl" x={r.x} y={r.y} dy="-5" transform={`rotate(${r.angle} ${r.x} ${r.y})`} text-anchor="middle">{r.name}</text>{/each}
    {#each segs as g}<line class="route" class:flight={g.flight} x1={g.a.x} y1={g.a.y} x2={g.b.x} y2={g.b.y} />{/each}
    {#each places as p}
      {#if p.dot}<circle class="pdot" class:cap={p.capital} cx={p.x} cy={p.y} r={p.capital ? 5 : 3.5} />{/if}
      {#if p.label}<text class="place" class:cap={p.capital} x={p.label.x} y={p.label.y} text-anchor={p.label.anchor} dominant-baseline="central">{p.label.text}</text>{/if}
    {/each}
    {#each markers as m (m.s.id)}
      <g class="mk" class:on={sel === m.s.id} role="button" tabindex="0" aria-label={m.s.name_ru || m.s.name} onclick={toggle(m.s.id)} onkeydown={key(m.s.id)}>
        <circle class="hitc" cx={m.x} cy={m.y} r={m.stop ? 16 : 12} />
        <circle cx={m.x} cy={m.y} r={m.stop ? R_STOP : R_SITE} fill={color[m.s.region] ?? '#333'} />
      </g>
    {/each}
    {#each numLabels as l}<text class="num" x={l.x} y={l.y} text-anchor={l.anchor} dominant-baseline="central">{l.text}</text>{/each}
  </svg>
  {#if selM}
    {@const s = selM.s}
    <div class="tip" class:below={selM.y < H * 0.3} class:left={selM.x < W * 0.3} class:right={selM.x > W * 0.7}
      style={`left:${(selM.x / W) * 100}%; top:${(selM.y / H) * 100}%`}>
      <strong>{s.name}</strong>
      {#if s.name_ru && s.name_ru !== s.name}<br />{s.name_ru}{/if}
      {#if s.elev_min != null}<br /><span class="muted">{s.elev_min}{s.elev_max != null && s.elev_max !== s.elev_min ? `–${s.elev_max}` : ''} м</span>{/if}
      {#if dayNums.has(s.id)}<br /><span class="muted">ночёвки: день {fmtDays(dayNums.get(s.id)!)}</span>{/if}
      <br /><a class="more" href={`${base}sites/${s.id}/`}>подробнее →</a>
    </div>
  {/if}
</div>
<p class="muted note">Крупные точки — ночёвки, цифры — дни; пунктир — дорога, точки — перелёт. Тап по точке — название и высота. Подложка: Natural Earth.</p>

<div class="legend">
  {#each regions as r}<span class="chip"><i style={`background:${r.color}`}></i>{r.name_ru}</span>{/each}
</div>

<h2>Профиль высот по дням</h2>
<div class="profile" role="img" aria-label="Высота ночёвки по дням">
  {#each profile as p, i}
    <a href={`${base}days/${p.d.date}/`} class="bar" class:today={i === todayIdx} title={`${p.d.date}: ${p.e} м`}>
      <span class="fill" style={`height:${(p.e / maxE) * 100}%; background:${color[p.d.region] ?? '#999'}`}></span>
      <span class="lbl">{typeof p.d.day === 'number' ? p.d.day : ''}</span>
    </a>
  {/each}
</div>
<p class="muted" style="font-size:.8rem">Столбики: высота места ночёвки, от уровня моря до {maxE} м. Тап по столбику открывает день.</p>

<style>
  .wrap {
    --map-sea: #d9e9f2; --map-land: #eceae2; --map-land-co: #fbf9f1; --map-border: #5c5e55; --map-dept: #cfcab8;
    --map-river: #5d9fd3; --map-text: #55574e; --map-halo: #fbf9f1; --map-marker-stroke: #fff;
    position: relative; width: min(100%, calc(70vh * var(--ar))); margin: 0 auto;
  }
  @media (prefers-color-scheme: dark) { :global(:root:not([data-theme="light"])) .wrap {
    --map-sea: #14222b; --map-land: #1f211c; --map-land-co: #2a2c25; --map-border: #a4a69b; --map-dept: #43463b;
    --map-river: #3f82b8; --map-text: #b0b2a7; --map-halo: #2a2c25; --map-marker-stroke: #131410;
  } }
  :global(:root[data-theme="dark"]) .wrap {
    --map-sea: #14222b; --map-land: #1f211c; --map-land-co: #2a2c25; --map-border: #a4a69b; --map-dept: #43463b;
    --map-river: #3f82b8; --map-text: #b0b2a7; --map-halo: #2a2c25; --map-marker-stroke: #131410;
  }
  svg { display: block; width: 100%; height: auto; border-radius: 12px; border: 1px solid var(--line); font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
  svg path, svg line, svg circle { vector-effect: non-scaling-stroke; }
  .sea { fill: var(--map-sea); }
  .nb { fill: var(--map-land); stroke: var(--map-dept); stroke-width: 0.8; }
  .co { fill: var(--map-land-co); }
  .dept { fill: none; stroke: var(--map-dept); stroke-width: 0.8; stroke-linejoin: round; }
  .riv { fill: none; stroke: var(--map-river); stroke-width: 1.1; stroke-linejoin: round; stroke-linecap: round; }
  .lake { fill: var(--map-sea); stroke: var(--map-river); stroke-width: 0.6; }
  .co-line { fill: none; stroke: var(--map-border); stroke-width: 1.4; stroke-linejoin: round; }
  text { paint-order: stroke; stroke: var(--map-halo); stroke-width: 3px; stroke-linejoin: round; }
  .place { font-size: 26px; fill: var(--map-text); }
  .place.cap { font-weight: 600; }
  .pdot { fill: var(--map-text); stroke: var(--map-halo); stroke-width: 1; }
  .country { font-size: 24px; letter-spacing: .25em; fill: var(--map-text); opacity: .6; stroke: none; }
  .ocean { font-size: 26px; font-style: italic; letter-spacing: .15em; fill: var(--map-river); stroke: none; }
  .rivlbl { font-size: 20px; font-style: italic; fill: var(--map-river); stroke: var(--map-land-co); stroke-width: 2px; }
  .route { fill: none; stroke: var(--accent-2); stroke-width: 2.5; stroke-dasharray: 7 5; stroke-linecap: round; }
  .route.flight { stroke-width: 1.5; stroke-dasharray: 1 5; opacity: .8; }
  .mk { cursor: pointer; outline: none; }
  .mk circle:not(.hitc) { stroke: var(--map-marker-stroke); stroke-width: 1.8; }
  .mk.on circle:not(.hitc), .mk:focus-visible circle:not(.hitc) { stroke: var(--fg); stroke-width: 2.5; }
  .hitc { fill: transparent; stroke: none; }
  .num { font-size: 28px; font-weight: 700; fill: var(--fg); stroke: var(--map-halo); }
  @media (min-width: 700px) {
    .place { font-size: 20px; } .num { font-size: 22px; } .country { font-size: 20px; } .ocean { font-size: 22px; } .rivlbl { font-size: 16px; }
  }
  .tip {
    position: absolute; transform: translate(-50%, calc(-100% - 14px)); background: var(--card); color: var(--fg);
    border: 1px solid var(--line); border-radius: 8px; padding: 6px 10px; font-size: .85rem; line-height: 1.35;
    box-shadow: 0 2px 10px rgba(0,0,0,.18); width: max-content; max-width: 220px; z-index: 2;
  }
  .tip.below { transform: translate(-50%, 14px); }
  .tip.left { transform: translate(-12px, calc(-100% - 14px)); }
  .tip.left.below { transform: translate(-12px, 14px); }
  .tip.right { transform: translate(calc(-100% + 12px), calc(-100% - 14px)); }
  .tip.right.below { transform: translate(calc(-100% + 12px), 14px); }
  .tip .more { display: inline-block; padding: 8px 0 2px; }
  .note { font-size: .8rem; margin: 6px 0 0; }
  .legend { margin: 10px 0; }
  .legend i { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; }
  .profile { display: flex; align-items: flex-end; gap: 2px; height: 120px; border-bottom: 1px solid var(--line); }
  .bar { flex: 1; display: flex; flex-direction: column; justify-content: flex-end; height: 100%; position: relative; min-width: 0; }
  .fill { display: block; border-radius: 3px 3px 0 0; opacity: .85; }
  .bar.today .fill { outline: 2px solid var(--fg); }
  .lbl { font-size: .6rem; color: var(--muted); text-align: center; position: absolute; bottom: -16px; left: 0; right: 0; }
</style>
