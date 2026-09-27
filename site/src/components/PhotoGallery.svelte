<script lang="ts">
  import Lightbox, { type LbPhoto } from './Lightbox.svelte';
  let { photos, alt, mediaBase }: { photos: LbPhoto[]; alt: string; mediaBase: string } = $props();
  let open = $state<number | null>(null);
  const url = (k: string) => `${mediaBase}/${k}`;
</script>

<div class="photos" class:single={photos.length === 1}>
  {#each photos as p, i}
    <figure>
      <button type="button" class="pic" onclick={() => (open = i)} aria-label={`Открыть фото ${i + 1} на весь экран`}>
        <img src={url(p.sizes.medium)} alt={alt} loading={i === 0 ? 'eager' : 'lazy'} />
        {#if p.kind === 'illustration'}<span class="tag">иллюстрация</span>{/if}
      </button>
      <figcaption class="muted">© {p.author} · {p.license} · <a href={p.source_url} target="_blank" rel="noopener">источник</a></figcaption>
    </figure>
  {/each}
</div>

<Lightbox {photos} {alt} {mediaBase} bind:open />

<style>
  .photos { display: grid; gap: 10px; grid-template-columns: repeat(2, 1fr); }
  .photos.single { grid-template-columns: 1fr; max-width: 640px; }
  @media (max-width: 480px) { .photos { grid-template-columns: 1fr; } }
  figure { margin: 0; min-width: 0; }
  .pic { display: block; width: 100%; padding: 0; border: 0; background: var(--chip); border-radius: 12px; overflow: hidden; cursor: zoom-in; position: relative; aspect-ratio: 4 / 3; }
  .pic img { width: 100%; height: 100%; object-fit: cover; display: block; }
  .tag { position: absolute; left: 8px; bottom: 8px; background: rgba(0,0,0,.55); color: #fff; font-size: .7rem; padding: 2px 8px; border-radius: 999px; }
  figcaption { font-size: .75rem; margin-top: 4px; }
</style>
