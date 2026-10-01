<script lang="ts">
  /**
   * «Офлайн» page island: downloads the offline pack into the service worker's caches and shows its status.
   * The download runs HERE (not in the worker); the worker (site/integrations/sw.template.js) only serves.
   * Caches: `cb-pages-v1` (pages, _astro, manifest) and `cb-media-v1` (R2 photos). The cb- prefix keeps them
   * apart from other projects on the shared fastasturtle.github.io origin (Cache Storage is per origin).
   *
   * Pack = dist/offline-manifest.json (built by site/integrations/offline.mjs):
   *   { version, hash, built, photoEstimate, files: [[url, ver, size?], ...] }
   * Progress is always recomputed from caches.keys() matched against the manifest, so closing the tab
   * mid-download costs nothing: the next run fetches only what is missing.
   *
   * Versions of dist files (pages, _astro, manifest, favicon): the cache alone cannot tell an old page from a
   * new one under the same URL, so localStorage `cb.offline.versions` keeps {url: ver} for every dist file
   * the downloader stored (written every PROGRESS_EVERY files and at the end). A cached dist file counts as
   * present only if its stored ver equals the manifest's ver; pages the worker cached during normal browsing
   * have no entry and are simply re-fetched once. (Map of ~2 200 entries ≈ 150 KB, well under the 5 MB limit.)
   * Photos have ver "key" (immutable on R2), so presence in the cache is enough.
   *
   * Other localStorage keys: `cb.offline.pack` = {version, hash, built} of the manifest the pack was last fully
   * downloaded against; `cb.offline.checked` = time of the last version check.
   *
   * Test hook: `window.__OFFLINE_MANIFEST_URL__` (e.g. set by Playwright's addInitScript) or `?manifest=<path>`
   * (same origin only) replaces the real manifest with a small one; version.json is then ignored.
   *
   * While a download runs, <html data-cb-downloading="1"> is set and `cb:download-start` / `cb:download-end`
   * are dispatched on document: the shell (Base.astro) then keeps the «Есть новая версия» toast (whose
   * «Обновить» reloads the page and would abort the run) hidden until the run ends.
   */
  import { onMount } from 'svelte';

  const BASE = import.meta.env.BASE_URL.replace(/\/?$/, '/'); // "/colombia-birds/"
  const PAGES = 'cb-pages-v1';
  const MEDIA = 'cb-media-v1';
  const CONCURRENCY = 6;
  const PROGRESS_EVERY = 20;
  const RETRIES = 3;
  const RETRY_MS = 1000;
  const K_PACK = 'cb.offline.pack';
  const K_CHECKED = 'cb.offline.checked';
  const K_VERSIONS = 'cb.offline.versions';

  type Entry = [string, string, number?];
  interface Manifest { version: string; hash: string; built: string; photoEstimate: Record<string, number>; files: Entry[] }
  interface Pack { version: string; hash: string; built: string }

  const abs = (u: string) => new URL(u, location.origin).href;
  const isPhoto = (e: Entry) => e[1] === 'key';

  // ---------- state ----------
  let supported = $state(true);
  let online = $state(true);
  let ios = $state(false);
  let standalone = $state(false);
  let notDownloadedHere = $state(false); // the worker served this page for a URL that is not cached
  let testMode = $state(false);

  let manifest = $state<Manifest | null>(null);
  let pack = $state<Pack | null>(null);
  let checked = $state<number | null>(null);
  let checking = $state(false);
  let loadError = $state('');

  let totalFiles = $state(0);
  let totalBytes = $state(0);
  let haveFiles = $state(0);
  let haveBytes = $state(0);
  let estimated = $state(false);

  let running = $state(false);
  let stopped = $state(false);
  let quota = $state(false);
  let errors = $state(0);
  let lastError = $state<{ url: string; status: string } | null>(null);
  let finished = $state(false);
  let deleted = $state(false);
  let confirmDelete = $state(false);

  // diagnostics
  let usage = $state<string>('—');
  let persisted = $state<string>('—');
  let swState = $state<string>('—');
  let swVersion = $state<string>('—');
  let ua = $state('');

  let ac: AbortController | null = null;
  let missing: Entry[] = [];

  // ---------- helpers ----------
  function readLS<T>(k: string): T | null {
    try { return JSON.parse(localStorage.getItem(k) ?? 'null') as T | null; } catch { return null; }
  }
  function writeLS(k: string, v: unknown) {
    try { localStorage.setItem(k, JSON.stringify(v)); } catch { /* private mode / full */ }
  }
  function removeLS(k: string) { try { localStorage.removeItem(k); } catch { /* ignore */ } }

  /** Tell the shell a download is (not) running; see the header comment. */
  function markDownloading(on: boolean) {
    const root = document.documentElement;
    if (on === (root.dataset.cbDownloading === '1')) return;
    if (on) root.dataset.cbDownloading = '1'; else delete root.dataset.cbDownloading;
    document.dispatchEvent(new CustomEvent(on ? 'cb:download-start' : 'cb:download-end'));
  }

  const nf = new Intl.NumberFormat('ru-RU');
  const mb = (b: number) => { const m = b / 1048576; return m >= 10 || m === 0 ? nf.format(Math.round(m)) : m.toFixed(1).replace('.', ','); };
  const date = (iso: string) => new Date(iso).toLocaleDateString('ru-RU');
  function time(ts: number) {
    const d = new Date(ts);
    const t = d.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
    return d.toDateString() === new Date().toDateString() ? t : `${d.toLocaleDateString('ru-RU')} ${t}`;
  }

  function sizeOf(e: Entry, m: Manifest): { size: number; est: boolean } {
    if (typeof e[2] === 'number') return { size: e[2], est: false };
    const suffix = Object.keys(m.photoEstimate ?? {}).find((s) => e[0].endsWith(s));
    return { size: suffix ? m.photoEstimate[suffix] : 0, est: true };
  }

  function manifestUrl(): string {
    const w = (window as unknown as { __OFFLINE_MANIFEST_URL__?: string }).__OFFLINE_MANIFEST_URL__;
    const q = new URLSearchParams(location.search).get('manifest');
    const t = w || q;
    if (t && new URL(t, location.origin).origin === location.origin) { testMode = true; return abs(t); }
    return abs(`${BASE}offline-manifest.json`);
  }

  async function cachedKeys(): Promise<Set<string>> {
    const set = new Set<string>();
    for (const name of [PAGES, MEDIA]) {
      const c = await caches.open(name);
      for (const r of await c.keys()) set.add(r.url);
    }
    return set;
  }

  /** Recount what is cached for the current manifest; fills `missing`. */
  async function recompute() {
    const m = manifest;
    if (!m) return;
    const keys = await cachedKeys();
    const versions = readLS<Record<string, string>>(K_VERSIONS) ?? {};
    let hf = 0, hb = 0, tb = 0, est = false;
    const miss: Entry[] = [];
    for (const e of m.files) {
      const s = sizeOf(e, m);
      tb += s.size; est ||= s.est;
      const have = keys.has(abs(e[0])) && (isPhoto(e) || versions[e[0]] === e[1]);
      if (have) { hf++; hb += s.size; } else miss.push(e);
    }
    missing = miss;
    totalFiles = m.files.length; totalBytes = tb; estimated = est;
    haveFiles = hf; haveBytes = hb;
  }

  // ---------- check for updates ----------
  async function check() {
    if (checking || running) return;
    checking = true; loadError = '';
    try {
      const url = manifestUrl();
      const pagesCache = await caches.open(PAGES);
      let m: Manifest | null = null;
      const copy = await pagesCache.match(url);
      if (copy) { try { m = await copy.json(); } catch { m = null; } }
      if (navigator.onLine !== false) {
        try {
          let wantNew = !m || testMode;
          if (!testMode) {
            const r = await fetch(`${BASE}version.json`, { cache: 'no-cache' });
            if (r.ok) {
              const v = await r.json() as Pack;
              if (!m || m.hash !== v.hash) wantNew = true;
            }
          }
          if (wantNew) {
            const r = await fetch(url, { cache: 'no-cache' });
            if (!r.ok) throw new Error(`HTTP ${r.status}`);
            m = await r.json();
          }
          checked = Date.now(); writeLS(K_CHECKED, checked);
        } catch (e) {
          if (!m) loadError = `Не удалось загрузить список файлов (${(e as Error).message}).`;
        }
      }
      manifest = m;
      await recompute();
      // everything already in place for a newer manifest (e.g. only deletions): just finalize
      if (m && missing.length === 0 && (!pack || pack.hash !== m.hash)) await finalize(m);
    } finally { checking = false; }
  }

  // ---------- download ----------
  async function download() {
    const m = manifest;
    if (!m || running || navigator.onLine === false) return;
    running = true; stopped = false; quota = false; finished = false; deleted = false; confirmDelete = false;
    errors = 0; lastError = null;
    markDownloading(true);
    try {
      try { persisted = (await navigator.storage?.persist?.()) ? 'да' : 'нет'; } catch { /* unsupported */ }
      ac = new AbortController();
      // keep the screen on while downloading (a locked phone suspends the page); best effort
      let wake: { release(): Promise<void> } | null = null;
      try { wake = await (navigator as unknown as { wakeLock?: { request(t: string): Promise<{ release(): Promise<void> }> } }).wakeLock?.request('screen') ?? null; } catch { /* unsupported or denied */ }
      const signal = ac.signal;
      const pagesCache = await caches.open(PAGES);
      const mediaCache = await caches.open(MEDIA);
      // keep a copy of the manifest so the status can be computed offline
      await pagesCache.put(manifestUrl(), new Response(JSON.stringify(m), { headers: { 'Content-Type': 'application/json' } }));
      await recompute();
      const todo = missing.slice();
      const versions = readLS<Record<string, string>>(K_VERSIONS) ?? {};
      let next = 0, done = 0, hf = haveFiles, hb = haveBytes, errs = 0;
      let last: { url: string; status: string } | null = null;
      const flushProgress = () => {
        haveFiles = hf; haveBytes = hb; errors = errs; lastError = last;
        writeLS(K_VERSIONS, versions);
      };

      /**
       * fetch with RETRIES extra attempts on a network error (flaky mobile links, dropped connections)
       * or a transient HTTP status (5xx, 429, 408: the Pages CDN sometimes answers one request with 503).
       * Backoff RETRY_MS * (attempt + 1), or a numeric Retry-After (seconds, capped at 10 s). After the
       * last attempt a network error is thrown and a bad status is returned as is (the caller records it).
       */
      async function get(url: string, init: RequestInit): Promise<Response> {
        for (let attempt = 0; ; attempt++) {
          let wait = RETRY_MS * (attempt + 1);
          try {
            const res = await fetch(url, init);
            if (!(res.status >= 500 || res.status === 429 || res.status === 408)) return res;
            if (signal.aborted || attempt >= RETRIES || navigator.onLine === false) return res;
            const h = res.headers.get('Retry-After')?.trim(); // null on a cross-origin photo (not CORS-exposed)
            const ra = h ? Number(h) : NaN;
            if (Number.isFinite(ra) && ra >= 0) wait = Math.min(ra, 10) * 1000;
            res.body?.cancel().catch(() => {});
          } catch (err) {
            if (signal.aborted || attempt >= RETRIES || navigator.onLine === false) throw err;
          }
          await new Promise((r) => setTimeout(r, wait));
        }
      }

      async function one(e: Entry) {
        const url = abs(e[0]);
        const photo = isPhoto(e);
        try {
          // cache: 'no-cache' also tells the service worker to stay out of the way (see sw.template.js)
          const res = await get(url, photo
            ? { mode: 'cors', credentials: 'omit', cache: 'no-cache', signal }
            : { cache: 'no-cache', signal });
          if (res.status === 200) {
            await (photo ? mediaCache : pagesCache).put(url, res);
            if (!photo) versions[e[0]] = e[1];
            hf++; hb += sizeOf(e, m!).size;
          } else {
            errs++; last = { url, status: String(res.status) };
          }
        } catch (err) {
          const name = (err as Error).name || 'Error';
          if (signal.aborted && name !== 'QuotaExceededError') return; // stopped (or stopping after a quota error)
          if (name === 'QuotaExceededError') { quota = true; ac?.abort(); }
          errs++; last = { url, status: name === 'TypeError' ? 'нет связи' : name };
        }
        if (++done % PROGRESS_EVERY === 0) flushProgress();
      }

      async function worker() {
        while (!signal.aborted && next < todo.length) await one(todo[next++]);
      }
      await Promise.all(Array.from({ length: CONCURRENCY }, worker));
      flushProgress();
      wake?.release().catch(() => {});
      running = false;
      stopped = signal.aborted && !quota;
      ac = null;
      await recompute();
      if (!signal.aborted && errs === 0 && missing.length === 0) { await finalize(m); finished = true; }
      refreshDiagnostics();
    } finally {
      running = false;
      markDownloading(false);
    }
    // the site may have been redeployed during the run: check() then loads the newer manifest,
    // which shows «Доступно обновление…» / «Обновить пакет»
    if (online) await check();
  }

  /** After a complete run: drop cache entries the manifest no longer lists, remember the pack version. */
  async function finalize(m: Manifest) {
    const want = new Set(m.files.map((e) => abs(e[0])));
    want.add(manifestUrl()); want.add(abs(`${BASE}offline/`));
    for (const name of [PAGES, MEDIA]) {
      const c = await caches.open(name);
      for (const r of await c.keys()) {
        // large photos are never in the pack; the ones viewed online stay as a bonus
        if (!want.has(r.url) && !r.url.endsWith('-large.jpg')) await c.delete(r);
      }
    }
    const versions = readLS<Record<string, string>>(K_VERSIONS) ?? {};
    const pruned: Record<string, string> = {};
    for (const e of m.files) if (!isPhoto(e) && versions[e[0]]) pruned[e[0]] = versions[e[0]];
    writeLS(K_VERSIONS, pruned);
    pack = { version: m.version, hash: m.hash, built: m.built };
    writeLS(K_PACK, pack);
    await recompute();
  }

  function stop() { ac?.abort(); }

  async function remove() {
    if (!confirmDelete) { confirmDelete = true; return; }
    confirmDelete = false;
    stop();
    await caches.delete(PAGES);
    await caches.delete(MEDIA);
    try {
      for (const r of await navigator.serviceWorker.getRegistrations()) await r.unregister();
    } catch { /* ignore */ }
    for (const k of [K_PACK, K_CHECKED, K_VERSIONS]) removeLS(k);
    pack = null; checked = null; errors = 0; lastError = null; finished = false;
    deleted = true;
    await recompute();
    refreshDiagnostics();
  }

  // ---------- diagnostics ----------
  async function refreshDiagnostics() {
    try {
      const e = await navigator.storage?.estimate?.();
      if (e) usage = `${mb(e.usage ?? 0)} из ${mb(e.quota ?? 0)}\u00a0МБ`;
    } catch { /* unsupported */ }
    try {
      const p = await navigator.storage?.persisted?.();
      if (p !== undefined && persisted === '—') persisted = p ? 'да' : 'нет';
      else if (p) persisted = 'да';
    } catch { /* unsupported */ }
    if (!('serviceWorker' in navigator)) { swState = 'не поддерживается'; return; }
    const reg = await navigator.serviceWorker.getRegistration(BASE).catch(() => undefined);
    const ctl = navigator.serviceWorker.controller;
    swState = !reg ? 'не зарегистрирован'
      : `зарегистрирован (${reg.active?.state ?? reg.installing?.state ?? reg.waiting?.state ?? '?'}), ${ctl ? 'управляет страницей' : 'страницей не управляет'}`;
    const target = ctl ?? reg?.active;
    if (target) {
      swVersion = await new Promise<string>((resolve) => {
        const ch = new MessageChannel();
        const t = setTimeout(() => resolve('нет ответа'), 1500);
        ch.port1.onmessage = (ev) => { clearTimeout(t); resolve(String(ev.data?.version ?? '?')); };
        target.postMessage({ type: 'GET_VERSION' }, [ch.port2]);
      });
    }
  }

  onMount(() => {
    ua = navigator.userAgent;
    ios = /iPad|iPhone|iPod/.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
    standalone = matchMedia('(display-mode: standalone)').matches || (navigator as unknown as { standalone?: boolean }).standalone === true;
    notDownloadedHere = location.pathname.replace(/\/?$/, '/') !== `${BASE}offline/`;
    supported = 'caches' in window && 'serviceWorker' in navigator;
    online = navigator.onLine !== false;
    pack = readLS<Pack>(K_PACK);
    checked = readLS<number>(K_CHECKED);
    const on = () => { online = true; }, off = () => { online = false; };
    addEventListener('online', on); addEventListener('offline', off);
    if (supported) {
      check().then(refreshDiagnostics);
      navigator.serviceWorker.addEventListener('controllerchange', refreshDiagnostics);
    }
    return () => { removeEventListener('online', on); removeEventListener('offline', off); ac?.abort(); markDownloading(false); };
  });

  const pct = $derived(totalFiles ? Math.floor((haveFiles / totalFiles) * 1000) / 10 : 0);
  const missingFiles = $derived(totalFiles - haveFiles);
  const missingBytes = $derived(totalBytes - haveBytes);
  const approx = $derived(estimated ? '≈ ' : '');
  const complete = $derived(!!manifest && missingFiles === 0);
  const isUpdate = $derived(!!pack && !complete);
