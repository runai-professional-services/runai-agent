# Batch Job Submission Guide

## Overview

The Run:AI Agent now supports **batch job submission**, allowing you to submit multiple workloads (training, distributed, or workspace) in a single operation.

## When to Use Batch Submission

Use `runai_submit_batch` when:
- ✅ Submitting multiple jobs to the same project
- ✅ Creating similar jobs with different configurations
- ✅ Bulk provisioning for multiple users/teams
- ✅ Automated job creation from scripts or pipelines
- ✅ User requests "multiple jobs", "list of jobs", "several jobs"
- ✅ User requests "Submit jobs for project X, Y, and Z"

Use single-job tools (`runai_submit_workload`, `runai_submit_distributed_workload`, `runai_submit_workspace`) when:
- ❌ Submitting only one job
- ❌ User requests a single specific workload

## Features

- 📦 **Multiple Job Types** - Submit training, distributed, and workspace jobs in one batch
- 🔄 **Continue on Error** - By default, continues submitting remaining jobs if one fails
- 📊 **Comprehensive Reporting** - Detailed success/failure status for each job
- 🛡️ **Same Safety Features** - Dry-run, confirmation, validation, project whitelist
- ⚡ **Efficient** - Single API connection for all jobs

## Usage Examples

### Example 1: Submit Multiple Training Jobs

**User Query:**
```
Submit 3 training jobs to project-01:
  - job1 with 2 GPUs using pytorch/pytorch:latest
  - job2 with 1 GPU using pytorch/pytorch:latest
  - job3 with 4 GPUs using tensorflow/tensorflow:latest
```

**Agent Function Call:**
```json
{
  "jobs": [
    {
      "type": "training",
      "name": "job1",
      "project": "project-01",
      "image": "pytorch/pytorch:latest",
      "gpus": 2
    },
    {
      "type": "training",
      "name": "job2",
      "project": "project-01",
      "image": "pytorch/pytorch:latest",
      "gpus": 1
    },
    {
      "type": "training",
      "name": "job3",
      "project": "project-01",
      "image": "tensorflow/tensorflow:latest",
      "gpus": 4
    }
  ],
  "dry_run": false,
  "confirmed": true
}
```

### Example 2: Mixed Job Types

**User Query:**
```
Submit these jobs to project-01:
  - training job named "model-training" with 2 GPUs
  - distributed job named "dist-training" with 4 workers and 2 GPUs per worker using pytorch
  - jupyter workspace named "analysis" with 1 GPU
```

**Agent Function Call:**
```json
{
  "jobs": [
    {
      "type": "training",
      "name": "model-training",
      "project": "project-01",
      "image": "pytorch/pytorch:latest",
      "gpus": 2
    },
    {
      "type": "distributed",
      "name": "dist-training",
      "project": "project-01",
      "image": "nvcr.io/nvidia/pytorch:latest",
      "workers": 4,
      "gpus": 2,
      "framework": "pytorch"
    },
    {
      "type": "workspace",
      "name": "analysis",
      "project": "project-01",
      "image": "jupyter/scipy-notebook",
      "gpus": 1,
      "workspace_type": "jupyter"
    }
  ],
  "dry_run": false,
  "confirmed": true
}
```

### Example 3: Across Multiple Projects

**User Query:**
```
Submit training jobs across projects:
  - job-a with 2 GPUs to project-01
  - job-b with 4 GPUs to project-02
  - job-c with 1 GPU to project-03
```

**Agent Function Call:**
```json
{
  "jobs": [
    {
      "type": "training",
      "name": "job-a",
      "project": "project-01",
      "image": "pytorch/pytorch:latest",
      "gpus": 2
    },
    {
      "type": "training",
      "name": "job-b",
      "project": "project-02",
      "image": "pytorch/pytorch:latest",
      "gpus": 4
    },
    {
      "type": "training",
      "name": "job-c",
      "project": "project-03",
      "image": "pytorch/pytorch:latest",
      "gpus": 1
    }
  ],
  "dry_run": false,
  "confirmed": true
}
```

## Job Specification Format

### Training Job
```json
{
  "type": "training",
  "name": "job-name",
  "project": "project-name",
  "image": "container-image:tag",
  "gpus": 2,
  "command": "python train.py"  // optional
}
```

### Distributed Training Job
```json
{
  "type": "distributed",
  "name": "dist-job",
  "project": "project-name",
  "image": "container-image:tag",
  "workers": 4,
  "gpus": 2,
  "framework": "pytorch",  // pytorch, tensorflow, mpi, jax, xgboost
  "command": "python train.py"  // optional
}
```

### Workspace
```json
{
  "type": "workspace",
  "name": "workspace-name",
  "project": "project-name",
  "image": "jupyter/scipy-notebook",
  "gpus": 1,
  "workspace_type": "jupyter"  // jupyter, vscode, or custom
}
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `jobs` | List[Dict] | **Required** | List of job specifications |
| `dry_run` | bool | `true` | Preview without submitting |
| `confirmed` | bool | `false` | Skip confirmation prompt |
| `continue_on_error` | bool | `true` | Continue if one job fails |

## Workflow

### Step 1: Dry-Run (Preview)
First call with `dry_run=true` to preview:

```json
{
  "jobs": [...],
  "dry_run": true
}
```

**Response:**
```
📋 Batch Job Preview

