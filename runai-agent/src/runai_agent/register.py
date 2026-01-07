# pylint: disable=unused-import
# flake8: noqa

# Import all functions to register them with NAT
from runai_agent.functions import (
    runailabs_environment_info,
    runailabs_job_generator,
    runai_submit_workload,
    runai_submit_distributed_workload,
    runai_submit_workspace,
    runai_submit_batch,
    runai_job_status,
    runai_kubectl_troubleshoot,
    runai_manage_workload,
    runai_proactive_monitor,
    runai_failure_analyzer,
    runai_template_executor,
)

# Import documentation helper (provides direct links to known topics)
from runai_agent.functions.runai_docs_helper import runai_docs_helper