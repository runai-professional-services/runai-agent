# Run:AI Environment Management Guide

## Overview

This guide covers creating and deleting Run:AI environment templates. Environment templates define compute resources, Docker images, environment variables, and other configurations that can be applied to multiple workloads.

### Available Functions

- **`runai_create_environment`**: Create new environment templates
- **`runai_delete_environment`**: Delete existing environment templates

## Features

- ✅ **Safety First**: Dry-run mode and explicit confirmation required
- ✅ **Validation**: Comprehensive spec validation before creation
- ✅ **Resource Limits**: Enforced limits on CPU, memory, and GPU allocation
- ✅ **Multi-Scope**: Support for cluster and project scopes
- ✅ **Auto-Fetch**: Automatic cluster ID retrieval for cluster scope
- ✅ **Detailed Preview**: See exactly what will be created before committing

## Quick Start

**Fastest way to create an environment:**

```bash
nat run --input "Create environment named my-env with image busybox for workspace and training" \
  --config_file runai-agent/configs/workflow.yaml
```

That's it! The agent handles everything automatically:
- ✅ Defaults to cluster scope
- ✅ Auto-fetches cluster ID
- ✅ Creates environment with proper configuration
- ✅ Returns success confirmation

## Configuration

The function can be configured in your `workflow.yaml`:

```yaml
runai_create_environment:
  _type: runai_create_environment
  dry_run_default: true            # Preview by default
  require_confirmation: true       # Require explicit confirmation
  allowed_scopes: ["tenant", "cluster", "project"]
  max_cpu_cores: 32.0             # Maximum CPU cores per environment
  max_memory_gb: 256              # Maximum memory in GB
  max_gpus: 8                     # Maximum GPUs per environment
```

## Usage Examples

### ⭐ Example 1: Using Natural Language (Easiest - Recommended)

The simplest way to create an environment is using natural language with the NAT agent:

```bash
# This command automatically handles everything!
nat run --input "Create a new runai environment named busybox-test with the image busybox for workspace and training workloads in the cluster scope." \
  --config_file runai-agent/configs/workflow.yaml
```

**What happens automatically:**
- ✅ Uses cluster scope (default and recommended)
- ✅ Auto-fetches the cluster ID from your Run:AI deployment
- ✅ Validates the environment spec
- ✅ Creates the environment with correct workload types
- ✅ Returns success confirmation with environment details

**Success Output:**
```
✅ Environment Created Successfully!

Environment ID: env-abc123
Name: busybox-test
Scope: cluster
Image: busybox
Image Pull Policy: IfNotPresent
Status: Created

Supported Workload Types:
  ✓ workspace
  ✓ training

🔧 Usage:
This environment can now be used as a template when creating:
- Training jobs
- Interactive workspaces
- Distributed training workloads

🌐 View in UI:
https://your-cluster.com/assets/environments
```

### Example 2: Cluster-Scoped Environment (No Cluster ID Needed)

Create an environment at cluster scope - the cluster ID is automatically fetched:

```python
env_spec = {
    "name": "ml-training-env",
    "scope": "cluster",  # Cluster ID will be auto-fetched!
    "description": "ML training environment with GPU support",
    "image": "nvcr.io/nvidia/pytorch:24.01-py3",
    "workload_types": ["workspace", "training"],  # List of supported workload types
}

# Step 1: Preview (dry-run mode)
result = runai_create_environment(env_spec=env_spec)
# Shows validation and preview

# Step 2: Actually create after reviewing preview
result = runai_create_environment(
    env_spec=env_spec,
    dry_run=False,
    confirmed=True
)
```

**Key Points:**
- ✅ `scope: "cluster"` is the recommended default
- ✅ No need to provide `scope_id` - it's fetched automatically
- ✅ Use `workload_types` as a list: `["workspace", "training", "inference"]`

### Example 3: Project-Scoped Environment

Create an environment at project scope (requires project ID):

```python
env_spec = {
    "name": "team-ml-env",
    "scope": "project",
    "scope_id": "project-01-id",  # Required for project scope
    "description": "Team-specific ML environment",
    "image": "nvcr.io/nvidia/pytorch:24.01-py3",
    "workload_types": ["workspace", "training"]
}

result = runai_create_environment(
    env_spec=env_spec,
    dry_run=False,
    confirmed=True
)
```

### Example 4: Distributed Training Environment

Create an environment that supports distributed training with PyTorch:

