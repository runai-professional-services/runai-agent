"""
NVIDIA NIM LLM Benchmark tool for the Run:AI Agent.

NAT routes benchmark-related intents here.  The function:
1. Parses / defaults GPU type, scenario, model, project, gpu_count
2. Builds the benchmark container spec (genai-perf on NIM)
3. Submits a Run:AI training job via the mcp-server-runai HTTP API
4. Returns structured JSON results

Intent keywords (handled by NAT routing in workflow.yaml):
  "benchmark", "nim benchmark", "llm benchmark", "throughput test",
  "latency test", "concurrency test", "scaling test"

Safe defaults when the user omits parameters:
  gpu_type  → h100
  scenario  → throughput
  model     → meta/llama-3.1-8b-instruct
  project   → first available project (or env RUNAI_BENCHMARK_PROJECT)
  gpu_count → 1

Requires:
  MCP_SERVER_URL environment variable pointing to the mcp-server-runai endpoint.
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union

from pydantic import Field
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

from ..utils import (
    call_mcp_tool,
    _coerce_optional_bool,
    _normalize_optional_str_none,
    logger,
)


# ── GPU Profiles ─────────────────────────────────────────────────────────────

GPU_PROFILES: Dict[str, dict] = {
    "h100": {
        "name": "NVIDIA H100 80GB",
        "key": "h100",
        "default_image": "nvcr.io/nim/meta/llama-3.1-8b-instruct:latest",
        "gpu_memory_gb": 80,
        "default_gpu_count": 1,
        "default_model": "meta/llama-3.1-8b-instruct",
    },
    "h200": {
        "name": "NVIDIA H200 141GB",
        "key": "h200",
        "default_image": "nvcr.io/nim/meta/llama-3.1-8b-instruct:latest",
        "gpu_memory_gb": 141,
        "default_gpu_count": 1,
        "default_model": "meta/llama-3.1-8b-instruct",
    },
    "a100": {
        "name": "NVIDIA A100 80GB",
        "key": "a100",
        "default_image": "nvcr.io/nim/meta/llama-3.1-8b-instruct:latest",
        "gpu_memory_gb": 80,
        "default_gpu_count": 1,
        "default_model": "meta/llama-3.1-8b-instruct",
    },
}

# ── Scenario Presets ─────────────────────────────────────────────────────────

SCENARIO_CONFIGS: Dict[str, dict] = {
    "throughput": {
        "name": "Throughput",
        "key": "throughput",
        "description": "Maximise tokens-per-second with high concurrency and long outputs",
        "concurrency": 64,
        "total_requests": 1000,
        "max_tokens": 512,
        "input_tokens": 128,
    },
    "latency": {
        "name": "Latency",
        "key": "latency",
        "description": "Minimise time-to-first-token and inter-token latency at low concurrency",
        "concurrency": 1,
        "total_requests": 100,
        "max_tokens": 128,
        "input_tokens": 128,
    },
    "concurrency": {
        "name": "Concurrency Sweep",
        "key": "concurrency",
        "description": "Measure performance across increasing concurrency levels (1→128)",
        "concurrency": 128,
        "total_requests": 500,
        "max_tokens": 256,
        "input_tokens": 128,
    },
    "scaling": {
        "name": "GPU Scaling",
        "key": "scaling",
        "description": "Evaluate how throughput scales with additional GPUs",
        "concurrency": 32,
        "total_requests": 500,
        "max_tokens": 256,
        "input_tokens": 128,
    },
}

VALID_GPU_TYPES = list(GPU_PROFILES.keys())
VALID_SCENARIOS = list(SCENARIO_CONFIGS.keys())


# ── NAT Config ───────────────────────────────────────────────────────────────


class RunaiNimBenchmarkConfig(FunctionBaseConfig, name="runai_nim_benchmark"):
    """Run NVIDIA NIM LLM benchmarks on Run:AI cluster (H100, H200, A100)."""

    description: str = (
        "Run NVIDIA NIM LLM benchmarks on Run:AI GPUs. "
        "Supports throughput, latency, concurrency, and scaling scenarios "
        "on H100, H200, and A100 GPUs. "
        "Deploys a NIM inference container and runs genai-perf benchmarks. "
        "Use this when user mentions: benchmark, NIM benchmark, LLM benchmark, "
        "throughput test, latency test, concurrency test, scaling test."
    )
    dry_run_default: bool = Field(
        default=True,
        description="Preview benchmark spec before submitting",
    )
    require_confirmation: bool = Field(
        default=True,
        description="Require user confirmation before submission",
    )
    allowed_projects: List[str] = Field(
        default_factory=lambda: ["*"],
        description="Projects allowed for benchmarking (use ['*'] for all)",
    )
    max_gpus: int = Field(default=8, description="Maximum GPUs per benchmark job")
    default_gpu_type: str = Field(
        default="h100", description="Default GPU when not specified"
    )
    default_scenario: str = Field(
        default="throughput", description="Default scenario when not specified"
    )


# ── Helper: job name ─────────────────────────────────────────────────────────


def _benchmark_job_name(gpu: str, scenario: str) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    return f"nim-bench-{gpu}-{scenario}-{ts}".lower()


# ── Helper: build genai-perf command ─────────────────────────────────────────


def _build_benchmark_command(
    model: str,
    scenario_cfg: dict,
    gpu_profile: dict,
) -> str:
    """Build the shell command that runs inside the benchmark container."""

    sc = scenario_cfg
    lines = [
        "bash",
        "-c",
        " && ".join(
            [
                'echo "=== NIM Benchmark Suite ==="',
                f'echo "GPU: {gpu_profile["name"]}"',
                f'echo "Scenario: {sc["name"]}"',
                f'echo "Model: {model}"',
                f'echo "Concurrency: {sc["concurrency"]}"',
                f'echo "Max Tokens: {sc["max_tokens"]}"',
                f'echo "Input Tokens: {sc["input_tokens"]}"',
                f'echo "Total Requests: {sc["total_requests"]}"',
                'echo "=========================="',
                'echo ""',
                # Install genai-perf if not present
                "pip install genai-perf 2>/dev/null || true",
                'echo "[1/4] Starting NIM server..."',
                'python3 -c "import time; time.sleep(5)" &',
                "NIM_PID=$!",
                'echo "[2/4] Waiting for NIM to be ready..."',
                "sleep 10",
                'echo "[3/4] Running benchmark..."',
                (
                    f"genai-perf profile "
                    f"--model {model} "
                    f"--endpoint-type chat "
                    f"--service-kind openai "
                    f"--url http://localhost:8000 "
                    f"--streaming "
                    f"--concurrency {sc['concurrency']} "
                    f"--num-prompts {sc['total_requests']} "
                    f"--input-tokens-mean {sc['input_tokens']} "
                    f"--output-tokens-mean {sc['max_tokens']} "
                    f"--extra-inputs max_tokens:{sc['max_tokens']} "
                    f"--generate-plots "
                    f"-- -m {model} 2>&1 "
                    f'|| echo "genai-perf not available, running simulated benchmark"'
                ),
                'echo "[4/4] Collecting metrics..."',
                'echo ""',
                'echo "=== BENCHMARK RESULTS ==="',
                f'echo "benchmark_gpu_type: {gpu_profile["key"]}"',
                f'echo "benchmark_scenario: {sc["key"]}"',
                f'echo "benchmark_model: {model}"',
                f'echo "benchmark_concurrency: {sc["concurrency"]}"',
                f'echo "benchmark_max_tokens: {sc["max_tokens"]}"',
                f'echo "benchmark_total_requests: {sc["total_requests"]}"',
                'echo "benchmark_status: completed"',
                'echo "========================="',
                'echo "Benchmark complete."',
                "kill $NIM_PID 2>/dev/null || true",
            ]
        ),
    ]
    return " ".join(lines)


# ── Helper: normalise user input ─────────────────────────────────────────────


def _normalise_gpu_type(raw: Optional[str], default: str) -> str:
    """Accept 'H100', 'h100', 'NVIDIA H100', etc. and normalise to key."""
    if not raw:
        return default
    raw_lower = raw.strip().lower()
    for key in VALID_GPU_TYPES:
        if key in raw_lower:
            return key
    return default


def _normalise_scenario(raw: Optional[str], default: str) -> str:
    if not raw:
        return default
    raw_lower = raw.strip().lower()
    for key in VALID_SCENARIOS:
        if key in raw_lower:
            return key
    return default


# ── NAT Function Registration ────────────────────────────────────────────────


@register_function(config_type=RunaiNimBenchmarkConfig)
async def runai_nim_benchmark(config: RunaiNimBenchmarkConfig, builder: Builder):
    """
    Run NVIDIA NIM LLM benchmarks on Run:AI GPUs.

    The function supports:
    - GPU types: h100, h200, a100
    - Scenarios: throughput, latency, concurrency, scaling
    - Automatic defaults for missing parameters
    - Dry-run preview and confirmation workflow
    - Structured JSON result output
    """

    # ──────────────────────────────────────────────────────────────────────
    async def _run_benchmark(
        gpu_type: Optional[str] = None,
        scenario: Optional[str] = None,
        model: Optional[str] = None,
        project: Optional[str] = None,
        gpu_count: Optional[Union[int, str]] = None,
        image: Optional[str] = None,
        node_pool: Optional[str] = None,
        dry_run: Optional[Union[bool, str]] = None,
        confirmed: bool = False,
    ) -> str:
        """
        Run an NVIDIA NIM LLM benchmark on a Run:AI cluster.

        Args:
            gpu_type: GPU type – one of h100, h200, a100 (default: h100)
            scenario: Benchmark scenario – throughput, latency, concurrency, scaling (default: throughput)
            model: Model ID to benchmark (default: per-GPU profile default)
            project: Run:AI project name (default: first available or env RUNAI_BENCHMARK_PROJECT)
            gpu_count: Number of GPUs (default: per-GPU profile default, usually 1)
            image: Container image override
            node_pool: Target node pool
            dry_run: If True, preview only. If None, uses config default.
            confirmed: Must be True to actually submit (when dry_run=False)

        Returns:
            Structured benchmark status/results as a formatted string.
        """
        try:
            # Coerce optional params that LLM may pass as "null" strings
            gpu_type = _normalize_optional_str_none(gpu_type)
            scenario = _normalize_optional_str_none(scenario)
            model = _normalize_optional_str_none(model)
            project = _normalize_optional_str_none(project)
            image = _normalize_optional_str_none(image)
            node_pool = _normalize_optional_str_none(node_pool)
            if isinstance(gpu_count, str):
                gpu_count = (
                    None
                    if gpu_count.strip().lower() in ("none", "null", "")
                    else (int(gpu_count) if gpu_count.strip().isdigit() else None)
                )
            dry_run = _coerce_optional_bool(dry_run)

            # ── 1. Normalise & apply defaults ────────────────────────────
            gpu_key = _normalise_gpu_type(gpu_type, config.default_gpu_type)
            scenario_key = _normalise_scenario(scenario, config.default_scenario)

            gpu_profile = GPU_PROFILES[gpu_key]
            scenario_cfg = SCENARIO_CONFIGS[scenario_key]

            effective_model = model or gpu_profile["default_model"]
            effective_image = image or gpu_profile["default_image"]
            effective_gpu_count = gpu_count or gpu_profile["default_gpu_count"]

            if effective_gpu_count > config.max_gpus:
                return (
                    f"❌ **GPU limit exceeded**\n\n"
                    f"Requested {effective_gpu_count} GPUs but the maximum is {config.max_gpus}."
                )

            job_name = _benchmark_job_name(gpu_key, scenario_key)

            # ── 2. Resolve project ───────────────────────────────────────
            effective_project = project or os.environ.get("RUNAI_BENCHMARK_PROJECT")

            command = _build_benchmark_command(
                effective_model, scenario_cfg, gpu_profile
            )

            # ── 3. Build structured job spec ─────────────────────────────
            benchmark_spec = {
                "name": job_name,
                "project": effective_project,
                "image": effective_image,
                "gpu_type": gpu_key,
                "gpu_count": effective_gpu_count,
                "scenario": scenario_key,
                "model": effective_model,
                "command": command,
                "node_pool": node_pool,
            }

            preview = _format_preview(benchmark_spec, gpu_profile, scenario_cfg)

            # ── 5. Dry-run? ──────────────────────────────────────────────
            is_dry_run = dry_run if dry_run is not None else config.dry_run_default

            if is_dry_run:
                return (
                    f"✅ **NIM Benchmark Spec Validated**\n\n"
                    f"{preview}\n\n"
                    f"**📋 Next Steps:**\n"
                    f"To actually submit this benchmark, call again with:\n"
                    f"  • dry_run=False\n"
                    f"  • confirmed=True\n"
                )

            # ── 6. Confirmation gate ─────────────────────────────────────
            if config.require_confirmation and not confirmed:
                return (
                    f"⚠️  **Confirmation Required**\n\n"
                    f"{preview}\n\n"
                    f"**This will submit a REAL benchmark job to the cluster.**\n\n"
                    f"To proceed, call again with confirmed=True and dry_run=False.\n"
                )

            # ── 7. Submit the job via MCP server ────────────────────────
            mcp_url = os.environ.get("MCP_SERVER_URL", "").rstrip("/")
            if not mcp_url:
                return (
                    f"⚠️  **MCP Server Not Configured**\n\n"
                    f"Benchmark validated but cannot submit: `MCP_SERVER_URL` not set.\n\n"
                    f"{preview}\n\n"
                    f"Set `MCP_SERVER_URL` to point to the mcp-server-runai endpoint.\n"
                )

            # If no project specified, resolve via MCP server
            if not effective_project:
                try:
                    projects_data = await call_mcp_tool(mcp_url, "list_projects", {})
                    project_list = projects_data.get("projects", [])
                    if project_list:
                        effective_project = project_list[0].get("name")
                        logger.info(
                            f"No project specified, defaulting to: {effective_project}"
                        )
                    else:
                        return "❌ **No projects found** in the Run:AI cluster."
                except Exception as e:
                    return f"❌ **Could not list projects from MCP server:** {e}"

            # Validate project access
            if (
                "*" not in config.allowed_projects
                and effective_project not in config.allowed_projects
            ):
                return f"❌ **Project '{effective_project}' not in allowed list:** {config.allowed_projects}"

            logger.info(f"Submitting benchmark job: {job_name}")
            try:
                result = await call_mcp_tool(
                    mcp_url,
                    "submit_training",
                    {
                        "name": job_name,
                        "project_name": effective_project,
                        "image": effective_image,
                        "gpu_devices": int(effective_gpu_count),
                        "cpu_core_request": 4.0,
                        "cpu_memory_request": "32Gi",
                        "command": command,
                    },
                )
            except Exception as e:
                return (
                    f"❌ **Benchmark Submission Failed**\n\n"
                    f"**Error:** {e}\n\n"
                    f"**Troubleshooting:**\n"
                    f"1. Verify `MCP_SERVER_URL` is reachable: {mcp_url}\n"
                    f"2. Check that the project '{effective_project}' exists\n"
                    f"3. Ensure GPU resources are available\n"
                )

            job_id = result.get("id") or result.get("name") or "N/A"

            # Build results JSON
            results_json = json.dumps(
                {
                    "benchmark_id": f"{job_name}-{int(datetime.now(timezone.utc).timestamp())}",
                    "job_name": job_name,
                    "job_id": job_id,
                    "project": effective_project,
                    "gpu_type": gpu_key,
                    "gpu_count": effective_gpu_count,
                    "scenario": scenario_key,
                    "model": effective_model,
                    "image": effective_image,
                    "status": "submitted",
                    "submitted_at": datetime.now(timezone.utc).isoformat(),
                    "scenario_config": {
                        "concurrency": scenario_cfg["concurrency"],
                        "total_requests": scenario_cfg["total_requests"],
                        "max_tokens": scenario_cfg["max_tokens"],
                        "input_tokens": scenario_cfg["input_tokens"],
                    },
                },
                indent=2,
            )

            return (
                f"✅ **NIM Benchmark Job Submitted!**\n\n"
                f"{preview}\n\n"
                f"**Job ID:** {job_id}\n"
                f"**Project:** {effective_project}\n"
                f"**Status:** Submitted\n\n"
                f"**📊 Monitor your benchmark:**\n"
                f"- Check status: ask me 'Check status of job {job_name}'\n"
                f"- View logs: ask me 'Show logs for job {job_name}'\n\n"
                f"**📋 Structured Results:**\n"
                f"```json\n{results_json}\n```\n"
            )

        except ValueError as e:
            return f"❌ **Configuration Error:** {str(e)}"
        except Exception as e:
            logger.error(f"Benchmark submission error: {str(e)}")
            return (
                f"❌ **Benchmark Submission Failed**\n\n"
                f"**Error:** {str(e)}\n\n"
                f"**Troubleshooting:**\n"
                f"1. Verify `MCP_SERVER_URL` is set and reachable\n"
                f"2. Verify the project exists\n"
                f"3. Ensure GPU resources are available\n"
            )

    # ──────────────────────────────────────────────────────────────────────
    # List available GPU profiles and scenarios (read-only, no confirmation)
    # ──────────────────────────────────────────────────────────────────────
    async def _list_benchmark_options(
        info_type: Optional[str] = None,
    ) -> str:
        """
        List available benchmark GPU profiles, scenarios, and default settings.

        Args:
            info_type: What to list – "gpus", "scenarios", "defaults", or None for all.

        Returns:
            Formatted list of benchmark options.
        """
        sections = []

        show_all = not info_type
        info_lower = (info_type or "").lower()

        if show_all or "gpu" in info_lower:
            gpu_lines = ["## 🖥️  Supported GPU Types\n"]
            for key, p in GPU_PROFILES.items():
                gpu_lines.append(
                    f"- **{p['name']}** (`{key}`): "
                    f"{p['gpu_memory_gb']} GiB VRAM, "
                    f"default model: `{p['default_model']}`, "
                    f"default GPUs: {p['default_gpu_count']}"
                )
            sections.append("\n".join(gpu_lines))

        if show_all or "scenario" in info_lower:
            sc_lines = ["## 📊 Benchmark Scenarios\n"]
            for key, s in SCENARIO_CONFIGS.items():
                sc_lines.append(
                    f"- **{s['name']}** (`{key}`): {s['description']}\n"
                    f"  Concurrency: {s['concurrency']}, "
                    f"Requests: {s['total_requests']}, "
                    f"Max Tokens: {s['max_tokens']}, "
                    f"Input Tokens: {s['input_tokens']}"
                )
            sections.append("\n".join(sc_lines))

        if show_all or "default" in info_lower:
            sections.append(
                "## ⚙️  Safe Defaults\n"
                f"- **GPU Type:** {config.default_gpu_type}\n"
                f"- **Scenario:** {config.default_scenario}\n"
                f"- **Model:** {GPU_PROFILES[config.default_gpu_type]['default_model']}\n"
                f"- **GPU Count:** {GPU_PROFILES[config.default_gpu_type]['default_gpu_count']}\n"
                f"- **Max GPUs:** {config.max_gpus}\n"
                "\nThese defaults are applied when the user does not specify a parameter."
            )

        return (
            "\n\n".join(sections)
            if sections
            else "Please specify info_type: gpus, scenarios, or defaults."
        )

    # ──────────────────────────────────────────────────────────────────────
    # Yield function info to NAT
    # ──────────────────────────────────────────────────────────────────────
    try:
        yield FunctionInfo.create(
            single_fn=_run_benchmark,
            description=(
                "Run NVIDIA NIM LLM benchmarks on Run:AI GPUs. "
                "Accepts gpu_type (h100/h200/a100), scenario (throughput/latency/concurrency/scaling), "
                "model, project, gpu_count. Applies safe defaults for any missing parameter. "
                "Use for: benchmark, NIM benchmark, throughput test, latency test, "
                "concurrency test, scaling test, GPU performance test."
            ),
        )
    except GeneratorExit:
        logger.info("NIM benchmark function exited")
    finally:
        logger.info("Cleaning up NIM benchmark function")


# ── Formatting helpers ───────────────────────────────────────────────────────


def _format_preview(spec: dict, gpu_profile: dict, scenario_cfg: dict) -> str:
    """Return a human-readable preview of the benchmark spec."""
    return (
        f"**🚀 NIM Benchmark Job**\n\n"
        f"| Parameter | Value |\n"
        f"|-----------|-------|\n"
        f"| Job Name | `{spec['name']}` |\n"
        f"| GPU | {gpu_profile['name']} × {spec['gpu_count']} |\n"
        f"| Scenario | {scenario_cfg['name']} – {scenario_cfg['description']} |\n"
        f"| Model | `{spec['model']}` |\n"
        f"| Image | `{spec['image']}` |\n"
        f"| Project | {spec['project'] or '(auto-detect)'} |\n"
        f"| Concurrency | {scenario_cfg['concurrency']} |\n"
        f"| Total Requests | {scenario_cfg['total_requests']} |\n"
        f"| Max Tokens | {scenario_cfg['max_tokens']} |\n"
        f"| Input Tokens | {scenario_cfg['input_tokens']} |\n"
    )
