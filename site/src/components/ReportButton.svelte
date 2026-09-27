<script lang="ts">
  // «Сообщить об ошибке»: inline form that POSTs to the report Worker (worker/), which files a GitHub issue.
  let { endpoint, species }: { endpoint: string; species?: string } = $props();
  const MAX = 1000;
  let open = $state(false);
  let message = $state('');
  let honeypot = $state('');
  let status = $state<'idle' | 'sending' | 'done' | 'error' | 'limit'>('idle');
  let area = $state<HTMLTextAreaElement>();

  async function toggle() {
    open = !open;
    if (open && status !== 'done') { await Promise.resolve(); area?.focus(); }
  }

  async function send(e: SubmitEvent) {
    e.preventDefault();
    if (!message.trim() || status === 'sending') return;
    status = 'sending';
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          page: location.href,
          species,
          heading: document.querySelector('main h1')?.textContent?.trim() ?? document.title,
          message: message.trim(),
          honeypot,
          ua: navigator.userAgent,
        }),
      });
      if (res.ok) { status = 'done'; message = ''; }
      else status = res.status === 429 ? 'limit' : 'error';
    } catch {
      status = 'error';
    }
  }
</script>

<div class="report">
  <button type="button" class="toggle" aria-expanded={open} onclick={toggle}>Сообщить об ошибке</button>
  {#if open}
    {#if status === 'done'}
      <p class="msg ok" role="status">Спасибо, записали!</p>
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
