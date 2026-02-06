/**
 * Benchmark CLI commands.
 *
 * Provides:
 *   runai-cli benchmark run     --gpu <type> --scenario <scenario> [options]
 *   runai-cli benchmark prompt  <text>   ← NEW: natural-language benchmark via NAT
 *   runai-cli benchmark list-gpus
 *   runai-cli benchmark list-scenarios
 *   runai-cli benchmark status  <jobName> [--project <p>]
 *   runai-cli benchmark logs    <jobName> [--project <p>]
 *   runai-cli benchmark export  <jobName> [--format json|csv]
 */

import { RunAIAgentClient } from '../api/client.js';
import { logger } from '../utils/logger.js';
import { loadConfig } from '../utils/config.js';
import { validateQuery, sanitizeInput } from '../utils/validation.js';
import { loadDotenv, requireEnvConfig, optionalEnv } from '../benchmark/env.js';
import {
  listGpuTypes,
  listScenarios,
  getGpuProfile,
  getScenarioConfig,
  GPU_PROFILES,
  SCENARIO_CONFIGS,
} from '../benchmark/configs.js';
import {
  buildBenchmarkJobSpec,
  submitBenchmarkJob,
  monitorBenchmarkJob,
  fetchBenchmarkLogs,
  parseMetricsFromLogs,
} from '../benchmark/runner.js';
import {
  exportResultsJson,
  exportResultsCsv,
  printResultSummary,
} from '../benchmark/results.js';
import type { BenchmarkResult } from '../benchmark/types.js';

// ---------------------------------------------------------------------------
// runai-cli benchmark run
// ---------------------------------------------------------------------------

export async function benchmarkRunCommand(options: {
  gpu: string;
  scenario: string;
  model?: string;
  project?: string;
  gpuCount?: string;
  image?: string;
  nodePool?: string;
  monitor?: boolean;
  export?: string;
}): Promise<void> {
  try {
    // Load .env if present
    loadDotenv();

    // Validate environment
    logger.startSpinner('Validating environment...');
    requireEnvConfig();
    logger.stopSpinner(true, 'Environment OK');

    // Validate GPU & scenario
    const profile = getGpuProfile(options.gpu);
    const scenario = getScenarioConfig(options.scenario);

    // Build job spec
    const spec = buildBenchmarkJobSpec({
      gpu: options.gpu,
      scenario: options.scenario,
      model: options.model,
      project: options.project,
      gpuCount: options.gpuCount ? parseInt(options.gpuCount, 10) : undefined,
      image: options.image,
      nodePool: options.nodePool,
    });

    // Print summary before submitting
    logger.header('🚀 NIM Benchmark Job');
    logger.table({
      'Job Name': spec.name,
      Project: spec.project,
      GPU: `${profile.name} x${spec.gpuCount}`,
      Scenario: scenario.name,
      Model: spec.model,
      Concurrency: String(scenario.concurrency),
      'Total Requests': String(scenario.totalRequests),
      Image: spec.image,
    });
    logger.plain('');

    // Submit the job
    logger.startSpinner('Submitting benchmark job to Run:AI...');
    const submitOutput = await submitBenchmarkJob(spec);
    logger.stopSpinner(true, 'Job submitted');
    logger.plain('');
    logger.plain(submitOutput);

    // Optionally monitor
    if (options.monitor) {
      logger.plain('');
      logger.startSpinner('Monitoring benchmark progress (timeout: 30m)...');
      const result = await monitorBenchmarkJob(spec.name, spec.project);
      result.gpuType = spec.gpuType;
      result.scenario = spec.scenario;
      result.model = spec.model;
      logger.stopSpinner(
        result.status === 'completed',
        result.status === 'completed' ? 'Benchmark completed' : 'Benchmark finished',
      );

      // Print summary
      printResultSummary(result);

      // Export if requested
      if (options.export) {
        const fmt = options.export.toLowerCase();
        const results: BenchmarkResult[] = [result];
        if (fmt === 'csv') {
          const p = exportResultsCsv(results);
          logger.success(`Results exported to ${p}`);
        } else {
          const p = exportResultsJson(results);
          logger.success(`Results exported to ${p}`);
        }
      }
    } else {
      logger.plain('');
      logger.info('💡 Use --monitor to wait for results and collect metrics.');
      logger.info(
        `💡 Check status later: runai-cli benchmark status ${spec.name} --project ${spec.project}`,
      );
    }
  } catch (error) {
    logger.stopSpinner(false);
    if (error instanceof Error) {
      logger.error(error.message);
    } else {
      logger.error('Unknown error occurred');
    }
    process.exit(1);
  }
}

