<script lang="ts">
  /**
   * Flashcards for birder's English (/words/). Words come from the page's <script id="words-data"> JSON
   * (see pages/words/index.astro), read on mount, so the shuffle never meets server-rendered markup.
   * The deck is shuffled on load and on «Заново»; each card shows English or Russian first at random.
   * Tap / Enter / Space flips the card, «Дальше», a left swipe or → goes to the next one.
   */
  import { onMount } from 'svelte';
  interface Word { en: string; ru: string; note: string | null; ex: { id: string; en: string }[] }

  const base = import.meta.env.BASE_URL;
  let words = $state<Word[]>([]);
  let order = $state<number[]>([]);
  let enFirst = $state<boolean[]>([]);
  let pos = $state(0);
  let flipped = $state(false);
  let instant = $state(false);

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
        <p class="ex" class:shown={flipped} aria-hidden={!flipped}>
          <span class="muted">Например:</span>
          {#each w.ex as s, i (s.id)}<a href={`${base}species/${s.id}/`} lang="en" tabindex={flipped ? 0 : -1}>{s.en}</a>{i < w.ex.length - 1 ? ', ' : ''}{/each}
        </p>
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
  .card { background: var(--card); border: 1px solid var(--line); border-radius: 16px; box-shadow: 0 2px 10px rgb(0 0 0 / .06); overflow: hidden; }
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
  .ex { margin: 0; padding: 10px 14px 12px; border-top: 1px solid var(--line); font-size: .88rem; line-height: 1.45; visibility: hidden; opacity: 0; transition: opacity .2s; }
  .ex.shown { visibility: visible; opacity: 1; }
  .ex a { white-space: nowrap; }
  .bar { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-top: 12px; }
  .count { color: var(--muted); font-variant-numeric: tabular-nums; }
  .btn { min-height: 44px; padding: 0 22px; border-radius: 999px; border: 1px solid var(--line); background: var(--card); color: var(--fg); font: inherit; font-weight: 600; cursor: pointer; }
  .btn.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
  @media (prefers-color-scheme: dark) { .btn.primary { color: #10150f; } }
  .btn:disabled { opacity: .5; cursor: default; }
  .end { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 14px; height: 240px; padding: 20px; }
  .endmsg { margin: 0; font-size: 1.1rem; }
</style>
