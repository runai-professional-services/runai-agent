"""Run:AI environment information function"""

import os

from pydantic import Field
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

from ..utils import call_mcp_tool, logger


class RunailabsEnvironmentConfig(FunctionBaseConfig, name="runailabs_environment_info"):
    """Show RunaiLabs env info."""
    description: str = "Get cluster information and list available environments. Use to show cluster details or available environment templates."
    show_details: bool = Field(default=True, description="Show detailed info")


@register_function(config_type=RunailabsEnvironmentConfig)
async def runailabs_environment_info(config: RunailabsEnvironmentConfig, builder: Builder):
    """
    Show Run:AI environment information including available projects and cluster details.
    Queries the MCP server for live project data.
    """
    async def _response_fn(input_message: str) -> str:
        try:
            mcp_url = os.environ.get("MCP_SERVER_URL", "").rstrip("/")
            if not mcp_url:
                return (
                    "⚠️  **MCP Server Not Configured**\n\n"
                    "Set `MCP_SERVER_URL` to point to the mcp-server-runai endpoint "
                    "(e.g. `http://mcp-server-runai:8080`)."
                )

            logger.info("Querying MCP server for environment information...")
            projects_data = await call_mcp_tool(mcp_url, "list_projects", {})
            project_list = projects_data.get("projects", [])

            response = "🧪 RunaiLabs Environment ✅\n\n**Projects:**\n"

            if project_list:
                for project in project_list:
                    project_name = project.get("name", "Unknown")
                    project_id = project.get("id", "Unknown")
                    cluster_name = project.get("clusterName", "Unknown")

                    status = project.get("status", {})
                    namespace = status.get("namespace", f"runai-{project_name}")

                    gpu_quota = project.get("totalResources", {}).get("gpuQuota", 0)
                    if gpu_quota == 0:
                        resources = project.get("resources", [])
                        if resources and isinstance(resources, list) and len(resources) > 0:
                            gpu_quota = resources[0].get("gpu", {}).get("deserved", 0)

                    response += (
                        f"\n- **{project_name}**\n"
                        f"  - Project ID: {project_id}\n"
                        f"  - Namespace: {namespace}\n"
                        f"  - Cluster: {cluster_name}\n"
                        f"  - GPU Quota: {gpu_quota} GPU(s)\n"
                    )
            else:
                response += "- No projects found\n"

            response += (
                "\n**Available Capabilities (via MCP server):**\n"
                "✅ Training workloads (list, submit, suspend, resume, delete)\n"
                "✅ Inference workloads (list, submit, delete)\n"
                "✅ Workspace workloads (list, submit, delete)\n"
                "✅ Project and department management\n"
                "✅ Node pool information\n"
                "✅ Access rules and user management\n"
                "✅ Data source assets (PVC, NFS, S3, Git)\n"
            )

            if config.show_details:
                response += f"\n**MCP Server:** {mcp_url}\n"
                response += f"**Projects Found:** {len(project_list)}\n"

            return response

        except Exception as e:
            logger.error(f"Environment info error: {str(e)}")
            return f"❌ Error retrieving environment info: {str(e)}"

    try:
        yield FunctionInfo.create(
            single_fn=_response_fn,
            description="Get cluster information and list available environments. Use to show cluster details or available environment templates."
        )
    except GeneratorExit:
        logger.info("Env info exited")
    finally:
        logger.info("Cleaning up env info")
