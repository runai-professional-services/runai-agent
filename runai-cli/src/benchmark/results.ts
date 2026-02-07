/**
 * Benchmark results – export to JSON, CSV, and console summary.
 */

import * as fs from 'fs';
import * as path from 'path';
import { logger } from '../utils/logger.js';
import { optionalEnv } from './env.js';
import type { BenchmarkResult, BenchmarkSummary, BenchmarkMetrics } from './types.js';

// ---------------------------------------------------------------------------
// Ensure output directory exists
// ---------------------------------------------------------------------------

function ensureDir(dir: string): void {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function getResultsDir(): string {
  return optionalEnv('RUNAI_BENCHMARK_RESULTS_DIR', './benchmark-results');
}

// ---------------------------------------------------------------------------
// JSON export
// ---------------------------------------------------------------------------

export function exportResultsJson(
  results: BenchmarkResult[],
  filePath?: string,
): string {
  const dir = getResultsDir();
  ensureDir(dir);
  const out = filePath ?? path.join(dir, `benchmark-${Date.now()}.json`);
  fs.writeFileSync(out, JSON.stringify(results, null, 2), 'utf-8');
  return out;
}

// ---------------------------------------------------------------------------
// CSV export
// ---------------------------------------------------------------------------

export function exportResultsCsv(
  results: BenchmarkResult[],
  filePath?: string,
): string {
  const dir = getResultsDir();
  ensureDir(dir);
  const out = filePath ?? path.join(dir, `benchmark-${Date.now()}.csv`);

  // Build header from metrics keys
  const metricKeys: (keyof BenchmarkMetrics)[] = [
    'tokensPerSecond',
    'requestsPerSecond',
    'timeToFirstTokenMs',
    'interTokenLatencyMs',
    'e2eLatencyP50Ms',
    'e2eLatencyP99Ms',
    'totalTokensGenerated',
    'totalRequests',
    'failedRequests',
    'durationSeconds',
    'gpuUtilisation',
    'gpuMemoryUtilisation',
  ];

  const header = [
    'id',
    'jobName',
    'gpuType',
    'scenario',
    'model',
    'status',
    'startedAt',
    'completedAt',
    ...metricKeys,
    'error',
  ];

  const rows = results.map((r) => {
    const base = [
      r.id,
      r.jobName,
      r.gpuType,
      r.scenario,
      r.model,
      r.status,
      r.startedAt,
      r.completedAt ?? '',
    ];
    const metricValues = metricKeys.map((k) =>
      r.metrics[k] !== undefined ? String(r.metrics[k]) : '',
    );
    return [...base, ...metricValues, r.error ?? ''];
  });

  const csv =
    header.join(',') + '\n' + rows.map((r) => r.join(',')).join('\n') + '\n';
  fs.writeFileSync(out, csv, 'utf-8');
  return out;
}

// ---------------------------------------------------------------------------
// Console summary
// ---------------------------------------------------------------------------

export function printResultSummary(result: BenchmarkResult): void {
  const m = result.metrics;

  logger.header(`📊 Benchmark Results: ${result.jobName}`);

  const statusIcon =
    result.status === 'completed'
      ? '✅'
      : result.status === 'failed'
        ? '❌'
        : '⏳';

  logger.table({
    Status: `${statusIcon} ${result.status}`,
    'GPU Type': result.gpuType.toUpperCase(),
    Scenario: result.scenario,
    Model: result.model,
    Started: result.startedAt,
    Completed: result.completedAt ?? 'N/A',
  });

  logger.plain('');

  if (Object.keys(m).length > 0) {
    logger.section('Metrics');

    const metricsDisplay: Record<string, string | number | undefined> = {};

    if (m.tokensPerSecond !== undefined)
      metricsDisplay['Tokens/sec'] = m.tokensPerSecond.toFixed(2);
    if (m.requestsPerSecond !== undefined)
      metricsDisplay['Requests/sec'] = m.requestsPerSecond.toFixed(2);
    if (m.timeToFirstTokenMs !== undefined)
      metricsDisplay['TTFT (ms)'] = m.timeToFirstTokenMs.toFixed(1);
    if (m.interTokenLatencyMs !== undefined)
      metricsDisplay['ITL (ms)'] = m.interTokenLatencyMs.toFixed(1);
    if (m.e2eLatencyP50Ms !== undefined)
      metricsDisplay['E2E Latency p50 (ms)'] = m.e2eLatencyP50Ms.toFixed(1);
    if (m.e2eLatencyP99Ms !== undefined)
      metricsDisplay['E2E Latency p99 (ms)'] = m.e2eLatencyP99Ms.toFixed(1);
    if (m.totalTokensGenerated !== undefined)
      metricsDisplay['Total Tokens'] = m.totalTokensGenerated;
    if (m.totalRequests !== undefined)
      metricsDisplay['Total Requests'] = m.totalRequests;
    if (m.failedRequests !== undefined)
      metricsDisplay['Failed Requests'] = m.failedRequests;
    if (m.durationSeconds !== undefined)
      metricsDisplay['Duration (s)'] = m.durationSeconds.toFixed(1);
    if (m.gpuUtilisation !== undefined)
      metricsDisplay['GPU Util (%)'] = m.gpuUtilisation.toFixed(1);
    if (m.gpuMemoryUtilisation !== undefined)
      metricsDisplay['GPU Mem Util (%)'] = m.gpuMemoryUtilisation.toFixed(1);

    if (Object.keys(metricsDisplay).length > 0) {
      logger.table(metricsDisplay);
    } else {
      logger.plain('  No parsed metrics available (check raw logs).');
    }
  }

  if (result.error) {
    logger.plain('');
    logger.error(`Error: ${result.error}`);
  }
}

export function buildSummary(result: BenchmarkResult, project: string): BenchmarkSummary {
  return {
    timestamp: new Date().toISOString(),
    gpuType: result.gpuType,
    scenario: result.scenario,
    model: result.model,
    status: result.status,
    metrics: result.metrics,
    gpuCount: 1,
    project,
  };
}

