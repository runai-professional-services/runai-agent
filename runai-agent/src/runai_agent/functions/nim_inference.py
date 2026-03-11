"""
NIM Inference Submission tool for the Run:AI Agent.

Wraps the MCP submit_inference tool with NVIDIA NIM-specific defaults:
  - Serving port: 8000 (NIM default)
  - NIM_SERVER_PORT, NIM_JSONL_LOGGING, NIM_LOG_LEVEL, OUTLINES_CACHE_DIR
  - NGC_API_KEY sourced from a Kubernetes Secret

Intent keywords (handled by NAT routing in workflow.yaml):
  "deploy NIM", "submit NIM inference", "run NIM", "NIM model", "NIM endpoint",
  "deploy inference", "serve model"
"""

import os
from typing import Optional

from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

from ..utils import call_mcp_tool, _normalize_optional_str_none, logger


# ── Constants ────────────────────────────────────────────────────────────────

# Run:AI prefixes the K8s secret name for ngcApiKey credentials.
# Credential named "my-ngc-key" → K8s secret "genericsecret-ngcgs-my-ngc-key"
_GENERIC_SECRET_PREFIX = "genericsecret-ngcgs-"

# ── Default NIM environment variables ─────────────────────────────────────────

NIM_DEFAULT_ENV_VARS = {
    "NIM_SERVER_PORT": "8000",
    "NIM_JSONL_LOGGING": "1",
    "NIM_LOG_LEVEL": "INFO",
    "OUTLINES_CACHE_DIR": "/tmp/outlines",
}


# ── NAT Config ────────────────────────────────────────────────────────────────


class RunaiNimInferenceConfig(FunctionBaseConfig, name="runai_nim_inference"):
    """Submit NVIDIA NIM inference endpoints on Run:AI with correct defaults."""

    description: str = (
        "Submit an NVIDIA NIM inference endpoint on a Run:AI cluster. "
        "Automatically sets NIM-required environment variables (NIM_SERVER_PORT, "
        "NIM_JSONL_LOGGING, NIM_LOG_LEVEL) and wires the NGC_API_KEY from a "
        "Kubernetes Secret. Use when user asks to deploy a NIM model, start a "
        "NIM inference endpoint, or serve a NIM container."
    )
    default_serving_port: int = 8000
    default_gpu_devices: int = 1
    default_cpu_cores: float = 4.0
    default_cpu_memory: str = "8G"


# ── NAT Function Registration ─────────────────────────────────────────────────


