# pylint: disable=unused-import
# flake8: noqa

# Patch NAT's TypeConverter to handle 'None' as empty JSON object.
#
# Two related bugs in NAT (confirmed through v1.4.1):
#
# Bug 1 — MCP tools (nat.plugins.mcp.client_base):
#   When a model outputs `Action Input: None`, NAT passes the string 'None' to
#   model_validate_json(), which fails because 'None' is not valid JSON.
#
# Bug 2 — Native NAT functions (nat.builder.function_base._convert_input):
#   The TypeConverter.convert() call has no str→BaseModel converter registered,
#   so converting the string 'None' to an InputArgsSchema raises:
#   ValueError: Cannot convert type <class 'str'> to InputArgsSchema. No match found.
#
# Fix: patch _try_direct_conversion to intercept 'None'/'null'/'' and directly
# instantiate the target BaseModel with model_validate_json('{}'), which succeeds
# for any model whose fields are all optional. Required-arg tools fail gracefully
# (ValidationError → except → fall through → model retries with proper args).
#
# Upstream issue: https://github.com/NVIDIA/NeMo-Agent-Toolkit
from nat.utils import type_converter as _tc
from pydantic import BaseModel as _BaseModel

_orig_try_direct = _tc.TypeConverter._try_direct_conversion


def _patched_try_direct(self, data, root):  # type: ignore[override]
    if isinstance(data, str) and data.strip() in ("None", "none", "null", ""):
        try:
            if isinstance(root, type) and issubclass(root, _BaseModel):
                return root.model_validate_json("{}")
        except Exception:
            pass
    return _orig_try_direct(self, data, root)


_tc.TypeConverter._try_direct_conversion = _patched_try_direct

# Patch MCPToolClient.acall to inject workspace tool defaults when submit_workspace
# is called without command/args.  The LLM often skips these despite system prompt
# instructions, so we enforce them here regardless of how the tool is invoked.
#
# Detection logic:
#   - "jupyter" in image  → Jupyter defaults (start-notebook.sh + base_url arg)
#   - "code-server" / "vscode" in image → VSCode defaults
#   - tool_type already set to a known value → use matching preset
from nat.plugins.mcp.client_base import MCPToolClient as _MCPToolClient

_WORKSPACE_PRESETS = {
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
    },
    "tensorboard": {
        "tool_type": "tensorboard",
        "tool_name": "TensorBoard",
        "tool_port": 6006,
    },
    "rstudio": {
        "tool_type": "rstudio",
        "tool_name": "RStudio",
        "tool_port": 8787,
    },
}

_TOOL_TYPE_TO_KEY = {
    "jupyter-notebook": "jupyter",
    "visual-studio-code": "vscode",
    "tensorboard": "tensorboard",
    "rstudio": "rstudio",
}

_orig_acall = _MCPToolClient.acall


async def _patched_acall(self, tool_args: dict) -> str:  # type: ignore[override]
    if self._tool_name == "submit_workspace":
        tool_args = dict(tool_args)

        # Detect preset: prefer explicit tool_type, fall back to image keyword
        image = (tool_args.get("image") or "").lower()
        existing_tool_type = tool_args.get("tool_type") or ""
        preset_key = _TOOL_TYPE_TO_KEY.get(existing_tool_type)
        if not preset_key:
            for key in ("jupyter", "vscode", "code-server", "tensorboard", "rstudio"):
                if key in image:
                    preset_key = "vscode" if key == "code-server" else key
                    break

        if preset_key and preset_key in _WORKSPACE_PRESETS:
            preset = _WORKSPACE_PRESETS[preset_key]
            # Always set tool metadata
            tool_args.setdefault("tool_type", preset["tool_type"])
            tool_args.setdefault("tool_name", preset["tool_name"])
            tool_args.setdefault("tool_port", preset["tool_port"])
            # Inject command/args only if not already provided
            if not tool_args.get("command") and preset.get("command"):
                tool_args["command"] = preset["command"]
            if not tool_args.get("args") and preset.get("args"):
                tool_args["args"] = preset["args"]

    return await _orig_acall(self, tool_args)


_MCPToolClient.acall = _patched_acall

# Import all functions to register them with NAT
from runai_agent.functions import (
    runailabs_environment_info,
    runailabs_job_generator,
    runai_kubectl_troubleshoot,
    runai_proactive_monitor,
    runai_failure_analyzer,
    runai_job_analytics,
)

# Import documentation helper (provides direct links to known topics)
from runai_agent.functions.runai_docs_helper import runai_docs_helper

# Import NIM benchmark function (NVIDIA NIM LLM benchmarking)
from runai_agent.functions.nim_benchmark import runai_nim_benchmark

# Import NIM inference submission function (deploy NIM endpoints with correct defaults)
from runai_agent.functions.nim_inference import runai_nim_inference

# Import resource listing function (formatted output for list operations)
from runai_agent.functions.list_resources import runai_list_resources

# Import workspace submission function (Jupyter/VSCode with correct defaults)
from runai_agent.functions.workspace import runai_workspace
