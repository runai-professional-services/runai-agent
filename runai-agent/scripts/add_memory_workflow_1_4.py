#!/usr/bin/env python3
"""Add NAT 1.4 memory workflow: memory section (embedder), runai_react_agent with inlined prompt, auto_memory_agent. No top-level anchor."""
import re

WORKFLOW_PATH = "configs/workflow.yaml"


def main():
    with open(WORKFLOW_PATH, "r") as f:
        content = f.read()

    # 1. Add memory section after general (use embedder for NAT 1.4 redis plugin)
    old = (
        "    host: \"0.0.0.0\"\n"
        "    port: 8000\n"
        "\n"
        "\n"
        "functions:"
    )
    new = (
        "    host: \"0.0.0.0\"\n"
        "    port: 8000\n"
        "\n"
        "# Redis-backed conversation memory (NAT 1.4 auto_memory_agent)\n"
        "memory:\n"
        "  redis_memory:\n"
        "    _type: nat.plugins.redis/redis_memory\n"
        "    host: ${REDIS_HOST:-localhost}\n"
        "    port: ${REDIS_PORT:-6379}\n"
        "    db: ${REDIS_DB:-0}\n"
        "    key_prefix: runai_agent\n"
        "    embedder_name: nv-embedqa-e5-v5\n"
        "\n"
        "functions:"
    )
    if "memory:\n  redis_memory:" in content:
        raise SystemExit("Memory section already present. Aborting.")
    content = content.replace(old, new, 1)

    # 2. Extract initial_prompt body from current workflow
    prompt_start_marker = "  initial_prompt: |\n"
    prompt_end_marker = "    Always provide complete, runnable code with proper error handling and security best practices.\n"
    workflow_start = content.find("\nworkflow:")
    prompt_start = content.find(prompt_start_marker, workflow_start)
    prompt_content_start = prompt_start + len(prompt_start_marker)
    prompt_end = content.find(prompt_end_marker, prompt_content_start) + len(prompt_end_marker)
    prompt_body = content[prompt_content_start:prompt_end]

    # 3. Add runai_react_agent before embedders (with inlined prompt)
    embedders_start = content.find("\nembedders:")
    inner_agent = (
        "\n  runai_react_agent:\n"
        "    _type: react_agent\n"
        "    tool_names:\n"
        "    - runailabs_environment_info\n"
        "    - runai_submit_workload\n"
        "    - runai_submit_distributed_workload\n"
        "    - runai_submit_workspace\n"
        "    - runai_submit_batch\n"
        "    - runai_job_status\n"
        "    - runai_cluster_resources\n"
        "    - runai_manage_workload\n"
        "    - runai_proactive_monitor\n"
        "    - runai_failure_analyzer\n"
        "    - runai_job_analytics\n"
        "    - runai_template_executor\n"
        "    - runai_kubectl_troubleshoot\n"
        "    - runailabs_job_generator\n"
        "    - runai_nim_benchmark\n"
        "    - runai_docs_helper\n"
        "    - runai_docs_search\n"
        "    - runai_api_docs\n"
        "    llm_name: demo_llm\n"
        "    verbose: false\n"
        "    max_iterations: 15\n"
        "    max_tool_calls: 15\n"
        "    initial_prompt: |\n"
        + prompt_body
        + "\n"
    )
    content = content[:embedders_start] + inner_agent + content[embedders_start:]

    # 4. Replace workflow section (from "workflow:" through end of initial_prompt) with auto_memory_agent
    workflow_start = content.find("\nworkflow:")
    # End of workflow = end of prompt (same markers, but content moved so search after workflow_start)
    prompt_start = content.find(prompt_start_marker, workflow_start)
    prompt_end = content.find(prompt_end_marker, prompt_start + len(prompt_start_marker)) + len(prompt_end_marker)
    replace_end = prompt_end
    new_workflow = (
        "\nworkflow:\n"
        "  _type: auto_memory_agent\n"
        "  inner_agent_name: runai_react_agent\n"
        "  memory_name: redis_memory\n"
        "  llm_name: demo_llm\n"
        "  save_user_messages_to_memory: true\n"
        "  retrieve_memory_for_every_response: true\n"
        "  save_ai_messages_to_memory: true\n"
        "  search_params:\n"
        "    top_k: 5\n"
        "\n"
    )
    content = content[: workflow_start + 1] + new_workflow + content[replace_end:]

    with open(WORKFLOW_PATH, "w") as f:
        f.write(content)
    print("Added memory workflow for NAT 1.4 (redis_memory, runai_react_agent, auto_memory_agent).")
    print("If backend fails on redis_memory.embedder, change embedder_name to embedder in workflow.yaml.")


if __name__ == "__main__":
    main()