```python
env_spec = {
    "name": "distributed-pytorch-env",
    "scope": "cluster",  # No cluster ID needed - auto-fetched
    "description": "Distributed PyTorch training with NCCL optimizations",
    "image": "nvcr.io/nvidia/pytorch:24.01-py3",
    "image_pull_policy": "IfNotPresent",  # Optional: default is "IfNotPresent"
    "workload_types": {
        "workspace": True,
        "training": True,
        "inference": False,
        "distributed": True,  # Enable distributed training
        "distFramework": "PyTorch"  # Required when distributed=True
    },
    "environment_variables": {
        "NCCL_DEBUG": "INFO",
        "NCCL_IB_DISABLE": "0",
        "NCCL_NET_GDR_LEVEL": "5",
        "OMP_NUM_THREADS": "8"
    }
}

result = runai_create_environment(
    env_spec=env_spec,
    dry_run=False,
    confirmed=True
)
```

**Important:** When using `distributed: True`, you MUST include `distFramework` (e.g., "PyTorch", "TensorFlow", "MPI")

### Example 5: Simple Workspace-Only Environment

Create a lightweight environment for interactive workspaces only:

```bash
# Using natural language
nat run --input "Create environment named jupyter-workspace with image jupyter/scipy-notebook for workspace workloads only" \
  --config_file runai-agent/configs/workflow.yaml
```

Or via API:
```python
env_spec = {
    "name": "jupyter-workspace",
    "scope": "cluster",
    "image": "jupyter/scipy-notebook",
    "workload_types": ["workspace"]  # Only workspace, no training
}

result = runai_create_environment(
    env_spec=env_spec,
    dry_run=False,
    confirmed=True
)
```

### Tenant-Level Environment

Create a tenant-wide environment accessible to all projects:

```python
env_spec = {
    "name": "standard-inference-env",
    "scope": "tenant",
    "description": "Standard inference environment for production deployments",
    "image": "nvcr.io/nvidia/tritonserver:24.01-py3",
    "compute": {
        "gpu": 1,
        "cpu_cores": 4,
        "memory": "32Gi"
    },
    "environment_variables": {
        "TRITON_SERVER_HTTP_PORT": "8000",
        "TRITON_SERVER_GRPC_PORT": "8001",
        "TRITON_SERVER_METRICS_PORT": "8002"
    }
}

result = runai_create_environment(
    env_spec=env_spec,
    dry_run=False,
    confirmed=True
)
```

### Minimal Environment

Create a minimal environment with just the required fields:

```python
env_spec = {
    "name": "basic-cpu-env",
    "scope": "project",
    "scope_id": "project-01-id",
    "image": "python:3.11-slim"
}

result = runai_create_environment(env_spec=env_spec)
```

## Environment Specification Fields

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Environment name (must be unique within scope) |
| `scope` | string | Scope level: `tenant`, `cluster`, or `project` |
| `image` | string | Default Docker image for this environment |

### Conditional Fields

| Field | Type | Required When | Description |
|-------|------|---------------|-------------|
| `scope_id` | string | scope is `cluster` or `project` | ID of the cluster or project |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Human-readable description |
| `compute` | object | Default compute resource configuration |
| `compute.gpu` | integer | Number of GPUs (0-8) |
| `compute.cpu_cores` | float | Number of CPU cores |
| `compute.memory` | string | Memory allocation (e.g., "64Gi", "128G") |
| `environment_variables` | dict | Environment variables as key-value pairs |
| `tools` | array | List of tool types (e.g., `["jupyter", "vscode"]`) |

## Memory Format

Memory can be specified in various units:

- `64Gi` - 64 Gibibytes (binary)
- `64G` - 64 Gigabytes (decimal)
- `32Mi` - 32 Mebibytes
- `32M` - 32 Megabytes
- `1Ti` - 1 Tebibyte
- `1T` - 1 Terabyte

## Validation Rules

The function enforces the following validation rules:

1. **Name**: Cannot be empty
2. **Scope**: Must be one of: `tenant`, `cluster`, `project`
3. **Scope ID**: Required for `cluster` and `project` scopes
4. **Image**: Must be specified
5. **Resource Limits**:
   - CPU cores: ≤ 32.0 (configurable)
   - Memory: ≤ 256 GB (configurable)
   - GPUs: ≤ 8 (configurable)

## Workflow

The environment creation follows a safe multi-step workflow:

```
1. Validate Spec
   ↓
2. Generate Preview
   ↓
3. [Dry-Run] Show Preview & Exit
   OR
   [Real Run] Continue...
   ↓
4. Require Confirmation
   ↓
5. Create Environment
   ↓
6. Return Status
```

## Agent Usage

When using the NAT agent, you can ask natural language questions:

