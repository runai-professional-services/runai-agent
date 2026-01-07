"""Run:AI job submission function with safety validations"""

from typing import List, Optional
from pydantic import Field
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

from ..utils import get_secure_config, sanitize_input, logger


class RunaiJobSubmitterConfig(FunctionBaseConfig, name="runai_submit_workload"):
    """Submit workloads to Run:AI cluster with safety validations"""
    description: str = "Submit single-node training jobs to Run:AI cluster. Use for standard training workloads with GPUs."
    dry_run_default: bool = Field(default=True, description="Always preview before submitting by default")
    require_confirmation: bool = Field(default=True, description="Require explicit user confirmation before submission")
    allowed_projects: List[str] = Field(default_factory=lambda: ["*"], description="Whitelisted projects that can be submitted to (use ['*'] for all)")
    max_gpus: int = Field(default=8, description="Maximum number of GPUs allowed per job")


@register_function(config_type=RunaiJobSubmitterConfig)
async def runai_submit_workload(config: RunaiJobSubmitterConfig, builder: Builder):
    """
    Submit workloads to Run:AI cluster with validation and safety checks.
    
    This function implements a safe job submission workflow:
    1. Validates job specification
    2. Checks resource limits and permissions
    3. Shows preview in dry-run mode
    4. Requires explicit confirmation for actual submission
    5. Submits via Run:AI API
    6. Returns job status and monitoring info
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
        logger.warning("⚠️  Run:AI SDK not installed. Job submission will be simulated.")
    
    def validate_job_spec(job_spec: dict) -> tuple[bool, str]:
        """Validate job specification structure and limits"""
        errors = []
        
        # Required field: name
        if "name" not in job_spec:
            errors.append(f"Missing required field: 'name'")
        
        # Required field: project (check multiple possible keys)
        project_name = None
        if "project" in job_spec:
            project_name = job_spec["project"]
        elif "projectId" in job_spec:
            project_name = job_spec["projectId"]
        elif "project_id" in job_spec:
            project_name = job_spec["project_id"]
        
        if not project_name:
            errors.append(f"Missing required field: 'project' (or 'projectId')")
        
        # Required field: image (check multiple possible locations)
        has_image = False
        if "image" in job_spec:
            has_image = True
        elif "spec" in job_spec and isinstance(job_spec["spec"], dict):
            if "image" in job_spec["spec"]:
                has_image = True
            elif "template" in job_spec["spec"]:
                # Check for Kubernetes-style template.spec.containers[].image
                template = job_spec["spec"].get("template", {})
                if isinstance(template, dict):
                    spec = template.get("spec", {})
                    if isinstance(spec, dict):
                        containers = spec.get("containers", [])
                        if containers and isinstance(containers, list) and len(containers) > 0:
                            if "image" in containers[0]:
                                has_image = True
        
        if not has_image:
            errors.append(f"Missing required field: 'image' (checked top-level, spec.image, and spec.template.spec.containers[].image)")
        
        # Project whitelist (support wildcard "*")
        if project_name and "*" not in config.allowed_projects and project_name not in config.allowed_projects:
            errors.append(f"Project '{project_name}' not in allowed list: {config.allowed_projects}")
        
        # GPU limits - check multiple possible locations
        gpu_count = 0
        if "gpu" in job_spec:
            gpu_count = job_spec["gpu"]
        elif "gpus" in job_spec:
            gpu_count = job_spec["gpus"]
        elif "resources" in job_spec and isinstance(job_spec["resources"], dict):
            gpu_count = job_spec["resources"].get("gpu") or job_spec["resources"].get("gpus", 0)
        elif "spec" in job_spec and isinstance(job_spec["spec"], dict):
            compute = job_spec["spec"].get("compute", {})
            if isinstance(compute, dict):
                gpu_count = compute.get("gpuDevicesRequest") or compute.get("gpu_devices_request", 0)
        
        if gpu_count and gpu_count > config.max_gpus:
            errors.append(f"GPU count {gpu_count} exceeds maximum {config.max_gpus}")
        
        # Name validation (K8s naming rules)
        if "name" in job_spec:
            name = job_spec["name"]
            if not name.replace("-", "").replace("_", "").isalnum():
                errors.append(f"Job name '{name}' contains invalid characters. Use alphanumeric, dash, or underscore only")
            if len(name) > 63:
                errors.append(f"Job name too long ({len(name)} chars). Maximum 63 characters")
        
        if errors:
            return False, "\n".join(f"  • {err}" for err in errors)
        return True, "✅ Validation passed"
    
    def generate_preview(job_spec: dict) -> str:
        """Generate human-readable preview of the job"""
        preview = f"""
