<script module lang="ts">
  export interface LbPhoto { sizes: { thumb: string; medium: string; large: string }; author: string; license: string; license_url?: string; source_url: string; kind?: string }
</script>

<script lang="ts">
  /** Full-screen photo viewer: tap/Esc/× closes, swipe or arrows step through several photos. */
  let { photos, alt, mediaBase, open = $bindable(null) }: { photos: LbPhoto[]; alt: string; mediaBase: string; open?: number | null } = $props();
  let startX = 0;
  const url = (k: string) => `${mediaBase}/${k}`;
  $effect(() => {
    document.body.style.overflow = open != null ? 'hidden' : '';
  });
  function close() { open = null; }
  function step(d: number) { if (open == null) return; open = (open + d + photos.length) % photos.length; }
  function onKey(e: KeyboardEvent) {
    if (open == null) return;
    if (e.key === 'Escape') close();
    else if (e.key === 'ArrowRight') step(1);
    else if (e.key === 'ArrowLeft') step(-1);
  }
  function onTouchStart(e: TouchEvent) { startX = e.touches[0].clientX; }
  function onTouchEnd(e: TouchEvent) {
    const dx = e.changedTouches[0].clientX - startX;
    if (Math.abs(dx) > 50) step(dx < 0 ? 1 : -1);
  }
</script>

<svelte:window onkeydown={onKey} />

{#if open != null && photos[open]}
  {@const p = photos[open]}
  <!-- svelte-ignore a11y_click_events_have_key_events, a11y_no_static_element_interactions, a11y_no_noninteractive_element_interactions -->
  <div class="lb" role="dialog" aria-modal="true" aria-label={alt} tabindex="-1" onclick={close} ontouchstart={onTouchStart} ontouchend={onTouchEnd}>
    <img src={url(p.sizes.large)} alt={alt} onclick={(e) => { e.stopPropagation(); if (photos.length > 1) step(1); else close(); }} />
    <div class="cap" onclick={(e) => e.stopPropagation()}>
      <span>{alt}</span>
      <span class="muted">© {p.author} · <a href={p.license_url ?? '#'} target="_blank" rel="noopener">{p.license}</a> · <a href={p.source_url} target="_blank" rel="noopener">источник</a>{#if photos.length > 1} · {open + 1}/{photos.length}{/if}</span>
    </div>
    <button type="button" class="x" onclick={(e) => { e.stopPropagation(); close(); }} aria-label="Закрыть">×</button>
    {#if photos.length > 1}
      <button type="button" class="nav prev" onclick={(e) => { e.stopPropagation(); step(-1); }} aria-label="Предыдущее">‹</button>
      <button type="button" class="nav next" onclick={(e) => { e.stopPropagation(); step(1); }} aria-label="Следующее">›</button>
    {/if}
  </div>
{/if}

<style>
  .lb { position: fixed; inset: 0; background: rgba(0,0,0,.94); z-index: 100; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: env(safe-area-inset-top) 0 env(safe-area-inset-bottom); }
  .lb img { max-width: 100vw; max-height: calc(100vh - 72px); object-fit: contain; }
  .cap { position: absolute; left: 0; right: 0; bottom: 0; padding: 10px 16px; color: #eee; background: linear-gradient(transparent, rgba(0,0,0,.7)); font-size: .85rem; display: flex; flex-direction: column; gap: 2px; }
  .cap .muted { color: #bbb; }
  .cap a { color: #9ad4a3; }
  .x, .nav { position: absolute; background: rgba(0,0,0,.4); color: #fff; border: 0; font-size: 2rem; line-height: 1; width: 44px; height: 44px; border-radius: 50%; cursor: pointer; }
  .x { top: 12px; right: 12px; }
  .nav { top: 50%; transform: translateY(-50%); }
  .prev { left: 8px; } .next { right: 8px; }
  @media (max-width: 480px) { .nav { display: none; } }
</style>
