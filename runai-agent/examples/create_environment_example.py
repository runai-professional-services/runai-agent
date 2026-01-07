"""
Example: Creating Run:AI Environments

This example demonstrates how to create Run:AI environment templates
using the runai_create_environment function.
"""

# Example 1: Basic ML Training Environment
# =========================================

basic_ml_env = {
    "name": "ml-training-basic",
    "scope": "project",
    "scope_id": "project-01-id",
    "description": "Basic ML training environment with GPU support",
    "image": "nvcr.io/nvidia/pytorch:24.01-py3",
    "compute": {
        "gpu": 2,
        "cpu_cores": 8,
        "memory": "64Gi"
    }
}

# Step 1: Preview the environment (dry-run mode)
# This validates and shows what will be created
# result = runai_create_environment(env_spec=basic_ml_env)

# Step 2: Actually create after reviewing preview
# result = runai_create_environment(
#     env_spec=basic_ml_env,
#     dry_run=False,
#     confirmed=True
# )


# Example 2: Distributed Training Environment
# ============================================

distributed_env = {
    "name": "distributed-training-env",
    "scope": "cluster",
    "scope_id": "my-cluster-id",
    "description": "Distributed training environment optimized for multi-node training",
    "image": "nvcr.io/nvidia/pytorch:24.01-py3",
    "compute": {
        "gpu": 4,
        "cpu_cores": 16,
        "memory": "128Gi"
    },
    "environment_variables": {
        "NCCL_DEBUG": "INFO",
        "NCCL_IB_DISABLE": "0",
        "NCCL_NET_GDR_LEVEL": "5",
        "OMP_NUM_THREADS": "8",
        "CUDA_VISIBLE_DEVICES": "0,1,2,3"
    },
    "tools": ["jupyter", "tensorboard"]
}

# result = runai_create_environment(
#     env_spec=distributed_env,
#     dry_run=False,
#     confirmed=True
# )


# Example 3: Data Science Team Environment
# =========================================

data_science_env = {
    "name": "data-science-standard",
    "scope": "project",
    "scope_id": "ds-team-project-id",
    "description": "Standard data science environment with Jupyter and common ML libraries",
    "image": "jupyter/datascience-notebook:latest",
    "compute": {
        "gpu": 1,
        "cpu_cores": 4,
        "memory": "32Gi"
    },
    "environment_variables": {
        "JUPYTER_ENABLE_LAB": "yes",
        "GRANT_SUDO": "yes"
    },
    "tools": ["jupyter", "tensorboard", "vscode"]
}

# result = runai_create_environment(
#     env_spec=data_science_env,
#     dry_run=False,
#     confirmed=True
# )


# Example 4: Production Inference Environment
# ===========================================

inference_env = {
    "name": "prod-inference",
    "scope": "cluster",
    "scope_id": "prod-cluster-id",
    "description": "Production-grade inference environment with Triton Server",
    "image": "nvcr.io/nvidia/tritonserver:24.01-py3",
    "compute": {
        "gpu": 2,
        "cpu_cores": 8,
        "memory": "64Gi"
    },
    "environment_variables": {
        "TRITON_SERVER_HTTP_PORT": "8000",
        "TRITON_SERVER_GRPC_PORT": "8001",
        "TRITON_SERVER_METRICS_PORT": "8002",
        "LOG_LEVEL": "INFO",
        "TRITON_MODEL_REPOSITORY": "/models"
    }
}

# result = runai_create_environment(
#     env_spec=inference_env,
#     dry_run=False,
#     confirmed=True
# )


# Example 5: Tenant-Level Default Environment
# ===========================================

tenant_default_env = {
    "name": "org-default-gpu",
    "scope": "tenant",
    "description": "Organization-wide default GPU environment",
    "image": "nvcr.io/nvidia/cuda:12.3.0-base-ubuntu22.04",
    "compute": {
        "gpu": 1,
        "cpu_cores": 4,
        "memory": "16Gi"
    },
    "environment_variables": {
        "CUDA_HOME": "/usr/local/cuda",
        "PATH": "/usr/local/cuda/bin:$PATH",
        "LD_LIBRARY_PATH": "/usr/local/cuda/lib64:$LD_LIBRARY_PATH"
    }
}

# result = runai_create_environment(
#     env_spec=tenant_default_env,
#     dry_run=False,
#     confirmed=True
# )


# Example 6: Minimal CPU-Only Environment
# ========================================

cpu_only_env = {
    "name": "cpu-lightweight",
    "scope": "project",
    "scope_id": "dev-project-id",
    "description": "Lightweight CPU-only environment for testing",
    "image": "python:3.11-slim",
    "compute": {
        "cpu_cores": 2,
        "memory": "8Gi"
    }
}

# result = runai_create_environment(
#     env_spec=cpu_only_env,
#     dry_run=False,
#     confirmed=True
# )


# Example 7: Using with NAT Agent
# ================================

# You can also use natural language with the agent:
"""
Agent prompts:
- "Create a new ML training environment with 4 GPUs and PyTorch"
- "Set up a Jupyter environment template for the data science team"
- "Create a tenant-level environment for inference workloads"
- "Make an environment for distributed training with NCCL optimizations"
"""


# Example 8: Error Handling
# ==========================

# Invalid environment (missing required fields)
invalid_env = {
    "name": "test-env"
    # Missing: scope, image
}

# This will fail validation:
# result = runai_create_environment(env_spec=invalid_env)
# Output: ❌ Environment Validation Failed
#         **Validation Errors:**
#           • Missing required field: 'scope' (tenant/cluster/project)
#           • Missing required field: 'image' or 'default_image'


# Example 9: Complete Workflow
# =============================

def create_environment_workflow(env_spec):
    """
    Complete workflow for creating an environment
    """
    print("Step 1: Validating environment spec...")
    # Preview first
    preview_result = runai_create_environment(env_spec=env_spec)
    print(preview_result)
    
    # Review the preview
    user_confirmed = input("\nDo you want to create this environment? (yes/no): ")
    
    if user_confirmed.lower() == 'yes':
        print("\nStep 2: Creating environment...")
        # Actually create
        create_result = runai_create_environment(
            env_spec=env_spec,
            dry_run=False,
            confirmed=True
        )
        print(create_result)
    else:
        print("Environment creation cancelled.")

# Usage:
# create_environment_workflow(basic_ml_env)


# Example 10: Integration with Job Submission
# ============================================

# After creating an environment, reference it in job submissions:
"""
# 1. Create the environment
env_result = runai_create_environment(
    env_spec=distributed_env,
    dry_run=False,
    confirmed=True
)

# 2. Use it in a job submission
job_spec = {
    "name": "my-training-job",
    "project": "project-01",
    "image": "nvcr.io/nvidia/pytorch:24.01-py3",  # From environment
    "gpu": 4,  # From environment defaults
    "command": "python",
    "args": "train.py --epochs 100",
    # Environment variables from template will be applied
}

job_result = runai_submit_workload(job_spec=job_spec, dry_run=False, confirmed=True)
"""