**Job Name:** {job_spec.get('name', 'N/A')}
**Project:** {job_spec.get('project', 'N/A')}
**Image:** {job_spec.get('image', 'N/A')}
**Command:** {job_spec.get('command', 'N/A')}

**Resources:**"""
        
        # Extract GPU count from multiple possible locations
        gpu_count = None
        if 'gpu' in job_spec:
            gpu_count = job_spec['gpu']
        elif 'gpus' in job_spec:
            gpu_count = job_spec['gpus']
        elif 'resources' in job_spec and isinstance(job_spec['resources'], dict):
            gpu_count = job_spec['resources'].get('gpu') or job_spec['resources'].get('gpus')
        elif 'spec' in job_spec and isinstance(job_spec['spec'], dict):
            compute = job_spec['spec'].get('compute', {})
            if isinstance(compute, dict):
                gpu_count = compute.get('gpuDevicesRequest') or compute.get('gpu_devices_request')
        
        if "resources" in job_spec:
            res = job_spec["resources"]
            preview += f"""
  • GPUs: {gpu_count if gpu_count is not None else res.get('gpu', 0)}
  • CPUs: {res.get('cpu', 'N/A')}
  • Memory: {res.get('memory', 'N/A')}"""
        elif gpu_count is not None:
            preview += f"""
  • GPUs: {gpu_count}
  • CPUs: N/A
  • Memory: N/A"""
        else:
            preview += "\n  • No resources specified"
        
        if "distributed" in job_spec:
            dist = job_spec["distributed"]
            preview += f"""

**Distributed Training:**
  • Nodes: {dist.get('nodes', 1)}
  • Processes per node: {dist.get('processes_per_node', 1)}
  • Framework: {dist.get('framework', 'N/A')}"""
        
        if "environment" in job_spec:
            preview += f"""

**Environment Variables:** {len(job_spec['environment'])} variables"""
        
        return preview
    
    async def _submit_job(
        job_spec: dict,
        dry_run: Optional[bool] = None,
        confirmed: bool = False
    ) -> str:
        """
        Submit a Run:AI workload
        
        Args:
            job_spec: Job specification dictionary with required fields:
                - name: Job name (required)
                - project: Run:AI project name (required)
                - image: Container image (required)
                - command: Command to run (optional)
                - resources: Dict with gpu, cpu, memory (optional)
                - distributed: Distributed training config (optional)
            dry_run: If True, only validate and preview. If None, uses config default.
            confirmed: Must be True to actually submit (when dry_run=False)
        
        Returns:
            String with validation results, preview, or submission status
        """
        try:
            # Log incoming job_spec for debugging
            logger.info(f"Received job_spec: {job_spec}")
            
            # Sanitize all string inputs
            if isinstance(job_spec, dict):
                job_spec = {k: sanitize_input(v) if isinstance(v, str) else v 
                           for k, v in job_spec.items()}
            
            # Determine dry-run mode
            is_dry_run = dry_run if dry_run is not None else config.dry_run_default
            
            # Step 1: Validate job spec
            is_valid, validation_msg = validate_job_spec(job_spec)
            if not is_valid:
                return f"""
❌ **Job Validation Failed**

{validation_msg}

Please fix the errors and try again.
"""
            
            # Step 2: Generate preview
            preview = generate_preview(job_spec)
            
            # Step 3: Dry-run mode - just show preview
            if is_dry_run:
                return f"""
✅ **Job Validation Passed**

{preview}

**📋 Next Steps:**
To actually submit this job, call this function again with:
  • dry_run=False
  • confirmed=True