</script>

{#if notDownloadedHere}
  <p class="card warn" role="alert"><b>Нет сети, и эта страница не скачана.</b> Её можно будет открыть, когда появится связь. Ниже — всё, что скачано для офлайна.</p>
{/if}

{#if ios}
  <p class="note">На iPhone откройте сайт с иконки на экране «Домой» и скачивайте пакет там: у приложения с экрана «Домой» своё хранилище, отдельное от Safari.</p>
  {#if !standalone}<p class="note hint">Сейчас сайт открыт в браузере, а не с экрана «Домой».</p>{/if}
{/if}

{#if !supported}
  <p class="card warn">Этот браузер не умеет хранить сайт офлайн (нет Service Worker / Cache Storage).</p>
{:else}
  <section class="card status" aria-live="polite">
    <p class="big">
      {#if deleted}Пакет удалён
      {:else if pack}Пакет: данные от {date(pack.built)}
      {:else if haveFiles > 0 && !complete}Пакет скачан не полностью
      {:else}Пакет не скачан{/if}
    </p>
    {#if manifest}
      <div class="bar" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow={pct}><span style:width="{pct}%"></span></div>
      <p class="nums">Скачано {nf.format(haveFiles)} из {nf.format(totalFiles)} файлов, {approx}{mb(haveBytes)} из {mb(totalBytes)}&nbsp;МБ</p>
    {/if}
    <p class="muted small">
      {#if checked}Проверено: {time(checked)}{:else}Ещё не проверялось{/if}
      {#if !online} · нет сети{/if}
      {#if testMode} · тестовый манифест{/if}
    </p>
    {#if loadError}<p class="err">{loadError}</p>{/if}
  </section>

  <section class="actions">
    {#if running}
      <p class="small">Скачиваем… осталось {nf.format(missingFiles)} файлов, {approx}{mb(missingBytes)}&nbsp;МБ. Не уходите с этой страницы, пока идёт скачивание; если прервётся, скачанное сохранится и можно будет докачать.</p>
    {:else if manifest && !complete}
      {#if isUpdate}
        <p class="small"><b>Доступно обновление:</b> {nf.format(missingFiles)} файлов, {approx}{mb(missingBytes)}&nbsp;МБ</p>
      {/if}
    {:else if complete && (finished || pack)}
      <p class="small ok">Пакет скачан: сайт работает без сети.</p>
    {/if}
    {#if stopped}<p class="small muted">Остановлено. Скачанное сохранилось, можно продолжить.</p>{/if}
    {#if quota}<p class="small err">Не хватает места на устройстве: освободите память и нажмите «Скачать» ещё раз.</p>{/if}
    {#if !running && errors > 0 && !quota}<p class="small err">Не скачалось {nf.format(errors)} файлов, нажмите «Скачать» ещё раз.</p>{/if}

    <div class="buttons">
      {#if running}
        <button type="button" class="btn" onclick={stop}>Остановить</button>
      {:else if manifest && !complete}
        <button type="button" class="btn primary" onclick={download} disabled={!online}>
          {isUpdate ? 'Обновить пакет' : haveFiles > 0 ? `Докачать пакет (${approx}${mb(missingBytes)}\u00a0МБ)` : `Скачать пакет (${approx}${mb(missingBytes)}\u00a0МБ)`}
        </button>
      {/if}
      <button type="button" class="btn" onclick={check} disabled={checking || running || !online}>{checking ? 'Проверяем…' : 'Проверить'}</button>
      {#if (haveFiles > 0 || pack) && !running}
        <button type="button" class="btn danger" onclick={remove}>{confirmDelete ? 'Точно удалить?' : 'Удалить пакет'}</button>
      {/if}
    </div>
    {#if confirmDelete}<p class="small muted">Нажмите ещё раз, чтобы удалить всё скачанное. <button type="button" class="link" onclick={() => (confirmDelete = false)}>Отмена</button></p>{/if}
    {#if !online && manifest && !complete}<p class="small muted">Скачать можно, когда появится связь.</p>{/if}
  </section>

  <details class="diag" open>
    <summary>Диагностика</summary>
    <dl>
      <dt>Хранилище</dt><dd>{usage}</dd>
      <dt>Постоянное хранение</dt><dd>{persisted}</dd>
      <dt>Service worker</dt><dd>{swState}</dd>
      <dt>Версия worker</dt><dd>{swVersion}</dd>
      <dt>Версия пакета</dt><dd>{pack ? `${pack.version} (${pack.hash})` : '—'}</dd>
      <dt>Версия на сайте</dt><dd>{manifest ? `${manifest.version} (${manifest.hash}), сборка ${new Date(manifest.built).toLocaleString('ru-RU')}` : '—'}</dd>
      <dt>С экрана «Домой»</dt><dd>{standalone ? 'да' : 'нет'}</dd>
      <dt>Ошибки скачивания</dt><dd>{errors}{#if lastError}: <span class="url">{lastError.url}</span> ({lastError.status}){/if}</dd>
      <dt>Браузер</dt><dd class="url">{ua}</dd>
    </dl>
  </details>
{/if}

<style>
  .note { font-size: .9rem; margin: 0 0 8px; }
  .hint { color: var(--accent-2); }
  .warn { border-color: var(--accent-2); margin: 0 0 12px; }
  .status { margin: 12px 0; }
  .big { font-size: 1.1rem; font-weight: 600; margin: 0 0 8px; }
  .bar { height: 8px; border-radius: 999px; background: var(--chip); overflow: hidden; }
  .bar span { display: block; height: 100%; background: var(--accent); transition: width .3s; }
  .nums { margin: 8px 0 4px; font-size: .95rem; }
  .small { font-size: .9rem; margin: 6px 0; }
  .ok { color: var(--accent); }
  .err { color: var(--accent-2); }
  .buttons { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0 6px; }
  .btn { min-height: 44px; padding: 0 18px; border: 1px solid var(--line); border-radius: 999px; background: var(--card); color: var(--fg); font: inherit; font-size: .95rem; cursor: pointer; }
  .btn.primary { background: var(--accent); border-color: var(--accent); color: var(--bg); font-weight: 600; }
  .btn.danger { color: var(--accent-2); }
  .btn:disabled { opacity: .5; cursor: default; }
  .link { background: none; border: 0; padding: 0; font: inherit; color: var(--accent); cursor: pointer; text-decoration: underline; }
  .diag { margin-top: 20px; font-size: .85rem; }
  .diag summary { cursor: pointer; min-height: 40px; display: flex; align-items: center; color: var(--muted); }
  dl { display: grid; grid-template-columns: max-content 1fr; gap: 4px 12px; margin: 4px 0 0; }
  dt { color: var(--muted); }
  dd { margin: 0; min-width: 0; }
  .url { overflow-wrap: anywhere; }
  @media (max-width: 480px) {
    dl { grid-template-columns: 1fr; gap: 0; }
    dd { margin-bottom: 6px; }
  }
</style>
