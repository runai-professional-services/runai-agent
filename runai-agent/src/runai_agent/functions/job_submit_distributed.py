"""Run:AI distributed training job submission function with safety validations"""

from typing import List, Optional
from pydantic import Field
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

from ..utils import get_secure_config, sanitize_input, logger


class RunaiDistributedJobSubmitterConfig(FunctionBaseConfig, name="runai_submit_distributed_workload"):
    """Submit distributed training workloads to Run:AI cluster with safety validations"""
    description: str = "Submit distributed/multi-node training jobs (PyTorch DDP, TensorFlow, MPI). Use when user mentions multiple workers or distributed training."
    dry_run_default: bool = Field(default=True, description="Always preview before submitting by default")
    require_confirmation: bool = Field(default=True, description="Require explicit user confirmation before submission")
    allowed_projects: List[str] = Field(default_factory=lambda: ["*"], description="Whitelisted projects that can be submitted to (use ['*'] for all)")
    max_gpus_per_worker: int = Field(default=8, description="Maximum number of GPUs allowed per worker")
    max_workers: int = Field(default=10, description="Maximum number of workers allowed")


@register_function(config_type=RunaiDistributedJobSubmitterConfig)
async def runai_submit_distributed_workload(config: RunaiDistributedJobSubmitterConfig, builder: Builder):
    """
    Submit distributed training workloads to Run:AI cluster with validation and safety checks.
    
    Distributed training jobs allow you to scale training across multiple nodes/workers.
    
    This function implements a safe distributed job submission workflow:
    1. Validates distributed job specification (workers, framework, etc.)
    2. Checks resource limits and permissions
    3. Shows preview in dry-run mode
    4. Requires explicit confirmation for actual submission
    5. Submits via Run:AI distributed workload API
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
        logger.warning("⚠️  Run:AI SDK not installed. Distributed job submission will be simulated.")
    
    def validate_distributed_job_spec(job_spec: dict) -> tuple[bool, str]:
        """Validate distributed job specification structure and limits"""
        errors = []
        
        # Required field: name
        if "name" not in job_spec:
            errors.append("Missing required field: 'name'")
        
        # Required field: project (check multiple possible keys)
        project_name = None
        if "project" in job_spec:
            project_name = job_spec["project"]
        elif "projectId" in job_spec:
            project_name = job_spec["projectId"]
        elif "project_id" in job_spec:
            project_name = job_spec["project_id"]
        
        if not project_name:
            errors.append("Missing required field: 'project' (or 'projectId')")
        
        # Required field: image
        has_image = False
        if "image" in job_spec:
            has_image = True
        elif "spec" in job_spec and isinstance(job_spec["spec"], dict):
            if "image" in job_spec["spec"]:
                has_image = True
        
        if not has_image:
            errors.append("Missing required field: 'image'")
        
        # Required for distributed: numWorkers
        num_workers = None
        if "numWorkers" in job_spec:
            num_workers = job_spec["numWorkers"]
        elif "num_workers" in job_spec:
            num_workers = job_spec["num_workers"]
        elif "workers" in job_spec:
            num_workers = job_spec["workers"]
        elif "spec" in job_spec and isinstance(job_spec["spec"], dict):
            num_workers = job_spec["spec"].get("numWorkers") or job_spec["spec"].get("num_workers")
        
        if not num_workers or num_workers < 1:
            errors.append("Missing or invalid 'numWorkers' field (must be >= 1)")
        elif num_workers > config.max_workers:
            errors.append(f"Number of workers ({num_workers}) exceeds maximum allowed ({config.max_workers})")
        
        # Required for distributed: framework
        framework = None
        if "distributedFramework" in job_spec:
            framework = job_spec["distributedFramework"]
        elif "framework" in job_spec:
            framework = job_spec["framework"]
        elif "spec" in job_spec and isinstance(job_spec["spec"], dict):
            framework = job_spec["spec"].get("distributedFramework") or job_spec["spec"].get("framework")
        
        if not framework:
            errors.append("Missing required field: 'distributedFramework' or 'framework' (e.g., 'PyTorch', 'TensorFlow', 'MPI')")
        elif framework.upper() not in ["PYTORCH", "TENSORFLOW", "TF", "MPI", "JAX", "XGBOOST"]:
            errors.append(f"Invalid framework '{framework}'. Supported: PyTorch, TensorFlow (TF), MPI, JAX, XGBoost")
        
        # Project whitelist (support wildcard "*")
        if project_name and "*" not in config.allowed_projects and project_name not in config.allowed_projects:
            errors.append(f"Project '{project_name}' not in allowed list: {config.allowed_projects}")
        
        # GPU limits per worker
        gpu_count = 0
        if "gpu" in job_spec:
            gpu_count = job_spec["gpu"]
        elif "gpus" in job_spec:
            gpu_count = job_spec["gpus"]
        elif "gpuPerWorker" in job_spec:
            gpu_count = job_spec["gpuPerWorker"]
        elif "resources" in job_spec and isinstance(job_spec["resources"], dict):
            gpu_count = job_spec["resources"].get("gpu") or job_spec["resources"].get("gpus", 1)
        elif "spec" in job_spec and isinstance(job_spec["spec"], dict):
            compute = job_spec["spec"].get("compute", {})
            if isinstance(compute, dict):
                gpu_count = compute.get("gpuDevicesRequest") or compute.get("gpu_devices_request", 1)
        
        if gpu_count > config.max_gpus_per_worker:
            errors.append(f"GPUs per worker ({gpu_count}) exceeds maximum allowed ({config.max_gpus_per_worker})")
        
        # Calculate total GPUs
        total_gpus = gpu_count * (num_workers or 1)
        if total_gpus > 100:  # Sanity check
            errors.append(f"Total GPUs ({total_gpus} = {gpu_count} GPUs × {num_workers} workers) seems excessive. Please verify.")
        
        if errors:
            return False, "**Validation Errors:**\n" + "\n".join(f"  • {err}" for err in errors)
        
        return True, "✓ Validation passed"
    
    def generate_preview(job_spec: dict) -> str:
        """Generate a human-readable preview of the distributed job"""
        
        # Extract fields with fallbacks
        name = job_spec.get("name", "N/A")
        project = job_spec.get("project") or job_spec.get("projectId") or job_spec.get("project_id", "N/A")
        image = job_spec.get("image") or (job_spec.get("spec", {}).get("image") if isinstance(job_spec.get("spec"), dict) else "N/A")
        
        # Distributed-specific fields
        num_workers = (job_spec.get("numWorkers") or job_spec.get("num_workers") or 
                      job_spec.get("workers") or 
                      (job_spec.get("spec", {}).get("numWorkers") if isinstance(job_spec.get("spec"), dict) else 2))
        
        framework = (job_spec.get("distributedFramework") or job_spec.get("framework") or
                    (job_spec.get("spec", {}).get("distributedFramework") if isinstance(job_spec.get("spec"), dict) else "PyTorch"))
        
        # GPU info
        gpu_count = 1  # default
        if "gpu" in job_spec:
            gpu_count = job_spec["gpu"]
        elif "gpus" in job_spec:
            gpu_count = job_spec["gpus"]
        elif "gpuPerWorker" in job_spec:
            gpu_count = job_spec["gpuPerWorker"]
        elif "spec" in job_spec and isinstance(job_spec["spec"], dict):
            compute = job_spec["spec"].get("compute", {})
            if isinstance(compute, dict):
                gpu_count = compute.get("gpuDevicesRequest") or compute.get("gpu_devices_request", 1)
        
        total_gpus = gpu_count * num_workers
        
        command = job_spec.get("command", "N/A")
        if "spec" in job_spec and isinstance(job_spec["spec"], dict):
            command = job_spec["spec"].get("command", command)
        
        preview = f"""