// ---------------------------------------------------------------------------
// runai-cli benchmark status
// ---------------------------------------------------------------------------

export async function benchmarkStatusCommand(
  jobName: string,
  options: { project?: string },
): Promise<void> {
  try {
    loadDotenv();
    const project = options.project || optionalEnv('RUNAI_BENCHMARK_PROJECT', 'benchmark');

    logger.startSpinner(`Checking benchmark status for ${jobName}...`);
    const result = await monitorBenchmarkJob(jobName, project, 30000); // 30s quick check
    logger.stopSpinner();

    printResultSummary(result);
  } catch (error) {
    logger.stopSpinner(false);
    if (error instanceof Error) {
      logger.error(error.message);
    } else {
      logger.error('Unknown error');
    }
    process.exit(1);
  }
}

// ---------------------------------------------------------------------------
// runai-cli benchmark logs
// ---------------------------------------------------------------------------

export async function benchmarkLogsCommand(
  jobName: string,
  options: { project?: string },
): Promise<void> {
  try {
    loadDotenv();
    const project = options.project || optionalEnv('RUNAI_BENCHMARK_PROJECT', 'benchmark');

    logger.startSpinner('Fetching benchmark logs...');
    const logs = await fetchBenchmarkLogs(jobName, project);
    logger.stopSpinner();

    logger.plain('');
    logger.plain(logs);
  } catch (error) {
    logger.stopSpinner(false);
    if (error instanceof Error) {
      logger.error(error.message);
    } else {
      logger.error('Unknown error');
    }
    process.exit(1);
  }
}

// ---------------------------------------------------------------------------
// runai-cli benchmark export
// ---------------------------------------------------------------------------

export async function benchmarkExportCommand(
  jobName: string,
  options: { project?: string; format?: string; output?: string },
): Promise<void> {
  try {
    loadDotenv();
    const project = options.project || optionalEnv('RUNAI_BENCHMARK_PROJECT', 'benchmark');
    const fmt = (options.format || 'json').toLowerCase();

    logger.startSpinner('Fetching benchmark data...');
    const logs = await fetchBenchmarkLogs(jobName, project);
    logger.stopSpinner();

    const metrics = parseMetricsFromLogs(logs);
    const result: BenchmarkResult = {
      id: `${jobName}-export`,
      jobName,
      gpuType: 'h100', // Determined from job metadata
      scenario: 'throughput',
      model: '',
      status: 'completed',
      startedAt: new Date().toISOString(),
      metrics,
      logs,
    };

    if (fmt === 'csv') {
      const p = exportResultsCsv([result], options.output);
      logger.success(`Results exported to ${p}`);
    } else {
      const p = exportResultsJson([result], options.output);
      logger.success(`Results exported to ${p}`);
    }
  } catch (error) {
    logger.stopSpinner(false);
    if (error instanceof Error) {
      logger.error(error.message);
    } else {
      logger.error('Unknown error');
    }
    process.exit(1);
  }
}

// ---------------------------------------------------------------------------
// runai-cli benchmark list-gpus
// ---------------------------------------------------------------------------

