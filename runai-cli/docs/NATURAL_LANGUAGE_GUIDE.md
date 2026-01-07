# 🚀 Natural Language Job Submission - User Guide

## Overview

The RunAI CLI now supports **GenAI-style natural language job submission**! Simply describe what you want in plain English, and the agent will handle all the complexity for you.

No more JSON files, no more flags, no more memorizing parameters - just tell it what you need!

## Quick Start

### Basic Usage

```bash
runai-cli submit "Create a training job with 2 GPUs"
```

That's it! The agent will:
- ✅ Understand your intent
- ✅ Generate the appropriate job configuration
- ✅ Handle all the technical details
- ✅ Submit the job for you

### Interactive Mode

If you prefer a guided experience, just run:

```bash
runai-cli submit
```

The CLI will prompt you to describe what you want and guide you through the process.

## Real-World Examples

### 1. Simple Training Job

```bash
runai-cli submit "Launch a PyTorch training job with 2 GPUs"
```

### 2. Distributed Training

```bash
runai-cli submit "Start distributed training with 4 workers using TensorFlow"
```

### 3. Jupyter Workspace

```bash
runai-cli submit "Create a Jupyter workspace with 8GB memory and 1 GPU"
```

### 4. Specific Project

```bash
runai-cli submit "Training job with 4 GPUs in project ml-team"
```

Or using the flag:

```bash
runai-cli submit "Training job with 4 GPUs" --project ml-team
```

### 5. With Specific Configuration

```bash
runai-cli submit "Create a training job using nvidia/pytorch:24.01-py3 image with 2 GPUs and 16GB memory"
```

### 6. Multi-Node Training

```bash
runai-cli submit "Distributed PyTorch training with 8 workers, 2 GPUs per worker"
```

### 7. Batch Jobs

```bash
runai-cli submit "Create 5 training jobs with different learning rates"
```

## Command Options

### Stream Mode (Real-time Response)

Get live updates as the agent processes your request:

```bash
runai-cli submit "Create training job" --stream
```

**Why use streaming?**
- See the agent's thinking process
- Get immediate feedback
- Better for complex requests

### Skip Confirmations

For automation or when you trust the configuration:

```bash
runai-cli submit "Training job with 2 GPUs" --no-confirm
```

⚠️ **Warning:** This will submit jobs without asking for confirmation. Use with caution!

### Specify Project

Target a specific project:

```bash
runai-cli submit "Training job" --project my-project
```

## What Can You Request?

The natural language interface understands:

### Job Types
- ✅ Training jobs
- ✅ Distributed training
- ✅ Interactive workspaces (Jupyter, VSCode, SSH)
- ✅ Batch jobs
- ✅ Inference jobs

### Resources
- ✅ GPU count ("2 GPUs", "4 A100s")
- ✅ CPU cores ("8 CPU cores")
- ✅ Memory ("32GB memory", "16Gi RAM")
- ✅ Storage ("100GB PVC")

### Frameworks
- ✅ PyTorch
- ✅ TensorFlow
- ✅ MPI
- ✅ Horovod
- ✅ JAX

### Configuration
- ✅ Docker images
- ✅ Environment variables
- ✅ Commands and arguments
- ✅ Node pools
- ✅ Tolerations

## Comparison: Old vs New Way

### Old Way (Traditional CLI)

```bash
# Create a JSON file
cat > job.json << EOF
{
  "name": "training-job-1",
  "project": "ml-team",
  "image": "nvcr.io/nvidia/pytorch:24.01-py3",
  "gpu": 2,
  "cpuCores": 8,
  "memory": "32Gi",
  "command": "python",
  "args": ["train.py", "--epochs", "100"]
}
EOF

# Submit using the JSON file
runai-cli job submit job.json
```

### New Way (Natural Language)

```bash
runai-cli submit "Create a PyTorch training job with 2 GPUs in ml-team"
```

**Result:** Same job, ~10x less effort! 🎉

## Tips for Better Results

### 1. Be Specific (But Don't Over-explain)

❌ **Too Vague:**
```bash
"Create a job"
```

✅ **Better:**
```bash
"Create a training job with 2 GPUs"
```

✅ **Even Better:**
```bash
"Create a PyTorch training job with 2 GPUs using the latest NVIDIA image"
```

### 2. Mention the Project

If you're working in a specific project:

```bash
runai-cli submit "Training job with 4 GPUs in project ml-research"
```

### 3. Include Resource Requirements

Be clear about what you need:

```bash
runai-cli submit "Training job with 8 GPUs, 64GB memory, and 500GB storage"
```

### 4. Specify Frameworks When Relevant

For distributed training:

```bash
runai-cli submit "Distributed TensorFlow training with 4 workers"
```

### 5. Use Natural Language

You don't need to use technical jargon - the agent understands both:

✅ **Casual:**
```bash
"Start a training thing with 2 GPUs"
```

✅ **Technical:**
```bash
"Instantiate a distributed PyTorch DDP workload with 4 worker nodes"
```

Both work!

## Advanced Usage

### Complex Multi-Step Requests

The agent can handle complex scenarios:

```bash
runai-cli submit "Create a distributed PyTorch training job with 8 workers, \
2 GPUs per worker, using the latest PyTorch image, mount the ml-data PVC, \
set NCCL_DEBUG=INFO, and run training for 100 epochs"
```

### Conditional Logic

The agent understands conditional requirements:

```bash
runai-cli submit "Create a training job with 4 GPUs if available, otherwise use 2"
```