**Example:**
```
runai_submit_workload(
    job_spec={{...}},
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

**This will submit a REAL job to the cluster.**

To proceed, call with confirmed=True:
```
runai_submit_workload(
    job_spec={{...}},
    dry_run=False,
    confirmed=True
)
```
"""
            
            # Step 5: Actually submit the job
            logger.info(f"Submitting job: {job_spec.get('name')}")
            
            secure_config = get_secure_config()
            
            # Check if SDK is available
            if not SDK_AVAILABLE:
                return f"""
⚠️  **Run:AI SDK Not Installed**

The Run:AI Python SDK is not available in this environment.
Job has been validated but cannot be submitted.

{preview}

**To enable actual job submission:**
```bash
pip install runapy
```

**Alternative - Generate submission code:**
You can use `runailabs_job_generator` to generate Python code that submits this job.

**Job spec ready for submission:**
```python
job_spec = {{
    "name": "{job_spec.get('name')}",
    "project": "{job_spec.get('project')}",
    "image": "{job_spec.get('image')}",
    "resources": {job_spec.get('resources', {})},
}}
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
                
                # Step 1: Get project_id from project name (check multiple possible keys)
                project_name = job_spec.get('project') or job_spec.get('projectId') or job_spec.get('project_id')
                if not project_name:
                    return "❌ Error: 'project' field not found in job_spec"
                projects_response = client.organizations.projects.get_projects()
                projects_data = projects_response.data if hasattr(projects_response, 'data') else projects_response
                
                # The data structure is: {"projects": [...]}
                project_list = projects_data.get("projects", []) if isinstance(projects_data, dict) else []
                
                project_id = None
                cluster_id = None
                
                logger.info(f"Looking for project: {project_name}")
                logger.info(f"Found {len(project_list)} projects in cluster")
                
                # Find the matching project
                for project in project_list:
                    p_name = project.get("name")
                    p_id = project.get("id")
                    p_cluster_id = project.get("clusterId") or project.get("cluster_id")
                    
                    logger.info(f"Checking project: name={p_name}, id={p_id}, cluster_id={p_cluster_id}")
                    
                    if p_name == project_name:
                        project_id = p_id
                        cluster_id = p_cluster_id
                        logger.info(f"✓ Matched project: {project_name}")
                        break
                
                if not project_id:
                    # Build available projects list
                    available_projects = [p.get("name") for p in project_list if p.get("name")]
                    
                    return f"""
❌ **Project Not Found**

The project "{project_name}" was not found in your Run:AI cluster.

**Available projects:**
{chr(10).join(f"  • {name}" for name in available_projects)}

Please use one of the available projects.
"""
                
                # Step 2: Build compute resources and spec
                # Extract GPU count from all possible locations before building compute
                gpu_count = None
                
                # Priority 1: Check top-level keys (most common from LLM)
                if 'gpu' in job_spec:
                    gpu_count = job_spec['gpu']
                    logger.info(f"✓ Found GPU count in 'gpu': {gpu_count}")
                elif 'gpus' in job_spec:
                    gpu_count = job_spec['gpus']
                    logger.info(f"✓ Found GPU count in 'gpus': {gpu_count}")
                
                # Priority 2: Check resources dict
                if gpu_count is None and 'resources' in job_spec and isinstance(job_spec['resources'], dict):
                    gpu_count = job_spec['resources'].get('gpu') or job_spec['resources'].get('gpus')
                    if gpu_count:
                        logger.info(f"✓ Found GPU count in 'resources': {gpu_count}")
                
                # Priority 3: Check compute structure
                existing_compute = None
                if 'compute' in job_spec and isinstance(job_spec['compute'], dict):
                    existing_compute = job_spec['compute']
                    logger.info(f"✓ Found compute at top level of job_spec")
                elif 'spec' in job_spec and isinstance(job_spec['spec'], dict):
                    existing_compute = job_spec['spec'].get('compute', {})
                    if existing_compute:
                        logger.info(f"✓ Found compute in spec.compute")
                
                if gpu_count is None and existing_compute and isinstance(existing_compute, dict):
                    gpu_count = existing_compute.get('gpuDevicesRequest') or existing_compute.get('gpu_devices_request')
                    if gpu_count:
                        logger.info(f"✓ Found GPU count in compute structure: {gpu_count}")
                
                # Default to 1 only if no GPU count found anywhere
                if gpu_count is None:
                    gpu_count = 1
                    logger.warning(f"GPU count not found in job_spec, defaulting to 1. job_spec keys: {job_spec.keys()}")
                
                logger.info(f"Final GPU count for submission: {gpu_count}")
                
                # Build compute structure - use dict to avoid SDK adding conflicting fields
                # Same approach as distributed jobs (which work correctly)
                gpu_count_float = float(gpu_count)
                
                if gpu_count_float < 1.0:
                    # Fractional GPU request (e.g., 0.25, 0.5) - use portion mode
                    # CRITICAL: Must set gpuDevicesRequest=1 so it allocates 1 device, then use portion of it
                    compute = {
                        "gpuDevicesRequest": 1,  # Allocate 1 GPU device
                        "gpuPortionRequest": gpu_count_float,  # Use this fraction of the device
                        "gpuRequestType": "portion",
                        "cpuCoreRequest": 0.1,
                        "cpuMemoryRequest": "100M"
                    }
                else:
                    # Full GPU request (1, 2, 4, 8, etc.) - use devices mode
                    compute = {
                        "gpuDevicesRequest": int(gpu_count_float),
                        "cpuCoreRequest": 0.1,
                        "cpuMemoryRequest": "100M"
                    }
                
                # Step 3: Extract image from multiple possible locations
                image = job_spec.get('image')
                if not image and 'spec' in job_spec:
                    spec_dict = job_spec.get('spec', {})
                    if isinstance(spec_dict, dict):
                        image = spec_dict.get('image')
                
                if not image:
                    return "❌ Error: 'image' field not found in job_spec"
                
                # Step 4: Build the training spec
                spec = models.TrainingSpecSpec(
                    image=image,
                    compute=compute
                )
                
                # Add command if specified (optional)
                if job_spec.get('command'):
                    spec.command = job_spec.get('command')
                
                # Step 4: Create the training request
                training_request = models.TrainingCreationRequest(
                    name=job_spec.get('name'),
                    project_id=project_id,
                    cluster_id=cluster_id,
                    spec=spec
                )
                
                # Step 5: Submit the job
                job = client.workloads.trainings.create_training1(training_request)
                
                return f"""
✅ **Job Submitted Successfully!**

**Job ID:** {job.id if hasattr(job, 'id') else 'N/A'}
**Name:** {job_spec['name']}
**Project:** {project_name} (ID: {project_id})
**Cluster ID:** {cluster_id}
**Status:** Submitted

**📊 Monitor your job:**
Check status in the Run:AI UI or CLI

**🌐 View in UI:**
{secure_config['RUNAI_BASE_URL']}/projects/{project_name}/jobs
"""
            except AttributeError as e:
                # Fallback if SDK doesn't have the expected API
                logger.warning(f"SDK API method not available: {e}")
                return f"""
⚠️  **Submission Method Not Available**

The Run:AI SDK is installed but the API method is not available.
This might be due to SDK version incompatibility.

**Tried:** `client.workloads.trainings.create_training1()`
**Error:** {str(e)}

**Alternative:** Use `runailabs_job_generator` to generate submission code.

**Job spec validated and ready:**
{preview}
"""
            except Exception as e:
                logger.error(f"Job submission failed: {str(e)}")
                return f"""
❌ **Job Submission Failed**

**Error:** {str(e)}

**Troubleshooting:**
1. Check your Run:AI credentials are valid
2. Verify the project "{job_spec.get('project')}" exists
3. Ensure you have permission to submit jobs
4. Check resource quotas are available

**Job spec that failed:**
{preview}
"""
                
        except Exception as e:
            logger.error(f"Workload submission error: {str(e)}")
            return f"❌ Error processing workload submission: {str(e)}"
    
    try:
        yield FunctionInfo.create(
            single_fn=_submit_job,
            description="Submit single-node training jobs to Run:AI cluster. Use for standard training workloads with GPUs."
        )
    except GeneratorExit:
        logger.info("Job submitter exited")
    finally:
        logger.info("Cleaning up job submitter")

