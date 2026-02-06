/**
 * Environment variable loader with optional .env file support.
 *
 * Reads variables from process.env and, when present, merges values from a
 * local .env or env.example file (the .env file takes priority).
 */

import * as fs from 'fs';
import * as path from 'path';

// ---------------------------------------------------------------------------
// .env file parser (zero-dependency)
// ---------------------------------------------------------------------------

function parseDotenv(content: string): Record<string, string> {
  const result: Record<string, string> = {};
  for (const raw of content.split('\n')) {
    const line = raw.trim();
    if (!line || line.startsWith('#')) continue;
    const eqIdx = line.indexOf('=');
    if (eqIdx === -1) continue;
    const key = line.slice(0, eqIdx).trim();
    let value = line.slice(eqIdx + 1).trim();
    // Strip surrounding quotes
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    result[key] = value;
  }
  return result;
}

/**
 * Load a .env file if it exists. Values do **not** override already-set
 * environment variables (real env wins).
 */
export function loadDotenv(dir?: string): void {
  const searchDirs = dir
    ? [dir]
    : [process.cwd(), path.resolve(process.cwd(), '..')];

  for (const d of searchDirs) {
    const envPath = path.join(d, '.env');
    if (fs.existsSync(envPath)) {
      const vars = parseDotenv(fs.readFileSync(envPath, 'utf-8'));
      for (const [k, v] of Object.entries(vars)) {
        if (!process.env[k] && v) {
          process.env[k] = v;
        }
      }
      return;
    }
  }
}

// ---------------------------------------------------------------------------
// Required variable helpers
// ---------------------------------------------------------------------------

export interface EnvConfig {
  runaiClientId: string;
  runaiClientSecret: string;
  runaiBaseUrl: string;
  nvidiaApiKey: string;
}

/**
 * Validate that all required environment variables are present and return
 * them in a typed object. Throws with a clear message listing any missing
 * variables.
 */
export function requireEnvConfig(): EnvConfig {
  const missing: string[] = [];

  const runaiClientId = process.env.RUNAI_CLIENT_ID ?? '';
  const runaiClientSecret = process.env.RUNAI_CLIENT_SECRET ?? '';
  const runaiBaseUrl = process.env.RUNAI_BASE_URL ?? '';
  const nvidiaApiKey = process.env.NVIDIA_API_KEY ?? '';

  if (!runaiClientId) missing.push('RUNAI_CLIENT_ID');
  if (!runaiClientSecret) missing.push('RUNAI_CLIENT_SECRET');
  if (!runaiBaseUrl) missing.push('RUNAI_BASE_URL');
  if (!nvidiaApiKey) missing.push('NVIDIA_API_KEY');

  if (missing.length > 0) {
    throw new Error(
      `Missing required environment variables:\n` +
        missing.map((v) => `  • ${v}`).join('\n') +
        `\n\nSet them in your shell or create a .env file (see env.example).`,
    );
  }

  return { runaiClientId, runaiClientSecret, runaiBaseUrl, nvidiaApiKey };
}

/**
 * Return the value of an optional env var (with a fallback).
 */
export function optionalEnv(key: string, fallback: string = ''): string {
  return process.env[key] ?? fallback;
}

