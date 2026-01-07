"""Run:AI batch job submission - submit multiple jobs in one operation"""

from typing import List, Optional, Dict, Any
from pydantic import Field
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

from ..utils import get_secure_config, sanitize_input, logger


class RunaiBatchJobSubmitterConfig(FunctionBaseConfig, name="runai_submit_batch"):
    """Submit multiple workloads to Run:AI cluster in one batch operation"""
    description: str = "Submit multiple jobs (training, distributed, or workspace) to Run:AI cluster in one batch. Use when user requests submitting multiple jobs, a list of jobs, or jobs for multiple projects."
    dry_run_default: bool = Field(default=True, description="Always preview before submitting by default")
    require_confirmation: bool = Field(default=True, description="Require explicit user confirmation before batch submission")
    allowed_projects: List[str] = Field(default_factory=lambda: ["*"], description="Whitelisted projects that can be submitted to (use ['*'] for all)")
    max_gpus_per_job: int = Field(default=8, description="Maximum number of GPUs allowed per individual job")
    max_batch_size: int = Field(default=20, description="Maximum number of jobs allowed in one batch")


@register_function(config_type=RunaiBatchJobSubmitterConfig)
async def runai_submit_batch(config: RunaiBatchJobSubmitterConfig, builder: Builder):
    """
    Submit multiple workloads to Run:AI cluster in one batch operation.
    
    This function allows submitting multiple jobs (training, distributed, or workspace) in a single call.
    Each job is validated and submitted independently, with comprehensive error handling.
    
    Args:
        jobs: List of job specifications, each containing:
            - type: "training", "distributed", or "workspace"
            - name: Job name
            - project: Project name
            - image: Container image
            - gpus: Number of GPUs (for training/workspace)
            - workers: Number of workers (for distributed only)
            - framework: Framework type (for distributed only)
            - workspace_type: Type of workspace (for workspace only)
            - command: Optional command
            - args: Optional arguments
        dry_run: Preview jobs without submitting (default: True)
        confirmed: Skip confirmation prompt (default: False)
        continue_on_error: Continue submitting remaining jobs if one fails (default: True)
    
    Returns:
        Detailed batch submission report with success/failure status for each job
    
    Examples:
        Submit 3 training jobs:
        {
            "jobs": [
                {"type": "training", "name": "job1", "project": "project-01", "image": "pytorch/pytorch:latest", "gpus": 2},
                {"type": "training", "name": "job2", "project": "project-01", "image": "pytorch/pytorch:latest", "gpus": 1},
                {"type": "training", "name": "job3", "project": "project-02", "image": "tensorflow/tensorflow:latest", "gpus": 4}
            ],
            "dry_run": False,
            "confirmed": True
        }
        
        Submit mixed workload types:
        {
            "jobs": [
                {"type": "training", "name": "training-job", "project": "project-01", "image": "pytorch/pytorch:latest", "gpus": 2},
                {"type": "distributed", "name": "dist-job", "project": "project-01", "image": "nvcr.io/nvidia/pytorch:latest", "workers": 4, "gpus": 2, "framework": "pytorch"},
                {"type": "workspace", "name": "jupyter-ws", "project": "project-01", "image": "jupyter/scipy-notebook", "gpus": 1, "workspace_type": "jupyter"}
            ],
            "dry_run": True
        }
    """
    
    # Check if Run:AI SDK is available
    try:
        from runai.runai_client import RunaiClient
        from runai import models
        SDK_AVAILABLE = True
        logger.debug("✓ Run:AI SDK is available for batch submission")
    except ImportError:
        SDK_AVAILABLE = False
        logger.warning("⚠️  Run:AI SDK not installed. Batch submission will be unavailable.")
    
    def generate_batch_preview(jobs: List[Dict[str, Any]]) -> str:
        """Generate a preview summary of all jobs in the batch"""
        preview_lines = ["📋 **Batch Job Preview**\n"]
        preview_lines.append(f"**Total Jobs:** {len(jobs)}\n")
        
        # Count by type
        type_counts = {}
        total_gpus = 0
        
        for job in jobs:
            job_type = job.get("type", "training")
            type_counts[job_type] = type_counts.get(job_type, 0) + 1
            
            # Calculate GPU count
            if job_type == "distributed":
                workers = job.get("workers", 1)
                gpus = job.get("gpus", 0)
                total_gpus += (workers + 1) * gpus  # workers + master
            else:
                total_gpus += job.get("gpus", 0)
        
        preview_lines.append(f"**Job Types:**")
        for job_type, count in type_counts.items():
            preview_lines.append(f"  • {job_type.title()}: {count}")
        
        preview_lines.append(f"\n**Total GPUs Required:** {total_gpus}\n")
        
        # List each job
        preview_lines.append("**Jobs to Submit:**\n")
        for idx, job in enumerate(jobs, 1):
            job_type = job.get("type", "training")
            name = job.get("name", f"job-{idx}")
            project = job.get("project", "unknown")
            image = job.get("image", "not specified")
            
            preview_lines.append(f"{idx}. **{name}** ({job_type})")
            preview_lines.append(f"   - Project: {project}")
            preview_lines.append(f"   - Image: {image}")
            
            if job_type == "distributed":
                workers = job.get("workers", 1)
                gpus = job.get("gpus", 0)
                framework = job.get("framework", "pytorch")
                preview_lines.append(f"   - Workers: {workers}, GPUs/worker: {gpus}, Framework: {framework}")
            elif job_type == "workspace":
                gpus = job.get("gpus", 0)
                workspace_type = job.get("workspace_type", "custom")
                preview_lines.append(f"   - Type: {workspace_type}, GPUs: {gpus}")
            else:  # training
                gpus = job.get("gpus", 0)
                preview_lines.append(f"   - GPUs: {gpus}")
            
            preview_lines.append("")
        
        return "\n".join(preview_lines)
    
    async def _submit_batch_jobs(
        jobs: List[Dict[str, Any]],
        dry_run: Optional[bool] = None,
        confirmed: bool = False,
        continue_on_error: bool = True
    ) -> str:
        """
        Submit a batch of jobs to Run:AI cluster
        """
        # Use config defaults if not explicitly set
        is_dry_run = dry_run if dry_run is not None else config.dry_run_default
        
        # Validate inputs
        if not jobs or not isinstance(jobs, list):
            return "❌ Error: 'jobs' must be a non-empty list"
        
        if len(jobs) > config.max_batch_size:
            return f"❌ Error: Batch size ({len(jobs)}) exceeds maximum allowed ({config.max_batch_size})"
        
        # Sanitize and validate each job spec
        validated_jobs = []
        for idx, job in enumerate(jobs, 1):
            if not isinstance(job, dict):
                return f"❌ Error: Job #{idx} must be a dictionary"
            
            # Set default type if not specified
            if "type" not in job:
                job["type"] = "training"
            
            # Validate job type
            job_type = job.get("type", "").lower()
            if job_type not in ["training", "distributed", "workspace"]:
                return f"❌ Error: Job #{idx} has invalid type '{job_type}'. Must be 'training', 'distributed', or 'workspace'"
            
            # Validate required fields
            if not job.get("name"):
                return f"❌ Error: Job #{idx} missing required field 'name'"
            
            if not job.get("project"):
                return f"❌ Error: Job #{idx} ({job.get('name')}) missing required field 'project'"
            
            if not job.get("image"):
                return f"❌ Error: Job #{idx} ({job.get('name')}) missing required field 'image'"
            
            # Validate project whitelist
            project_name = job.get("project")
            if "*" not in config.allowed_projects and project_name not in config.allowed_projects:
                return f"❌ Error: Job #{idx} ({job.get('name')}): Project '{project_name}' is not in allowed list: {config.allowed_projects}"
            
            # Validate GPU limits
            if job_type == "distributed":
                gpus_per_worker = job.get("gpus", 0)
                if gpus_per_worker > config.max_gpus_per_job:
                    return f"❌ Error: Job #{idx} ({job.get('name')}): GPUs per worker ({gpus_per_worker}) exceeds max ({config.max_gpus_per_job})"
            else:
                gpus = job.get("gpus", 0)
                if gpus > config.max_gpus_per_job:
                    return f"❌ Error: Job #{idx} ({job.get('name')}): GPU count ({gpus}) exceeds max ({config.max_gpus_per_job})"
            
            validated_jobs.append(job)
        
        # Generate preview
        preview = generate_batch_preview(validated_jobs)
        
        # If dry-run, return preview
        if is_dry_run:
            return f"""
{preview}

✅ **Validation Passed**

This is a **DRY RUN** - no jobs will be submitted.

To submit these jobs, set:
- `dry_run=False`
- `confirmed=True`
"""
        
        # If not confirmed, ask for confirmation
        if config.require_confirmation and not confirmed:
            return f"""
{preview}

⚠️  **Confirmation Required**

You are about to submit **{len(validated_jobs)} jobs** to Run:AI cluster.

To proceed, set `confirmed=True` in your request.
To cancel, do not resubmit or set `confirmed=False`.
"""
        
        # Check SDK availability (checked at top level)
        if not SDK_AVAILABLE:
            return """
⚠️  **Run:AI SDK Not Installed**

The batch submission feature requires the Run:AI SDK.

**Installation:**
```bash
pip install runapy==1.223.0
```

**Alternative:** Use individual submission tools:
- `runai_submit_workload` for single training jobs
- `runai_submit_distributed_workload` for distributed jobs
- `runai_submit_workspace` for workspace submissions
"""
        
        # Get Run:AI credentials
        try:
            secure_config = get_secure_config()
        except ValueError as e:
            return f"❌ Configuration Error: {str(e)}"
        
        # Initialize Run:AI client
        try:
            from runai.configuration import Configuration
            from runai.api_client import ApiClient
            
            configuration = Configuration(
                client_id=secure_config['RUNAI_CLIENT_ID'],
                client_secret=secure_config['RUNAI_CLIENT_SECRET'],
                runai_base_url=secure_config['RUNAI_BASE_URL'],
            )
            client = RunaiClient(ApiClient(configuration))
            logger.info("✓ Run:AI client initialized for batch submission")
        except Exception as e:
            logger.error(f"Failed to initialize Run:AI client: {str(e)}")
            return f"❌ Failed to initialize Run:AI client: {str(e)}"
        
        # Submit each job
        results = []
        success_count = 0
        failure_count = 0
        
        for idx, job in enumerate(validated_jobs, 1):
            job_name = job.get("name")
            job_type = job.get("type")
            project_name = job.get("project")
            
            logger.info(f"Submitting job {idx}/{len(validated_jobs)}: {job_name} ({job_type})")
            
            try:
                # Get project details
                projects_response = client.organizations.projects.get_projects()
                projects_data = projects_response.data if hasattr(projects_response, 'data') else projects_response
                projects = projects_data.get("projects", []) if isinstance(projects_data, dict) else []
                
                project = next((p for p in projects if p.get("name") == project_name), None)
                if not project:
                    error_msg = f"Project '{project_name}' not found"
                    results.append({
                        "job": job_name,
                        "status": "failed",
                        "error": error_msg
                    })
                    failure_count += 1
                    logger.error(f"✗ Job {idx} failed: {error_msg}")
                    
                    if not continue_on_error:
                        break
                    continue
                
                # Convert to string for API compatibility
                project_id = str(project.get("id"))
                cluster_id = str(project.get("clusterId"))
                
                # Submit based on job type
                if job_type == "training":
                    result = await _submit_training_job(client, models, job, project_id, cluster_id)
                elif job_type == "distributed":
                    result = await _submit_distributed_job(client, models, job, project_id, cluster_id)
                elif job_type == "workspace":
                    result = await _submit_workspace_job(client, models, job, project_id, cluster_id)
                else:
                    result = {"status": "failed", "error": f"Unknown job type: {job_type}"}
                
                result["job"] = job_name
                results.append(result)
                
                if result.get("status") == "success":
                    success_count += 1
                    logger.info(f"✓ Job {idx} submitted successfully: {job_name}")
                else:
                    failure_count += 1
                    logger.error(f"✗ Job {idx} failed: {result.get('error', 'Unknown error')}")
                    
                    if not continue_on_error:
                        break
                
            except Exception as e:
                error_msg = str(e)
                results.append({
                    "job": job_name,
                    "status": "failed",
                    "error": error_msg
                })
                failure_count += 1
                logger.error(f"✗ Job {idx} failed with exception: {error_msg}")
                
                if not continue_on_error:
                    break
        
        # Generate final report
        report_lines = ["🎯 **Batch Submission Complete**\n"]
        report_lines.append(f"**Total Jobs:** {len(validated_jobs)}")
        report_lines.append(f"**Successful:** {success_count} ✅")
        report_lines.append(f"**Failed:** {failure_count} ❌\n")
        
        report_lines.append("**Detailed Results:**\n")
        for result in results:
            job_name = result.get("job", "unknown")
            status = result.get("status", "unknown")
            
            if status == "success":
                job_id = result.get("job_id", "N/A")
                report_lines.append(f"✅ **{job_name}**")
                report_lines.append(f"   Status: Submitted")
                report_lines.append(f"   Job ID: {job_id}")
            else:
                error = result.get("error", "Unknown error")
                report_lines.append(f"❌ **{job_name}**")
                report_lines.append(f"   Status: Failed")
                report_lines.append(f"   Error: {error}")
            
            report_lines.append("")
        
        # Add summary message
        if failure_count == 0:
            report_lines.append("🎉 **All jobs submitted successfully!**")
        elif success_count > 0:
            report_lines.append("⚠️  **Partial success** - Some jobs failed. Check details above.")
        else:
            report_lines.append("❌ **All jobs failed** - Check errors above and retry.")
        
        return "\n".join(report_lines)
    
    async def _submit_training_job(client, models, job: Dict, project_id: str, cluster_id: str) -> Dict:
        """Submit a single training job"""
        try:
            gpus = job.get("gpus", 0)
            
            compute = models.SupersetSpecAllOfCompute(
                gpu_devices_request=int(gpus) if gpus else 0,
                gpu_portion_request=1,
                cpu_core_request=0.1,
                cpu_memory_request="100M",
                gpu_request_type="portion"
            )
            
            spec = models.TrainingSpecSpec(
                image=job.get("image"),
                compute=compute
            )
            
            if job.get("command"):
                spec.command = job.get("command")
            
            training_request = models.TrainingCreationRequest(
                name=job.get("name"),
                project_id=project_id,  # Already a string
                cluster_id=cluster_id,  # Already a string
                spec=spec
            )
            
            result = client.workloads.trainings.create_training1(training_request)
            
            return {
                "status": "success",
                "job_id": result.id if hasattr(result, 'id') else 'N/A'
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _submit_distributed_job(client, models, job: Dict, project_id: str, cluster_id: str) -> Dict:
        """Submit a single distributed training job"""
        try:
            workers = job.get("workers", 2)
            gpus = job.get("gpus", 1)
            framework = job.get("framework", "pytorch").upper()
            
            # Map framework names
            framework_map = {
                "PYTORCH": "PyTorch",
                "TENSORFLOW": "TensorFlow",
                "TF": "TensorFlow",
                "MPI": "MPI",
                "JAX": "JAX",
                "XGBOOST": "XGBoost"
            }
            framework_str = framework_map.get(framework, "PyTorch")
            
            compute = models.SupersetSpecAllOfCompute(
                gpu_devices_request=int(gpus) if gpus else 0,
                gpu_portion_request=1,
                cpu_core_request=0.1,
                cpu_memory_request="100M",
                gpu_request_type="portion"
            )
            
            spec = models.DistributedSpecSpec(
                image=job.get("image"),
                distributed_framework=framework_str,
                num_workers=int(workers),
                compute=compute,
                slots_per_worker=None,
                ssh_auth_mount_path=None
            )
            
            if job.get("command"):
                spec.command = job.get("command")
            
            distributed_request = models.DistributedCreationRequest(
                name=job.get("name"),
                project_id=project_id,  # Already a string
                cluster_id=cluster_id,  # Already a string
                master_spec_same_as_worker=True,
                spec=spec
            )
            
            result = client.workloads.distributed.create_distributed(
                distributed_creation_request=distributed_request
            )
            
            return {
                "status": "success",
                "job_id": result.id if hasattr(result, 'id') else 'N/A'
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _submit_workspace_job(client, models, job: Dict, project_id: str, cluster_id: str) -> Dict:
        """Submit a single workspace"""
        try:
            gpus = job.get("gpus", 0)
            workspace_type = job.get("workspace_type", "jupyter").lower()
            
            compute = models.SupersetSpecAllOfCompute(
                gpu_devices_request=int(gpus) if gpus >= 1 else 0,
                gpu_portion_request=float(gpus) if gpus < 1 and gpus > 0 else 1,
                cpu_core_request=0.1,
                cpu_memory_request="100M",
                gpu_request_type="portion"
            )
            
            # Workspace configurations
            workspace_configs = {
                "jupyter": {
                    "command": None,
                    "args": ["start-notebook.sh", "--NotebookApp.base_url=/${RUNAI_PROJECT}/${RUNAI_JOB_NAME}", "--NotebookApp.token=''"],
                    "port": 8888,
                    "tool_type": "jupyter-notebook",
                    "tool_name": "Jupyter"
                },
                "vscode": {
                    "command": None,
                    "args": None,
                    "port": 8080,
                    "tool_type": "vscode",
                    "tool_name": "VSCode"
                }
            }
            
            config_data = workspace_configs.get(workspace_type, {
                "command": None,
                "args": None,
                "port": 8080,
                "tool_type": "custom",
                "tool_name": workspace_type.title()
            })
            
            exposed_urls = [
                models.ExposedUrl(
                    container=config_data["port"],
                    tool_type=config_data["tool_type"],
                    tool_name=config_data["tool_name"],
                    name=config_data["tool_name"]
                )
            ]
            
            spec = models.WorkspaceSpecSpec(
                image=job.get("image"),
                command=job.get("command") or config_data["command"],
                args=job.get("args") or config_data["args"],
                compute=compute,
                exposedUrls=exposed_urls,
                imagePullPolicy="IfNotPresent"
            )
            
            workspace_request = models.WorkspaceCreationRequest(
                name=job.get("name"),
                projectId=project_id,  # Already a string
                clusterId=cluster_id,  # Already a string
                spec=spec
            )
            
            result = client.workloads.workspaces.create_workspace1(workspace_request)
            
            return {
                "status": "success",
                "job_id": result.id if hasattr(result, 'id') else 'N/A'
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    try:
        yield FunctionInfo.create(
            single_fn=_submit_batch_jobs,
            description=config.description
        )
    except GeneratorExit:
        logger.info("Batch job submitter exited")
    finally:
        logger.info("Cleaning up batch job submitter")