**Distributed Training Job Preview:**

**Job Configuration:**
- Name: `{name}`
- Project: `{project}`
- Framework: `{framework}`
- Image: `{image}`

**Distributed Configuration:**
- Number of Workers: {num_workers}
- GPUs per Worker: {gpu_count}
- Total GPUs: {total_gpus}

**Resources:**
- Worker 0 (Master): {gpu_count} GPU(s)
- Workers 1-{num_workers-1}: {gpu_count} GPU(s) each
"""
        
        if command != "N/A":
            preview += f"- Command: `{command}`\n"
        
        return preview
    
    async def _submit_distributed_job(
        job_spec: dict,
        dry_run: Optional[bool] = None,
        confirmed: bool = False
    ) -> str:
        """
        Submit a distributed training job to Run:AI.
        
        Args:
            job_spec: Dictionary containing distributed job configuration
                Required fields:
                - name: Job name
                - project: Project name to submit to
                - image: Docker image to use
                - numWorkers: Number of worker nodes
                - distributedFramework: Framework (PyTorch, TensorFlow/TF, MPI, JAX, XGBoost)
                Optional fields:
                - gpu: GPUs per worker (default: 1)
                - command: Command to run
                - slotsPerWorker: Slots per worker (optional)
                - compute: Full compute specification
            dry_run: If True, only validate and preview. If None, uses config default
            confirmed: If True, actually submit the job (requires dry_run=False)
        
        Returns:
            Status message with job details or validation errors
        """
        try:
            # Sanitize string inputs
            if isinstance(job_spec, dict):
                job_spec = {k: sanitize_input(v) if isinstance(v, str) else v 
                           for k, v in job_spec.items()}
            
            # Determine dry-run mode
            is_dry_run = dry_run if dry_run is not None else config.dry_run_default
            
            # Step 1: Validate distributed job spec
            is_valid, validation_msg = validate_distributed_job_spec(job_spec)
            if not is_valid:
                return f"""
