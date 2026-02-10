"""Cluster resource summary: GPU quota and usage across projects."""

import os
from typing import List
from pydantic import Field
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

from ..utils import get_secure_config, logger


class RunaiClusterResourcesConfig(FunctionBaseConfig, name="runai_cluster_resources"):
    """Configuration for cluster resource summary."""
    description: str = (
        "Show cluster resource summary: GPU quota and GPU in use per project, plus cluster totals. "
        "Use when the user asks 'How is my cluster doing?', 'How many GPUs are in use?', "
        "'Cluster capacity', 'GPU utilization', or 'Which projects use the most GPUs?'"
    )
    allowed_projects: List[str] = Field(
        default_factory=lambda: ["*"],
        description="Projects to include (use ['*'] for all)",
    )
    max_projects: int = Field(default=100, description="Maximum number of projects to include in the table")


def _gpu_quota(project: dict) -> float:
    """Extract GPU quota from project (totalResources or resources[].gpu.deserved)."""
    quota = project.get("totalResources", {}).get("gpuQuota")
    if quota is not None and quota != 0:
        return float(quota)
    resources = project.get("resources", [])
    if resources and isinstance(resources, list) and len(resources) > 0:
        deserved = resources[0].get("gpu", {}).get("deserved")
        if deserved is not None:
            return float(deserved)
    return 0.0


def _gpu_allocated(project: dict) -> float:
    """Extract GPU allocated (in use) from project status.quotaStatus."""
    status = project.get("status") or {}
    quota_status = status.get("quotaStatus") or {}
    allocated = quota_status.get("allocated") or {}
    gpu = allocated.get("gpu")
    if gpu is not None:
        return float(gpu)
    return 0.0


def _gpu_requested(project: dict) -> float:
    """Extract GPU requested from project status.quotaStatus."""
    status = project.get("status") or {}
    quota_status = status.get("quotaStatus") or {}
    requested = quota_status.get("requested") or {}
    gpu = requested.get("gpu")
    if gpu is not None:
        return float(gpu)
    return 0.0


def _cpu_quota(project: dict) -> float:
    """Extract CPU quota from project totalResources (millicores)."""
    quota = project.get("totalResources", {}).get("cpuQuota")
    if quota is not None:
        return float(quota)
    return 0.0


def _cpu_allocated(project: dict) -> float:
    """Extract CPU allocated from project status.quotaStatus (millicores)."""
    status = project.get("status") or {}
    allocated = (status.get("quotaStatus") or {}).get("allocated") or {}
    cpu = allocated.get("cpu")
    if cpu is not None:
        return float(cpu)
    return 0.0


def _memory_quota(project: dict) -> float:
    """Extract memory quota from project totalResources (MB)."""
    quota = project.get("totalResources", {}).get("memoryQuota")
    if quota is not None:
        return float(quota)
    return 0.0


def _memory_allocated(project: dict) -> float:
    """Extract memory allocated from project status.quotaStatus (MB)."""
    status = project.get("status") or {}
    allocated = (status.get("quotaStatus") or {}).get("allocated") or {}
    mem = allocated.get("memory")
    if mem is not None:
        return float(mem)
    return 0.0


# Number of projects to list in "Top N by GPU usage"
TOP_N_GPU_USAGE = 3


