"""Run:AI workspace submission function with safety validations"""

from typing import List, Optional
from pydantic import Field
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

from ..utils import get_secure_config, sanitize_input, logger


class RunaiWorkspaceSubmitterConfig(FunctionBaseConfig, name="runai_submit_workspace"):
    """Submit workspace workloads to Run:AI cluster with safety validations"""
    description: str = "Submit interactive workspace sessions (Jupyter, VSCode, SSH). Use for development environments, not training jobs."
    dry_run_default: bool = Field(default=True, description="Always preview before submitting by default")
    require_confirmation: bool = Field(default=True, description="Require explicit user confirmation before submission")
    allowed_projects: List[str] = Field(default_factory=lambda: ["*"], description="Whitelisted projects that can be submitted to (use ['*'] for all)")
    max_gpus: int = Field(default=8, description="Maximum number of GPUs allowed per workspace")


@register_function(config_type=RunaiWorkspaceSubmitterConfig)
async def runai_submit_workspace(config: RunaiWorkspaceSubmitterConfig, builder: Builder):
    """
    Submit workspace workloads (Jupyter, VSCode, etc.) to Run:AI cluster with validation and safety checks.
    
    Workspaces are interactive environments with web interfaces.
    
    This function implements a safe workspace submission workflow:
    1. Validates workspace specification
    2. Checks resource limits and permissions
    3. Shows preview in dry-run mode
    4. Requires explicit confirmation for actual submission
    5. Submits via Run:AI workspace API
    6. Returns workspace status and access info
    """
    
    # Check if Run:AI SDK is available
    try:
        from runai.configuration import Configuration
        from runai.api_client import ApiClient
        from runai.runai_client import RunaiClient
        SDK_AVAILABLE = True
        logger.debug("✓ Run:AI SDK is available")
    except ImportError:
        SDK_AVAILABLE = False
        logger.warning("⚠️  Run:AI SDK not installed. Workspace submission will be simulated.")
    
    def validate_workspace_spec(workspace_spec: dict) -> tuple[bool, str]:
        """Validate workspace specification structure and limits"""
        errors = []
        
        # Required field: name
        if "name" not in workspace_spec:
            errors.append("Missing required field: 'name'")
        
        # Required field: project
        project_name = None
        if "project" in workspace_spec:
            project_name = workspace_spec["project"]
        elif "projectId" in workspace_spec:
            project_name = workspace_spec["projectId"]
        elif "project_id" in workspace_spec:
            project_name = workspace_spec["project_id"]
        
        if not project_name:
            errors.append("Missing required field: 'project' (or 'projectId')")
        
        # Required field: image
        has_image = False
        if "image" in workspace_spec:
            has_image = True
        elif "spec" in workspace_spec and isinstance(workspace_spec["spec"], dict):
            if "image" in workspace_spec["spec"]:
                has_image = True
        
        if not has_image:
            errors.append("Missing required field: 'image'")
        
        # Project whitelist (support wildcard "*")
        if project_name and "*" not in config.allowed_projects and project_name not in config.allowed_projects:
            errors.append(f"Project '{project_name}' not in allowed list: {config.allowed_projects}")
        
        # GPU limits
        gpu_count = 0
        gpu_portion = 0.0
        
        if "gpu" in workspace_spec:
            gpu_count = workspace_spec["gpu"]
        elif "gpus" in workspace_spec:
            gpu_count = workspace_spec["gpus"]
        elif "gpu_portion" in workspace_spec or "gpuPortion" in workspace_spec:
            gpu_portion = workspace_spec.get("gpu_portion") or workspace_spec.get("gpuPortion", 0)
        elif "spec" in workspace_spec and isinstance(workspace_spec["spec"], dict):
            compute = workspace_spec["spec"].get("compute", {})
            if isinstance(compute, dict):
                gpu_count = compute.get("gpuDevicesRequest", 0)
                gpu_portion = compute.get("gpuPortionRequest", 0)
        
        if gpu_count > config.max_gpus:
            errors.append(f"GPU count ({gpu_count}) exceeds maximum allowed ({config.max_gpus})")
        
        if gpu_portion > 1.0:
            errors.append(f"GPU portion ({gpu_portion}) cannot exceed 1.0")
        
        if errors:
            return False, "**Validation Errors:**\n" + "\n".join(f"  • {err}" for err in errors)
        
        return True, "✓ Validation passed"
    
    def generate_preview(workspace_spec: dict) -> str:
        """Generate a human-readable preview of the workspace"""
        
        name = workspace_spec.get("name", "N/A")
        project = workspace_spec.get("project") or workspace_spec.get("projectId") or workspace_spec.get("project_id", "N/A")
        image = workspace_spec.get("image") or (workspace_spec.get("spec", {}).get("image") if isinstance(workspace_spec.get("spec"), dict) else "N/A")
        
        workspace_type = workspace_spec.get("workspace_type") or workspace_spec.get("workspaceType", "custom")
        
        # GPU info
        gpu_count = 0
        gpu_portion = 0.0
        
        if "gpu" in workspace_spec:
            gpu_count = workspace_spec["gpu"]
        elif "gpus" in workspace_spec:
            gpu_count = workspace_spec["gpus"]
        elif "gpu_portion" in workspace_spec or "gpuPortion" in workspace_spec:
            gpu_portion = workspace_spec.get("gpu_portion") or workspace_spec.get("gpuPortion", 0)
        elif "spec" in workspace_spec and isinstance(workspace_spec["spec"], dict):
            compute = workspace_spec["spec"].get("compute", {})
            if isinstance(compute, dict):
                gpu_count = compute.get("gpuDevicesRequest", 0)
                gpu_portion = compute.get("gpuPortionRequest", 0)
        
        if gpu_count > 0:
            gpu_display = f"{gpu_count} GPU(s)"
        elif gpu_portion > 0:
            gpu_display = f"{gpu_portion*100}% GPU portion"
        else:
            gpu_display = "1 GPU (default)"
        
        preview = f"""
**Workspace Preview:**

**Configuration:**
- Name: `{name}`
- Project: `{project}`
- Type: {workspace_type}
- Image: `{image}`

**Resources:**
- GPU: {gpu_display}

**Access:**
- Web interface will be accessible via Run:AI UI once running
"""
        
        return preview
    
    async def _submit_workspace(
        workspace_spec: dict,
        dry_run: Optional[bool] = None,
        confirmed: bool = False
    ) -> str:
        """
        Submit a workspace to Run:AI.
        
        Args:
            workspace_spec: Dictionary containing workspace configuration
                Required fields:
                - name: Workspace name
                - project: Project name to submit to
                - image: Docker image to use
                Optional fields:
                - workspace_type: Type of workspace (jupyter, vscode, custom)
                - gpu or gpus: Number of full GPUs
                - gpu_portion or gpuPortion: GPU fraction (0.0-1.0)
                - command: Command to run
                - args: Arguments for the command
                - port: Port to expose
            dry_run: If True, only validate and preview. If None, uses config default
            confirmed: If True, actually submit the workspace (requires dry_run=False)
        
        Returns:
            Status message with workspace details or validation errors
        """
        try:
            # Sanitize string inputs
            if isinstance(workspace_spec, dict):
                workspace_spec = {k: sanitize_input(v) if isinstance(v, str) else v 
                               for k, v in workspace_spec.items()}
            
            # Determine dry-run mode
            is_dry_run = dry_run if dry_run is not None else config.dry_run_default
            
            # Step 1: Validate workspace spec
            is_valid, validation_msg = validate_workspace_spec(workspace_spec)
            if not is_valid:
                return f"""
❌ **Workspace Validation Failed**

{validation_msg}

Please fix the errors and try again.

**Example workspace spec:**
```python
{{
    "name": "my-jupyter-workspace",
    "project": "project-01",
    "image": "jupyter/scipy-notebook",
    "workspace_type": "jupyter",
    "gpu": 1
}}
```
"""
            
            # Step 2: Generate preview
            preview = generate_preview(workspace_spec)
            
            # Step 3: Dry-run mode - just show preview
            if is_dry_run:
                return f"""
✅ **Workspace Validation Passed**

{preview}

**📋 Next Steps:**
To actually submit this workspace, call this function again with:
  • dry_run=False
  • confirmed=True

**Example:**
```
runai_submit_workspace(
    workspace_spec={{...}},
    dry_run=False,
    confirmed=True
)
```
"""
            
            # Step 4: Require explicit confirmation
            if config.require_confirmation and not confirmed:
                return f"""
⚠️  **Confirmation Required**

{preview}

**This will submit a REAL workspace to the cluster.**

To proceed, call with confirmed=True:
```
runai_submit_workspace(
    workspace_spec={{...}},
    dry_run=False,
    confirmed=True
)
```
"""
            
            # Step 5: Actually submit the workspace
            logger.info(f"Submitting workspace: {workspace_spec.get('name')}")
            
            secure_config = get_secure_config()
            
            # Check if SDK is available
            if not SDK_AVAILABLE:
                return f"""
⚠️  **Run:AI SDK Not Installed**

The Run:AI Python SDK is not available in this environment.
Workspace has been validated but cannot be submitted.

{preview}

**To enable actual workspace submission:**
```bash
pip install runapy==1.223.0
```
"""
            
            # SDK is available - proceed with submission
            try:
                from runai import models
                
                configuration = Configuration(
                    client_id=secure_config['RUNAI_CLIENT_ID'],
                    client_secret=secure_config['RUNAI_CLIENT_SECRET'],
                    runai_base_url=secure_config['RUNAI_BASE_URL'],
                )
                client = RunaiClient(ApiClient(configuration))
                
                # Step 1: Get project_id from project name
                project_name = workspace_spec.get('project') or workspace_spec.get('projectId') or workspace_spec.get('project_id')
                if not project_name:
                    return "❌ Error: 'project' field not found in workspace_spec"
                
                projects_response = client.organizations.projects.get_projects()
                projects_data = projects_response.data if hasattr(projects_response, 'data') else projects_response
                project_list = projects_data.get("projects", []) if isinstance(projects_data, dict) else []
                
                project_id = None
                cluster_id = None
                
                logger.info(f"Looking for project: {project_name}")
                
                for project in project_list:
                    p_name = project.get("name")
                    if p_name == project_name:
                        project_id = project.get("id")
                        cluster_id = project.get("clusterId") or project.get("cluster_id")
                        logger.info(f"✓ Matched project: {project_name}")
                        break
                
                if not project_id:
                    available_projects = [p.get("name") for p in project_list if p.get("name")]
                    return f"""
❌ **Project Not Found**

The project "{project_name}" was not found in your Run:AI cluster.

**Available projects:**
{chr(10).join(f"  • {name}" for name in available_projects)}

Please use one of the available projects.
"""
                
                # Step 2: Extract workspace parameters
                image = workspace_spec.get('image')
                if not image and 'spec' in workspace_spec:
                    spec_dict = workspace_spec.get('spec', {})
                    if isinstance(spec_dict, dict):
                        image = spec_dict.get('image')
                
                if not image:
                    return "❌ Error: 'image' field not found in workspace_spec"
                
                workspace_type = workspace_spec.get("workspace_type") or workspace_spec.get("workspaceType", "custom")
                
                # Step 3: Build compute resources - Extract GPU from all possible locations
                gpu_count = None
                gpu_portion = None
                
                # Priority 1: Check top-level keys (most common from LLM)
                if 'gpu' in workspace_spec:
                    gpu_count = workspace_spec['gpu']
                    logger.info(f"✓ Found GPU count in 'gpu': {gpu_count}")
                elif 'gpus' in workspace_spec:
                    gpu_count = workspace_spec['gpus']
                    logger.info(f"✓ Found GPU count in 'gpus': {gpu_count}")
                
                # Check for GPU portion
                if 'gpu_portion' in workspace_spec:
                    gpu_portion = workspace_spec['gpu_portion']
                    logger.info(f"✓ Found GPU portion in 'gpu_portion': {gpu_portion}")
                elif 'gpuPortion' in workspace_spec:
                    gpu_portion = workspace_spec['gpuPortion']
                    logger.info(f"✓ Found GPU portion in 'gpuPortion': {gpu_portion}")
                
                # Priority 2: Check resources dict
                if gpu_count is None and 'resources' in workspace_spec and isinstance(workspace_spec['resources'], dict):
                    gpu_count = workspace_spec['resources'].get('gpu') or workspace_spec['resources'].get('gpus')
                    if gpu_count:
                        logger.info(f"✓ Found GPU count in 'resources': {gpu_count}")
                
                # Priority 3: Check compute structure
                if gpu_count is None and 'spec' in workspace_spec and isinstance(workspace_spec['spec'], dict):
                    compute = workspace_spec['spec'].get('compute', {})
                    if isinstance(compute, dict):
                        gpu_count = compute.get('gpuDevicesRequest')
                        gpu_portion = compute.get('gpuPortionRequest')
                        if gpu_count:
                            logger.info(f"✓ Found GPU count in compute structure: {gpu_count}")
                        if gpu_portion:
                            logger.info(f"✓ Found GPU portion in compute structure: {gpu_portion}")
                
                # Default to 0 if not found
                if gpu_count is None:
                    gpu_count = 0
                if gpu_portion is None:
                    gpu_portion = 0.0
                
                logger.info(f"Final GPU allocation for workspace - count: {gpu_count}, portion: {gpu_portion}")
                
                cpu_cores = workspace_spec.get('cpu_cores') or workspace_spec.get('cpuCores', 0.1)
                memory = workspace_spec.get('memory', "2Gi")
                
                # Determine GPU request type
                # Note: Workspaces only accept 'portion', 'memory', or 'migProfile' for gpuRequestType
                compute_dict = {}
                if gpu_count > 0:
                    # For workspaces, convert full GPUs to portion (1 GPU = 1.0 portion)
                    # CRITICAL: Must set gpuDevicesRequest for both full and fractional GPUs
                    compute_dict["gpuDevicesRequest"] = max(1, int(float(gpu_count)))  # At least 1 device
                    compute_dict["gpuPortionRequest"] = float(gpu_count)
                    compute_dict["gpuRequestType"] = "portion"
                elif gpu_portion > 0:
                    # Fractional GPU via gpu_portion parameter
                    compute_dict["gpuDevicesRequest"] = 1  # Must be 1 for fractional
                    compute_dict["gpuPortionRequest"] = float(gpu_portion)
                    compute_dict["gpuRequestType"] = "portion"
                else:
                    # Default to 1 full GPU (1.0 portion)
                    compute_dict["gpuDevicesRequest"] = 1
                    compute_dict["gpuPortionRequest"] = 1.0
                    compute_dict["gpuRequestType"] = "portion"
                
                compute_dict["cpuCoreRequest"] = float(cpu_cores)
                compute_dict["cpuMemoryRequest"] = memory
                
                compute = models.SupersetSpecAllOfCompute(**compute_dict)
                
                # Step 4: Configure workspace type defaults
                workspace_configs = {
                    "jupyter": {
                        "command": "start-notebook.sh",
                        "args": "--NotebookApp.base_url=/${RUNAI_PROJECT}/${RUNAI_JOB_NAME} --NotebookApp.token=''",
                        "port": 8888,
                        "tool_type": "jupyter-notebook",
                        "tool_name": "Jupyter",
                    },
                    "vscode": {
                        "command": "code-server",
                        "args": "--auth none --bind-addr 0.0.0.0:8080",
                        "port": 8080,
                        "tool_type": "vscode",
                        "tool_name": "VSCode",
                    },
                }
                
                command = workspace_spec.get('command')
                args = workspace_spec.get('args')
                port = workspace_spec.get('port')
                
                if workspace_type in workspace_configs:
                    ws_config = workspace_configs[workspace_type]
                    if not command:
                        command = ws_config["command"]
                    if not args:
                        args = ws_config["args"]
                    if not port:
                        port = ws_config["port"]
                    tool_type = ws_config["tool_type"]
                    tool_name = ws_config["tool_name"]
                else:
                    # Custom workspace type
                    if not port:
                        port = 8080
                    tool_type = "custom"
                    tool_name = workspace_type.title()
                
                # Step 5: Build exposed URLs
                exposed_urls = [
                    models.ExposedUrl(
                        container=port,
                        tool_type=tool_type,
                        tool_name=tool_name,
                        name=tool_name,
                    )
                ]
                
                # Step 6: Build workspace spec
                spec = models.WorkspaceSpecSpec(
                    image=image,
                    command=command,
                    args=args,
                    compute=compute,
                    exposedUrls=exposed_urls,
                    imagePullPolicy="IfNotPresent",
                )
                
                # Step 7: Create workspace request
                workspace_request = models.WorkspaceCreationRequest(
                    name=workspace_spec.get('name'),
                    projectId=project_id,
                    clusterId=cluster_id,
                    spec=spec
                )
                
                # Step 8: Submit the workspace
                logger.info(f"Submitting workspace: {workspace_spec.get('name')} (type: {workspace_type})")
                workspace = client.workloads.workspaces.create_workspace1(
                    workspace_creation_request=workspace_request
                )
                
                gpu_display = f"{gpu_count} GPU(s)" if gpu_count > 0 else f"{gpu_portion*100}% GPU portion"
                
                return f"""
✅ **Workspace Submitted Successfully!**

**Workspace ID:** {workspace.id if hasattr(workspace, 'id') else 'N/A'}
**Name:** {workspace_spec['name']}
**Project:** {project_name} (ID: {project_id})
**Type:** {workspace_type}
**Image:** {image}
**GPU:** {gpu_display}
**Status:** Submitted

**📊 Access your workspace:**
Once running, access {tool_name} via the Run:AI UI

**🌐 View in UI:**
{secure_config['RUNAI_BASE_URL']}/projects/{project_name}/workspaces
"""
            except AttributeError as e:
                logger.warning(f"SDK API method not available: {e}")
                return f"""
⚠️  **Submission Method Not Available**

The Run:AI SDK is installed but the workspace API method is not available.
This might be due to SDK version incompatibility.

**Tried:** `client.workloads.workspaces.create_workspace1()`
**Error:** {str(e)}

**Workspace spec validated and ready:**
{preview}
"""
            except Exception as e:
                logger.error(f"Workspace submission failed: {str(e)}")
                return f"""
❌ **Workspace Submission Failed**

**Error:** {str(e)}

**Troubleshooting:**
1. Check your Run:AI credentials are valid
2. Verify the project "{workspace_spec.get('project')}" exists
3. Ensure you have permission to submit workspaces
4. Check that GPU quotas are available

**Workspace spec that failed:**
{preview}
"""
                
        except Exception as e:
            logger.error(f"Workspace submission error: {str(e)}")
            return f"❌ Error processing workspace submission: {str(e)}"
    
    try:
        yield FunctionInfo.create(
            single_fn=_submit_workspace,
            description="Submit interactive workspace sessions (Jupyter, VSCode, SSH). Use for development environments, not training jobs."
        )
    except GeneratorExit:
        logger.info("Workspace submitter exited")
    finally:
        logger.info("Cleaning up workspace submitter")

