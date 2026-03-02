# pylint: disable=unused-import
# flake8: noqa

# Patch NAT's MCP type converter to handle 'None' as empty JSON object.
#
# When a model outputs `Action Input: None` for a no-argument or optional-argument
# MCP tool, NAT passes the string 'None' to model_validate_json(), which fails
# because 'None' is not valid JSON. This patch converts 'None'/'null'/'' → '{}'
# before the Pydantic validator sees it, so those tools are called with no args
# instead of raising a ValidationError.
#
# Upstream issue: https://github.com/NVIDIA/NeMo-Agent-Toolkit
# Fixed in NAT: not yet (confirmed through v1.4.1)
from nat.utils import type_converter as _tc
from pydantic import BaseModel as _BaseModel

_orig_try_direct = _tc.TypeConverter._try_direct_conversion


def _patched_try_direct(self, data, root):  # type: ignore[override]
    if isinstance(data, str) and data.strip() in ("None", "none", "null", ""):
        try:
            if isinstance(root, type) and issubclass(root, _BaseModel):
                data = "{}"
        except TypeError:
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
