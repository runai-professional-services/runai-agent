"""Run:AI resource listing function — formats MCP list results as clean markdown."""

import os
from typing import Optional

from pydantic import Field
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

from ..utils import call_mcp_tool, logger


class RunaiListResourcesConfig(FunctionBaseConfig, name="runai_list_resources"):
    description: str = (
        "List any Run:AI resource and return a clean formatted summary. "
        "Use this for: 'list projects', 'show all projects', 'list departments', "
        "'list training jobs', 'show running jobs', 'list workspaces', "
        "'list inferences', 'show node pools', 'list users', 'list roles', "
        "'list PVCs', 'list datasources', 'list access rules'. "
        "Pass resource_type as one of: projects, departments, trainings, workspaces, "
        "inferences, node_pools, users, roles, pvcs, s3, nfs, git, access_rules. "
        "Optionally pass project to filter workloads/datasources by project."
    )


def _gpu_quota(project: dict) -> int:
    quota = project.get("totalResources", {}).get("gpuQuota", 0)
    if not quota:
        resources = project.get("resources", [])
        if resources and isinstance(resources, list):
            quota = resources[0].get("gpu", {}).get("deserved", 0)
    return quota or 0


def _gpu_in_use(project: dict) -> Optional[int]:
    """Try to extract current GPU usage from overtimeData."""
    overtime = project.get("overtimeData", {})
    if isinstance(overtime, dict):
        day = overtime.get("lastDay", {})
        if isinstance(day, dict):
            alloc = day.get("gpuAllocation")
            if alloc is not None:
                try:
                    return int(round(float(alloc)))
                except (TypeError, ValueError):
                    pass
    return None


