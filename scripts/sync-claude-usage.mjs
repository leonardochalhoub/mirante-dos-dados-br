// Pulls daily Claude Code usage from `ccusage` and writes a static JSON
// to app/public/data/claude_usage.json so the ClaudeOps vertical can read it.
//
// Source of truth: ~/.claude/projects/ (JSONL transcripts written by Claude Code).
// `ccusage` parses those into daily totals + per-model breakdowns.
//
// Runs in predev/prebuild — must be local (CI doesn't have access to ~/.claude/).

import { execSync } from 'node:child_process';
import { mkdir, writeFile } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');
const OUT = join(ROOT, 'app', 'public', 'data', 'claude_usage.json');

function pullCcusage() {
  try {
    const raw = execSync('npx ccusage@latest --json', {
      encoding: 'utf8',
      maxBuffer: 64 * 1024 * 1024,
      stdio: ['ignore', 'pipe', 'ignore'],
    });
    const start = raw.indexOf('{');
    if (start < 0) throw new Error('no JSON in ccusage output');
    return JSON.parse(raw.slice(start));
  } catch (err) {
    console.warn(`[sync-claude-usage] ccusage unavailable (${err.message}). Skipping refresh.`);
    return null;
  }
}

const data = pullCcusage();
if (!data) process.exit(0);

const days = (data.daily ?? []).map((d) => ({
  date: d.date,
  input_tokens: d.inputTokens ?? 0,
  output_tokens: d.outputTokens ?? 0,
  cache_creation_tokens: d.cacheCreationTokens ?? 0,
  cache_read_tokens: d.cacheReadTokens ?? 0,
  total_tokens: d.totalTokens ?? 0,
  total_cost: d.totalCost ?? 0,
  models: d.modelsUsed ?? [],
  by_model: (d.modelBreakdowns ?? []).map((m) => ({
    model: m.modelName,
    cost: m.cost ?? 0,
    total_tokens:
      (m.inputTokens ?? 0) + (m.outputTokens ?? 0) + (m.cacheCreationTokens ?? 0) + (m.cacheReadTokens ?? 0),
  })),
}));

const totalCost = days.reduce((s, d) => s + d.total_cost, 0);
const totalTokens = days.reduce((s, d) => s + d.total_tokens, 0);

const payload = {
  generated_at: new Date().toISOString(),
  source: 'ccusage (local ~/.claude/projects)',
  totals: {
    days: days.length,
    total_cost_usd: totalCost,
    total_tokens: totalTokens,
    avg_cost_per_day_usd: days.length ? totalCost / days.length : 0,
  },
  daily: days,
};

await mkdir(dirname(OUT), { recursive: true });
await writeFile(OUT, JSON.stringify(payload, null, 2));
console.log(
  `[sync-claude-usage] wrote ${OUT} — ${days.length} days, $${totalCost.toFixed(2)} total`,
);
