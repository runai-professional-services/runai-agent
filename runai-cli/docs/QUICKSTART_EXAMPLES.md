# Quick Start Examples - Natural Language Submit

## 30-Second Quickstart

```bash
# Start the server
runai-cli server start --background

# Submit your first job (that's it!)
runai-cli submit "Create a training job with 2 GPUs"
```

## Common Use Cases

### 1. Quick Training Job

```bash
runai-cli submit "Training job with 2 GPUs"
```

**What the agent understands:**
- Creates a training workload
- Assigns 2 GPUs
- Uses sensible defaults for everything else

### 2. Specific Framework

```bash
runai-cli submit "PyTorch training with 4 GPUs"
```

**Agent adds:**
- Uses PyTorch Docker image
- Configures for PyTorch training
- Sets up appropriate environment

### 3. Interactive Development

```bash
runai-cli submit "Jupyter notebook with 1 GPU and 16GB memory"
```

**Result:**
- Jupyter workspace
- 1 GPU allocated
- 16GB memory  
- Ready for interactive work

### 4. Distributed Training

```bash
runai-cli submit "Distributed training with 8 workers, 2 GPUs each"
```

**Agent configures:**
- Multi-node distributed setup
- 8 worker nodes
- 2 GPUs per worker
- Proper networking

### 5. Project-Specific

```bash
runai-cli submit "Training job in ml-research project with 4 A100 GPUs"
```

**Includes:**
- Targets ml-research project
- Requests A100 GPUs specifically
- 4 GPUs total

## Progressive Examples (Simple → Advanced)

### Level 1: Absolute Beginner

```bash
runai-cli submit "training job"
```

The agent will ask clarifying questions!

### Level 2: Adding Detail

```bash
runai-cli submit "training job with 2 GPUs"
```

Better! Now the agent knows resource requirements.

### Level 3: Framework Specific

```bash
runai-cli submit "PyTorch training job with 2 GPUs"
```

Even better - now the agent can pick the right image.

### Level 4: Full Specification

```bash
runai-cli submit "PyTorch training job with 2 GPUs, 32GB memory, using nvidia/pytorch:24.01-py3 image"
```

Complete control while still using natural language!

### Level 5: Production Ready

```bash
runai-cli submit "Distributed PyTorch training with 8 workers, 2 A100 GPUs per worker, \
mount ml-data PVC, set NCCL_DEBUG=INFO, run for 100 epochs in ml-prod project"
```

Enterprise-grade configuration via natural language!

## Comparison with Traditional Method

### Traditional Way (Multiple Steps)

```bash
# 1. Create a JSON file
cat > job.json << 'EOF'
{
  "name": "pytorch-training",
  "project": "ml-team",
  "image": "nvcr.io/nvidia/pytorch:24.01-py3",
  "gpu": 2,
  "cpuCores": 8,
  "memory": "32Gi",
  "command": "python",
  "args": ["train.py"]
}
EOF

# 2. Submit the job
runai-cli job submit job.json

# 3. Check if it worked
runai-cli job status pytorch-training --project ml-team
```

**Lines of code:** ~20  
**Time:** ~2-3 minutes  
**Potential for errors:** High (JSON syntax, missing fields)

### New Way (One Command)

```bash
runai-cli submit "PyTorch training with 2 GPUs in ml-team project"
```

**Lines of code:** 1  
**Time:** ~10 seconds  
**Potential for errors:** Low (natural language)

## Real-World Scenarios

### Scenario 1: Data Scientist Prototyping

**Goal:** Quick experiment with a new model

```bash
runai-cli submit "spin up a training job with 1 GPU"
```

**Result:** Job running in < 1 minute!

### Scenario 2: ML Engineer - Production Training

**Goal:** Launch production training run

```bash
runai-cli submit "distributed PyTorch training, 8 A100 GPUs, use imagenet dataset, \
run for 200 epochs in ml-production project" --stream
```

**Benefit:** See the setup process in real-time

### Scenario 3: Researcher - Hyperparameter Sweep

**Goal:** Test multiple configurations

```bash
runai-cli submit "create 10 training jobs with learning rates from 0.001 to 0.01"
```

**Result:** All 10 jobs configured and submitted automatically!

### Scenario 4: Team Lead - Resource Management

**Goal:** Set up workspaces for team members

```bash
runai-cli submit "create Jupyter workspaces for users alice, bob, and charlie, \
each with 2 GPUs in team-research project"
```

