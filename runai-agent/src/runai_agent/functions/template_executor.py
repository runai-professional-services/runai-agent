"""
Template-Based Run:AI API Executor

Replaces LLM-driven code generation with deterministic Jinja2 templates.
Provides consistent, fast datasource and project management.
"""

import os
from typing import List, Optional
from pydantic import Field
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

from ..template_manager import TemplateManager
from ..utils.helpers import _get_secure_runai_config, logger


class RunaiTemplateExecutorConfig(FunctionBaseConfig, name="runai_template_executor"):
    """Configuration for Template-Based Executor"""
    description: str = (
        "Manage datasources and projects using templates (NFS, PVC, Git, S3, HostPath + project create/list/delete). "
        "Fast, deterministic, and consistent operations."
    )
    allowed_projects: List[str] = Field(
        default_factory=lambda: ["*"],
        description="List of projects where execution is allowed ('*' = all)"
    )
    require_confirmation: bool = Field(
        default=True,
        description="Require explicit confirmation before executing operations"
    )
    dry_run_default: bool = Field(
        default=True,
        description="Show generated code by default before execution"
    )
    allowed_resource_types: List[str] = Field(
        default_factory=lambda: ["nfs", "pvc", "git", "s3", "hostpath", "host-path", "project", "department"],
        description="List of resource types that can be managed"
    )
    debug_mode: bool = Field(
        default=False,
        description="Enable verbose debug logging to see all parameters and API calls"
    )


