/**
 * NVIDIA NIM Benchmark types and interfaces.
 *
 * Follows the metrics and configurations from:
 * https://docs.nvidia.com/nim/benchmarking/llm/latest/index.html
 */

// ---------------------------------------------------------------------------
// GPU Profiles
// ---------------------------------------------------------------------------

export type GpuType = 'h100' | 'h200' | 'a100';

export interface GpuProfile {
  /** Display name (e.g. "NVIDIA H100 80GB") */
  name: string;
  /** Short key used on the CLI */
  key: GpuType;
  /** Default container image for NIM inference */
  defaultImage: string;
  /** GPU memory in GiB */
  gpuMemoryGb: number;
  /** Suggested number of GPUs for a single benchmark pod */
  defaultGpuCount: number;
  /** Default model to benchmark when none specified */
  defaultModel: string;
  /** Optional Run:AI node-pool selector */
  nodePoolSelector?: string;
}

// ---------------------------------------------------------------------------
// Benchmark Scenarios
// ---------------------------------------------------------------------------

export type BenchmarkScenario =
  | 'throughput'
  | 'latency'
  | 'concurrency'
  | 'scaling';

export interface ScenarioConfig {
  /** Human-readable scenario name */
  name: string;
  key: BenchmarkScenario;
  /** Description shown in --help text */
  description: string;
  /** Number of concurrent virtual users / streams */
  concurrency: number;
  /** Total number of requests to send */
  totalRequests: number;
  /** Maximum tokens to generate per request */
  maxTokens: number;
  /** Input prompt length (tokens) */
  inputTokens: number;
  /** Duration cap in seconds (0 = unlimited) */
  durationSeconds: number;
}

// ---------------------------------------------------------------------------
// Benchmark Job Definition (submitted to Run:AI)
// ---------------------------------------------------------------------------

export interface BenchmarkJobSpec {
  /** Unique job name */
  name: string;
  /** Run:AI project */
  project: string;
  /** Container image */
  image: string;
  /** GPU type selector */
  gpuType: GpuType;
  /** Number of GPUs */
  gpuCount: number;
  /** Benchmark scenario */
  scenario: BenchmarkScenario;
  /** Model ID to benchmark */
  model: string;
  /** CPU cores */
  cpuCores: number;
  /** Memory limit */
  memory: string;
  /** Additional environment variables */
  envVars: Record<string, string>;
  /** Container command */
  command: string;
  /** Node pool name (optional) */
  nodePool?: string;
}

// ---------------------------------------------------------------------------
// Benchmark Results
// ---------------------------------------------------------------------------

export type BenchmarkStatus =
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled';

export interface BenchmarkMetrics {
  /** Tokens per second (throughput) */
  tokensPerSecond?: number;
  /** Requests per second */
  requestsPerSecond?: number;
  /** Time-to-first-token (ms) */
  timeToFirstTokenMs?: number;
  /** Inter-token latency (ms) */
  interTokenLatencyMs?: number;
  /** End-to-end latency – p50 (ms) */
  e2eLatencyP50Ms?: number;
  /** End-to-end latency – p99 (ms) */
  e2eLatencyP99Ms?: number;
  /** Total tokens generated */
  totalTokensGenerated?: number;
  /** Total requests completed */
  totalRequests?: number;
  /** Total requests failed */
  failedRequests?: number;
  /** Total benchmark duration (seconds) */
  durationSeconds?: number;
  /** GPU utilisation (0-100) */
  gpuUtilisation?: number;
  /** GPU memory utilisation (0-100) */
  gpuMemoryUtilisation?: number;
}

export interface BenchmarkResult {
  /** Unique run ID */
  id: string;
  /** Job name submitted to Run:AI */
  jobName: string;
  /** GPU type */
  gpuType: GpuType;
  /** Scenario that was run */
  scenario: BenchmarkScenario;
  /** Model benchmarked */
  model: string;
  /** Status of the benchmark */
  status: BenchmarkStatus;
  /** When the benchmark started */
  startedAt: string;
  /** When the benchmark finished */
  completedAt?: string;
  /** Collected metrics */
  metrics: BenchmarkMetrics;
  /** Raw logs (truncated for JSON export) */
  logs?: string;
  /** Error details if failed */
  error?: string;
}

// ---------------------------------------------------------------------------
// Summary Report
// ---------------------------------------------------------------------------

export interface BenchmarkSummary {
  /** Run timestamp */
  timestamp: string;
  /** GPU used */
  gpuType: GpuType;
  /** Scenario */
  scenario: BenchmarkScenario;
  /** Model */
  model: string;
  /** Overall status */
  status: BenchmarkStatus;
  /** Key metrics */
  metrics: BenchmarkMetrics;
  /** Number of GPUs */
  gpuCount: number;
  /** Run:AI project */
  project: string;
}

