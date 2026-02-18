#!/usr/bin/env python3
"""Revert workflow.yaml to react_agent-only (no memory) so NAT 1.3.1 can start."""
import re

WORKFLOW_PATH = "configs/workflow.yaml"


def main():
    with open(WORKFLOW_PATH, "r") as f:
        content = f.read()

    # 1. Remove memory section
    mem_start = content.find("\n# Redis-backed conversation memory")
    mem_end = content.find("\n# Shared prompt for runai_react_agent")
    content = content[:mem_start] + content[mem_end:]

    # 2. Remove default_initial_prompt and capture prompt body for workflow
    anchor_start = content.find("\n# Shared prompt for runai_react_agent")
    prompt_start = content.find("default_initial_prompt: &default_initial_prompt |\n", anchor_start)
    prompt_content_start = prompt_start + len("default_initial_prompt: &default_initial_prompt |\n")
    prompt_end_marker = "    Always provide complete, runnable code with proper error handling and security best practices.\n"
    prompt_end = content.find(prompt_end_marker, prompt_content_start) + len(prompt_end_marker)
    prompt_body = content[prompt_content_start:prompt_end]
    # Remove the whole block from "# Shared prompt" through end of prompt
    content = content[:anchor_start] + "\n" + content[prompt_end:]

    # 3. Remove runai_react_agent function block
    repl_start = content.find("\n  runai_react_agent:")
    repl_end = content.find("    initial_prompt: *default_initial_prompt\n", repl_start) + len("    initial_prompt: *default_initial_prompt\n")
    content = content[:repl_start] + content[repl_end:]

    # 4. Replace workflow section (auto_memory_agent) with react_agent + full prompt
    workflow_start = content.find("\nworkflow:")
    # Find end of current workflow (next line that is not indented 2 spaces, or EOF)
    rest = content[workflow_start + 1 :]
    workflow_end = 0
    for i, line in enumerate(rest.split("\n")):
        if i > 0 and line and not line.startswith("  ") and not line.startswith(" "):
            workflow_end = workflow_start + 1 + rest.find("\n" + line)
            break
    if workflow_end == 0:
        workflow_end = len(content)
    new_workflow = """workflow:
  _type: react_agent
  tool_names:
    - runailabs_environment_info
    - runai_submit_workload
    - runai_submit_distributed_workload
    - runai_submit_workspace
    - runai_submit_batch
    - runai_job_status
    - runai_cluster_resources
    - runai_manage_workload
    - runai_proactive_monitor
    - runai_failure_analyzer
    - runai_job_analytics
    - runai_template_executor
    - runai_kubectl_troubleshoot
    - runailabs_job_generator
    - runai_nim_benchmark
    - runai_docs_helper
    - runai_docs_search
    - runai_api_docs
  llm_name: demo_llm
  verbose: false
  max_iterations: 15
  max_tool_calls: 15

  initial_prompt: |
""" + prompt_body + "\n"
    content = content[: workflow_start] + new_workflow + content[workflow_end:]

    with open(WORKFLOW_PATH, "w") as f:
        f.write(content)
    print("Reverted workflow.yaml to react_agent (no memory). Backend should start with NAT 1.3.1.")


if __name__ == "__main__":
    main()
