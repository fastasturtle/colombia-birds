/**
 * colombia-birds-reports: receives «Сообщить об ошибке» submissions from the site
 * and files them as GitHub issues labelled `report` (+ `species`).
 *
 * POST /report  {page, species?, heading?, message, honeypot, ua}
 * GET  /        health check
 */

export interface Env {
  RATE: KVNamespace;
  GITHUB_REPORTS_TOKEN: string;
}

const REPO = 'fastasturtle/colombia-birds';
const ALLOWED_ORIGINS = new Set(['https://fastasturtle.github.io', 'http://localhost:4321']);
const MAX_MESSAGE = 1000;
const RATE_WINDOW_S = 600; // 10 minutes
const RATE_MAX = 5;

function cors(origin: string | null): Record<string, string> {
  const h: Record<string, string> = { Vary: 'Origin' };
  if (origin && ALLOWED_ORIGINS.has(origin)) {
    h['Access-Control-Allow-Origin'] = origin;
    h['Access-Control-Allow-Methods'] = 'POST, OPTIONS';
    h['Access-Control-Allow-Headers'] = 'Content-Type';
    h['Access-Control-Max-Age'] = '86400';
  }
  return h;
}

function json(body: unknown, status: number, origin: string | null): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json; charset=utf-8', ...cors(origin) },
  });
}

const str = (v: unknown, max: number): string => (typeof v === 'string' ? v.trim().slice(0, max) : '');

/** Wrap user text in a code fence longer than any backtick run inside it (no mentions, no markup). */
function fence(text: string): string {
  const longest = Math.max(0, ...(text.match(/`+/g) ?? []).map((s) => s.length));
  const f = '`'.repeat(Math.max(3, longest + 1));
  return `${f}text\n${text}\n${f}`;
}

async function rateLimited(env: Env, ip: string): Promise<boolean> {
  const window = Math.floor(Date.now() / 1000 / RATE_WINDOW_S);
  const key = `rl:${ip}:${window}`;
  const n = Number((await env.RATE.get(key)) ?? '0');
  if (n >= RATE_MAX) return true;
  await env.RATE.put(key, String(n + 1), { expirationTtl: RATE_WINDOW_S });
  return false;
}

async function handleReport(req: Request, env: Env, origin: string | null): Promise<Response> {
  if (!origin || !ALLOWED_ORIGINS.has(origin)) return json({ ok: false, error: 'forbidden' }, 403, origin);

  let data: Record<string, unknown>;
  try {
    const parsed = await req.json();
    if (!parsed || typeof parsed !== 'object') throw new Error();
    data = parsed as Record<string, unknown>;
  } catch {
    return json({ ok: false, error: 'bad request' }, 400, origin);
  }

  if (str(data.honeypot, 200)) return json({ ok: false, error: 'bad request' }, 400, origin);
  const message = typeof data.message === 'string' ? data.message.trim() : '';
  if (!message || message.length > MAX_MESSAGE) {
    return json({ ok: false, error: 'message must be 1-1000 characters' }, 400, origin);
  }
  const page = str(data.page, 500);
  const speciesRaw = str(data.species, 100);
  const species = /^[a-z0-9-]+$/.test(speciesRaw) ? speciesRaw : '';
  const heading = str(data.heading, 120).replace(/[\r\n]+/g, ' ');
  const ua = str(data.ua, 300);

  const ip = req.headers.get('CF-Connecting-IP') ?? 'unknown';
  if (await rateLimited(env, ip)) return json({ ok: false, error: 'too many reports, try later' }, 429, origin);

  let path = page;
  try { path = new URL(page).pathname; } catch { /* keep raw */ }
  const subject = (species && heading) || species || path || 'site';
  const body = [
    `**Страница:** ${page || '—'}`,
    `**Вид (id):** ${species ? `\`${species}\`` : '—'}`,
    `**Время:** ${new Date().toISOString()}`,
    '',
    '**Сообщение:**',
    fence(message),
    '',
    `<sub>User-Agent: ${ua.replace(/[<>`]/g, '') || '—'}</sub>`,
  ].join('\n');

  try {
    const gh = await fetch(`https://api.github.com/repos/${REPO}/issues`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${env.GITHUB_REPORTS_TOKEN}`,
        Accept: 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'colombia-birds-reports',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        title: `[report] ${subject}`.slice(0, 200),
        body,
        labels: species ? ['report', 'species'] : ['report'],
      }),
    });
    if (!gh.ok) {
      console.error('github error', gh.status, (await gh.text()).slice(0, 500));
      return json({ ok: false, error: 'could not save the report' }, 502, origin);
    }
    const issue = (await gh.json()) as { number: number };
    return json({ ok: true, issue: issue.number }, 200, origin);
  } catch (e) {
    console.error('github fetch failed', String(e));
    return json({ ok: false, error: 'could not save the report' }, 502, origin);
  }
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    const origin = req.headers.get('Origin');
    if (req.method === 'OPTIONS') return new Response(null, { status: 204, headers: cors(origin) });
    if (url.pathname === '/' && req.method === 'GET') {
      return json({ ok: true, service: 'colombia-birds-reports' }, 200, origin);
    }
    if (url.pathname === '/report') {
      if (req.method !== 'POST') return json({ ok: false, error: 'method not allowed' }, 405, origin);
      try {
        return await handleReport(req, env, origin);
      } catch (e) {
        console.error('unhandled', String(e));
        return json({ ok: false, error: 'internal error' }, 500, origin);
      }
    }
    return json({ ok: false, error: 'not found' }, 404, origin);
  },
} satisfies ExportedHandler<Env>;
