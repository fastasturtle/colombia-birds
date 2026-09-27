<script lang="ts">
  /**
   * One per page: opens the Lightbox for any `[data-lb]` element (thumbnail buttons rendered by
   * SpeciesRow.astro). `data-lb` holds JSON `{ alt, photo }` with photo = species photos[0].
   */
  import Lightbox, { type LbPhoto } from './Lightbox.svelte';
  let { mediaBase }: { mediaBase: string } = $props();
  let photos = $state<LbPhoto[]>([]);
  let alt = $state('');
  let open = $state<number | null>(null);
  $effect(() => {
    const onClick = (e: MouseEvent) => {
      const el = (e.target as Element | null)?.closest?.('[data-lb]') as HTMLElement | null;
      if (!el) return;
      e.preventDefault();
      try {
        const d = JSON.parse(el.dataset.lb!);
        photos = [d.photo]; alt = d.alt; open = 0;
      } catch { /* malformed: ignore */ }
    };
    document.addEventListener('click', onClick);
    return () => document.removeEventListener('click', onClick);
  });
</script>

<Lightbox {photos} {alt} {mediaBase} bind:open />
