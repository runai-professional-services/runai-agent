# pylint: disable=unused-import
# flake8: noqa

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
