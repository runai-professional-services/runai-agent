"""Run:AI job status checking function"""

import os
from typing import List
from pydantic import Field
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

from ..utils import _search_workload_by_name_helper, logger


class RunaiJobStatusConfig(FunctionBaseConfig, name="runai_job_status"):
    """Check status of Run:AI jobs for troubleshooting"""
    description: str = "Check the status of running/completed jobs. Use to get quick status updates for workloads."
    include_details: bool = Field(default=True, description="Include detailed status information")
    allowed_projects: List[str] = Field(default_factory=lambda: ["*"], description="Projects this function can access (use ['*'] for all)")


@register_function(config_type=RunaiJobStatusConfig)
async def runai_job_status(config: RunaiJobStatusConfig, builder: Builder):
    """
    Check the status of a Run:AI job and provide troubleshooting information.
    
    This function fetches job status from the Run:AI API and provides:
    - Current job state (Running, Failed, Pending, Completed, etc.)
    - Basic job information (GPUs, image, project)
    - Time information (created, started, duration)
    - Quick diagnosis for common issues
    """
    
    def get_secure_config():
        """Get Run:AI credentials from environment"""
        return {
            'RUNAI_CLIENT_ID': os.environ.get('RUNAI_CLIENT_ID', ''),
            'RUNAI_CLIENT_SECRET': os.environ.get('RUNAI_CLIENT_SECRET', ''),
            'RUNAI_BASE_URL': os.environ.get('RUNAI_BASE_URL', ''),
        }
    
    async def _status_fn(job_name: str) -> str:
        """Check status of a specific job
        
        Args:
            job_name: Either the job name (e.g., 'myjob') or workload UUID
        """
        
        secure_config = get_secure_config()
        
        # Check if credentials are available
        if not all([secure_config['RUNAI_CLIENT_ID'], 
                   secure_config['RUNAI_CLIENT_SECRET'],
                   secure_config['RUNAI_BASE_URL']]):
            return """
⚠️ **Run:AI Credentials Not Configured**

Cannot check job status without Run:AI API credentials.

**Required environment variables:**
- `RUNAI_CLIENT_ID`
- `RUNAI_CLIENT_SECRET`
- `RUNAI_BASE_URL`

**Alternative:** Use `kubectl get pods` to check pod status directly.
"""
        
        
        # Check if runapy SDK is available
        try:
            from runai import models
            logger.debug("✓ Run:AI SDK is available for status checks")
        except ImportError:
            return """
⚠️ **Run:AI SDK Not Available**

The runapy SDK is not installed. Install it with:

```bash
pip install runapy==1.223.0
```

**Alternative:** Use Run:AI CLI or kubectl to check job status.
"""
        
        try:
            from runai.configuration import Configuration
            from runai.api_client import ApiClient
            from runai.runai_client import RunaiClient
            
            logger.info(f"Checking status for job: {job_name}")
            
            # Initialize Run:AI client
            configuration = Configuration(
                client_id=secure_config['RUNAI_CLIENT_ID'],
                client_secret=secure_config['RUNAI_CLIENT_SECRET'],
                runai_base_url=secure_config['RUNAI_BASE_URL'],
            )
            client = RunaiClient(ApiClient(configuration))
            
            # Get all projects to find the job
            projects_response = client.organizations.projects.get_projects()
            projects_data = projects_response.data if hasattr(projects_response, 'data') else projects_response
            project_list = projects_data.get("projects", []) if isinstance(projects_data, dict) else []
            
            # Search for the job across projects
            job_found = None
            job_project = None
            job_type = None  # training, workspace, distributed, inference
            
            for project in project_list:
                project_name = project.get("name")
                project_id = project.get("id")
                cluster_id = project.get("clusterId")
                
                # Check if project is allowed (support wildcard "*")
                if "*" not in config.allowed_projects and project_name not in config.allowed_projects:
                    continue
                
                logger.info(f"Searching for job '{job_name}' in project: {project_name}")
                
                # Search for workload using API or kubectl
                workload_uuid, found_type = _search_workload_by_name_helper(client, job_name, project_id, cluster_id)
                
                if not workload_uuid:
                    # Check if job_name is already a UUID
                    if len(job_name) == 36 and job_name.count('-') == 4:
                        workload_uuid = job_name
                        found_type = None  # Will try all types
                        logger.info(f"Using provided UUID: {workload_uuid}")
                    else:
                        logger.debug(f"Could not find job '{job_name}' in {project_name}")
                        continue
                else:
                    logger.info(f"Found workload '{job_name}' with UUID: {workload_uuid}")
                
                # If we know the type, fetch it directly; otherwise try all types
                # Map API type names to internal type names
                type_mapping = {
                    'training': 'training',
                    'workspace': 'workspace', 
                    'distributed': 'distributed',
                    'distributedworkload': 'distributed',  # API might return this
                }
                
                normalized_type = type_mapping.get(found_type.lower() if found_type else None)
                types_to_try = [(normalized_type, None)] if normalized_type else [
                    ('training', lambda: client.workloads.trainings.get_training(workload_uuid)),
                    ('workspace', lambda: client.workloads.workspaces.get_workspace(workload_uuid)),
                    ('distributed', lambda: client.workloads.distributed.get_distributed(workload_uuid)),
                ]
                
                for wtype, get_fn in types_to_try:
                    try:
                        # If we already know the type, fetch it directly
                        if normalized_type:
                            if wtype == 'training':
                                response = client.workloads.trainings.get_training(workload_uuid)
                            elif wtype == 'workspace':
                                response = client.workloads.workspaces.get_workspace(workload_uuid)
                            elif wtype == 'distributed':
                                response = client.workloads.distributed.get_distributed(workload_uuid)
                            else:
                                continue
                        else:
                            response = get_fn()
                        
                        workload_data = response.data if hasattr(response, 'data') else response
                        
                        if workload_data:
                            logger.info(f"✓ Found job '{job_name}' (UUID: {workload_uuid}) as {wtype} workload")
                            job_found = workload_data
                            job_project = project_name
                            job_type = wtype
                            break
                    except Exception as e:
                        error_msg = str(e)
                        # Check if it's a 404 (not found) vs other errors
                        if "404" in error_msg or "not found" in error_msg.lower():
                            logger.debug(f"Workload {workload_uuid} not found as {wtype}")
                        else:
                            logger.warning(f"Error checking {wtype} workload {workload_uuid}: {error_msg}")
                        continue
                
                if job_found:
                    break
            
            if not job_found:
                # List available projects for user
                available_projects = [p.get("name") for p in project_list if p.get("name") in config.allowed_projects]
                
                return f"""
❌ **Job Not Found: `{job_name}`**

The job was not found in any accessible projects.

**Searched projects:**
{chr(10).join(f"  • {name}" for name in available_projects)}

**Possible reasons:**
1. Job name is incorrect (check spelling)
2. Job was deleted or completed long ago
3. Job is in a different project you don't have access to

**Tip:** List all jobs with `kubectl get pods -n runai-<project>` or check the Run:AI UI.
"""
            
            # Extract status information from workload data
            # The Run:AI API uses 'actualPhase' for current status
            actual_phase = job_found.get("actualPhase", "Unknown")
            desired_phase = job_found.get("desiredPhase", "N/A")
            
            # Get additional info
            created_at = job_found.get("createdAt", "N/A")
            created_by = job_found.get("createdBy", "N/A")
            workload_id = job_found.get("workloadId", "N/A")
            
            # Get spec information
            spec = job_found.get("spec", {})
            image = spec.get("image", "N/A") if isinstance(spec, dict) else "N/A"
            
            # Get compute resources
            compute = spec.get("compute", {}) if isinstance(spec, dict) else {}
            gpu_request = compute.get("gpuDevicesRequest", "N/A") if isinstance(compute, dict) else "N/A"
            cpu_request = compute.get("cpuCoreRequest", "N/A") if isinstance(compute, dict) else "N/A"
            memory_request = compute.get("cpuMemoryRequest", "N/A") if isinstance(compute, dict) else "N/A"
            
            # Determine status emoji and message based on actualPhase
            status_emoji = {
                "Running": "🟢",
                "Completed": "✅",
                "Failed": "❌",
                "Pending": "🟡",
                "Initializing": "🔄",
                "Succeeded": "✅",
                "Stopped": "🛑",
                "Error": "❌",
                "Deleting": "🗑️",
            }.get(actual_phase, "⚪")
            
            response = f"""
{status_emoji} **Job Status: `{job_name}`**

**Project:** {job_project}
**Type:** {job_type.capitalize()} Workload
**Current Status:** {actual_phase}
**Desired Status:** {desired_phase}
**Image:** {image}
**Resources:**
  - GPUs: {gpu_request}
  - CPU: {cpu_request} cores
  - Memory: {memory_request}
**Created:** {created_at}
**Created By:** {created_by}

"""
            
            # Add status-specific information and tips
            if actual_phase == "Running":
                response += f"""
**Status:** Job is currently running ✓

**Quick checks:**
- Monitor progress in Run:AI UI
- Check logs: `kubectl logs -n runai-{job_project} -l workloadName={job_name}`
- View GPU utilization in cluster dashboard

**Tip:** If job seems stuck, check logs for errors.
"""
            
            elif actual_phase == "Initializing":
                response += f"""
**Status:** Job is starting up 🔄

**This means:**
- Kubernetes is scheduling the pod
- Container image is being pulled
- Resources are being allocated

**Next steps:**
- Wait a few minutes for initialization
- If stuck >5 minutes, check events: `kubectl describe pod -n runai-{job_project} -l workloadName={job_name}`

**Common initialization issues:**
- `ImagePullBackOff` → Image not found or no registry access
- `Pending` → Waiting for GPU resources
"""
            
            elif actual_phase in ["Failed", "Error"]:
                response += f"""
**Status:** Job has failed ⚠️

**Next steps:**
1. Check pod logs for error messages
2. Common issues:
   - Out of Memory (OOM)
   - Image pull errors
   - Configuration problems
   
**Get logs:**
```bash
kubectl logs -n runai-{job_project} -l workloadName={job_name}
```

**Common error patterns to look for:**
- `OOMKilled` → Increase memory or reduce batch size
- `ImagePullBackOff` → Check image name: `{image}`
- `CrashLoopBackOff` → Check command/entrypoint
"""
            
            elif actual_phase == "Pending":
                response += f"""
**Status:** Job is waiting to start

**Common reasons:**
- Waiting for {gpu_request} GPU(s) to become available
- Image being pulled
- Node scheduling constraints

**Next steps:**
1. Check cluster capacity in Run:AI UI
2. View events: `kubectl describe pod -n runai-{job_project} -l workloadName={job_name}`
3. Consider reducing GPU request from {gpu_request} if waiting too long

**Tip:** If pending >10 minutes, there might be insufficient cluster resources.
"""
            
            elif actual_phase in ["Completed", "Succeeded"]:
                response += """
**Status:** Job completed successfully! ✅

**Next steps:**
- Check output/results in your workspace
- View final logs if needed
- Clean up resources if no longer needed

**Tip:** Successful jobs are automatically cleaned up after retention period.
"""
            
            elif actual_phase == "Stopped":
                response += """
**Status:** Job has been stopped 🛑

**This could mean:**
- Job was manually stopped by user
- Job was preempted by higher priority workload
- Job reached its runtime limit

**To investigate:** Check Run:AI UI for stop reason
"""
            
            elif actual_phase == "Deleting":
                response += """
**Status:** Job is being deleted 🗑️

**This means:**
- Resources are being cleaned up
- Job will be removed shortly

**Note:** This is a normal shutdown process.
"""
            
            else:
                response += f"""
**Status:** {actual_phase}

**Note:** This is an uncommon status. Check the Run:AI UI or use kubectl for more details.

**Get more info:**
```bash
kubectl get pods -n runai-{job_project} -l workloadName={job_name}
kubectl describe pod -n runai-{job_project} -l workloadName={job_name}
```
"""
            
            return response
            
        except Exception as e:
            logger.error(f"Error checking job status: {str(e)}")
            return f"""
❌ **Error Checking Job Status**

**Job:** `{job_name}`
**Error:** {str(e)}

**Troubleshooting:**
1. Verify Run:AI credentials are correct
2. Check if you have permission to access this project
3. Try using Run:AI CLI: `runai list jobs`
4. Check Run:AI UI for job status

**API Error:** {type(e).__name__}
"""
    
    try:
        yield FunctionInfo.create(
            single_fn=_status_fn,
            description="Check the status of running/completed jobs. Use to get quick status updates for workloads."
        )
    except GeneratorExit:
        logger.info("Job status checker exited")
    finally:
        logger.info("Cleaning up job status checker")

