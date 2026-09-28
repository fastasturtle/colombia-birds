<script lang="ts">
  // «Сообщить об ошибке»: inline form that POSTs to the report Worker (worker/), which files a GitHub issue.
  // Offline (navigator.onLine === false, or fetch throws) the payload goes into localStorage `cb.report.queue`
  // (at most QUEUE_MAX items) and is sent on the next page load / `online` event. HTTP errors are not queued.
  import { onMount } from 'svelte';
  let { endpoint, species }: { endpoint: string; species?: string } = $props();
  const MAX = 1000;
  const QUEUE_KEY = 'cb.report.queue';
  const QUEUE_MAX = 20;
  let open = $state(false);
  let message = $state('');
  let honeypot = $state('');
  let status = $state<'idle' | 'sending' | 'done' | 'queued' | 'error' | 'limit'>('idle');
  let area = $state<HTMLTextAreaElement>();

  async function toggle() {
    open = !open;
    if (open && status !== 'done' && status !== 'queued') { await Promise.resolve(); area?.focus(); }
  }

  type Payload = Record<string, unknown>;
  const post = (body: Payload) => fetch(endpoint, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  function readQueue(): Payload[] {
    try { const q = JSON.parse(localStorage.getItem(QUEUE_KEY) ?? '[]'); return Array.isArray(q) ? q : []; } catch { return []; }
  }
  function writeQueue(q: Payload[]) {
    try { if (q.length) localStorage.setItem(QUEUE_KEY, JSON.stringify(q.slice(-QUEUE_MAX))); else localStorage.removeItem(QUEUE_KEY); } catch { /* storage off */ }
  }
  function enqueue(body: Payload) {
    const q = readQueue(); q.push(body); writeQueue(q);
    status = 'queued'; message = '';
  }

  /** Send queued reports one by one; stop at the first failure and keep the rest. */
  let flushing = false;
  async function flush() {
    if (flushing || navigator.onLine === false) return;
    flushing = true;
    try {
      let q = readQueue();
      while (q.length) {
        try {
          const res = await post(q[0]);
          if (!res.ok) break;
        } catch { break; }
        q = readQueue().slice(1); // re-read: another tab may have added items meanwhile
        writeQueue(q);
      }
    } finally { flushing = false; }
  }

  onMount(() => {
    flush();
    addEventListener('online', flush);
    return () => removeEventListener('online', flush);
  });

  async function send(e: SubmitEvent) {
    e.preventDefault();
    if (!message.trim() || status === 'sending') return;
    const body: Payload = {
      page: location.href,
      species,
      heading: document.querySelector('main h1')?.textContent?.trim() ?? document.title,
      message: message.trim(),
      honeypot,
      ua: navigator.userAgent,
    };
    if (navigator.onLine === false) { enqueue(body); return; }
    status = 'sending';
    try {
      const res = await post(body);
      if (res.ok) { status = 'done'; message = ''; }
      else status = res.status === 429 ? 'limit' : 'error';
    } catch {
      enqueue(body); // network error: keep it for later
    }
  }
</script>

<div class="report">
  <button type="button" class="toggle" aria-expanded={open} onclick={toggle}>Сообщить об ошибке</button>
  {#if open}
    {#if status === 'done'}
      <p class="msg ok" role="status">Спасибо, записали!</p>
    {:else if status === 'queued'}
      <p class="msg ok" role="status">Нет сети: сообщение сохранено, отправим при появлении связи.</p>
    {:else}
      <form onsubmit={send}>
        <label for="report-text">Что не так на этой странице? Имя, фото, описание, карта…</label>
        <textarea id="report-text" bind:this={area} bind:value={message} maxlength={MAX} rows="4" required></textarea>
        <input class="hp" type="text" name="website" tabindex="-1" autocomplete="off" aria-hidden="true" bind:value={honeypot} />
        <div class="actions">
          <span class="muted count">{message.length}/{MAX}</span>
          <button type="submit" class="send" disabled={!message.trim() || status === 'sending'}>
            {status === 'sending' ? 'Отправляем…' : 'Отправить'}
          </button>
        </div>
        {#if status === 'error'}<p class="msg err" role="alert">Не получилось отправить. Проверьте связь и попробуйте ещё раз.</p>{/if}
        {#if status === 'limit'}<p class="msg err" role="alert">Слишком много сообщений подряд. Попробуйте через 10 минут.</p>{/if}
      </form>
    {/if}
  {/if}
</div>

<style>
  .report { margin-bottom: 16px; }
  .toggle { min-height: 40px; padding: 0 14px; border: 1px solid var(--line); border-radius: 999px; background: var(--card); color: var(--muted); font: inherit; font-size: .9rem; cursor: pointer; }
  .toggle[aria-expanded="true"] { color: var(--fg); }
  form { margin-top: 10px; display: flex; flex-direction: column; gap: 8px; max-width: 560px; }
  label { font-size: .9rem; color: var(--fg); }
  textarea { width: 100%; font: inherit; font-size: 16px; padding: 8px 10px; border: 1px solid var(--line); border-radius: 8px; background: var(--card); color: var(--fg); resize: vertical; }
  .hp { position: absolute; left: -10000px; width: 1px; height: 1px; opacity: 0; }
  .actions { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
  .count { font-size: .8rem; }
  .send { min-height: 40px; padding: 0 18px; border: 0; border-radius: 999px; background: var(--accent); color: var(--bg); font: inherit; font-weight: 600; cursor: pointer; }
  .send:disabled { opacity: .5; cursor: default; }
  .msg { margin: 8px 0 0; font-size: .9rem; }
  .ok { color: var(--accent); }
  .err { color: var(--accent-2); }
</style>
