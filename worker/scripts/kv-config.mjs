// Find (or create) the KV namespace for the rate limiter and write wrangler.deploy.toml
// with its real id. Idempotent; used by .github/workflows/worker.yml.
import { execFileSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';

const TITLE = 'colombia-birds-reports-RATE';
const wrangler = (...args) =>
  execFileSync('npx', ['wrangler', ...args], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'inherit'] });

function findId() {
  const out = wrangler('kv', 'namespace', 'list');
  const start = out.search(/^\[/m); // skip any banner lines before the JSON array
  if (start < 0) throw new Error('unexpected output of wrangler kv namespace list');
  const list = JSON.parse(out.slice(start));
  return list.find((ns) => ns.title === TITLE)?.id;
}

let id = findId();
if (!id) {
  console.log(`Creating KV namespace ${TITLE}`);
  wrangler('kv', 'namespace', 'create', TITLE);
  id = findId();
}
if (!id) throw new Error(`KV namespace ${TITLE} not found after create`);
console.log(`KV namespace ${TITLE}: ${id}`);

const toml = readFileSync('wrangler.toml', 'utf8');
if (!toml.includes('id = "local-rate"')) throw new Error('placeholder id not found in wrangler.toml');
writeFileSync('wrangler.deploy.toml', toml.replace('id = "local-rate"', `id = "${id}"`));
