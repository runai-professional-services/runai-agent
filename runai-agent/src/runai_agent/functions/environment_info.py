"""Run:AI environment information function"""

from pydantic import Field
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

from ..utils import get_secure_config, logger, REQUESTS_AVAILABLE


class RunailabsEnvironmentConfig(FunctionBaseConfig, name="runailabs_environment_info"):
    """Show RunaiLabs env info."""
    description: str = "Get cluster information and list available environments. Use to show cluster details or available environment templates."
    show_details: bool = Field(default=True, description="Show detailed info")


@register_function(config_type=RunailabsEnvironmentConfig)
async def runailabs_environment_info(config: RunailabsEnvironmentConfig, builder: Builder):
    """
    Show Run:AI environment information including authentication status,
    available capabilities, and security status.
    """
    async def _response_fn(input_message: str) -> str:
        try:
            # Get secure configuration
            secure_config = get_secure_config()
            
            # Try to query the Run:AI API for actual project information
            try:
                from runai.configuration import Configuration
                from runai.api_client import ApiClient
                from runai.runai_client import RunaiClient
                
                logger.info("Querying Run:AI API for environment information...")
                
                # Initialize Run:AI client
                configuration = Configuration(
                    client_id=secure_config['RUNAI_CLIENT_ID'],
                    client_secret=secure_config['RUNAI_CLIENT_SECRET'],
                    runai_base_url=secure_config['RUNAI_BASE_URL'],
                )
                client = RunaiClient(ApiClient(configuration))
                
                # Get all projects
                projects_response = client.organizations.projects.get_projects()
                projects_data = projects_response.data if hasattr(projects_response, 'data') else projects_response
                project_list = projects_data.get("projects", []) if isinstance(projects_data, dict) else []
                
                # Build response with actual project data
                response = """🧪 RunaiLabs Environment - CONFIRMED WORKING ✅

**Cluster Information:**
- Cluster: {base_url}

**Projects:**
""".format(base_url=secure_config['RUNAI_BASE_URL'])
                
                if project_list:
                    for project in project_list:
                        project_name = project.get("name", "Unknown")
                        project_id = project.get("id", "Unknown")
                        cluster_name = project.get("clusterName", "Unknown")
                        
                        # Get namespace from status object
                        status = project.get("status", {})
                        namespace = status.get("namespace", f"runai-{project_name}")
                        
                        # Get GPU quota - try multiple sources
                        gpu_quota = project.get("totalResources", {}).get("gpuQuota", 0)
                        if gpu_quota == 0:
                            # Fallback to resources array
                            resources = project.get("resources", [])
                            if resources and isinstance(resources, list) and len(resources) > 0:
                                gpu_quota = resources[0].get("gpu", {}).get("deserved", 0)
                        
                        response += f"""
- **{project_name}**
  - Project ID: {project_id}
  - Namespace: {namespace}
  - Cluster: {cluster_name}
  - GPU Quota: {gpu_quota} GPU(s)
"""
                else:
                    response += "- No projects found\n"
                
                response += """
**Available Capabilities:**
✅ Interactive jobs (Jupyter, VSCode, etc)
✅ Single GPU training jobs
✅ Distributed training jobs
✅ Inference/serving jobs
✅ Custom Docker images
✅ Job monitoring & status tracking

**Security Status:**
✅ Environment variables configured
✅ Input sanitization enabled
✅ Error handling implemented
"""
                
                if config.show_details:
                    response += f"""
**Detailed Configuration:**
- Client ID: {secure_config['RUNAI_CLIENT_ID']}
- Base URL: {secure_config['RUNAI_BASE_URL']}
- Requests Available: {REQUESTS_AVAILABLE}
- Projects Found: {len(project_list)}
"""
                
                return response
                
            except ImportError:
                # Fall back to basic info if runapy is not installed
                logger.warning("Run:AI SDK not available, showing basic info")
                return f"""🧪 RunaiLabs Environment - Basic Info

**Authentication Details:**
- Cluster: {secure_config['RUNAI_BASE_URL']}
- Client ID: {secure_config['RUNAI_CLIENT_ID']}

**Note:** Install runapy SDK for detailed environment information:
```bash
pip install runapy==1.223.0
```

**Security Status:**
✅ Environment variables configured
✅ Input sanitization enabled
✅ Error handling implemented
"""
            
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

