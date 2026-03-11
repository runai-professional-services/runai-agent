"""
Workspace submission tool for the Run:AI Agent.

Wraps the MCP submit_workspace tool with tool-specific defaults so the LLM
only needs to supply name, project_name, image, and gpu_devices:
  - Jupyter: command=start-notebook.sh, args with NotebookApp.base_url/token,
             tool_type=jupyter-notebook, tool_port=8888
  - VSCode:  tool_type=visual-studio-code, tool_port=8080
  - Custom:  pass-through with no overrides
"""

import os
from typing import Optional

from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

from ..utils import call_mcp_tool, _normalize_optional_str_none, logger


# ── Tool presets ──────────────────────────────────────────────────────────────

_TOOL_PRESETS = {
    "jupyter": {
        "tool_type": "jupyter-notebook",
        "tool_name": "Jupyter",
        "tool_port": 8888,
        "command": "start-notebook.sh",
        "args": "--NotebookApp.base_url=/${RUNAI_PROJECT}/${RUNAI_JOB_NAME} --NotebookApp.token=''",
    },
    "vscode": {
        "tool_type": "visual-studio-code",
        "tool_name": "VSCode",
        "tool_port": 8080,
        "command": None,
        "args": None,
    },
    "tensorboard": {
        "tool_type": "tensorboard",
        "tool_name": "TensorBoard",
        "tool_port": 6006,
        "command": None,
        "args": None,
    },
    "rstudio": {
        "tool_type": "rstudio",
        "tool_name": "RStudio",
        "tool_port": 8787,
        "command": None,
        "args": None,
    },
}


# ── NAT Config ────────────────────────────────────────────────────────────────

class RunaiWorkspaceConfig(FunctionBaseConfig, name="runai_workspace"):
    """Submit interactive workspace workloads on Run:AI with correct defaults."""

    description: str = (
        "Submit an interactive workspace (Jupyter, VSCode, etc.) on Run:AI. "
        "Automatically sets the correct command, args, tool_type, and tool_port "
        "for the requested tool type."
    )
    default_gpu_devices: int = 1
    default_cpu_cores: float = 1.0
    default_cpu_memory: str = "2G"


# ── NAT Function Registration ─────────────────────────────────────────────────

@register_function(config_type=RunaiWorkspaceConfig)
async def runai_workspace(config: RunaiWorkspaceConfig, builder: Builder):
    """Submit interactive workspace workloads with tool-specific defaults."""

    async def _submit_workspace(
        name: str,
        project_name: str,
        image: str,
        tool: str = "jupyter",
        gpu_devices: Optional[int] = None,
        gpu_portion: float = 1.0,
        cpu_core_request: Optional[float] = None,
        cpu_memory_request: Optional[str] = None,
    ) -> str:
        """
        Submit an interactive workspace workload on Run:AI.

        Args:
            name: Workload name.
            project_name: Run:AI project to submit into.
            image: Container image (e.g. 'jupyter/scipy-notebook').
            tool: Tool type — 'jupyter', 'vscode', 'tensorboard', 'rstudio',
                  or 'custom'. Defaults to 'jupyter'.
            gpu_devices: Number of GPU devices (default: 1).
            gpu_portion: GPU fraction per device (default: 1.0).
            cpu_core_request: CPU cores to request (default: 1.0).
            cpu_memory_request: CPU memory request (default: '2G').

        Returns:
            Confirmation message with workload details, or error description.
        """
        try:
            tool_key = (_normalize_optional_str_none(tool) or "jupyter").lower()
            preset = _TOOL_PRESETS.get(tool_key, {})

            effective_gpus = gpu_devices if gpu_devices is not None else config.default_gpu_devices
            effective_cpu = cpu_core_request or config.default_cpu_cores
            effective_mem = cpu_memory_request or config.default_cpu_memory

            mcp_url = os.environ.get("MCP_SERVER_URL", "").rstrip("/")
            if not mcp_url:
                return (
                    "⚠️  **MCP Server Not Configured**\n\n"
                    "Cannot submit workspace: `MCP_SERVER_URL` is not set."
                )

            payload = {
                "name": name,
                "project_name": project_name,
                "image": image,
                "gpu_devices": effective_gpus,
                "gpu_portion": gpu_portion,
                "cpu_core_request": effective_cpu,
                "cpu_memory_request": effective_mem,
                "tool_type": preset.get("tool_type", "custom"),
                "tool_name": preset.get("tool_name", tool_key.capitalize()),
                "tool_port": preset.get("tool_port", 8888),
            }

            if preset.get("command"):
                payload["command"] = preset["command"]
            if preset.get("args"):
                payload["args"] = preset["args"]

            logger.info(
                "Submitting workspace: name=%s project=%s image=%s tool=%s gpus=%d",
                name, project_name, image, tool_key, effective_gpus,
            )

            result = await call_mcp_tool(mcp_url, "submit_workspace", payload)

            if isinstance(result, dict) and result.get("error"):
                return (
                    f"❌ **Workspace Submission Failed**\n\n"
                    f"**Error:** {result.get('detail', 'Unknown error')}"
                )

            workload_id = result.get("workloadId") or result.get("id") or "N/A"
            tool_name = preset.get("tool_name", tool_key.capitalize())
            tool_port = preset.get("tool_port", 8888)

            return (
                f"✅ **Workspace Submitted**\n\n"
                f"| Parameter | Value |\n"
                f"|-----------|-------|\n"
                f"| Workload | `{name}` |\n"
                f"| Project | `{project_name}` |\n"
                f"| Image | `{image}` |\n"
                f"| Tool | {tool_name} (port {tool_port}) |\n"
                f"| GPUs | {effective_gpus} × {gpu_portion} |\n"
                f"| Workload ID | `{workload_id}` |\n\n"
                f"**📊 Monitor:** Once Running, use the Connect button in the Run:AI UI "
                f"or ask me 'list workspaces in {project_name}'."
            )

        except Exception as exc:
            logger.error("Workspace submission error: %s", exc)
            return (
                f"❌ **Workspace Submission Failed**\n\n"
                f"**Error:** {exc}\n\n"
                f"**Troubleshooting:**\n"
                f"1. Verify `MCP_SERVER_URL` is reachable\n"
                f"2. Check that project `{project_name}` exists\n"
                f"3. Ensure GPU resources are available in the cluster\n"
            )

    try:
        yield FunctionInfo.create(
            single_fn=_submit_workspace,
            description=(
                "Submit an interactive workspace (Jupyter, VSCode, TensorBoard, RStudio) on Run:AI. "
                "Automatically applies the correct command, args, tool_type, and tool_port for the "
                "chosen tool. Use when user asks to create or submit a workspace, Jupyter notebook, "
                "or VSCode session."
            ),
        )
    except GeneratorExit:
        logger.info("Workspace function exited")
    finally:
        logger.info("Cleaning up workspace function")