export function benchmarkListGpusCommand(): void {
  logger.header('Supported GPU Types');
  for (const key of listGpuTypes()) {
    const p = GPU_PROFILES[key as keyof typeof GPU_PROFILES];
    logger.table({
      Key: p.key,
      Name: p.name,
      'VRAM (GiB)': String(p.gpuMemoryGb),
      'Default Model': p.defaultModel,
      'Default GPUs': String(p.defaultGpuCount),
    });
    logger.plain('');
  }
}

// ---------------------------------------------------------------------------
// runai-cli benchmark list-scenarios
// ---------------------------------------------------------------------------

export function benchmarkListScenariosCommand(): void {
  logger.header('Benchmark Scenarios');
  for (const key of listScenarios()) {
    const s = SCENARIO_CONFIGS[key as keyof typeof SCENARIO_CONFIGS];
    logger.table({
      Key: s.key,
      Name: s.name,
      Description: s.description,
      Concurrency: String(s.concurrency),
      'Total Requests': String(s.totalRequests),
      'Max Tokens': String(s.maxTokens),
      'Input Tokens': String(s.inputTokens),
    });
    logger.plain('');
  }
}

// ---------------------------------------------------------------------------
// runai-cli benchmark prompt  (natural-language benchmark via NAT agent)
// ---------------------------------------------------------------------------

/**
 * Send a natural-language benchmark request to the NAT agent.
 *
 * The agent's ReAct loop routes the request to `runai_nim_benchmark` based
 * on intent keywords (benchmark, throughput, latency, …).
 *
 * Examples:
 *   runai-cli benchmark prompt "Run NIM throughput benchmark on H100"
 *   runai-cli benchmark prompt "Benchmark latency on A100"
 *   runai-cli benchmark prompt "Run concurrency benchmark on H200 using the default model"
 *   runai-cli benchmark prompt "Test GPU performance on 2 H100s in project ml-team"
 */
export async function benchmarkPromptCommand(
  prompt: string,
  options: { stream?: boolean; project?: string },
): Promise<void> {
  try {
    // Validate input
    validateQuery(prompt);
    const sanitizedPrompt = sanitizeInput(prompt);

    // Load config and create client
    const config = loadConfig();
    const client = new RunAIAgentClient(config.agentUrl, config.timeout);

    logger.header('🧠 NIM Benchmark (NAT prompt)');
    logger.plain('');
    logger.plain(`Prompt: "${sanitizedPrompt}"`);
    logger.plain('');

    // Check server health
    logger.startSpinner('Connecting to agent...');
    const health = await client.healthCheck();

    if (!health.running) {
      logger.stopSpinner(false);
      logger.error(`Agent server is not running at ${config.agentUrl}`);
      logger.info('Start the server with: runai-cli server start');
      process.exit(1);
    }

    // Enhance prompt with project context if provided
    let enhancedPrompt = sanitizedPrompt;
    if (options.project) {
      enhancedPrompt += ` in project ${options.project}`;
    }

    logger.updateSpinner('Agent is routing to benchmark workflow...');

    // Handle streaming vs non-streaming
    const useStream = options.stream || config.stream;

    if (useStream) {
      logger.clearSpinner();
      logger.section('Agent Response');
      logger.plain('');

      for await (const chunk of client.queryStream(enhancedPrompt)) {
        process.stdout.write(chunk);
      }

      logger.plain('\n');
    } else {
      const response = await client.query(enhancedPrompt, false);
      logger.stopSpinner(true, 'Agent responded');

      if (response.status === 'error') {
        logger.error('Benchmark request failed:');
        logger.plain(response.error || 'Unknown error');
        process.exit(1);
      }

      logger.plain('');
      logger.section('Agent Response');
      logger.plain('');
      logger.plain(response.output);
    }

    logger.plain('');
    logger.info('💡 The agent uses NAT intent routing → runai_nim_benchmark tool.');
    logger.info('💡 For explicit flags use: runai-cli benchmark run --gpu h100 --scenario throughput');
  } catch (error) {
    logger.stopSpinner(false);
    if (error instanceof Error) {
      logger.error(error.message);
    } else {
      logger.error('Unknown error occurred');
    }
    process.exit(1);
  }
}

