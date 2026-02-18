#!/usr/bin/env python3
"""One-off script: add default_initial_prompt anchor, runai_react_agent function, and switch workflow to auto_memory_agent."""
import re

WORKFLOW_PATH = "configs/workflow.yaml"


def main():
    with open(WORKFLOW_PATH, "r") as f:
        content = f.read()

    # Find the workflow section and extract the initial_prompt block (from "  initial_prompt: |" to end of prompt)
    workflow_start = content.index("\nworkflow:")
    prompt_start_marker = "  initial_prompt: |\n"
    prompt_start = content.index(prompt_start_marker, workflow_start)
    prompt_content_start = prompt_start + len(prompt_start_marker)
    # End of prompt: last line that is part of the literal block (indented 4 spaces)
    # Find "Always provide complete, runnable code with proper error handling and security best practices."
    prompt_end_marker = "    Always provide complete, runnable code with proper error handling and security best practices.\n"
    prompt_end = content.index(prompt_end_marker, prompt_content_start) + len(prompt_end_marker)
    prompt_block = content[prompt_content_start:prompt_end]

    # Build default_initial_prompt anchor (insert after memory section, before functions)
    memory_section_end = content.index("\nfunctions:", content.index("\nmemory:"))
    anchor_block = (
        "\n# Shared prompt for runai_react_agent (used by auto_memory_agent)\n"
        "default_initial_prompt: &default_initial_prompt |\n"
        + prompt_block  # prompt_block is already indented (4 spaces per line)
    )
    content = content[:memory_section_end] + anchor_block + content[memory_section_end:]

    # Add runai_react_agent function (before embedders)
    embedders_start = content.index("\nembedders:")
    inner_agent_block = """
  runai_react_agent:
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
    initial_prompt: *default_initial_prompt
"""
    content = content[:embedders_start] + inner_agent_block + content[embedders_start:]

    # Replace workflow section: from "workflow:" through end of initial_prompt with auto_memory_agent
    # We need to find workflow start again (content changed)
    workflow_start = content.index("\nworkflow:")
    prompt_start = content.index(prompt_start_marker, workflow_start)
    prompt_content_start = prompt_start + len(prompt_start_marker)
    prompt_end = content.index(prompt_end_marker, prompt_content_start) + len(prompt_end_marker)
    # From start of "workflow:" through end of prompt
    replace_start = workflow_start + 1  # after the newline
    replace_end = prompt_end

    new_workflow = """workflow:
  _type: auto_memory_agent
  inner_agent_name: runai_react_agent
  memory_name: redis_memory
  llm_name: demo_llm
  save_user_messages_to_memory: true
  retrieve_memory_for_every_response: true
  save_ai_messages_to_memory: true
  search_params:
    top_k: 5

"""
    content = content[:replace_start] + new_workflow + content[replace_end:]

    with open(WORKFLOW_PATH, "w") as f:
        f.write(content)
    print("Updated workflow.yaml: added default_initial_prompt, runai_react_agent, and auto_memory_agent workflow.")


if __name__ == "__main__":
    main()
