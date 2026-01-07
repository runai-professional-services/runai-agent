"""
Run:AI Workload Lifecycle Management
Unified function to suspend, resume, and delete workloads with safety validations
"""

import os
from typing import List, Literal
from pydantic import Field
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

from ..utils.helpers import _search_workload_by_name_helper, _get_secure_runai_config, logger

# Check if SDK is available
try:
    from runai.configuration import Configuration
    from runai.api_client import ApiClient
    from runai.runai_client import RunaiClient
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    logger.warning("Run:AI SDK not available - workload lifecycle management will be disabled")


class RunaiWorkloadLifecycleConfig(FunctionBaseConfig, name="runai_manage_workload"):
    """Configuration for Run:AI workload lifecycle management"""
    description: str = "Manage workload lifecycle (suspend/resume/delete jobs). Use for pausing, resuming, or removing training jobs and workspaces."
    allowed_projects: List[str] = Field(
        default_factory=lambda: ["*"],
        description="List of projects where workload management is allowed"
    )
    require_confirmation_for_delete: bool = Field(
        default=True,
        description="Require explicit confirmation before deleting workloads"
    )


@register_function(config_type=RunaiWorkloadLifecycleConfig)
async def runai_manage_workload(config: RunaiWorkloadLifecycleConfig, builder: Builder):
    """
    Manage Run:AI workload lifecycle: suspend, resume, or delete workloads.
    
    This unified function handles all lifecycle operations for Run:AI workloads
    including training jobs, workspaces, and distributed workloads.
    """
    
    async def _manage_workload(
        workload_name: str, 
        project: str, 
        action: Literal["suspend", "resume", "delete"],
        confirmed: bool = False
    ) -> str:
        """
        Manage a Run:AI workload lifecycle
        
        Args:
            workload_name: Name of the workload
            project: Project name where the workload exists
            action: Action to perform - "suspend", "resume", or "delete"
            confirmed: Whether user has confirmed the action (required for delete)
            
        Returns:
            Status message about the operation
        """
        
        action = action.lower().strip()
        logger.info(f"Request to {action} workload: {workload_name} in project: {project}")
        
        # Validation
        errors = []
        
        # Action validation
        valid_actions = ["suspend", "resume", "delete"]
        if action not in valid_actions:
            errors.append(f"Invalid action '{action}'. Must be one of: {', '.join(valid_actions)}")
        
        # Project whitelist (support wildcard "*")
        if "*" not in config.allowed_projects and project not in config.allowed_projects:
            errors.append(f"Project '{project}' not in allowed list: {config.allowed_projects}")
        
        # Name validation
        if not workload_name or not workload_name.strip():
            errors.append("Workload name cannot be empty")
        
        if errors:
            error_msg = "\n".join([f"  • {err}" for err in errors])
            return f"""
❌ **Workload Management Validation Failed**

{error_msg}

Please fix these issues and try again.
"""
        
        # Confirmation check for delete
        if action == "delete" and config.require_confirmation_for_delete and not confirmed:
            return f"""
⚠️  **Confirm Workload Deletion**

You are about to **permanently delete** the following workload:
- **Workload Name:** `{workload_name}`
- **Project:** `{project}`

**⚠️  This action cannot be undone. The workload and all its data will be permanently removed.**

To proceed, call this function again with `confirmed=True`.
"""
        
        # Check if SDK is available
        if not SDK_AVAILABLE:
            action_verb = {"suspend": "suspension", "resume": "resumption", "delete": "deletion"}[action]
            return f"""
⚠️  **Run:AI SDK Not Installed**

The Run:AI Python SDK is not available in this environment.
Workload {action_verb} has been validated but cannot be executed.

**Workload Details:**
- **Workload Name:** `{workload_name}`
- **Project:** `{project}`
- **Action:** `{action}`

**To enable actual workload management:**
```bash
pip install runapy
```
"""
        
        # Execute the action
        try:
            action_verb = {"suspend": "Suspending", "resume": "Resuming", "delete": "Deleting"}[action]
            logger.info(f"{action_verb} workload: {workload_name}")
            
            # Get secure configuration
            secure_config = _get_secure_runai_config()
            
            # Check if credentials are available
            if not all([secure_config['RUNAI_CLIENT_ID'], 
                       secure_config['RUNAI_CLIENT_SECRET'], 
                       secure_config['RUNAI_BASE_URL']]):
                return "❌ Error: Run:AI credentials not configured. Please set RUNAI_CLIENT_ID, RUNAI_CLIENT_SECRET, and RUNAI_BASE_URL environment variables."
            
            configuration = Configuration(
                client_id=secure_config['RUNAI_CLIENT_ID'],
                client_secret=secure_config['RUNAI_CLIENT_SECRET'],
                runai_base_url=secure_config['RUNAI_BASE_URL'],
            )
            
            client = RunaiClient(ApiClient(configuration))
            
            # Step 1: Find the workload by name
            workloads_response = client.workloads.workloads.get_workloads().data
            workload_list = workloads_response.get("workloads", [])
            
            workload = None
            for w in workload_list:
                if w.get("name") == workload_name and w.get("projectName") == project:
                    workload = w
                    logger.info(f"Found workload: {workload_name} in project {project}")
                    break
            
            if not workload:
                return f"""
❌ **Workload Not Found**

Could not find workload `{workload_name}` in project `{project}`.

Please check:
- Workload name is spelled correctly
- Workload exists in the specified project
- You have permission to view this workload
"""
            
            workload_id = workload.get("id")
            workload_type = workload.get("type", "").lower()
            
            logger.info(f"Found workload: {workload_name} (ID: {workload_id}, Type: {workload_type})")
            
            # Step 2: Execute the appropriate action based on workload type
            if action == "suspend":
                result = await _suspend_workload(client, workload_id, workload_type, workload_name, project)
            elif action == "resume":
                result = await _resume_workload(client, workload_id, workload_type, workload_name, project)
            elif action == "delete":
                result = await _delete_workload(client, workload_id, workload_type, workload_name, project)
            
            return result
            
        except Exception as e:
            logger.error(f"Error {action}ing workload: {e}")
            return f"""
❌ **Workload {action.title()} Failed**

An error occurred while trying to {action} the workload:

**Error:** {str(e)}

**Workload:** `{workload_name}`
**Project:** `{project}`
"""
    
    async def _suspend_workload(client, workload_id: str, workload_type: str, workload_name: str, project: str) -> str:
        """Suspend a workload based on its type"""
        try:
            if workload_type == "training":
                client.workloads.trainings.suspend_training(workload_id)
            elif workload_type == "workspace":
                # Workspaces don't have suspend - they can only be stopped (deleted)
                return f"""
⚠️  **Workspaces Cannot Be Suspended**

The workload `{workload_name}` is a workspace. Workspaces cannot be suspended, only stopped (deleted).

To stop this workspace, use the delete action instead:
```
runai_manage_workload(workload_name="{workload_name}", project="{project}", action="delete")
```
"""
            elif workload_type == "distributed":
                # Distributed workloads might not support suspend
                return f"""
⚠️  **Distributed Workloads Cannot Be Suspended**

The workload `{workload_name}` is a distributed training job. Distributed workloads typically cannot be suspended, only deleted.

To stop this workload, use the delete action instead.
"""
            else:
                return f"""
⚠️  **Unsupported Workload Type**

Cannot suspend workload of type: {workload_type}

Supported types for suspension: training
"""
            
            return f"""
✅ **Workload Suspended Successfully!**

**Workload ID:** {workload_id}
**Name:** {workload_name}
**Project:** {project}
**Type:** {workload_type}

The workload has been suspended. Resources have been released but the workload configuration is preserved.
You can resume it later using the resume action.
"""
        except Exception as e:
            raise Exception(f"Failed to suspend workload: {str(e)}")
    
    async def _resume_workload(client, workload_id: str, workload_type: str, workload_name: str, project: str) -> str:
        """Resume a workload based on its type"""
        try:
            if workload_type == "training":
                client.workloads.trainings.resume_training(workload_id)
            elif workload_type == "workspace":
                return f"""
⚠️  **Workspaces Cannot Be Resumed**

The workload `{workload_name}` is a workspace. Workspaces cannot be resumed.

To start a new workspace, submit a new workspace workload.
"""
            elif workload_type == "distributed":
                return f"""
⚠️  **Distributed Workloads Cannot Be Resumed**

The workload `{workload_name}` is a distributed training job. Distributed workloads cannot be resumed once stopped.

To restart training, submit a new distributed workload.
"""
            else:
                return f"""
⚠️  **Unsupported Workload Type**

Cannot resume workload of type: {workload_type}

Supported types for resumption: training
"""
            
            return f"""
✅ **Workload Resumed Successfully!**

**Workload ID:** {workload_id}
**Name:** {workload_name}
**Project:** {project}
**Type:** {workload_type}

The workload has been resumed and is now running again.
"""
        except Exception as e:
            raise Exception(f"Failed to resume workload: {str(e)}")
    
    async def _delete_workload(client, workload_id: str, workload_type: str, workload_name: str, project: str) -> str:
        """Delete a workload based on its type"""
        try:
            if workload_type == "training":
                client.workloads.trainings.delete_training(workload_id)
            elif workload_type == "workspace":
                client.workloads.workspaces.delete_workspace(workload_id)
            elif workload_type == "distributed":
                client.workloads.distributed.delete_distributed(workload_id)
            else:
                return f"""
⚠️  **Unsupported Workload Type**

Cannot delete workload of type: {workload_type}

Please contact support if you need to delete this workload.
"""
            
            return f"""
✅ **Workload Deleted Successfully!**

**Workload ID:** {workload_id}
**Name:** {workload_name}
**Project:** {project}
**Type:** {workload_type}

⚠️  The workload and all its data have been permanently removed.
This action cannot be undone.
"""
        except Exception as e:
            raise Exception(f"Failed to delete workload: {str(e)}")
    
    # Create and return the function info
    yield FunctionInfo.from_fn(
        _manage_workload,
        description=(
            "Manage workload lifecycle (suspend/resume/delete workloads). "
            "Use this tool to pause, resume, or remove training jobs and workspaces. "
            "\n\n"
            "Required parameters:\n"
            "- workload_name: Name of the job/workspace to manage (e.g., 'my-training-job')\n"
            "- project: Project name where the workload exists (e.g., 'my-project')\n"
            "- action: One of 'suspend', 'resume', or 'delete'\n"
            "- confirmed: Set to true for delete operations (default: false)\n"
            "\n"
            "Examples:\n"
            "- Delete job 'test-job' in project 'my-project': workload_name='test-job', project='my-project', action='delete', confirmed=true\n"
            "- Suspend job 'training-run': workload_name='training-run', project='ml-project', action='suspend'\n"
            "- Resume workspace 'jupyter-ws': workload_name='jupyter-ws', project='dev-project', action='resume'"
        )
    )
    
    # Cleanup
    logger.info("Cleaning up workload lifecycle manager")

