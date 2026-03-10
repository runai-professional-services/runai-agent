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
