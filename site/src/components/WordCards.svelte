<script lang="ts">
  /**
   * Flashcards for birder's English (/words/). Words come from the page's <script id="words-data"> JSON
   * (see pages/words/index.astro), read on mount, so the shuffle never meets server-rendered markup.
   * The deck is shuffled on load and on «Заново»; each card shows English or Russian first at random.
   * Tap / Enter / Space flips the card, «Дальше», a left swipe or → goes to the next one.
   * Under the card, up to three example species (thumb + English name, links to the species page) appear once the card
   * is flipped; the row grows open under the card (and collapses when it turns back), and images are only requested after the first flip of a card.
   */
  import { onMount } from 'svelte';
  interface Word { en: string; ru: string; note: string | null; ex: { id: string; en: string; ph: string | null }[] }
  /** Media base with a trailing slash (mediaUrl('') on the page); a photo URL is media + ph. */
  let { media }: { media: string } = $props();

  const base = import.meta.env.BASE_URL;
  let words = $state<Word[]>([]);
  let order = $state<number[]>([]);
  let enFirst = $state<boolean[]>([]);
  let pos = $state(0);
  let flipped = $state(false);
  let instant = $state(false);
  /** This card has been flipped at least once: its example photos may load. */
  let seen = $state(false);

  let done = $derived(words.length > 0 && pos >= order.length);
  let w = $derived(!done && order.length ? words[order[pos]] : null);
  let front = $derived(w ? (enFirst[pos] ? { text: w.en, lang: 'en' } : { text: w.ru, lang: 'ru' }) : null);
  let back = $derived(w ? (enFirst[pos] ? { text: w.ru, lang: 'ru' } : { text: w.en, lang: 'en' }) : null);

  function shuffle() {
    const a = words.map((_, i) => i);
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [a[i], a[j]] = [a[j], a[i]];
    }
    order = a;
    enFirst = a.map(() => Math.random() < 0.5);
    pos = 0;
    unflip();
  }

  /** Turn the card face up without animating, so the next word's back side never shows mid-turn. */
  function unflip() {
    instant = true;
    flipped = false;
    seen = false;
    requestAnimationFrame(() => requestAnimationFrame(() => (instant = false)));
  }

  function next() {
    if (done) return;
    pos += 1;
    unflip();
  }

  onMount(() => {
    try { words = JSON.parse(document.getElementById('words-data')?.textContent || '[]'); } catch { words = []; }
    shuffle();
  });

  // Left swipe = next; the click that follows the swipe must not flip the card.
  let x0: number | null = null;
  let y0 = 0;
  let swiped = false;
  function down(e: PointerEvent) { x0 = e.clientX; y0 = e.clientY; swiped = false; }
  function up(e: PointerEvent) {
    if (x0 === null) return;
    const dx = e.clientX - x0, dy = e.clientY - y0;
    x0 = null;
    if (dx < -50 && Math.abs(dx) > Math.abs(dy) * 1.5) { swiped = true; next(); }
  }
  function click() {
    if (swiped) { swiped = false; return; }
    flipped = !flipped;
    if (flipped) seen = true;
  }
  function key(e: KeyboardEvent) {
    if (e.key === 'ArrowRight') { e.preventDefault(); next(); }
  }
</script>