```
User: "Create an ML training environment with 4 GPUs and PyTorch"

Agent: [Creates environment spec and calls function]
```

Example prompts:
- "Create a new environment for distributed training"
- "Set up a Jupyter environment with 2 GPUs"
- "Create a tenant-level environment for inference workloads"
- "Make an environment template for PyTorch training"

## Error Handling

The function provides detailed error messages for common issues:

### Validation Errors

```
❌ Environment Validation Failed

**Validation Errors:**
  • Missing required field: 'name'
  • Scope 'invalid' not in allowed list: ['tenant', 'cluster', 'project']
  • GPU count (16) exceeds maximum allowed (8)
```

### SDK Not Available

```
⚠️ Run:AI SDK Not Installed

The Run:AI Python SDK is not available in this environment.

To enable actual environment creation:
pip install runapy==1.223.0
```

### API Method Not Available

```
⚠️ Environment Creation Method Not Available

The Run:AI SDK is installed but the environment creation API is not available.

Alternative Approaches:
1. Create environments via Run:AI UI
2. Use Run:AI CLI: `runai environment create`
3. Update runapy SDK to the latest version
```

## Success Response

When successful, the function returns:

```
✅ Environment Created Successfully!

**Environment ID:** env-12345
**Name:** ml-training-env
**Scope:** project
**Image:** nvcr.io/nvidia/pytorch:24.01-py3
**Status:** Created

🔧 Usage:
This environment can now be used as a template when creating:
- Training jobs
- Interactive workspaces
- Distributed training workloads

🌐 View in UI:
https://your-runai-cluster.com/environments
```

## Common Use Cases

### Use Case 1: Quick Test Environment

**Goal:** Create a simple test environment quickly

```bash
# Fastest way - one command!
nat run --input "Create environment named test-env with busybox image" \
  --config_file runai-agent/configs/workflow.yaml
```

**Result:** Environment created in seconds with sensible defaults (cluster scope, workspace + training support)

### Use Case 2: Team Development Environment  

**Goal:** Create a shared environment for your team

```bash
nat run --input "Create environment named team-dev-env with jupyter/scipy-notebook image for workspace workloads" \
  --config_file runai-agent/configs/workflow.yaml
```

### Use Case 3: Production ML Training

**Goal:** Create production-grade environment with specific configurations

```python
env_spec = {
    "name": "prod-ml-training",
    "scope": "cluster",
    "description": "Production ML training environment",
    "image": "nvcr.io/nvidia/pytorch:24.01-py3",
    "image_pull_policy": "Always",  # Always pull latest
    "workload_types": ["training"],  # Training only, no workspace
    "environment_variables": {
        "CUDA_VISIBLE_DEVICES": "0,1,2,3",
        "NCCL_DEBUG": "WARN"
    }
}

result = runai_create_environment(
    env_spec=env_spec,
    dry_run=False,
    confirmed=True
)
```

### Use Case 4: Distributed Training Setup

**Goal:** Environment for multi-node distributed training

```python
env_spec = {
    "name": "distributed-pytorch",
    "scope": "cluster",
    "image": "nvcr.io/nvidia/pytorch:24.01-py3",
    "workload_types": {
        "workspace": False,
        "training": True,
        "inference": False,
        "distributed": True,  # Enable distributed
        "distFramework": "PyTorch"  # REQUIRED when distributed=True
    },
    "environment_variables": {
        "NCCL_DEBUG": "INFO",
        "NCCL_SOCKET_IFNAME": "eth0"
    }
}

result = runai_create_environment(env_spec=env_spec, dry_run=False, confirmed=True)
```

### Use Case 5: Multiple Environments for Different Teams

```bash
# Data Science Team
nat run --input "Create environment ds-jupyter with jupyter/datascience-notebook for workspace"

# ML Engineering Team  
nat run --input "Create environment ml-training with pytorch image for training"

# DevOps Team
nat run --input "Create environment devops-tools with ubuntu image for workspace"
```

## API Reference

### Function Signature

```python
async def _create_environment(
    env_spec: dict,
    dry_run: Optional[bool] = None,
    confirmed: bool = False
) -> str
```

### Parameters

- **env_spec** (dict): Environment specification dictionary
- **dry_run** (Optional[bool]): If True, only validate and preview. If None, uses config default
- **confirmed** (bool): If True, actually create the environment (requires dry_run=False)

### Returns

- **str**: Status message with environment details or validation/error messages

## Integration with Other Functions

Once an environment is created, it can be referenced when:

1. **Submitting Training Jobs**: Use the environment template
2. **Creating Workspaces**: Apply environment settings
3. **Distributed Training**: Use consistent configurations across workers

## Best Practices

1. **Always Preview First**: Use dry-run mode to validate before creation
2. **Use Descriptive Names**: Make environment names clear and purposeful
3. **Set Appropriate Limits**: Configure resource limits based on actual needs
4. **Document Environments**: Use the description field to explain purpose
5. **Scope Appropriately**:
   - Use `tenant` for organization-wide templates
   - Use `cluster` for cluster-specific configurations
   - Use `project` for team-specific environments
6. **Include Environment Variables**: Pre-configure common variables
7. **Version Control**: Track environment specs in version control

## Troubleshooting

### Issue: "Scope ID not found"

**Solution**: Verify the scope_id exists:
```python
# Get available projects
result = runailabs_environment_info(input_message="show projects")
```

### Issue: "Resource limits exceeded"

**Solution**: Check your configuration limits in `workflow.yaml` or reduce requested resources

### Issue: "Environment API not available"

**Solution**: 
1. Update runapy SDK: `pip install --upgrade runapy`
2. Check your RunAI version supports environment API
3. Create environments via UI instead

## Examples by Use Case

### Data Science Team Environment

```python
{
    "name": "data-science-standard",
    "scope": "project",
    "scope_id": "ds-team-project",
    "description": "Standard data science environment with Jupyter and common ML libraries",
    "image": "jupyter/datascience-notebook:latest",
    "compute": {
        "gpu": 1,
        "cpu_cores": 4,
        "memory": "32Gi"
    },
    "tools": ["jupyter", "tensorboard"]
}
```

### Production Inference Environment

```python
{
    "name": "prod-inference",
    "scope": "cluster",
    "scope_id": "prod-cluster",
    "description": "Production-grade inference environment with Triton",
    "image": "nvcr.io/nvidia/tritonserver:24.01-py3",
    "compute": {
        "gpu": 2,
        "cpu_cores": 8,
        "memory": "64Gi"
    },
    "environment_variables": {
        "TRITON_SERVER_HTTP_PORT": "8000",
        "LOG_LEVEL": "INFO"
    }
}
```

### Development Environment

```python
{
    "name": "dev-lightweight",
    "scope": "project",
    "scope_id": "dev-project",
    "description": "Lightweight development environment for testing",
    "image": "python:3.11-slim",
    "compute": {
        "cpu_cores": 2,
        "memory": "8Gi"
    }
}
```

## Environment Deletion

### Deleting Environments ✅ Tested & Working!

Delete environment templates that are no longer needed.

#### Example 1: Delete via Natural Language (Easiest)

```bash
# Delete an environment - confirmation required by default
nat run --input "Delete the environment named busybox-test" \
  --config_file runai-agent/configs/workflow.yaml
```

**What happens:**
1. ✅ Finds the environment by name
2. ✅ Shows environment details
3. ✅ Requires confirmation (safety feature)
4. ✅ Deletes the environment
5. ✅ Confirms deletion with details

**Success Output:**
```
✅ Environment Deleted Successfully

The environment has been permanently removed:
- Environment Name: busybox-test
- Environment ID: 17c0d816-5ad5-4f3b-b019-c26ad316b94d
- Scope: cluster
- Image: busybox
- Supported Workloads: workspace, training

Note: Existing workloads created from this environment are not affected,
but new workloads cannot use this environment template.

🌐 Verify in UI:
https://your-cluster.com/assets/environments
```

#### Example 2: Delete via API (Direct)

```python
# Step 1: Preview deletion (shows confirmation prompt)
result = runai_delete_environment(environment_name="test-env")

# Step 2: Actually delete with confirmation
result = runai_delete_environment(
    environment_name="test-env",
    confirmed=True
)
```

#### Example 3: More Natural Language Examples

```bash
# Various ways to ask for deletion
nat run --input "Remove environment ml-training-env"
nat run --input "Delete the busybox environment"
nat run --input "Remove the environment called test-env"
```

### Important Notes About Deletion

**✅ Safe:**
- Requires explicit confirmation before deletion
- Lists available environments if name not found
- Shows full environment details before deletion

**ℹ️ What Gets Deleted:**
- The environment template/asset is removed
- Environment configuration is deleted
- Environment no longer appears in the UI

**✅ What's NOT Affected:**
- Existing workloads created from the environment continue running
- Jobs, workspaces, and training workloads are unaffected
- Only the template is removed, not the workloads using it

### Deletion Workflow