Total Jobs: 3
Job Types:
  • Training: 3

Total GPUs Required: 7

Jobs to Submit:
1. job1 (training)
   - Project: project-01
   - Image: pytorch/pytorch:latest
   - GPUs: 2
...

✅ Validation Passed
This is a DRY RUN - no jobs will be submitted.
```

### Step 2: Confirmation
Call with `dry_run=false` but `confirmed=false`:

**Response:**
```
⚠️  Confirmation Required

You are about to submit 3 jobs to Run:AI cluster.
To proceed, set confirmed=True in your request.
```

### Step 3: Submit
Call with `confirmed=true`:

```json
{
  "jobs": [...],
  "dry_run": false,
  "confirmed": true
}
```

**Response:**
```
🎯 Batch Submission Complete

Total Jobs: 3
Successful: 3 ✅
Failed: 0 ❌

Detailed Results:

✅ job1
   Status: Submitted
   Job ID: abc-123

✅ job2
   Status: Submitted
   Job ID: def-456

✅ job3
   Status: Submitted
   Job ID: ghi-789

🎉 All jobs submitted successfully!
```

## Safety Features

- ✅ **Dry-run by default** - Always preview before submitting
- ✅ **Explicit confirmation** - Requires user approval
- ✅ **Project whitelist** - Only submits to approved projects
- ✅ **Resource limits** - Enforces GPU quotas per job
- ✅ **Validation checks** - Verifies all job specs before submission
- ✅ **Continue on error** - Partial success supported
- ✅ **Detailed reporting** - Clear success/failure status for each job

## Configuration

Edit `runai-agent/configs/workflow.yaml`:

```yaml
runai_submit_batch:
  _type: runai_submit_batch
  dry_run_default: true           # Always preview first
  require_confirmation: true      # Require explicit approval
  max_gpus_per_job: 8            # Max GPUs per individual job
  max_batch_size: 20             # Max jobs in one batch
  # allowed_projects: ["project-01", "project-02"]  # Optional whitelist
```

## Error Handling

### Partial Success
If some jobs fail, the agent continues with remaining jobs (by default):

```
🎯 Batch Submission Complete

Total Jobs: 3
Successful: 2 ✅
Failed: 1 ❌

Detailed Results:

✅ job1
   Status: Submitted
   Job ID: abc-123

❌ job2
   Status: Failed
   Error: Project 'invalid-project' not found

✅ job3
   Status: Submitted
   Job ID: ghi-789

⚠️  Partial success - Some jobs failed. Check details above.
```

### Stop on First Error
Set `continue_on_error=false` to stop on first failure:

```json
{
  "jobs": [...],
  "dry_run": false,
  "confirmed": true,
  "continue_on_error": false
}
```

## LLM Routing Rules

The agent uses these rules to route batch vs single submissions:

**Batch Submission Triggers:**
- "Submit multiple jobs"
- "List of jobs"
- "Several jobs"
- "Submit 5 training jobs"
- "Create 10 workspaces"
- "Submit jobs for project X, Y, Z"
- "Bulk submit"
- "Batch create"

**Single Submission Triggers:**
- "Submit a job"
- "Create one workspace"
- "Submit this training job"

## Testing

Test the batch submission feature:

```bash
# 1. Start the agent
./deploy/start-local.sh

# 2. Test with dry-run (safe)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Submit 3 training jobs to project-01 with 1, 2, and 4 GPUs",
    "dry_run": true
  }'

# 3. Confirm submission
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Yes, submit them",
    "confirmed": true
  }'
```

## Benefits

**Before Batch Submission:**
- ❌ Multiple API calls required
- ❌ Manual confirmation for each job
- ❌ No consolidated reporting
- ❌ Slow for bulk operations

**After Batch Submission:**
- ✅ Single API call for all jobs
- ✅ One confirmation for entire batch
- ✅ Comprehensive batch report
- ✅ Fast and efficient

## Troubleshooting

### Issue: "Batch size exceeds maximum"
**Solution:** Reduce number of jobs or increase `max_batch_size` in config

### Issue: "GPU count exceeds max"
**Solution:** Reduce GPUs per job or increase `max_gpus_per_job` in config

### Issue: "Project not in allowed list"
**Solution:** Add project to `allowed_projects` or use `["*"]` for all projects

### Issue: Some jobs failed
**Solution:** Check error messages in detailed report and fix job specifications

## Best Practices

1. **Start with Dry-Run**: Always preview batch before submitting
2. **Reasonable Batch Sizes**: Keep batches under 20 jobs for best performance
3. **Same Project**: Submit to same project when possible for consistency
4. **Error Handling**: Use `continue_on_error=true` for large batches
5. **Validation**: Ensure all jobs have required fields before submitting
6. **Resource Planning**: Calculate total GPU requirements before submission

## Monitoring Batch Jobs

After submission, monitor jobs with:

```
Check status of all jobs in project-01
```

Or use proactive monitoring:

```
Start monitoring all jobs in project-01
```

---

**For more information:**
- [README.md](../README.md) - Main documentation
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
- [QUICKSTART.md](QUICKSTART.md) - Getting started