@register_function(config_type=RunaiClusterResourcesConfig)
async def runai_cluster_resources(config: RunaiClusterResourcesConfig, builder: Builder):
    """
    Return a cluster resource summary: GPU quota and GPU in use per project,
    plus cluster-wide totals. Uses Run:AI Projects API (status.quotaStatus).
    """
    def get_secure_config() -> dict:
        return {
            "RUNAI_CLIENT_ID": os.environ.get("RUNAI_CLIENT_ID", ""),
            "RUNAI_CLIENT_SECRET": os.environ.get("RUNAI_CLIENT_SECRET", ""),
            "RUNAI_BASE_URL": os.environ.get("RUNAI_BASE_URL", ""),
        }

    async def _summary_fn(input_message: str = "") -> str:
        """
        Build cluster resource summary (quota and in-use per project, cluster totals).
        If input_message is a non-empty string, treat it as an optional project name to filter to one project.

        Args:
            input_message: Optional; if provided, show only that project. Otherwise show all (up to max_projects).

        Returns:
            Markdown summary string.
        """
        project = (input_message or "").strip() or None
        secure_config = get_secure_config()
        if not all([
            secure_config["RUNAI_CLIENT_ID"],
            secure_config["RUNAI_CLIENT_SECRET"],
            secure_config["RUNAI_BASE_URL"],
        ]):
            return """
⚠️ **Run:AI Credentials Not Configured**

Cannot show cluster resources without Run:AI API credentials.

**Required environment variables:**
- `RUNAI_CLIENT_ID`
- `RUNAI_CLIENT_SECRET`
- `RUNAI_BASE_URL`
"""

        try:
            from runai.configuration import Configuration
            from runai.api_client import ApiClient
            from runai.runai_client import RunaiClient
        except ImportError:
            return """
⚠️ **Run:AI SDK Not Available**

Install dependencies: `pip install runapy==1.223.0`
"""

        try:
            configuration = Configuration(
                client_id=secure_config["RUNAI_CLIENT_ID"],
                client_secret=secure_config["RUNAI_CLIENT_SECRET"],
                runai_base_url=secure_config["RUNAI_BASE_URL"],
            )
            client = RunaiClient(ApiClient(configuration))
            projects_response = client.organizations.projects.get_projects()
            projects_data = projects_response.data if hasattr(projects_response, "data") else projects_response
            project_list = projects_data.get("projects", []) if isinstance(projects_data, dict) else []

            if not project_list:
                return """
📊 **Cluster Resource Summary**

No projects found. Cluster may have no projects yet, or credentials may not have access to list projects.

**Next steps (example prompts):**
- "Can you create a project named [name] with [N] GPU quota?"
- Check cluster access and Run:AI credentials
"""

            # Filter by project name if specified
            if project and project.strip():
                want = project.strip()
                project_list = [p for p in project_list if (p.get("name") or "").strip() == want]
                if not project_list:
                    return f"""
📊 **Cluster Resource Summary**

No project named **{want}** found.

**Next steps (example prompts):**
- Check project name spelling and case
- "Show me all projects"
"""

            # Apply allowed_projects
            if "*" not in config.allowed_projects:
                allowed_set = set(config.allowed_projects)
                project_list = [p for p in project_list if (p.get("name") or "") in allowed_set]

            # Cap at max_projects
            truncated = False
            if len(project_list) > config.max_projects:
                project_list = project_list[: config.max_projects]
                truncated = True

            # Build per-project rows and cluster totals (GPU + optional CPU/memory)
            total_gpu_q = 0.0
            total_gpu_a = 0.0
            total_cpu_q = 0.0
            total_cpu_a = 0.0
            total_mem_q = 0.0
            total_mem_a = 0.0
            rows = []

            for p in project_list:
                name = (p.get("name") or "unknown").strip()
                gq = _gpu_quota(p)
                ga = _gpu_allocated(p)
                cq = _cpu_quota(p)
                ca = _cpu_allocated(p)
                mq = _memory_quota(p)
                ma = _memory_allocated(p)
                total_gpu_q += gq
                total_gpu_a += ga
                total_cpu_q += cq
                total_cpu_a += ca
                total_mem_q += mq
                total_mem_a += ma
                # GPU utilization
                if gq > 0:
                    gpu_util = f"{round(100.0 * ga / gq, 1)}%"
                else:
                    gpu_util = "—" if ga == 0 else "over"
                # CPU utilization (only if quota set)
                if cq > 0:
                    cpu_util = f"{round(100.0 * ca / cq, 1)}%"
                else:
                    cpu_util = "—"
                if mq > 0:
                    mem_util = f"{round(100.0 * ma / mq, 1)}%"
                else:
                    mem_util = "—"
                over_quota = gq > 0 and ga > gq
                rows.append((name, gq, ga, gpu_util, cq, ca, cpu_util, mq, ma, mem_util, over_quota))

            # Sort by GPU allocated descending so "who uses most" is at top
            rows.sort(key=lambda r: (r[2], r[1]), reverse=True)

            show_cpu = total_cpu_q > 0
            show_memory = total_mem_q > 0

            base_url = secure_config["RUNAI_BASE_URL"]
            cluster_line = (
                f"**Cluster total:** {total_gpu_a:.0f} GPU(s) in use / {total_gpu_q:.0f} GPU(s) quota"
            )
            if total_gpu_q > 0:
                cluster_pct = round(100.0 * total_gpu_a / total_gpu_q, 1)
                cluster_line += f" ({cluster_pct}% utilization)"
            if show_cpu:
                cluster_line += f" | CPU: {total_cpu_a:.0f} / {total_cpu_q:.0f} millicores"
            if show_memory:
                cluster_line += f" | Memory: {total_mem_a:.0f} / {total_mem_q:.0f} MB"
            cluster_line += "\n"

            # Top N by GPU usage
            top_n = rows[:TOP_N_GPU_USAGE]
            top_parts = [f"**{name}** ({ga:.0f})" for name, gq, ga, *_ in top_n if ga > 0]
            if not top_parts:
                top_parts = ["(none in use)"]
            top_line = f"**Top {min(TOP_N_GPU_USAGE, len(rows))} by GPU usage:** " + ", ".join(top_parts) + "\n\n"

            # Over-quota projects note
            over_quota_projects = [r[0] for r in rows if r[10]]
            over_quota_line = ""
            if over_quota_projects:
                over_quota_line = f"⚠️ **Over quota:** {', '.join(over_quota_projects)} (GPU in use > GPU quota)\n\n"

            # Table header and rows
            table_header = "| Project | GPU Quota | GPU In Use | GPU Util |"
            table_sep = "|---------|-----------|------------|----------|"
            if show_cpu:
                table_header += " CPU (mc) Quota | CPU (mc) In Use | CPU Util |"
                table_sep += "----------------|-----------------|----------|"
            if show_memory:
                table_header += " Mem (MB) Quota | Mem (MB) In Use | Mem Util |"
                table_sep += "----------------|-----------------|----------|"
            table_header += " Note |"
            table_sep += "------|"
            table = table_header + "\n" + table_sep + "\n"
            for r in rows:
                name, gq, ga, gpu_util, cq, ca, cpu_util, mq, ma, mem_util, over_quota = r
                note = "⚠️ Over quota" if over_quota else "—"
                line = f"| {name} | {gq:.0f} | {ga:.0f} | {gpu_util} |"
                if show_cpu:
                    line += f" {cq:.0f} | {ca:.0f} | {cpu_util} |"
                if show_memory:
                    line += f" {mq:.0f} | {ma:.0f} | {mem_util} |"
                line += f" {note} |\n"
                table += line

            response = f"""
📊 **Cluster Resource Summary**

**Cluster:** {base_url}

{cluster_line}
{top_line}
{over_quota_line}
**By project:**
{table}
"""
            if truncated:
                response += f"\n_Showing first {config.max_projects} projects; total project count is higher._\n"

            response += """
**Next steps (example prompts):**
- "Can you show me job status for [project name]?"
- "Show me job performance analytics"
"""
            return response.strip()

        except Exception as e:
            logger.error(f"Cluster resources error: {str(e)}")
            return f"""
❌ **Error Building Cluster Summary**

**Error:** {str(e)}

**Troubleshooting:**
1. Verify Run:AI credentials and base URL
2. Ensure the Run:AI API is reachable
3. Check logs for details
"""

    try:
        yield FunctionInfo.create(
            single_fn=_summary_fn,
            description=config.description,
        )
    except GeneratorExit:
        logger.info("Cluster resources exited")
    finally:
        logger.info("Cleaning up cluster resources")