```
1. Request Deletion
   ↓
2. Find Environment by Name
   ↓
3. [Not Found] → Show Available Environments
   OR
   [Found] → Continue...
   ↓
4. Show Environment Details
   ↓
5. [No Confirmation] → Show Warning & Exit
   OR
   [Confirmed] → Continue...
   ↓
6. Delete Environment
   ↓
7. Return Success Status
```

### Error Handling

#### Environment Not Found

```
❌ Environment Not Found

Could not find environment `test-env`.

Available environments:
  • ml-training-env
  • jupyter-workspace
  • distributed-pytorch
  ... and 5 more

Please check:
- Environment name is spelled correctly
- Environment exists in your Run:AI cluster
- You have permission to view this environment
```

#### Confirmation Required

```
⚠️ Confirm Environment Deletion

You are about to permanently delete the following environment:
- Environment Name: `test-env`

⚠️ This action cannot be undone.

Note: Deleting an environment does not affect existing workloads created from it,
but new workloads will not be able to use this environment template.

To proceed, call this function again with `confirmed=True`.
```

## Cheat Sheet

### Quick Commands

#### Creation

```bash
# Basic environment
nat run --input "Create environment named my-env with busybox image"

# Workspace only
nat run --input "Create environment named jupyter with jupyter/scipy-notebook for workspace"

# Training only
nat run --input "Create environment named training with pytorch image for training workloads"

# Both workspace and training
nat run --input "Create environment named dev-env with ubuntu for workspace and training"
```

#### Deletion ✅ New!

```bash
# Delete environment
nat run --input "Delete environment named test-env"

# Remove environment
nat run --input "Remove the environment called busybox-test"
```

### Environment Lifecycle Management

```bash
# Basic environment
nat run --input "Create environment named my-env with busybox image"

# Workspace only
nat run --input "Create environment named jupyter with jupyter/scipy-notebook for workspace"

# Training only
nat run --input "Create environment named training with pytorch image for training workloads"

# Both workspace and training
nat run --input "Create environment named dev-env with ubuntu for workspace and training"
```

### Minimum Required Fields

```python
{
    "name": "my-env",
    "scope": "cluster",  # or "project" (with scope_id)
    "image": "your-image:tag",
    "workload_types": ["workspace", "training"]
}
```

### Workload Types Options

```python
# Simple list (recommended)
"workload_types": ["workspace", "training"]

# Full dict (for distributed)
"workload_types": {
    "workspace": True,
    "training": True,
    "inference": False,
    "distributed": True,
    "distFramework": "PyTorch"  # MUST be set if distributed=True
}
```

### Scope Options

| Scope | Requires scope_id? | Auto-fetch? | Recommended |
|-------|-------------------|-------------|-------------|
| `cluster` | No | ✅ Yes | ⭐ **Yes** |
| `project` | Yes | ❌ No | For team-specific |
| `tenant` | No | ❌ No | Requires special permissions |

### Common Images

```python
# PyTorch
"image": "nvcr.io/nvidia/pytorch:24.01-py3"

# TensorFlow
"image": "nvcr.io/nvidia/tensorflow:24.01-tf2-py3"

# Jupyter
"image": "jupyter/scipy-notebook"

# Simple test
"image": "busybox"

# Ubuntu
"image": "ubuntu:22.04"
```

### Complete Lifecycle Example

```bash
# 1. Create an environment
nat run --input "Create environment named test-env with busybox for workspace and training"

# 2. Use the environment (create workloads from it)
# ... workloads are created using this environment template ...

# 3. Delete the environment when no longer needed
nat run --input "Delete environment named test-env"
```

**Result:** 
- ✅ Environment template removed
- ✅ Existing workloads continue running
- ✅ New workloads cannot use the deleted template

## Function Reference

### Create Environment

```python
runai_create_environment(
    env_spec: dict,
    dry_run: Optional[bool] = None,
    confirmed: bool = False
) -> str
```

**Parameters:**
- `env_spec`: Environment specification dictionary
- `dry_run`: Preview mode (default: True)
- `confirmed`: Confirm creation (required for actual creation)

### Delete Environment

```python
runai_delete_environment(
    environment_name: str,
    confirmed: bool = False
) -> str
```

**Parameters:**
- `environment_name`: Name of environment to delete
- `confirmed`: Confirm deletion (required for actual deletion)

## See Also

- [Job Submission Guide](./job_submission_guide.md)
- [Workspace Creation Guide](./workspace_guide.md)
- [Run:AI Documentation](https://docs.run.ai/)
- [Feature Overview](../../docs/ENVIRONMENT_CREATION_FEATURE.md)

