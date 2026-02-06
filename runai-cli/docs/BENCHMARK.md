# NVIDIA NIM Benchmark Integration

Run GPU-specific LLM benchmarks on your Run:AI cluster using the `runai-cli benchmark` commands. Benchmarks follow [NVIDIA's official NIM LLM benchmarking methodology](https://docs.nvidia.com/nim/benchmarking/llm/latest/index.html) and use **GenAI-Perf** for metrics collection.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Quick Start](#quick-start)
- [Commands Reference](#commands-reference)
- [GPU Profiles](#gpu-profiles)
- [Benchmark Scenarios](#benchmark-scenarios)
- [Results & Export](#results--export)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Requirement | Purpose |
|---|---|
| Node.js ≥ 18 | CLI runtime |
| Run:AI cluster access | Job submission target |
| NVIDIA API Key | NIM model access |
| GPU nodes (H100 / H200 / A100) | Benchmark execution hardware |

## Environment Setup

### 1. Set Required Variables

```bash
export RUNAI_CLIENT_ID="your-client-id"
export RUNAI_CLIENT_SECRET="your-client-secret"
export RUNAI_BASE_URL="https://your-cluster.run.ai"
export NVIDIA_API_KEY="nvapi-..."
```

### 2. Optional: Use a `.env` File

Copy the template and fill in your values:

```bash
cp env.example .env
# Edit .env with your credentials
```

The CLI automatically loads `.env` from the current directory or the project root. **Real environment variables always take priority** over the `.env` file.

### 3. Optional Benchmark Variables

```bash
export RUNAI_BENCHMARK_PROJECT="benchmark"        # Default project
export RUNAI_BENCHMARK_NODE_POOL="gpu-pool"       # Target node pool
export RUNAI_BENCHMARK_RESULTS_DIR="./results"    # Export directory
```

---

## Quick Start

```bash
# Install & build CLI
cd runai-cli
npm install && npm run build && npm link

# Run a throughput benchmark on H100
runai-cli benchmark run --gpu h100 --scenario throughput

# Run a latency benchmark on A100 with monitoring
runai-cli benchmark run --gpu a100 --scenario latency --monitor

# Export results as CSV
runai-cli benchmark run --gpu h200 --scenario concurrency --monitor --export csv
```

---

## Commands Reference

### `benchmark run`

Submit and optionally monitor a benchmark workload.

```
runai-cli benchmark run --gpu <type> --scenario <scenario> [options]
```

| Flag | Required | Description |
|---|---|---|
| `--gpu, -g` | ✅ | GPU type: `h100`, `h200`, `a100` |
| `--scenario, -s` | ✅ | Scenario: `throughput`, `latency`, `concurrency`, `scaling` |
| `--model, -m` | | Model ID (default per GPU profile) |
| `--project, -p` | | Run:AI project (default: `$RUNAI_BENCHMARK_PROJECT` or `benchmark`) |
| `--gpu-count` | | Number of GPUs (default: 1) |
| `--image` | | Override container image |
| `--node-pool` | | Target Run:AI node pool |
| `--monitor` | | Wait for completion and collect metrics |
| `--export <fmt>` | | Export results as `json` or `csv` |

### `benchmark status <jobName>`

Check the status of a running or completed benchmark job.

```
runai-cli benchmark status nim-bench-h100-throughput-20250206 --project benchmark
```

### `benchmark logs <jobName>`

Fetch raw logs from a benchmark job.

```
runai-cli benchmark logs nim-bench-h100-throughput-20250206 --project benchmark
```

### `benchmark export <jobName>`

Export benchmark results from a completed job.

```
runai-cli benchmark export nim-bench-h100-throughput-20250206 --format csv --output results.csv
```

### `benchmark list-gpus`

List all supported GPU profiles and their defaults.

```
runai-cli benchmark list-gpus
```

### `benchmark list-scenarios`

List all benchmark scenarios with parameter details.

```
runai-cli benchmark list-scenarios
```

---

## GPU Profiles

| GPU | VRAM | Default Model | Default GPUs |
|---|---|---|---|
| **H100** | 80 GiB | `meta/llama-3.1-8b-instruct` | 1 |
| **H200** | 141 GiB | `meta/llama-3.1-8b-instruct` | 1 |
| **A100** | 80 GiB | `meta/llama-3.1-8b-instruct` | 1 |

Override the model with `--model`:

```bash
runai-cli benchmark run --gpu h100 --scenario throughput --model meta/llama-3.1-70b-instruct --gpu-count 4
```

---

## Benchmark Scenarios

| Scenario | Concurrency | Requests | Max Tokens | Purpose |
|---|---|---|---|---|
| **throughput** | 64 | 1,000 | 512 | Maximise tokens/sec |
| **latency** | 1 | 100 | 128 | Minimise TTFT and ITL |
| **concurrency** | 128 | 500 | 256 | Sweep across concurrency levels |
| **scaling** | 32 | 500 | 256 | Measure multi-GPU throughput scaling |

---

## Results & Export

### Metrics Collected

| Metric | Unit | Description |
|---|---|---|
| `tokensPerSecond` | tok/s | Output throughput |
| `requestsPerSecond` | req/s | Request throughput |
| `timeToFirstTokenMs` | ms | Time to first token (TTFT) |
| `interTokenLatencyMs` | ms | Inter-token latency (ITL) |
| `e2eLatencyP50Ms` | ms | End-to-end latency (p50) |
| `e2eLatencyP99Ms` | ms | End-to-end latency (p99) |
| `totalTokensGenerated` | count | Total output tokens |
| `totalRequests` | count | Requests completed |
| `failedRequests` | count | Requests that errored |
| `durationSeconds` | sec | Total benchmark duration |
| `gpuUtilisation` | % | GPU compute utilisation |
| `gpuMemoryUtilisation` | % | GPU memory utilisation |

### JSON Export

```bash
runai-cli benchmark run --gpu h100 --scenario throughput --monitor --export json
# → ./benchmark-results/benchmark-1738857600000.json
```

### CSV Export

```bash
runai-cli benchmark run --gpu h100 --scenario throughput --monitor --export csv
# → ./benchmark-results/benchmark-1738857600000.csv
```

---

## Examples

### Throughput Test on H100

```bash
runai-cli benchmark run \
  --gpu h100 \
  --scenario throughput \
  --project my-team \
  --monitor \
  --export json
```

### Latency Test on H200

```bash
runai-cli benchmark run \
  --gpu h200 \
  --scenario latency \
  --monitor
```

### Concurrency Sweep on A100

```bash
runai-cli benchmark run \
  --gpu a100 \
  --scenario concurrency \
  --project ml-benchmarks \
  --gpu-count 2 \
  --monitor \
  --export csv
```

### GPU Scaling Test (Multi-GPU)

```bash
# 1 GPU baseline
runai-cli benchmark run --gpu h100 --scenario scaling --gpu-count 1 --monitor --export json

# 2 GPUs
runai-cli benchmark run --gpu h100 --scenario scaling --gpu-count 2 --monitor --export json

# 4 GPUs
runai-cli benchmark run --gpu h100 --scenario scaling --gpu-count 4 --monitor --export json
```

### Custom Model Benchmark

```bash
runai-cli benchmark run \
  --gpu h100 \
  --scenario throughput \
  --model meta/llama-3.1-70b-instruct \
  --gpu-count 4 \
  --image nvcr.io/nim/meta/llama-3.1-70b-instruct:latest \
  --monitor
```

---

## Troubleshooting

### Missing Environment Variables

```
✗ Missing required environment variables:
  • RUNAI_CLIENT_ID
  • NVIDIA_API_KEY

Set them in your shell or create a .env file (see env.example).
```

**Fix:** Export the missing variables or create a `.env` file.

### Agent Not Running

```
✗ Agent server is not running at http://localhost:8000
```

**Fix:** Start the agent first:

```bash
runai-cli server start
# or connect to a remote agent:
runai-cli connect https://your-agent-url.com
```

### Job Submission Failed

Check that:
1. Your Run:AI credentials are valid
2. The target project exists and you have access
3. GPU resources are available in the cluster
4. The container image is accessible

### No Metrics in Results

Metrics are parsed from job logs. If GenAI-Perf is not available in the container, the benchmark runs in simulated mode. Ensure the benchmark image has GenAI-Perf installed:

```bash
pip install genai-perf
```

### Node Pool Issues

If benchmark jobs stay pending, the GPU node pool may not match. Check available pools:

```bash
runai-cli ask "Show me available node pools"
```

Then target a specific pool:

```bash
runai-cli benchmark run --gpu h100 --scenario throughput --node-pool gpu-h100-pool
```

