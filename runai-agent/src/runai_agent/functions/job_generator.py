"""Run:AI job generation function with real GitHub examples"""

import os
import json
from datetime import datetime
from typing import Dict, Optional
from pathlib import Path
from pydantic import Field, validator
import aiofiles
from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

from ..utils import get_secure_config, sanitize_input, examples_fetcher, logger


class RunailabsJobGeneratorConfig(FunctionBaseConfig, name="runailabs_job_generator"):
    """Generate RunaiLabs job submission code for any workload type."""
    description: str = "Generate Python code for job submission by fetching real examples from GitHub. Use when user requests code generation or examples."
    show_code_in_output: bool = Field(default=True, description="Whether to display generated code in stdout output")
    save_to_file: bool = Field(default=False, description="Whether to save generated code to a file")
    auto_search_examples: bool = Field(default=True, description="Automatically search for real SDK examples before generating code (requires runapy_code_search function)")
    
    @validator('*', pre=True)
    def validate_inputs(cls, v):
        """Validate and sanitize all inputs."""
        if isinstance(v, str):
            return sanitize_input(v)
        return v


@register_function(config_type=RunailabsJobGeneratorConfig)
async def runailabs_job_generator(config: RunailabsJobGeneratorConfig, builder: Builder):
    """Generate Python code for submitting Run:AI jobs"""
    
    async def _response_fn(input_message: str) -> str:
        try:
            # Sanitize input
            input_message = sanitize_input(input_message)
            input_lower = input_message.lower()
            now = datetime.now().strftime('%Y%m%d-%H%M%S')
            
            # Fetch real examples from GitHub
            real_example = None
            search_note = ""
            
            if config.auto_search_examples:
                try:
                    logger.info("🔍 Fetching runapy examples from GitHub...")
                    
                    # Fetch examples (uses cache if available)
                    examples = await examples_fetcher.get_examples()
                    
                    # Determine category based on job type
                    if any(word in input_lower for word in ['distributed', 'multi-gpu', 'parallel']):
                        category = "distributed"
                    elif any(word in input_lower for word in ['workspace', 'notebook', 'jupyter']):
                        category = "workspace"
                    elif any(word in input_lower for word in ['inference', 'serving']):
                        category = "general"  # inference examples might be in general
                    else:
                        category = "training"
                    
                    # Find relevant example
                    real_example = examples_fetcher.find_relevant_example(input_message, category)
                    
                    if real_example:
                        search_note = f"\n✅ **Using real example from GitHub**: `{real_example['filename']}`\n{real_example['description']}\n"
                        logger.info(f"✓ Using example: {real_example['filename']}")
                    else:
                        search_note = "\n💡 **Note**: No specific examples found. Using fallback template.\n"
                        logger.warning("No examples found, using fallback template")
                        
                except Exception as e:
                    logger.warning(f"Example fetch failed: {e}")
                    search_note = "\n💡 **Note**: Could not fetch examples from GitHub. Using fallback template.\n"
            else:
                search_note = "\n💡 **Note**: Auto-search disabled. Using template-based generation.\n"

            # Get secure configuration
            secure_config = get_secure_config()

            # Default output directory (user-writable, can override with RUNAI_OUTPUT_DIR)
            output_dir = Path(os.getenv("RUNAI_OUTPUT_DIR", "/tmp/runai/output"))
            output_dir.mkdir(parents=True, exist_ok=True)

            # Enhanced workload detection with better patterns
            workload_patterns = {
                'jupyter_workspace': ['workspace', 'notebook', 'jupyter', 'dev', 'interactive'],
                'inference': ['inference', 'serving', 'model', 'predict', 'triton'],
                'distributed': ['distributed', 'multi-gpu', 'multi-gpu', 'parallel'],
                'training': ['train', 'training', 'fit', 'epoch', 'model training']
            }

            # Detect workload type
            job_type = None
            for pattern_type, patterns in workload_patterns.items():
                if any(pattern in input_lower for pattern in patterns):
                    job_type = pattern_type
                    break

            if not job_type:
                # Default to training if no specific pattern detected
                job_type = 'training'

            # Generate job template based on type
            job_template = await generate_job_template(
                job_type, 
                input_message, 
                now, 
                secure_config,
                output_dir,
                config.show_code_in_output,
                config.save_to_file,
                search_note,
                real_example
            )

            return job_template

        except Exception as e:
            logger.error(f"Job generation error: {str(e)}")
            return f"❌ Error generating job: {str(e)}"

    async def generate_job_template(
        job_type: str, 
        input_message: str, 
        timestamp: str, 
        config: Dict[str, str],
        output_dir: Path,
        show_code_in_output: bool = True,
        save_to_file: bool = False,
        search_note: str = "",
        real_example: Optional[Dict[str, str]] = None
    ) -> str:
        """Generate job template with enhanced security and validation."""
        
        # If we have a real example from GitHub, use it as the base
        if real_example:
            logger.info(f"Using real example: {real_example['filename']}")
            
            # Use the real example code with minimal modifications
            example_code = real_example['code']
            
            # Add configuration setup at the top if not present
            if "Configuration(" not in example_code:
                config_header = """# Secure configuration from environment variables
from runai.configuration import Configuration
from runai.api_client import ApiClient
from runai.runai_client import RunaiClient

configuration = Configuration(
    client_id=os.environ.get('RUNAI_CLIENT_ID'),
    client_secret=os.environ.get('RUNAI_CLIENT_SECRET'),
    runai_base_url=os.environ.get('RUNAI_BASE_URL'),
)
client = RunaiClient(ApiClient(configuration))

"""
                example_code = config_header + example_code
            
            # Return with clear markdown formatting (must preserve newlines)
            response_message = f"""✅ Generated {job_type.replace('_', ' ').title()} job code using real GitHub example: `{real_example['filename']}`

📄 **Complete Python Script:**

```python
{example_code}
```

💡 **To use this code:**
1. Copy the complete script above
2. Set environment variables: RUNAI_CLIENT_ID, RUNAI_CLIENT_SECRET, RUNAI_BASE_URL  
3. Run: `python your_script.py`
"""
            return response_message
        
        # Fallback: Use template-based generation
        base_config = f"""
# RunaiLabs {job_type.replace('_', ' ').title()} Job
import os
import sys
from runai.configuration import Configuration
from runai.api_client import ApiClient
from runai.runai_client import RunaiClient
from datetime import datetime

# Secure configuration from environment variables
configuration = Configuration(
    client_id=os.environ.get('RUNAI_CLIENT_ID'),
    client_secret=os.environ.get('RUNAI_CLIENT_SECRET'),
    runai_base_url=os.environ.get('RUNAI_BASE_URL'),
)
client = RunaiClient(ApiClient(configuration))
"""

        # Job-specific configurations
        job_configs = {
            'jupyter_workspace': {
                'name': f"jupyter-workspace-{timestamp}",
                'image': "jupyter/scipy-notebook:latest",
                'command': "start-notebook.sh --NotebookApp.token='' --NotebookApp.allow_origin='*'",
                'resources': {"gpu": 1, "cpu": 4, "memory": "16Gi"},
                'external_url': {"container": 8888},
                'description': "Interactive Jupyter workspace for development and experimentation"
            },
            'inference': {
                'name': f"inference-service-{timestamp}",
                'image': "nvcr.io/nvidia/tritonserver:23.10-py3",
                'command': "tritonserver --model-repository=/models --http-thread-count=4",
                'resources': {"gpu": 1, "cpu": 2, "memory": "8Gi"},
                'external_url': {"container": 8000, "external": 8080},
                'description': "Model inference service using NVIDIA Triton"
            },
            'distributed': {
                'name': f"dist-training-{timestamp}",
                'image': "pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime",
                'command': "python -m torch.distributed.launch --nproc_per_node=1 train.py --epochs 90",
                'resources': {"gpu": 1, "cpu": 4, "memory": "16Gi"},
                'distributed': {
                    "nodes": 2,
                    "processes_per_node": 1,
                    "framework": "PyTorch"
                },
                'description': "Distributed training job with PyTorch"
            },
            'training': {
                'name': f"training-job-{timestamp}",
                'image': "pytorch/pytorch:2.1.0-cuda12.1-cudnn8-runtime",
                'command': "python train.py --epochs 50 --batch-size 32",
                'resources': {"gpu": 1, "cpu": 4, "memory": "16Gi"},
                'description': "Single-GPU training job"
            }
        }

        job_spec = job_configs[job_type]
        
        # Generate the complete job code
        job_code = f"""{base_config}

# Job specification
job_spec = {{
    "name": "{job_spec['name']}",
    "project": "test",
    "image": "{job_spec['image']}",
    "command": "{job_spec['command']}",
    "resources": {json.dumps(job_spec['resources'], indent=4)},
"""

        # Add job-specific fields
        if 'external_url' in job_spec:
            job_code += f'    "external_url": {json.dumps(job_spec["external_url"], indent=4)},\n'
        if 'expose_ports' in job_spec:
            job_code += f'    "expose_ports": {json.dumps(job_spec["expose_ports"], indent=4)},\n'  # kept for safety if present
        if 'distributed' in job_spec:
            job_code += f'    "distributed": {json.dumps(job_spec["distributed"], indent=4)},\n'

        job_code += """}

print(f"📋 {job_spec['description']}")
print("Job Configuration:")
print(json.dumps(job_spec, indent=2))

# Submit the job using the correct Run:AI API
# Uncomment the code below to actually submit:
# 
# from runai import models
# 
# # Get project details
# projects_response = client.organizations.projects.get_projects()
# projects_data = projects_response.data
# project_list = projects_data.get("projects", [])
# 
# # Find project and cluster IDs
# project_id = None
# cluster_id = None
# for project in project_list:
#     if project.get("name") == job_spec["project"]:
#         project_id = project.get("id")
#         cluster_id = project.get("clusterId")
#         break
# 
# # Build compute resources
# compute = models.SupersetSpecAllOfCompute(
#     gpu_devices_request=job_spec["resources"]["gpu"],
#     gpu_portion_request=1,
#     cpu_core_request=job_spec["resources"].get("cpu", 0.1),
#     cpu_memory_request=job_spec["resources"].get("memory", "100M"),
#     gpu_request_type="portion"
# )
# 
# # Build training spec
# spec = models.TrainingSpecSpec(
#     image=job_spec["image"],
#     command=job_spec["command"],
#     compute=compute
# )
# 
# # Create training request
# training_request = models.TrainingCreationRequest(
#     name=job_spec["name"],
#     project_id=project_id,
#     cluster_id=cluster_id,
#     spec=spec
# )
# 
# # Submit the job
# try:
#     job = client.workloads.trainings.create_training1(training_request)
#     print(f"✅ Job submitted successfully!")
#     print(f"Job Name: {job_spec['name']}")
#     print(f"Project: {job_spec['project']}")
# except Exception as e:
#     print(f"❌ Job submission failed: {{str(e)}}")
"""

        # Build the response message with explicit instruction for the agent
        response_message = f"""✅ Generated {job_type.replace('_', ' ').title()} Job Template

**Job Type:** {job_spec['description']}
**Resources:** {job_spec['resources']}

{search_note}
"""

        # Conditionally save to file
        if save_to_file:
            filename = output_dir / f"{job_type}_{timestamp}.py"
            async with aiofiles.open(filename, 'w') as f:
                await f.write(job_code)
            response_message += f"\n**File:** {filename}\n\nThe job template has been saved to: {filename}\n"
        
        # Add usage instructions
        response_message += "\nTo submit the job, uncomment the submission code in the script below."

        # Add generated code to output if requested
        if show_code_in_output:
            response_message += f"""

## 📄 Generated Code:

```python
{job_code}
```
"""
        
        return response_message

    try:
        yield FunctionInfo.create(
            single_fn=_response_fn,
            description="Generate Python code for job submission by fetching real examples from GitHub. Use when user requests code generation or examples."
        )
    except GeneratorExit:
        logger.info("Job generator exited")
    finally:
        logger.info("Cleaning up job generator")