def _unwrap(data, key: str) -> list:
    """Extract a list from MCP result whether it's a dict{key:[]} or a bare list."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return data.get(key, data.get("items", []))
    return []


def _format_projects(data: dict) -> str:
    projects = _unwrap(data, "projects")
    if not projects:
        return "No projects found."
    lines = [f"Found {len(projects)} project(s):"]
    for p in projects:
        name = p.get("name", "unknown")
        quota = _gpu_quota(p)
        in_use = _gpu_in_use(p)
        if in_use is not None and quota > 0:
            pct = int(round(in_use / quota * 100))
            lines.append(f"- **{name}**: {quota} GPU quota ({in_use} in use, {pct}% utilized)")
        elif in_use is not None:
            lines.append(f"- **{name}**: {quota} GPU quota ({in_use} in use)")
        else:
            lines.append(f"- **{name}**: {quota} GPU quota")
    return "\n".join(lines)


def _format_departments(data: dict) -> str:
    departments = _unwrap(data, "departments")
    if not departments:
        return "No departments found."
    lines = [f"Found {len(departments)} department(s):"]
    for d in departments:
        name = d.get("name", "unknown")
        resources = d.get("resources", [])
        gpu_quota = -1
        if resources and isinstance(resources, list):
            gpu_quota = resources[0].get("gpu", {}).get("deserved", -1)
        quota_str = "Unlimited" if gpu_quota == -1 else f"{gpu_quota} GPU quota"
        lines.append(f"- **{name}**: {quota_str}")
    return "\n".join(lines)


def _format_workloads(data: dict, kind: str) -> str:
    key_map = {"trainings": "trainings", "workspaces": "workspaces", "inferences": "inferences"}
    key = key_map.get(kind, kind)
    items = _unwrap(data, key)
    if not items:
        return f"No {kind} found."
    lines = [f"Found {len(items)} {kind}:"]
    for w in items:
        name = w.get("name", "unknown")
        project = w.get("projectName", w.get("project", ""))
        phase = w.get("actualPhase", w.get("phase", "Unknown"))
        spec = w.get("spec", {}) or {}
        compute = spec.get("compute", {}) or {}
        gpu = compute.get("gpuDevicesRequest") or compute.get("gpu_devices_request")
        if gpu is None:
            gpu = w.get("gpuDevices", w.get("gpu_devices", ""))
        gpu_str = f" | {gpu} GPU(s)" if gpu else ""
        project_str = f" ({project})" if project else ""
        lines.append(f"- **{name}**{project_str} — {phase}{gpu_str}")
    return "\n".join(lines)


def _format_node_pools(data: dict) -> str:
    pools = _unwrap(data, "nodePools")
    if not pools:
        return "No node pools found."
    lines = [f"Found {len(pools)} node pool(s):"]
    for p in pools:
        name = p.get("name", "unknown")
        gpu_type = p.get("gpuType", p.get("labelValue", ""))
        total = p.get("resources", {}).get("gpu", {}).get("total", "")
        available = p.get("resources", {}).get("gpu", {}).get("available", "")
        parts = [f"- **{name}**"]
        if gpu_type:
            parts.append(f"GPU type: {gpu_type}")
        if total != "":
            parts.append(f"{total} total GPUs")
        if available != "":
            parts.append(f"{available} available")
        lines.append(", ".join(parts) if len(parts) > 1 else parts[0])
    return "\n".join(lines)


def _format_users(data: dict) -> str:
    users = _unwrap(data, "users")
    if not users:
        return "No users found."
    lines = [f"Found {len(users)} user(s):"]
    for u in users:
        name = u.get("name", u.get("username", ""))
        email = u.get("email", "")
        display = f"**{name}**" if name else ""
        if email and email != name:
            display += f" ({email})"
        lines.append(f"- {display or 'unknown'}")
    return "\n".join(lines)


def _format_roles(data: dict) -> str:
    roles = _unwrap(data, "roles")
    if not roles:
        return "No roles found."
    lines = [f"Found {len(roles)} role(s):"]
    for i, r in enumerate(roles, 1):
        name = r.get("name", r.get("roleName", str(r)))
        lines.append(f"{i}. {name}")
    return "\n".join(lines)


def _format_datasources(data: dict, kind: str) -> str:
    key_map = {
        "pvcs": "pvcs",
        "s3": "s3Assets",
        "nfs": "nfsAssets",
        "git": "gitAssets",
    }
    key = key_map.get(kind, kind)
    items = _unwrap(data, key)
    if not items:
        return f"No {kind} datasources found."
    lines = [f"Found {len(items)} {kind} datasource(s):"]
    for item in items:
        name = item.get("name", "unknown")
        project = item.get("projectName", item.get("project", ""))
        scope = item.get("scope", "")
        project_str = f" ({project})" if project else (f" [{scope}]" if scope else "")
        lines.append(f"- **{name}**{project_str}")
    return "\n".join(lines)


def _format_access_rules(data: dict) -> str:
    rules = _unwrap(data, "accessRules")
    if not rules:
        return "No access rules found."
    lines = [f"Found {len(rules)} access rule(s):"]
    for r in rules:
        subject = r.get("subjectName", r.get("subject", "unknown"))
        role = r.get("roleName", r.get("role", ""))
        scope = r.get("scopeName", r.get("scope", ""))
        rule_id = r.get("accessRuleId", r.get("id", ""))
        parts = [f"- **{subject}**"]
        if role:
            parts.append(f"role: {role}")
        if scope:
            parts.append(f"scope: {scope}")
        if rule_id:
            parts.append(f"id: {rule_id}")
        lines.append(" | ".join(parts))
    return "\n".join(lines)


_TOOL_MAP = {
    "projects": "list_projects",
    "departments": "list_departments",
    "trainings": "list_trainings",
    "workspaces": "list_workspaces",
    "inferences": "list_inferences",
    "node_pools": "list_node_pools",
    "users": "list_users",
    "roles": "list_roles",
    "pvcs": "list_pvcs",
    "s3": "list_s3_assets",
    "nfs": "list_nfs_assets",
    "git": "list_git_assets",
    "access_rules": "list_access_rules",
}


@register_function(config_type=RunaiListResourcesConfig)
async def runai_list_resources(config: RunaiListResourcesConfig, builder: Builder):
    """List any Run:AI resource and return a clean formatted markdown summary."""

    async def _list_fn(
        resource_type: str,
        project: Optional[str] = None,
    ) -> str:
        resource_type = (resource_type or "").strip().lower()

        mcp_url = os.environ.get("MCP_SERVER_URL", "").rstrip("/")
        if not mcp_url:
            return "⚠️ MCP_SERVER_URL is not configured."

        if resource_type not in _TOOL_MAP:
            return (
                f"Unknown resource_type '{resource_type}'. "
                f"Valid values: {', '.join(sorted(_TOOL_MAP.keys()))}"
            )

        tool_name = _TOOL_MAP[resource_type]
        args = {}
        if project and resource_type in ("trainings", "workspaces", "inferences", "pvcs", "s3", "nfs", "git"):
            args["projectName"] = project

        try:
            logger.info(f"Listing {resource_type} via MCP tool '{tool_name}' args={args}")
            data = await call_mcp_tool(mcp_url, tool_name, args)
        except Exception as e:
            logger.error(f"MCP call failed for {tool_name}: {e}")
            return f"❌ Failed to list {resource_type}: {e}"

        if resource_type == "projects":
            return _format_projects(data)
        elif resource_type == "departments":
            return _format_departments(data)
        elif resource_type in ("trainings", "workspaces", "inferences"):
            return _format_workloads(data, resource_type)
        elif resource_type == "node_pools":
            return _format_node_pools(data)
        elif resource_type == "users":
            return _format_users(data)
        elif resource_type == "roles":
            return _format_roles(data)
        elif resource_type in ("pvcs", "s3", "nfs", "git"):
            return _format_datasources(data, resource_type)
        elif resource_type == "access_rules":
            return _format_access_rules(data)
        else:
            return str(data)

    try:
        yield FunctionInfo.from_fn(
            _list_fn,
            description=config.description,
        )
    except GeneratorExit:
        logger.info("list_resources exited")
    finally:
        logger.info("Cleaning up list_resources")