**Benefit:** Bulk provisioning via natural language!

### Scenario 5: DevOps - Automated Deployment

**Goal:** CI/CD integration

```bash
#!/bin/bash
# In your deployment script
runai-cli submit "deploy model training job with parameters from config.yaml" \
  --no-confirm --project $PROJECT_NAME
```

**Benefit:** Natural language + automation = powerful!

## Tips & Tricks

### Tip 1: Use Streaming for Complex Requests

```bash
runai-cli submit "complex distributed setup..." --stream
```

See exactly what the agent is doing in real-time.

### Tip 2: Start Vague, Get Specific

Start simple:
```bash
runai-cli submit "training job"
```

If agent needs more info, add details:
```bash
runai-cli submit "PyTorch training job with 2 GPUs for image classification"
```

### Tip 3: Mention Everything You Care About

```bash
runai-cli submit "training job with:
- 4 GPUs
- 64GB memory
- PyTorch 2.0
- ImageNet dataset mounted
- In project ml-team"
```

The agent handles multi-line input!

### Tip 4: Use Interactive Mode for Guidance

```bash
runai-cli submit
```

The CLI will guide you through the process.

### Tip 5: Combine with Other Commands

```bash
# Submit
runai-cli submit "training job with 2 GPUs"

# Check status
runai-cli job status training-job

# View logs
runai-cli ask "show me logs for the training job"
```

Mix and match for the best workflow!

## Troubleshooting Common Scenarios

### "I don't know what resources to request"

```bash
runai-cli submit "training job for image classification, suggest resources"
```

The agent can provide recommendations!

### "I need to match an existing configuration"

```bash
runai-cli submit "training job similar to the one I ran yesterday"
```

The agent can reference past jobs (if available).

### "The job failed, I need to retry"

```bash
runai-cli ask "why did my last job fail?"
# Then:
runai-cli submit "retry the last job with double the memory"
```

Natural language works for debugging too!

## Advanced Patterns

### Pattern 1: Resource-Aware Submission

```bash
runai-cli submit "training job with as many GPUs as available, max 8"
```

### Pattern 2: Conditional Configuration

```bash
runai-cli submit "training job with 4 A100s if available, otherwise 8 V100s"
```

### Pattern 3: Template-Based

```bash
runai-cli submit "training job using our standard template with 4 GPUs"
```

### Pattern 4: Time-Bound

```bash
runai-cli submit "training job that runs for maximum 2 hours"
```

### Pattern 5: Dependency-Aware

```bash
runai-cli submit "training job that waits for data-prep-job to complete"
```

## Integration Examples

### Jupyter Notebook Integration

```python
import subprocess

def submit_training_job(description):
    """Submit a training job using natural language"""
    result = subprocess.run(
        ['runai-cli', 'submit', description, '--no-confirm'],
        capture_output=True,
        text=True
    )
    return result.stdout

# Use it
submit_training_job("Training job with current notebook's configuration")
```

### Shell Script Integration

```bash
#!/bin/bash
# automated-training.sh

DESCRIPTION="Training job with $NUM_GPUS GPUs in $PROJECT_NAME"

runai-cli submit "$DESCRIPTION" \
  --no-confirm \
  --project "$PROJECT_NAME"
```

### Python Script Integration

```python
#!/usr/bin/env python3
import sys
import subprocess

def submit_job(prompt: str, **kwargs):
    """Submit job with natural language + options"""
    cmd = ['runai-cli', 'submit', prompt]
    
    if kwargs.get('project'):
        cmd.extend(['--project', kwargs['project']])
    if kwargs.get('stream'):
        cmd.append('--stream')
    if kwargs.get('no_confirm'):
        cmd.append('--no-confirm')
    
    subprocess.run(cmd)

if __name__ == '__main__':
    submit_job(
        "Distributed training with 8 workers",
        project="ml-team",
        stream=True
    )
```

## Next Steps

1. **Try it now:**
   ```bash
   runai-cli submit "your first training job"
   ```

2. **Read the full guide:**
   [NATURAL_LANGUAGE_GUIDE.md](NATURAL_LANGUAGE_GUIDE.md)

3. **Explore more examples:**
   ```bash
   runai-cli submit --help
   ```

4. **Join the conversation:**
   Ask the agent questions: `runai-cli chat`

---

**Happy Training! 🚀**