@register_function(config_type=RunaiTemplateExecutorConfig)
async def runai_template_executor(config: RunaiTemplateExecutorConfig, builder: Builder):
    """
    Manage datasources and projects using deterministic templates.
    
    Supports:
    - Datasources: NFS, PVC, Git, S3, HostPath (create/list/delete)
    - Projects: Create with GPU quotas, list, delete
    - Departments: Create with GPU quotas, list, delete
    """
    
    # Initialize template manager
    template_manager = TemplateManager()
    
    # Check for debug mode override from environment variable
    debug_mode_override = os.getenv('RUNAI_TEMPLATE_DEBUG', '').lower() in ('true', '1', 'yes', 'on')
    effective_debug_mode = debug_mode_override or config.debug_mode
    
    if debug_mode_override:
        logger.info("🔍 DEBUG MODE enabled via RUNAI_TEMPLATE_DEBUG environment variable")
    elif effective_debug_mode:
        logger.info("🔍 DEBUG MODE enabled via configuration")
    
    async def _execute_template_operation(
        action: str,
        resource_type: str = "nfs",
        project: str = "",
        resource_name: str = "",
        name: str = "",  # Alias for resource_name
        server: str = "",
        path: str = "",
        size: str = "",
        repository: str = "",
        branch: str = "",
        bucket: str = "",
        endpoint: str = "",
        storage_class: str = "",
        gpu_quota: int = 0,
        department_id: Optional[int] = None,
        dry_run: bool = None,
        confirmed: bool = False
    ) -> str:
        """
        Execute a Run:AI API operation using templates
        
        Args:
            action: Action to perform (create, delete, list)
            resource_type: Type of resource (nfs, pvc, git, s3, project, etc.)
            project: Project name (required for datasources)
            resource_name or name: Name of the resource
            server: NFS server address
            path: Path (NFS, Git, HostPath)
            size: Storage size (PVC) or GPU quota (Project)
            repository: Git repository URL
            branch: Git branch name
            bucket: S3 bucket name
            endpoint: S3 endpoint URL
            storage_class: Storage class for PVC
            gpu_quota: GPU quota for projects/departments
            department_id: Department ID for project creation
            dry_run: If True, show generated code without executing
            confirmed: If True, execute the operation
            
        Returns:
            Status message with operation results or generated code
        """
        
        # === DEBUG MODE ===
        if effective_debug_mode:
            logger.info("=" * 80)
            logger.info("🔍 DEBUG MODE ENABLED - Template Executor Call")
            logger.info("=" * 80)
            logger.info(f"Action: {action}")
            logger.info(f"Resource Type: {resource_type}")
            logger.info(f"Resource Name: {resource_name or name}")
            logger.info(f"Project: {project}")
            logger.info(f"Parameters: dry_run={dry_run}, confirmed={confirmed}")
            logger.info(f"Config: require_confirmation={config.require_confirmation}, dry_run_default={config.dry_run_default}")
            logger.info(f"Additional params: server={server}, path={path}, size={size}, repository={repository}, branch={branch}")
            logger.info("=" * 80)
        else:
            logger.info(f"Template Executor: {action} {resource_type} in project {project}")
            logger.info(f"Parameters: dry_run={dry_run}, confirmed={confirmed}, require_confirmation={config.require_confirmation}")
        
        # SECURITY: Prevent agents from bypassing confirmation by passing confirmed=True without dry_run=False
        # If confirmed=True but dry_run is not explicitly False, reset confirmed to False
        if confirmed and dry_run != False:
            logger.warning(f"⚠️  SECURITY: Ignoring confirmed=True because dry_run={dry_run} (must be explicitly False to confirm)")
            confirmed = False
        
        # Use 'name' if 'resource_name' is empty
        if not resource_name and name:
            resource_name = name
        
        # Normalize resource type
        resource_type = resource_type.lower().replace("-", "")
        
        # === VALIDATION ===
        errors = []
        
        # Resource type validation
        if "*" not in config.allowed_resource_types and resource_type not in config.allowed_resource_types:
            errors.append(f"Resource type '{resource_type}' not allowed. Supported: {config.allowed_resource_types}")
        
        # Project validation (skip for project/department creation)
        if (resource_type not in ["project", "department"] and project and 
            "*" not in config.allowed_projects and 
            project not in config.allowed_projects):
            errors.append(f"Project '{project}' not in allowed list: {config.allowed_projects}")
        
        # Action-specific validation
        if action in ["create", "delete"]:
            if not resource_name or not resource_name.strip():
                errors.append(f"resource_name is required for {action} operations")
        
        if action == "create":
            if resource_type == "nfs":
                if not server or not server.strip():
                    errors.append("server is required for NFS creation")
                if not path or not path.strip():
                    errors.append("path is required for NFS creation")
            elif resource_type == "pvc":
                if not size or not size.strip():
                    errors.append("size is required for PVC creation (e.g., '10Gi', '100Gi')")
            elif resource_type == "git":
                if not repository or not repository.strip():
                    errors.append("repository is required for Git creation")
                if not branch or not branch.strip():
                    errors.append("branch is required for Git creation")
            elif resource_type == "s3":
                if not bucket or not bucket.strip():
                    errors.append("bucket is required for S3 creation")
            elif resource_type in ["project", "department"]:
                # Projects and departments need at least a name
                pass
        
        if errors:
            error_msg = "\n".join([f"  • {err}" for err in errors])
            return f"""
❌ **Template Executor Validation Failed**

{error_msg}

Please fix these issues and try again.
"""
        
        # Determine dry-run mode
        # READ-ONLY operations (list, get) should never require dry-run or confirmation
        read_only_actions = ['list', 'get']
        if action in read_only_actions:
            is_dry_run = False
            confirmed = True  # Auto-confirm read-only operations
        else:
            is_dry_run = dry_run if dry_run is not None else config.dry_run_default
        
        # === CONFIRMATION FLOW ===
        if config.require_confirmation and not is_dry_run and not confirmed and action not in read_only_actions:
            return f"""
🛑 **CONFIRMATION REQUIRED - NO ACTION TAKEN YET**

**Operation Details:**
- **Resource Type:** {resource_type}
- **Action:** {action}
- **Project:** {project or 'N/A'}
{f"- **Resource Name:** {resource_name}" if resource_name else ""}

⚠️  **IMPORTANT:** This operation has NOT been executed yet. Confirmation is required.

**Next Steps:**
1. To preview the generated code first: Call again with `dry_run=True`
2. To execute this operation: Call again with `confirmed=True` and `dry_run=False`

**Example:** 
- Dry run: `runai_template_executor(action="{action}", resource_type="{resource_type}", resource_name="{resource_name}", project="{project}", dry_run=True)`
- Execute: `runai_template_executor(action="{action}", resource_type="{resource_type}", resource_name="{resource_name}", project="{project}", confirmed=True, dry_run=False)`
"""
        
        # === TEMPLATE RENDERING ===
        try:
            # Get credentials
            secure_config = _get_secure_runai_config()
            
            # Prepare template variables
            template_vars = {
                'name': resource_name,
                'project': project,
                'server': server,
                'path': path,
                'size': size,
                'repository': repository,
                'branch': branch,
                'bucket': bucket,
                'endpoint': endpoint,
                'storage_class': storage_class,
                'gpu_quota': gpu_quota or size,  # size can be GPU quota for projects
                'department_id': department_id
            }
            
            # Render template
            code = template_manager.render(resource_type, action, **template_vars)
            
            # DRY RUN: Show code without executing
            if is_dry_run:
                return f"""
🔍 **DRY RUN - NO ACTION TAKEN**

⚠️  **IMPORTANT:** This is a preview only. The {resource_type} has NOT been {action}d yet.

The template system has generated the following code that WOULD be executed:

```python
{code}
```

**To execute this operation:**
Call the function again with BOTH:
- `dry_run=False`
- `confirmed=True`

**This code was generated from templates** - deterministic and consistent.
"""
            
            # === EXECUTION ===
            logger.info(f"Executing template for {action} {resource_type}")
            
            # Prepare execution context
            exec_context = {
                'base_url': secure_config['RUNAI_BASE_URL'],
                'client_id': secure_config['RUNAI_CLIENT_ID'],
                'client_secret': secure_config['RUNAI_CLIENT_SECRET']
            }
            
            if effective_debug_mode:
                logger.info("=" * 80)
                logger.info("🔧 DEBUG: Executing Template")
                logger.info("=" * 80)
                logger.info(f"Base URL: {exec_context['base_url']}")
                logger.info(f"Template Variables:")
                logger.info(f"  - name: {resource_name}")
                logger.info(f"  - project: {project}")
                logger.info(f"  - server: {server}")
                logger.info(f"  - path: {path}")
                logger.info(f"  - size: {size}")
                logger.info(f"Generated Code (first 500 chars):")
                logger.info(code[:500] + "..." if len(code) > 500 else code)
                logger.info("=" * 80)
            
            # Execute the code
            result = template_manager.execute(code, exec_context)
            
            if effective_debug_mode:
                logger.info("=" * 80)
                logger.info("✅ DEBUG: Execution Result")
                logger.info("=" * 80)
                logger.info(f"Result: {result}")
                logger.info("=" * 80)
            
            # Format success response
            if action == "create":
                return f"""
✅ **{resource_type.upper()} Created Successfully!**

**Name:** {resource_name}
{f"**Project:** {project}" if project else ""}
{f"**Server:** {server}" if server else ""}
{f"**Path:** {path}" if path else ""}
{f"**Size:** {size}" if size else ""}
{f"**Repository:** {repository}" if repository else ""}
{f"**GPU Quota:** {gpu_quota}" if gpu_quota else ""}

**Response:** {result}
"""
            elif action == "delete":
                return f"""
✅ **{resource_type.upper()} Deleted Successfully!**

**Name:** {resource_name}
{f"**Project:** {project}" if project else ""}

**Response:** {result}
"""
            elif action == "list":
                # Parse result to count items
                count = 0
                if isinstance(result, list):
                    count = len(result)
                elif isinstance(result, dict):
                    for key in ['items', 'data', resource_type + 's']:
                        if key in result and isinstance(result[key], list):
                            count = len(result[key])
                            break
                
                return f"""
✅ **{resource_type.upper()} List Retrieved**

{f"**Project:** {project}" if project else "**Scope:** Cluster-wide"}
**Found:** {count} items

**Response:** {result}
"""
            else:
                return f"""
✅ **Operation Complete**

**Action:** {action}
**Resource:** {resource_type}

**Response:** {result}
"""
                
        except Exception as e:
            logger.error(f"Template execution failed: {str(e)}")
            return f"""
❌ **Template Execution Failed**

**Error:** {str(e)}

**Troubleshooting:**
1. Check your Run:AI credentials are valid
{f"2. Verify the project '{project}' exists" if project else ""}
3. Check resource parameters are correct
4. Review logs for detailed error information

**Operation:** {action} {resource_type}
{f"**Resource Name:** {resource_name}" if resource_name else ""}
"""
    
    try:
        yield FunctionInfo.create(
            single_fn=_execute_template_operation,
            description=(
                "Manage datasources and projects using deterministic templates (NFS, PVC, Git, S3, HostPath + project create/list/delete). "
                "Fast, consistent, and debuggable operations."
            )
        )
    except GeneratorExit:
        logger.info("Template executor exited")
    finally:
        logger.info("Cleaning up template executor")