❌ **Distributed Job Validation Failed**

{validation_msg}

Please fix the errors and try again.

**Example distributed job spec:**
```python
{{
    "name": "my-distributed-training",
    "project": "project-01",
    "image": "nvcr.io/nvidia/pytorch:24.01-py3",
    "distributedFramework": "PyTorch",
    "numWorkers": 4,
    "gpu": 1,
    "command": "python train.py --distributed"
}}
```
"""
            
            # Step 2: Generate preview
            preview = generate_preview(job_spec)
            
            # Step 3: Dry-run mode - just show preview
            if is_dry_run:
                return f"""
✅ **Distributed Job Validation Passed**

{preview}

**📋 Next Steps:**
To actually submit this distributed job, call this function again with:
  • dry_run=False
  • confirmed=True

**Example:**
```
runai_submit_distributed_workload(
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

**This will submit a REAL distributed training job to the cluster.**

To proceed, call with confirmed=True:
```
runai_submit_distributed_workload(
    job_spec={{...}},
    dry_run=False,
    confirmed=True
)
```
"""
            
            # Step 5: Actually submit the distributed job
            logger.info(f"Submitting distributed job: {job_spec.get('name')}")
            
            secure_config = get_secure_config()
            
            # Check if SDK is available
            if not SDK_AVAILABLE:
                return f"""
⚠️  **Run:AI SDK Not Installed**

The Run:AI Python SDK is not available in this environment.
Distributed job has been validated but cannot be submitted.

{preview}

**To enable actual job submission:**
```bash
pip install runapy==1.223.0
```

**Alternative - Generate submission code:**
You can use `runailabs_job_generator` to generate Python code that submits this job.
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
                project_name = job_spec.get('project') or job_spec.get('projectId') or job_spec.get('project_id')
                if not project_name:
                    return "❌ Error: 'project' field not found in job_spec"
                
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
                
                # Step 2: Extract distributed-specific parameters
                num_workers = (job_spec.get("numWorkers") or job_spec.get("num_workers") or 
                              job_spec.get("workers") or 2)
                
                framework_str = (job_spec.get("distributedFramework") or 
                               job_spec.get("framework") or "PyTorch").upper()
                
                # Map framework string to enum
                framework_map = {
                    "PYTORCH": models.DistributedFramework.PYTORCH,
                    "TENSORFLOW": models.DistributedFramework.TF,
                    "TF": models.DistributedFramework.TF,
                    "MPI": models.DistributedFramework.MPI,
                    "JAX": models.DistributedFramework.JAX,
                    "XGBOOST": models.DistributedFramework.XGBOOST,
                }
                
                distributed_framework = framework_map.get(framework_str, models.DistributedFramework.PYTORCH)
                
                slots_per_worker = job_spec.get("slotsPerWorker") or job_spec.get("slots_per_worker")
                
                # Step 3: Build compute resources - use simpler structure for distributed
                # Extract GPU count from all possible locations
                gpu_count = None
                
                # Priority 1: Check top-level keys (most common from LLM)
                if 'gpu' in job_spec:
                    gpu_count = job_spec['gpu']
                    logger.info(f"✓ Found GPU count in 'gpu': {gpu_count}")
                elif 'gpus' in job_spec:
                    gpu_count = job_spec['gpus']
                    logger.info(f"✓ Found GPU count in 'gpus': {gpu_count}")
                elif 'gpuPerWorker' in job_spec:
                    gpu_count = job_spec['gpuPerWorker']
                    logger.info(f"✓ Found GPU count in 'gpuPerWorker': {gpu_count}")
                
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
                
                logger.info(f"Final GPU count for distributed submission: {gpu_count}")
                
                # Extract CPU resources if compute structure exists
                cpu_cores = 0
                cpu_memory = "0M"
                if existing_compute and isinstance(existing_compute, dict):
                    cpu_cores = existing_compute.get('cpuCoreRequest', 0)
                    cpu_memory = existing_compute.get('cpuMemoryRequest', "0M")
                
                # Use dict for compute to avoid SDK adding extra fields
                compute = {
                    "gpuDevicesRequest": int(gpu_count),
                    "cpuCoreRequest": cpu_cores,
                    "cpuMemoryRequest": cpu_memory
                }
                
                # Step 4: Extract image
                image = job_spec.get('image')
                if not image and 'spec' in job_spec:
                    spec_dict = job_spec.get('spec', {})
                    if isinstance(spec_dict, dict):
                        image = spec_dict.get('image')
                
                if not image:
                    return "❌ Error: 'image' field not found in job_spec"
                
                # Step 5: Build the distributed spec
                # CRITICAL FIX: Must explicitly set slots_per_worker=None and ssh_auth_mount_path=None
                # The SDK has hardcoded defaults (slots_per_worker=1, ssh_auth_mount_path="/root/.ssh")
                # These MPI defaults cause API rejection for PyTorch. Setting to None works!
                spec = models.DistributedSpecSpec(
                    image=image,
                    distributed_framework=distributed_framework,
                    num_workers=int(num_workers),
                    compute=compute,
                    # Explicitly set MPI parameters to None for non-MPI frameworks
                    slots_per_worker=int(slots_per_worker) if slots_per_worker and framework_str == "MPI" else None,
                    ssh_auth_mount_path=None,  # Critical: override SDK default
                )
                
                # Add optional command
                if job_spec.get('command'):
                    spec.command = job_spec.get('command')
                
                # Step 6: Create the distributed request with masterSpecSameAsWorker
                distributed_request = models.DistributedCreationRequest(
                    name=job_spec.get('name'),
                    project_id=project_id,
                    cluster_id=cluster_id,
                    master_spec_same_as_worker=True,  # Critical field from UI
                    spec=spec
                )
                
                # Step 7: Submit the distributed job
                logger.info(f"Submitting distributed job with {num_workers} workers using {framework_str}")
                job = client.workloads.distributed.create_distributed(
                    distributed_creation_request=distributed_request
                )
                
                total_gpus = gpu_count * num_workers
                
                return f"""
✅ **Distributed Training Job Submitted Successfully!**

**Job ID:** {job.id if hasattr(job, 'id') else 'N/A'}
**Name:** {job_spec['name']}
**Project:** {project_name} (ID: {project_id})
**Framework:** {framework_str}
**Workers:** {num_workers}
**GPUs per Worker:** {gpu_count}
**Total GPUs:** {total_gpus}
**Status:** Submitted

**📊 Monitor your job:**
Check status in the Run:AI UI or use the `runai_job_status` function

**🌐 View in UI:**
{secure_config['RUNAI_BASE_URL']}/projects/{project_name}/jobs
"""
            except AttributeError as e:
                logger.warning(f"SDK API method not available: {e}")
                return f"""
⚠️  **Submission Method Not Available**

The Run:AI SDK is installed but the distributed API method is not available.
This might be due to SDK version incompatibility.

**Tried:** `client.workloads.distributed.create_distributed()`
**Error:** {str(e)}

**Alternative:** Use `runailabs_job_generator` to generate submission code.

**Job spec validated and ready:**
{preview}
"""
            except Exception as e:
                logger.error(f"Distributed job submission failed: {str(e)}")
                return f"""
❌ **Distributed Job Submission Failed**

**Error:** {str(e)}

**Troubleshooting:**
1. Check your Run:AI credentials are valid
2. Verify the project "{job_spec.get('project')}" exists
3. Ensure you have permission to submit distributed jobs
4. Check that GPU quotas are available for {job_spec.get('numWorkers', 'N/A')} workers
5. Verify the distributed framework is supported on your cluster

**Job spec that failed:**
{preview}
"""
                
        except Exception as e:
            logger.error(f"Distributed workload submission error: {str(e)}")
            return f"❌ Error processing distributed workload submission: {str(e)}"
    
    try:
        yield FunctionInfo.create(
            single_fn=_submit_distributed_job,
            description="Submit distributed/multi-node training jobs (PyTorch DDP, TensorFlow, MPI). Use when user mentions multiple workers or distributed training."
        )
    except GeneratorExit:
        logger.info("Distributed job submitter exited")
    finally:
        logger.info("Cleaning up distributed job submitter")

