<script lang="ts">
  import { onMount } from 'svelte';
  interface Site { id: string; name: string; name_ru: string; region: string; lat: number; lon: number; elev_min: number | null; elev_max: number | null }
  interface Day { date: string; day: number | string; title_ru: string; sites: string[]; overnight_site: string | null; region: string; elev_sleep: number | null }
  interface Region { id: string; name_ru: string; color: string }
  let { days, sites, regions }: { days: Day[]; sites: Site[]; regions: Region[] } = $props();
  let el: HTMLDivElement;
  let offline = $state(false);
  const color = Object.fromEntries(regions.map((r) => [r.id, r.color]));
  const siteOf = Object.fromEntries(sites.map((s) => [s.id, s]));
  // route line: overnight sites in day order, falling back to first site of the day
  const stops = days.map((d) => siteOf[d.overnight_site ?? d.sites[0]]).filter(Boolean);
  const line = stops.map((s) => [s.lon, s.lat]);
  const todayIdx = (() => { const t = new Date().toISOString().slice(0, 10); return days.findIndex((d) => d.date === t); })();

  onMount(async () => {
    if (!navigator.onLine) { offline = true; return; }
    try {
      const maplibregl = (await import('maplibre-gl')).default;
      await import('maplibre-gl/dist/maplibre-gl.css');
      const map = new maplibregl.Map({
        container: el,
        style: 'https://tiles.openfreemap.org/styles/liberty',
        center: [-76.2, 2.4], zoom: 6.2, attributionControl: { compact: true },
      });
      map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right');
      map.on('load', () => {
        map.addSource('route', { type: 'geojson', data: { type: 'Feature', properties: {}, geometry: { type: 'LineString', coordinates: line } } });
        map.addLayer({ id: 'route', type: 'line', source: 'route', paint: { 'line-color': '#b45309', 'line-width': 3, 'line-dasharray': [2, 1.5] } });
        for (const s of sites) {
          const dot = document.createElement('div');
          dot.className = 'dot';
          dot.style.background = color[s.region] ?? '#333';
          const popup = new maplibregl.Popup({ offset: 12, closeButton: false }).setHTML(
            `<strong>${s.name}</strong>${s.name_ru && s.name_ru !== s.name ? `<br>${s.name_ru}` : ''}${s.elev_min != null ? `<br>${s.elev_min}–${s.elev_max} м` : ''}<br><a href="#${s.id}">подробнее</a>`);
          new maplibregl.Marker({ element: dot }).setLngLat([s.lon, s.lat]).setPopup(popup).addTo(map);
        }
        const b = new maplibregl.LngLatBounds();
        for (const s of sites) b.extend([s.lon, s.lat]);
        map.fitBounds(b, { padding: 40, maxZoom: 8 });
      });
      map.on('error', () => { offline = true; });
    } catch { offline = true; }
  });
  // simple SVG fallback (offline): normalized coordinates
  const lons = sites.map((s) => s.lon), lats = sites.map((s) => s.lat);
  const minLon = Math.min(...lons) - 0.3, maxLon = Math.max(...lons) + 0.3, minLat = Math.min(...lats) - 0.3, maxLat = Math.max(...lats) + 0.3;
  const X = (lon: number) => ((lon - minLon) / (maxLon - minLon)) * 100;
  const Y = (lat: number) => (1 - (lat - minLat) / (maxLat - minLat)) * 100;
  const profile = days.map((d) => ({ d, e: d.elev_sleep ?? siteOf[d.sites[0]]?.elev_min ?? 0 }));
  const maxE = Math.max(3000, ...profile.map((p) => p.e));
</script>

<div class="map" bind:this={el} class:hidden={offline}></div>
{#if offline}
  <svg class="fallback" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Схема маршрута">
    <polyline points={line.map(([lon, lat]) => `${X(lon)},${Y(lat)}`).join(' ')} fill="none" stroke="#b45309" stroke-width="0.6" stroke-dasharray="1.5 1" />
    {#each sites as s}
      <circle cx={X(s.lon)} cy={Y(s.lat)} r="1.6" fill={color[s.region]} stroke="#fff" stroke-width="0.3" />
    {/each}
  </svg>
  <p class="muted" style="font-size:.85rem">Офлайн: показана схема без карты-подложки.</p>
{/if}

<div class="legend">
  {#each regions as r}<span class="chip"><i style={`background:${r.color}`}></i>{r.name_ru}</span>{/each}
</div>

<h2>Профиль высот по дням</h2>
<div class="profile" role="img" aria-label="Высота ночёвки по дням">
  {#each profile as p, i}
    <a href={`#d${p.d.date}`} class="bar" class:today={i === todayIdx} title={`${p.d.date}: ${p.e} м`}>
      <span class="fill" style={`height:${(p.e / maxE) * 100}%; background:${color[p.d.region] ?? '#999'}`}></span>
      <span class="lbl">{typeof p.d.day === 'number' ? p.d.day : ''}</span>
    </a>
  {/each}
</div>
<p class="muted" style="font-size:.8rem">Столбики: высота места ночёвки, от уровня моря до {maxE} м. Тап по столбику ведёт к дню.</p>

<style>
  .map { width: 100%; height: min(70vh, 520px); border-radius: 12px; overflow: hidden; border: 1px solid var(--line); }
  .hidden { display: none; }
  .fallback { width: 100%; height: min(60vh, 420px); background: var(--card); border-radius: 12px; border: 1px solid var(--line); }
  :global(.dot) { width: 16px; height: 16px; border-radius: 50%; border: 2px solid #fff; box-shadow: 0 0 0 1px rgba(0,0,0,.3); cursor: pointer; }
  :global(.maplibregl-popup-content) { color: #1d1d1b; font: 14px/1.4 system-ui, sans-serif; border-radius: 8px; }
  .legend { margin: 10px 0; }
  .legend i { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; }
  .profile { display: flex; align-items: flex-end; gap: 2px; height: 120px; border-bottom: 1px solid var(--line); }
  .bar { flex: 1; display: flex; flex-direction: column; justify-content: flex-end; height: 100%; position: relative; min-width: 0; }
  .fill { display: block; border-radius: 3px 3px 0 0; opacity: .85; }
  .bar.today .fill { outline: 2px solid var(--fg); }
  .lbl { font-size: .6rem; color: var(--muted); text-align: center; position: absolute; bottom: -16px; left: 0; right: 0; }
</style>
