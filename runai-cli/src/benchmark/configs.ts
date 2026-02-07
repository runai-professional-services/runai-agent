/**
 * GPU profiles and benchmark scenario configurations.
 *
 * These follow the NVIDIA NIM LLM benchmarking guidelines:
 * https://docs.nvidia.com/nim/benchmarking/llm/latest/index.html
 */

import type { GpuProfile, GpuType, ScenarioConfig, BenchmarkScenario } from './types.js';

// ---------------------------------------------------------------------------
// GPU Profiles
// ---------------------------------------------------------------------------

export const GPU_PROFILES: Record<GpuType, GpuProfile> = {
  h100: {
    name: 'NVIDIA H100 80GB',
    key: 'h100',
    defaultImage: 'nvcr.io/nim/meta/llama-3.1-8b-instruct:latest',
    gpuMemoryGb: 80,
    defaultGpuCount: 1,
    defaultModel: 'meta/llama-3.1-8b-instruct',
  },
  h200: {
    name: 'NVIDIA H200 141GB',
    key: 'h200',
    defaultImage: 'nvcr.io/nim/meta/llama-3.1-8b-instruct:latest',
    gpuMemoryGb: 141,
    defaultGpuCount: 1,
    defaultModel: 'meta/llama-3.1-8b-instruct',
  },
  a100: {
    name: 'NVIDIA A100 80GB',
    key: 'a100',
    defaultImage: 'nvcr.io/nim/meta/llama-3.1-8b-instruct:latest',
    gpuMemoryGb: 80,
    defaultGpuCount: 1,
    defaultModel: 'meta/llama-3.1-8b-instruct',
  },
};

// ---------------------------------------------------------------------------
// Benchmark Scenarios
// ---------------------------------------------------------------------------

export const SCENARIO_CONFIGS: Record<BenchmarkScenario, ScenarioConfig> = {
  throughput: {
    name: 'Throughput',
    key: 'throughput',
    description: 'Maximise tokens-per-second with high concurrency and long outputs',
    concurrency: 64,
    totalRequests: 1000,
    maxTokens: 512,
    inputTokens: 128,
    durationSeconds: 0,
  },
  latency: {
    name: 'Latency',
    key: 'latency',
    description: 'Minimise time-to-first-token and inter-token latency at low concurrency',
    concurrency: 1,
    totalRequests: 100,
    maxTokens: 128,
    inputTokens: 128,
    durationSeconds: 0,
  },
  concurrency: {
    name: 'Concurrency Sweep',
    key: 'concurrency',
    description: 'Measure performance across increasing concurrency levels (1→128)',
    concurrency: 128,
    totalRequests: 500,
    maxTokens: 256,
    inputTokens: 128,
    durationSeconds: 0,
  },
  scaling: {
    name: 'GPU Scaling',
    key: 'scaling',
    description: 'Evaluate how throughput scales with additional GPUs',
    concurrency: 32,
    totalRequests: 500,
    maxTokens: 256,
    inputTokens: 128,
    durationSeconds: 0,
  },
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

export function getGpuProfile(gpu: string): GpuProfile {
  const key = gpu.toLowerCase() as GpuType;
  const profile = GPU_PROFILES[key];
  if (!profile) {
    throw new Error(
      `Unknown GPU type "${gpu}". Supported: ${Object.keys(GPU_PROFILES).join(', ')}`,
    );
  }
  return profile;
}

export function getScenarioConfig(scenario: string): ScenarioConfig {
  const key = scenario.toLowerCase() as BenchmarkScenario;
  const cfg = SCENARIO_CONFIGS[key];
  if (!cfg) {
    throw new Error(
      `Unknown scenario "${scenario}". Supported: ${Object.keys(SCENARIO_CONFIGS).join(', ')}`,
    );
  }
  return cfg;
}

/** List all available GPU types (for CLI --help). */
export function listGpuTypes(): string[] {
  return Object.keys(GPU_PROFILES);
}

/** List all available scenarios (for CLI --help). */
export function listScenarios(): string[] {
  return Object.keys(SCENARIO_CONFIGS);
}