<div class="deck">
  {#if done}
    <div class="card end">
      <p class="endmsg">Все {order.length} слов пройдены.</p>
      <button class="btn primary" onclick={shuffle}>Заново</button>
    </div>
  {:else}
    <div class="card">
      <button
        class="flip"
        class:flipped
        class:instant
        disabled={!w}
        onclick={click}
        onpointerdown={down}
        onpointerup={up}
        onpointercancel={() => (x0 = null)}
        onkeydown={key}
      >
        <span class="inner">
          <span class="face" aria-hidden={flipped}>
            {#if front}
              <span class="tag">{front.lang === 'en' ? 'EN' : 'RU'}</span>
              <span class="word" lang={front.lang}>{front.text}</span>
              <span class="hint">нажмите, чтобы перевернуть</span>
            {:else}
              <span class="word muted">…</span>
            {/if}
          </span>
          <span class="face backside" aria-hidden={!flipped}>
            {#if back && w}
              <span class="tag">{back.lang === 'en' ? 'EN' : 'RU'}</span>
              <span class="word" lang={back.lang}>{back.text}</span>
              <span class="small" lang={front?.lang}>{front?.text}</span>
              {#if w.note}<span class="note">{w.note}</span>{/if}
            {/if}
          </span>
        </span>
      </button>
      {#if w && w.ex.length}
        <div class="ex" class:shown={flipped} class:instant aria-hidden={!flipped}>
          <div class="exin">
            <p class="exh muted">Например:</p>
            <ul>
              {#each w.ex as s (s.id)}
                <li>
                  <a href={`${base}species/${s.id}/`} tabindex={flipped ? 0 : -1}>
                    {#if s.ph && seen}<img src={media + s.ph} alt="" loading="lazy" decoding="async" />{:else}<span class="ph">{s.ph ? '' : '🐦'}</span>{/if}
                    <span class="nm" lang="en">{s.en}</span>
                  </a>
                </li>
              {/each}
            </ul>
          </div>
        </div>
      {/if}
    </div>
    <div class="bar">
      <span class="count">{order.length ? `${pos + 1} / ${order.length}` : ''}</span>
      <button class="btn primary" onclick={next} disabled={!w}>Дальше</button>
    </div>
  {/if}
</div>

<style>
  .deck { max-width: 480px; margin: 12px auto 8px; }
  .card { padding: 0; background: var(--card); border: 1px solid var(--line); border-radius: 16px; box-shadow: 0 2px 10px rgb(0 0 0 / .06); overflow: hidden; }
  .flip {
    display: block; width: 100%; height: 240px; padding: 0; border: 0; background: none; color: inherit; font: inherit;
    cursor: pointer; perspective: 900px; -webkit-tap-highlight-color: transparent; touch-action: pan-y; user-select: none; -webkit-user-select: none;
  }
  .flip:focus-visible { outline: 2px solid var(--accent); outline-offset: -4px; border-radius: 16px; }
  .inner {
    position: relative; display: block; width: 100%; height: 100%;
    transform-style: preserve-3d; -webkit-transform-style: preserve-3d; transition: transform .45s ease;
  }
  .flipped .inner { transform: rotateY(180deg); }
  .instant .inner { transition: none; }
  @media (prefers-reduced-motion: reduce) { .inner { transition: none; } }
  .face {
    position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px;
    padding: 36px 18px 22px; text-align: center; backface-visibility: hidden; -webkit-backface-visibility: hidden;
  }
  .backside { transform: rotateY(180deg); }
  .tag { position: absolute; top: 12px; left: 14px; font-size: .72rem; font-weight: 600; letter-spacing: .06em; color: var(--muted); background: var(--chip); border-radius: 999px; padding: 2px 8px; }
  .word { font-size: 2rem; line-height: 1.15; font-weight: 650; overflow-wrap: anywhere; }
  .backside .word { color: var(--accent); font-size: 1.75rem; }
  .hint { position: absolute; bottom: 12px; left: 0; right: 0; font-size: .78rem; color: var(--muted); }
  .small { font-size: .95rem; color: var(--muted); }
  .note { font-size: .92rem; line-height: 1.35; max-width: 34ch; }
  .ex { display: grid; grid-template-rows: 0fr; visibility: hidden; opacity: 0; transition: grid-template-rows .3s ease, opacity .25s ease, visibility .3s; }
  .ex.shown { grid-template-rows: 1fr; visibility: visible; opacity: 1; }
  .ex.instant { transition: none; }
  @media (prefers-reduced-motion: reduce) { .ex { transition: none; } }
  .exin { min-height: 0; overflow: hidden; border-top: 1px solid var(--line); }
  .exh { margin: 0 0 8px; padding: 10px 14px 0; font-size: .82rem; }
  .ex ul { list-style: none; margin: 0; padding: 0 14px 12px; display: flex; flex-wrap: wrap; gap: 12px 14px; }
  .ex li { width: 88px; min-width: 0; }
  .ex a { color: inherit; display: flex; flex-direction: column; gap: 4px; font-size: .75rem; line-height: 1.25; }
  .ex a:hover { text-decoration: none; }
  .ex a:hover .nm { text-decoration: underline; }
  .ex img, .ex .ph { width: 88px; height: 88px; border-radius: 10px; object-fit: cover; background: var(--chip); display: block; }
  .ex .ph { display: grid; place-items: center; color: var(--muted); font-size: 1.6rem; }
  .nm { font-weight: 600; overflow-wrap: break-word; hyphens: auto; }
  .bar { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 12px; }
  .count { color: var(--muted); font-variant-numeric: tabular-nums; }
  .btn { min-height: 44px; padding: 0 22px; border-radius: 999px; border: 1px solid var(--line); background: var(--card); color: var(--fg); font: inherit; font-weight: 600; cursor: pointer; }
  .btn.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
  @media (prefers-color-scheme: dark) { .btn.primary { color: #10150f; } }
  .btn:disabled { opacity: .5; cursor: default; }
  .end { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 14px; height: 240px; padding: 20px; }
  .endmsg { margin: 0; font-size: 1.1rem; }
</style>