@register_function(config_type=RunaiNimInferenceConfig)
async def runai_nim_inference(config: RunaiNimInferenceConfig, builder: Builder):
    """Submit NVIDIA NIM inference endpoints with correct defaults."""

    async def _submit_nim(
        name: str,
        project_name: str,
        image: str,
        ngc_credential_name: Optional[str] = None,
        ngc_api_key_secret: Optional[str] = None,
        ngc_api_key_secret_key: str = "NGC_API_KEY",
        serving_port: Optional[int] = None,
        gpu_devices: Optional[int] = None,
        gpu_portion: float = 1.0,
        cpu_core_request: Optional[float] = None,
        cpu_memory_request: Optional[str] = None,
        min_replicas: int = 1,
        max_replicas: int = 1,
        extra_env_vars: Optional[dict] = None,
    ) -> str:
        """
        Submit a NVIDIA NIM inference workload with NIM-specific defaults.

        Args:
            name: Workload name (e.g. 'llama-31-8b').
            project_name: Run:AI project to deploy into.
            image: NIM container image (e.g. 'nvcr.io/nim/meta/llama-3.1-8b-instruct:latest').
            ngc_credential_name: Name of the Run:AI credential asset created via
                create_ngc_api_key_credential (e.g. 'my-ngc-key'). The K8s secret
                name is automatically derived as 'genericsecret-ngcgs-<ngc_credential_name>'.
                Use this OR ngc_api_key_secret, not both.
            ngc_api_key_secret: Name of the Kubernetes Secret holding the NGC API key.
                Use this when referencing a raw K8s secret directly instead of a
                Run:AI credential. The secret must exist in the project namespace.
            ngc_api_key_secret_key: Key within the secret that holds NGC_API_KEY (default: 'NGC_API_KEY').
            serving_port: Port NIM listens on (default: 8000).
            gpu_devices: Number of GPUs (default: 1).
            gpu_portion: GPU fraction per device (default: 1.0).
            cpu_core_request: CPU cores to request (default: 4.0).
            cpu_memory_request: CPU memory (default: '8G').
            min_replicas: Min autoscaling replicas (default: 1).
            max_replicas: Max autoscaling replicas (default: 1).
            extra_env_vars: Additional plain-text environment variables as a dict.

        Returns:
            Confirmation message with workload details, or error description.
        """
        try:
            # Normalise optional strings the LLM may pass as "null"
            ngc_credential_name = _normalize_optional_str_none(ngc_credential_name)
            ngc_api_key_secret = _normalize_optional_str_none(ngc_api_key_secret)
            extra_env_vars = extra_env_vars or {}

            # Derive K8s secret name from Run:AI credential name if provided
            if ngc_credential_name and not ngc_api_key_secret:
                ngc_api_key_secret = f"{_GENERIC_SECRET_PREFIX}{ngc_credential_name}"
                logger.info(
                    "Derived K8s secret name '%s' from credential name '%s'",
                    ngc_api_key_secret,
                    ngc_credential_name,
                )

            effective_port = serving_port or config.default_serving_port
            effective_gpus = gpu_devices or config.default_gpu_devices
            effective_cpu = cpu_core_request or config.default_cpu_cores
            effective_mem = cpu_memory_request or config.default_cpu_memory

            mcp_url = os.environ.get("MCP_SERVER_URL", "").rstrip("/")
            if not mcp_url:
                return (
                    "⚠️  **MCP Server Not Configured**\n\n"
                    "Cannot submit NIM inference: `MCP_SERVER_URL` is not set."
                )

            # Build plain env vars: NIM defaults + any user extras
            plain_env_vars = {**NIM_DEFAULT_ENV_VARS, **extra_env_vars}

            # Build secret env var list
            secret_env_vars = []
            if ngc_api_key_secret:
                secret_env_vars.append(
                    {
                        "name": "NGC_API_KEY",
                        "secret_name": ngc_api_key_secret,
                        "secret_key": ngc_api_key_secret_key,
                    }
                )
            else:
                logger.warning(
                    "No NGC API key secret provided for NIM inference '%s'. "
                    "The workload may fail if the image requires authentication.",
                    name,
                )

            logger.info(
                "Submitting NIM inference: name=%s project=%s image=%s port=%d gpus=%d",
                name,
                project_name,
                image,
                effective_port,
                effective_gpus,
            )

            result = await call_mcp_tool(
                mcp_url,
                "submit_inference",
                {
                    "name": name,
                    "project_name": project_name,
                    "image": image,
                    "serving_port": effective_port,
                    "gpu_devices": effective_gpus,
                    "gpu_portion": gpu_portion,
                    "cpu_core_request": effective_cpu,
                    "cpu_memory_request": effective_mem,
                    "min_replicas": min_replicas,
                    "max_replicas": max_replicas,
                    "environment_variables": plain_env_vars,
                    "secret_environment_variables": secret_env_vars,
                },
            )

            # Surface any API-level errors
            if isinstance(result, dict) and result.get("error"):
                return (
                    f"❌ **NIM Inference Submission Failed**\n\n"
                    f"**Error:** {result.get('detail', 'Unknown error')}"
                )

            workload_id = result.get("workloadId") or result.get("id") or "N/A"
            url = f"http://{name}.runai-{project_name}.svc.cluster.local"

            ngc_note = (
                f"NGC API key sourced from secret `{ngc_api_key_secret}` (key: `{ngc_api_key_secret_key}`)"
                if ngc_api_key_secret
                else "⚠️  No NGC API key secret provided — workload may fail to pull model weights"
            )

            return (
                f"✅ **NIM Inference Submitted**\n\n"
                f"| Parameter | Value |\n"
                f"|-----------|-------|\n"
                f"| Workload | `{name}` |\n"
                f"| Project | `{project_name}` |\n"
                f"| Image | `{image}` |\n"
                f"| Serving Port | `{effective_port}` |\n"
                f"| GPUs | {effective_gpus} × {gpu_portion} |\n"
                f"| Replicas | {min_replicas}–{max_replicas} |\n"
                f"| Workload ID | `{workload_id}` |\n\n"
                f"**🔑 Credentials:** {ngc_note}\n\n"
                f"**🌐 Internal URL:** `{url}`\n\n"
                f"**📋 NIM Environment Variables Set:**\n"
                + "".join(f"- `{k}={v}`\n" for k, v in plain_env_vars.items())
                + f"\n**📊 Monitor:** Ask me 'show inferences in {project_name}' or "
                f"'troubleshoot {name}' if the workload doesn't reach Running state."
            )

        except Exception as exc:
            logger.error("NIM inference submission error: %s", exc)
            return (
                f"❌ **NIM Inference Submission Failed**\n\n"
                f"**Error:** {exc}\n\n"
                f"**Troubleshooting:**\n"
                f"1. Verify `MCP_SERVER_URL` is reachable\n"
                f"2. Check that project `{project_name}` exists\n"
                f"3. Confirm the NGC API key secret exists in the project namespace\n"
                f"4. Ensure GPU resources are available in the cluster\n"
            )

    try:
        yield FunctionInfo.create(
            single_fn=_submit_nim,
            description=(
                "Submit an NVIDIA NIM inference endpoint on Run:AI with correct NIM defaults. "
                "Automatically sets NIM_SERVER_PORT=8000, NIM_JSONL_LOGGING, NIM_LOG_LEVEL, "
                "and wires NGC_API_KEY from a Kubernetes Secret. "
                "Use when user asks to: deploy a NIM model, start a NIM inference endpoint, "
                "run a NIM container, or serve a NIM model."
            ),
        )
    except GeneratorExit:
        logger.info("NIM inference function exited")
    finally:
        logger.info("Cleaning up NIM inference function")