### Multiple Jobs

```bash
runai-cli submit "Create training jobs for projects ml-team1, ml-team2, and ml-team3 \
with 2 GPUs each"
```

## Interactive Mode Details

When you run `runai-cli submit` without a prompt:

```bash
$ runai-cli submit

🎯 Interactive Job Submission

Describe what you want to create. Be as detailed or simple as you like.

Examples:
  • "Training job with 2 GPUs"
  • "Distributed PyTorch training with 4 workers"
  • "Jupyter workspace in project-ml with 8GB memory"

What would you like to create? _
```

Just type your description and press Enter!

## Error Handling

The CLI provides helpful error messages:

### Server Not Running

```bash
$ runai-cli submit "Training job"

❌ Agent server is not running at http://localhost:8000
ℹ Start the server with: runai-cli server start
```

### Invalid Request

```bash
$ runai-cli submit ""

❌ Error: Query cannot be empty
ℹ Need help? Try: runai-cli --help
```

## Integration with Existing Commands

The `submit` command works alongside traditional commands:

```bash
# Natural language submission
runai-cli submit "Training job with 2 GPUs"

# Check status
runai-cli job status training-job-1

# List all jobs
runai-cli job list

# Traditional JSON submission still works
runai-cli job submit job.json
```

Choose the method that works best for your use case!

## Configuration

### Enable Streaming by Default

```bash
runai-cli config set stream true
```

Now all `submit` commands will stream by default.

### Set Default Project

While there's no global project setting, you can create an alias:

```bash
alias submit-ml='runai-cli submit --project ml-team'

# Now use it:
submit-ml "Training job with 4 GPUs"
```

## Troubleshooting

### "Cannot connect to agent server"

**Solution:** Start the agent server first:

```bash
runai-cli server start --background
```

### "Request timed out"

**Solution:** Increase the timeout:

```bash
runai-cli config set timeout 120000  # 2 minutes
```

### Response seems incomplete

**Solution:** Try streaming mode to see the full process:

```bash
runai-cli submit "..." --stream
```

## Examples Gallery

### Example 1: Quick Prototyping

```bash
# Developer wants to quickly test a model
runai-cli submit "Spin up a quick training job with 1 GPU"
```

### Example 2: Production Training

```bash
# ML Engineer needs a production training run
runai-cli submit "Create a distributed PyTorch training job with 8 A100 GPUs, \
use the nvcr.io/nvidia/pytorch:24.01-py3 image, mount the imagenet-data PVC, \
and run train.py with --epochs 100 --batch-size 256"
```

### Example 3: Development Workspace

```bash
# Data Scientist needs an interactive environment
runai-cli submit "Launch a Jupyter workspace with 2 GPUs and 32GB memory \
in project data-science"
```

### Example 4: Batch Experimentation

```bash
# Researcher wants to run multiple experiments
runai-cli submit "Create 10 training jobs with learning rates from 0.001 to 0.01"
```

### Example 5: Resource-Constrained

```bash
# User needs to work with limited resources
runai-cli submit "Create a training job using fractional GPU (0.5) and 8GB memory"
```

## Best Practices

### 1. Start Simple, Add Details as Needed

Begin with a basic request, then add more details if the agent asks:

```bash
# First try
runai-cli submit "Training job"

# If agent needs more info, be more specific
runai-cli submit "PyTorch training job with 2 GPUs for image classification"
```

### 2. Use Streaming for Complex Requests

For multi-step or complex jobs:

```bash
runai-cli submit "Complex distributed training setup..." --stream
```

### 3. Leverage Project Context

Always mention the project to avoid ambiguity:

```bash
runai-cli submit "Training job in project ml-team"
```

### 4. Review Before Disabling Confirmations

Unless automating, keep confirmations enabled:

```bash
# Let the agent show you what it will do
runai-cli submit "Training job with 8 GPUs"

# Only skip confirmation when you're confident
runai-cli submit "Standard training job" --no-confirm
```

## FAQ

### Q: Do I still need JSON files?

**A:** No! But they still work if you prefer them. Use `submit` for natural language or `job submit` for JSON files.

### Q: Can I see what the agent will do before it runs?

**A:** Yes! By default, the agent shows you the configuration before submission (unless you use `--no-confirm`).

### Q: Does it work offline?

**A:** No, it requires the agent server to be running. The server processes your natural language and interacts with the RunAI cluster.

### Q: Can I use this in scripts?

**A:** Yes! Combine with `--no-confirm` for automated workflows:

```bash
#!/bin/bash
runai-cli submit "Training job with 2 GPUs" --no-confirm --project "$PROJECT_NAME"
```

### Q: How is this different from `ask`?

**A:** 
- `submit` is optimized for job submission with better UX
- `ask` is for general questions and operations
- Both use the same agent backend

### Q: What if the agent doesn't understand?

**A:** Try rephrasing or adding more details. The agent will ask clarifying questions if needed.

## Future Enhancements

Coming soon:
- 🎯 Smart defaults based on your history
- 🔄 Job templates from natural language
- 📊 Resource recommendations
- 🤖 Multi-turn conversations for complex setups
- 💾 Save common patterns as shortcuts

## Feedback

Have ideas for improving the natural language interface? Let us know!

---

**Happy Submitting! 🚀**

For more information, see:
- [CLI README](README.md) - Full CLI documentation
- [Setup Guide](SETUP_AND_RUN.md) - Installation instructions
- [Examples](examples/) - More example specifications

