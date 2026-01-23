# Run:AI Agent with NeMo Agent Toolkit

[![Tests](https://github.com/runai-professional-services/runai-agent/workflows/Test%20Suite/badge.svg)](https://github.com/runai-professional-services/runai-agent/actions/workflows/test.yml)
[![Docker](https://github.com/runai-professional-services/runai-agent/workflows/Build%20and%20Push%20Docker%20Image/badge.svg)](https://github.com/runai-professional-services/runai-agent/actions/workflows/docker.yml)
[![Release](https://github.com/runai-professional-services/runai-agent/workflows/Release/badge.svg)](https://github.com/runai-professional-services/runai-agent/actions/workflows/release.yml)
[![Helm](https://github.com/runai-professional-services/runai-agent/workflows/Publish%20Helm%20Chart/badge.svg)](https://github.com/runai-professional-services/runai-agent/actions/workflows/helm-publish.yml)

An intelligent conversational agent built with NVIDIA's NeMo Agent Toolkit (NAT), featuring a modern web UI and specialized tools for Run:Ai cluster management.

## 📑 Table of Contents

- [🎯 Features](#-features)
- [📋 Prerequisites](#-prerequisites)
- [🚀 Quick Start](#-quick-start)
  - [Deploy to Kubernetes with Helm](#deploy-to-kubernetes-with-helm-)
  - [Local Development](#local-development)
- [📁 Project Structure](#-project-structure)
- [🤖 What Can the Agent Do?](#-what-can-the-agent-do)
- [🚀 Submitting Jobs with the Agent](#-submitting-jobs-with-the-agent)
- [🔄 Job Lifecycle Management](#-job-lifecycle-management)
- [🔔 Proactive Monitoring & Auto-Troubleshooting](#-proactive-monitoring--auto-troubleshooting)
- [🔬 Advanced Failure Analysis](#-advanced-failure-analysis)
- [🧠 REST API Executor (Datasource Management)](#-rest-api-executor-datasource-management)
- [🏗️ Architecture](#️-architecture)
- [🔧 Configuration](#-configuration)
- [📚 Documentation](#-documentation)
- [🧪 Development](#-development)
- [🐛 Troubleshooting](#-troubleshooting)
- [🤝 Contributing](#-contributing)
- [📊 CI/CD Pipeline](#-cicd-pipeline)
- [📄 License](#-license)
- [👥 Maintainers](#-maintainers)

## 🎯 Features

- 🤖 **Intelligent Agent** - Powered by NVIDIA Llama 3.3 Nemotron Super (49B) with ReAct reasoning
- 💬 **Web UI** - Beautiful, responsive chat interface with real-time streaming
- 🔧 **Run:Ai Integration** - Specialized tools for cluster management and job creation
- 🚀 **Direct Job Submission** - Submit workloads to Run:AI with built-in safety validations
- 📦 **Batch Job Submission** - Submit multiple jobs (training, distributed, workspace) in one operation
- 🔄 **Unified Lifecycle Management** - Suspend, resume, and delete any workload type with one tool
- 🔔 **Proactive Monitoring** - Continuously monitor jobs and auto-troubleshoot failures with Slack alerts
- 🔬 **Advanced Failure Analysis** - Pattern recognition, cross-job correlation, and automated remediation suggestions
- 🗑️ **Two-Step Confirmation** - Safe deletion with explicit user confirmation
- ⚡ **Template-Based API Executor** - Fast, deterministic datasource management (NFS, PVC, Git, S3 with CRUD operations) - 20-50x faster than LLM
- 🔍 **Job Status & Troubleshooting** - Check job status and get detailed kubectl diagnostics
- 🩺 **Deep Troubleshooting** - Get pod logs, events, and AI-powered diagnosis for broken jobs
- 📚 **Documentation Search** - Ask questions about Run:AI features and get answers from official docs
- 🧠 **Agent Reasoning** - Optional intermediate steps view for debugging (disabled by default)
- 🔒 **Auto-Configuration** - Zero-config deployment in Run:Ai environments
- 🌙 **Dark/Light Theme** - Choose your preferred appearance

## 📋 Prerequisites

- Nvidia API Key for NIMs. [Nvidia Build](https://build.nvidia.com)
- Run:Ai environment with a provisioned `Application` for API access. [How to Create a Run:Ai Application](https://run-ai-docs.nvidia.com/self-hosted/2.22/infrastructure-setup/authentication/applications)
- Docker Registry
- Docker CLI

**macOS Users:** If running locally and you encounter OpenMP library conflicts, set this environment variable:
```bash
export KMP_DUPLICATE_LIB_OK=TRUE
# Add to your ~/.zshrc or ~/.bashrc to make it permanent
```

## 🚀 Quick Start

### Deploy to Kubernetes with Helm 🎯

Deploy the agent with all features enabled using Helm (recommended deployment method):

```bash
# 1. Create namespace and secrets
kubectl create namespace runai-agent

kubectl create secret generic runai-creds \
  --namespace runai-agent \
  --from-literal=RUNAI_CLIENT_ID="[YOUR_CLIENT_ID]" \
  --from-literal=RUNAI_CLIENT_SECRET="[YOUR_CLIENT_SECRET]" \
  --from-literal=RUNAI_BASE_URL="https://your-cluster.run.ai"

kubectl create secret generic nvidia-key \
  --namespace runai-agent \
  --from-literal=NVIDIA_API_KEY="[YOUR_NVIDIA_API_KEY]"

# 2. Install with Helm
helm install runai-agent ./deploy/helm/runai-agent \
  --namespace runai-agent \
  --set runai.existingSecret="runai-creds" \
  --set nvidia.existingSecret="nvidia-key" \
  --set failureAnalysis.persistence.storageClassName="your-rwx-storage-class"
```

**Features Included:**
- ✅ Monitoring sidecar (continuous failure detection)
- ✅ Persistent failure database (2Gi PVC)
- ✅ RBAC for kubectl access
- ✅ Auto-configured secrets

See [Helm Chart README](deploy/helm/runai-agent/README.md) for advanced configuration options.

---

### Local Development

#### Quick Start Script (Recommended)

```bash
# 1. Set required environment variables
export NVIDIA_API_KEY="[YOUR_NVIDIA_API_KEY]"
export RUNAI_CLIENT_ID="[YOUR_CLIENT_ID]"
export RUNAI_CLIENT_SECRET="[YOUR_CLIENT_SECRET]"
export RUNAI_BASE_URL="https://your-cluster.run.ai"

# 2. Run the agent
./deploy/start-local.sh
```

**Access the API:** http://localhost:8000/docs

#### Docker Deployment

```bash
# 1. Build the Docker image
./deploy/build-docker.sh

# 2. Run with Docker
docker run -p 3000:3000 -p 8000:8000 \
  -e NVIDIA_API_KEY="[YOUR_NVIDIA_API_KEY]" \
  -e RUNAI_CLIENT_ID="[YOUR_CLIENT_ID]" \
  -e RUNAI_CLIENT_SECRET="[YOUR_CLIENT_SECRET]" \
  -e RUNAI_BASE_URL="[YOUR_RUNAI_BASE_URL]" \
  ghcr.io/runai-professional-services/runai-agent:latest
```

**Access the UI:** http://localhost:3000

#### With kubectl Troubleshooting (Optional)

To enable kubectl troubleshooting features, mount your kubeconfig:

```bash
docker run -p 3000:3000 -p 8000:8000 \
  -e NVIDIA_API_KEY="[YOUR_NVIDIA_API_KEY]" \
  -e RUNAI_CLIENT_ID="[YOUR_CLIENT_ID]" \
  -e RUNAI_CLIENT_SECRET="[YOUR_CLIENT_SECRET]" \
  -e RUNAI_BASE_URL="[YOUR_RUNAI_BASE_URL]" \
  -e KUBECONFIG="/root/.kube/config" \
  -v "/path/to/your/kubeconfig.yaml:/root/.kube/config:ro" \
  ghcr.io/runai-professional-services/runai-agent:latest
```

**Example:**
```bash
# If your kubeconfig is at ~/.kube/config
docker run -p 3000:3000 -p 8000:8000 \
  -e NVIDIA_API_KEY="[YOUR_NVIDIA_API_KEY]" \
  -e RUNAI_CLIENT_ID="[YOUR_CLIENT_ID]" \
  -e RUNAI_CLIENT_SECRET="[YOUR_CLIENT_SECRET]" \
  -e RUNAI_BASE_URL="[YOUR_RUNAI_BASE_URL]" \
  -e GITHUB_TOKEN="[YOUR_GITHUB_TOKEN]" \
  -e KUBECONFIG="/root/.kube/config" \
  -v "$HOME/.kube/config:/root/.kube/config:ro" \
  ghcr.io/runai-professional-services/runai-agent:latest
```

**Important:**
- The `-e KUBECONFIG="/root/.kube/config"` tells kubectl where to find the config INSIDE the container
- The `-v "HOST_PATH:/root/.kube/config:ro"` mounts your HOST kubeconfig to the container's expected path
- Replace `HOST_PATH` with the absolute path to your kubeconfig file

**What this enables:**
- ✅ Job code generation (requires only `NVIDIA_API_KEY`)
- ✅ Job submission (requires Run:AI credentials)
- ✅ Job status checking (requires Run:AI credentials)
- ✅ Kubectl troubleshooting with logs and events (requires `KUBECONFIG`)

**Note:** When deployed in Kubernetes, the agent automatically uses the ServiceAccount for kubectl access (no KUBECONFIG needed).

See [docs/QUICKSTART.md](docs/QUICKSTART.md) for detailed instructions.

---

## 🖥️ RunAI CLI - Remote Agent Connection

The `runai-cli` is a TypeScript CLI that connects to remote agent deployments for team collaboration.

### Quick Start

```bash
# 1. Install CLI
cd runai-cli
npm install && npm run build && npm link

# 2. Connect to remote agent (Helm/Docker deployment)
runai-cli connect https://your-agent-url.com

# 3. Verify connection
runai-cli server status

# 4. Use the CLI
runai-cli ask "Show me all projects"
runai-cli submit "Create a training job with 2 GPUs"
runai-cli chat  # Interactive mode
```

### Key Features

- 🌐 **Connect to any deployment** - Helm, Docker, Kubernetes
- 💬 **Natural language** - Submit jobs using plain English
- 🔄 **Switch agents** - Easily switch between prod/staging/local
- 📊 **Full functionality** - All agent features available remotely

### Your Ingress Configuration

```yaml
# Expose port 3000 - Nginx handles internal routing to backend (8000)
spec:
  rules:
  - host: runai-agent.your-domain.com
    http:
      paths:
      - backend:
          service:
            name: runai-agent
            port:
              number: 3000  # ✅ Correct!
```

**📚 Full CLI Documentation:** [runai-cli/docs/REMOTE_CONNECTION.md](runai-cli/docs/REMOTE_CONNECTION.md)

---

## 📁 Project Structure

```
├── apps/
│   └── runai-agent-test-frontend/    # Next.js Web UI
├── runai-agent/         # Custom Run:AI agent (uses NAT 1.3.1 from PyPI)
│   ├── config/
│   │   └── workflow.yaml              # Agent configuration & function definitions
│   ├── src/
│   │   └── runai_agent/
│   │       ├── functions/             # Agent function modules
│   │       │   ├── environment_info.py            # Environment status & listing
│   │       │   ├── job_generator.py               # Python code generation from GitHub
│   │       │   ├── job_status.py                  # Job status checking
│   │       │   ├── job_submit.py                  # Single-node training job submission
│   │       │   ├── job_submit_distributed.py     # Distributed/multi-node training
│   │       │   ├── job_submit_workspace.py        # Interactive workspace submission
│   │       │   ├── job_submit_batch.py            # Batch submission (multiple jobs)
│   │       │   ├── kubectl_troubleshoot.py        # Deep kubectl troubleshooting
│   │       │   ├── template_executor.py           # Template-based API executor (fast!)
│   │       │   ├── proactive_monitor.py           # Proactive monitoring & auto-troubleshooting
│   │       │   └── workload_lifecycle.py          # Suspend/resume/delete jobs
│   │       ├── templates/             # Jinja2 templates for API operations
│   │       │   ├── _base/                   # Shared auth & lookup templates
│   │       │   ├── datasource/              # NFS, PVC, Git, S3 templates
│   │       │   ├── org_unit/                # Project, Department templates
│   │       │   └── generic/                 # Universal list/get/delete
│   │       ├── template_manager.py    # Template rendering & execution
│   │       ├── rest_api/              # REST API integration
│   │       │   ├── swagger_fetcher.py       # OpenAPI schema fetching
│   │       │   └── endpoint_finder.py       # Semantic endpoint discovery
│   │       ├── utils/                 # Shared utilities
│   │       │   └── helpers.py               # Security, validation, workload search
│   │       └── register.py            # Function registration with NAT
│   ├── pyproject.toml                 # Package config (NAT 1.3.1 dependency)
│   └── README.md                      # Custom agent documentation
├── docs/                               # Documentation
│   ├── QUICKSTART.md                  # Getting started guide
│   ├── DEPLOYMENT.md                  # Deployment instructions
│   ├── SIDECAR_DEPLOYMENT.md          # Production sidecar deployment guide
│   ├── PROACTIVE_MONITORING.md        # Proactive monitoring & auto-troubleshooting guide
│   └── FAILURE_ANALYSIS.md            # Advanced failure analysis guide
├── deploy/                             # Deployment configurations
│   ├── build-docker.sh                 # Docker build script
│   ├── Dockerfile                      # Simplified combined Docker image (UI + Backend)
│   ├── nginx.conf                      # Static Nginx configuration
│   ├── SIMPLIFICATION_SUMMARY.md       # Architecture simplification details
│   ├── helm/                           # Helm chart (recommended deployment)
│   │   └── runai-agent/                   # Production-ready Helm chart
│   ├── k8s/                            # Kubernetes manifests (alternative to Helm)
│   │   ├── rbac.yaml                      # RBAC for kubectl access
│   │   ├── runai-agent-with-sidecar.yaml  # Agent with monitoring sidecar
│   │   └── failure-analysis-pvc.yaml      # PVC for shared failure database
│   └── start-local.sh                  # Quick start script for local development
├── runai-cli/                          # TypeScript CLI for remote agent connection
│   ├── docs/
│   │   ├── REMOTE_CONNECTION.md           # Remote connection guide (Helm, Docker, etc.)
│   │   ├── NATURAL_LANGUAGE_GUIDE.md      # Natural language job submission
│   │   └── QUICKSTART_EXAMPLES.md         # Quick usage examples
│   └── README.md                       # Full CLI command reference
└── CHANGELOG.md                        # Version history
```

**Dependencies:**
- **NVIDIA NeMo Agent Toolkit 1.3.1** - Installed from PyPI (`nvidia-nat>=1.3.0`)
- **nat_simple_web_query plugin** - Installed from GitHub for `webpage_query` tool
  - Required for Run:AI documentation search (`runai_docs_search`)
  - Required for API documentation search (`runai_api_docs`) used by `llm_smart_executor`
  - Not available on PyPI, must be installed from NAT source repository

## 🤖 What Can the Agent Do?

### Run:Ai Operations
- Query cluster environment and configuration
- **Submit jobs directly to Run:AI cluster** (with safety validations)
- **Submit distributed training jobs** (PyTorch, TensorFlow, MPI) with multi-worker support
- **Submit interactive workspaces** (Jupyter, VSCode, custom environments)
- **Batch job submission** - Submit multiple jobs in one operation (any mix of training, distributed, workspace)
- **Check job status and troubleshoot issues** (works in any environment)
- **Proactively monitor workloads** - Auto-detect failures and send alerts with troubleshooting reports
- **Manage datasources & projects** - Fast template-based CRUD operations (NFS, PVC, Git, S3, Projects, Departments)
- **Search Run:AI official documentation** (answers questions about Run:AI features and concepts)
- Generate Python code for job submissions (uses real GitHub examples)
- Generate job YAML files (training, interactive, Jupyter)
- Explain Run:Ai concepts and best practices
- Search Run:Ai code examples from GitHub

### Example Queries

**General Operations:**
```
"Show me the current status of the environment"
"How do I submit a job using the Runapy SDK?"
```

**Documentation Search:**
```
"What is a nodePool in Run:AI?"
"How do I configure GPU quotas?"
"Explain Run:AI environments"
"What are the different workload types in Run:AI?"
"How does Run:AI scheduler work?"
```

**Job Submission:**
```
"Submit a training job with 2 GPUs to project-01"
"Preview a job submission without actually submitting it"
"Submit a distributed PyTorch job with 4 workers and 2 GPUs per worker"
"Submit a distributed TensorFlow training job to project-01"
```

**Batch Job Submission:**
```
"Submit 5 training jobs to project-01"
"Create 3 Jupyter workspaces with different configurations"
"Submit training jobs for projects project-01, project-02, and project-03"
"Batch submit 10 jobs with the following specs..."
```

**Workspace Submission:**
```
"Create a Jupyter workspace with 1 GPU in project-01"
"Submit a VSCode workspace named 'my-workspace' with 0.5 GPU"
"Launch a Jupyter notebook workspace for data analysis"
```

**Code Generation:**
```
"Generate Python code for the runapy sdk for a distributed training job with 4 GPUs"
"What is an example of submitting a training job with the Python runapy sdk?"
```

**Datasource Management:**
```
"Create an NFS datasource named ml-data in project-01 with server 10.0.1.50 and path /data"
"List all PVC datasources in project-01"
"Create an S3 storage datasource named ml-s3 in project-01 with S3 bucket name my-datasets"
"Delete the Git datasource named old-code from project-01"
```

**Status & Troubleshooting:**
```
"What is the status of my-training-job in project-01?"
"Troubleshoot job broken in project-01"
"Debug the training job my-job in project-02"
"Show me logs and events for failed-job"
"What's wrong with my job that keeps failing?"
```

**Proactive Monitoring:**
```
"Start monitoring all jobs in the cluster"
"Monitor project-01 for failures"
"Watch for job failures for the next 30 minutes"
"What's the monitoring status?"
```

## 🚀 Submitting Jobs with the Agent

The agent can now **directly submit workloads** to your Run:AI cluster with built-in safety validations.

### 🔒 Safety Features

- ✅ **Dry-run by default** - Always previews before submitting
- ✅ **Explicit confirmation** - Requires user approval
- ✅ **Project whitelist** - Only submits to approved projects
- ✅ **Resource limits** - Enforces GPU quotas
- ✅ **Validation checks** - Verifies job specs before submission

### 📝 Job Submission Examples

#### Example 1: Simple Training Job

```
Submit a training job:
  name: my-training-job
  project: project-01
  image: pytorch/pytorch:latest
  gpus: 2
```

**Agent Response:**
```
✅ Job Submitted Successfully!

Job ID: 12345
Name: my-training-job
Project: project-01
Status: Submitted

📊 Monitor your job:
View the running job under `Workloads on the `Workload Manager` tab.
```

#### Example 2: Dry-Run (Preview Only)

```
Preview this job without submitting:
  name: test-job
  project: project-01
  image: nvidia/cuda:12.1.0-base
  gpu: 1
  dry_run: true
```

**Agent Response:**
```
✅ Job Validation Passed

Job Name: test-job
Project: project-01
Image: nvidia/cuda:12.1.0-base
Resources:
  • GPU: 1
  • CPU: 0.1 cores
  • Memory: 100M

This is a DRY RUN - job will NOT be submitted.
Set dry_run=false and confirmed=true to actually submit.
```

#### Example 3: Quick Start Demo

```
Submit a quickstart demo job to project-01 with 1 GPU
```

The agent will:
1. ✅ Validate the job spec
2. 📋 Show you a preview
3. ⚠️  Ask for confirmation
4. 🚀 Submit to Run:AI cluster
5. 📊 Provide monitoring links

#### Example 4: Custom Configuration

```
Submit training job:
  name: distributed-training
  project: project-01
  image: gcr.io/run-ai-demo/quickstart-demo
  command: python train.py --distributed
  gpus: 4
  confirmed: true
```

#### Example 5: Distributed Training Job (PyTorch)

```
Submit a distributed PyTorch job:
  name: pytorch-distributed-training
  project: project-01
  image: kubeflow/pytorch-dist-mnist:latest
  framework: pytorch
  workers: 2
  gpus: 1
```

**Agent Response:**
```
✅ Distributed Job Submitted Successfully!

Job Name: pytorch-distributed-training
Project: project-01
Framework: PyTorch
Workers: 2 (+ 1 master)
GPUs per Worker: 1
Total GPUs: 3

📊 Monitor your job:
View the distributed workload under `Workloads` on the `Workload Manager` tab.
```

#### Example 6: Distributed Training Job (TensorFlow)

```
Submit a distributed TensorFlow job named "tf-dist-job" to project-01:
  image: tensorflow/tensorflow:latest-gpu
  framework: tensorflow
  workers: 4
  gpus: 2
```

**Agent Response:**
```
✅ Distributed Job Submitted Successfully!

Job Name: tf-dist-job
Project: project-01
Framework: TensorFlow
Workers: 4 (+ 1 master)
GPUs per Worker: 2
Total GPUs: 10

The job uses the TensorFlow distributed training framework with:
  • Master: 1 pod with 2 GPUs (coordinates training)
  • Workers: 4 pods with 2 GPUs each (parallel training)

📊 Monitor your job:
View the distributed workload under `Workloads` on the `Workload Manager` tab.
```

#### Example 7: Interactive Workspace (Jupyter)

```
Submit a Jupyter workspace:
  name: my-jupyter-workspace
  project: project-01
  image: jupyter/scipy-notebook
  gpu: 1
```

**Agent Response:**
```
✅ Workspace Submitted Successfully!

Workspace ID: abc123
Name: my-jupyter-workspace
Project: project-01
Type: jupyter
GPU: 1.0 GPU portion

📊 Access your workspace:
Once running, access Jupyter via the Run:AI UI

🌐 View in UI:
https://runcluster.example.com/projects/project-01/workspaces
```

#### Example 8: VSCode Workspace with GPU Portion

```
Submit a VSCode workspace named "vscode-dev" with 0.5 GPU in project-01
```

**Agent Response:**
```
✅ Workspace Submitted Successfully!

Workspace ID: xyz789
Name: vscode-dev
Project: project-01
Type: vscode
GPU: 50% GPU portion

📊 Access your workspace:
Once running, access VSCode via the Run:AI UI
```

**Key Differences - Workspaces vs Training Jobs:**
- **Workspaces** are interactive environments with web interfaces (Jupyter, VSCode)
- Support **GPU portions** (e.g., 0.5 GPU) for efficient resource sharing
- Automatically configured with exposed URLs and ports
- Ideal for development, experimentation, and interactive analysis
- **Training Jobs** are for batch processing and model training

#### Example 9: Batch Job Submission (Multiple Jobs at Once)

The agent supports **batch submission** to submit multiple jobs in a single operation:

```
Submit 3 training jobs to project-01:
  - job1 with 2 GPUs using pytorch/pytorch:latest
  - job2 with 1 GPU using pytorch/pytorch:latest
  - job3 with 4 GPUs using tensorflow/tensorflow:latest
```

**Agent Response:**
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

2. job2 (training)
   - Project: project-01
   - Image: pytorch/pytorch:latest
   - GPUs: 1

3. job3 (training)
   - Project: project-01
   - Image: tensorflow/tensorflow:latest
   - GPUs: 4

⚠️  Confirmation Required

You are about to submit 3 jobs to Run:AI cluster.
```

After confirmation:
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

**Batch Submission Features:**
- ✅ Submit multiple jobs (training, distributed, workspace) in one operation
- ✅ Mix different job types in the same batch
- ✅ Continue on error (partial success supported)
- ✅ Comprehensive reporting with success/failure status for each job
- ✅ Same safety features as single submission (dry-run, confirmation, validation)
- ✅ **Production Ready** - Fully tested and validated on live Run:AI clusters

**Example - Mixed Job Types:**
```
Submit these jobs to project-01:
  - training job named "model-training" with 2 GPUs
  - distributed job named "dist-training" with 4 workers and 2 GPUs per worker using pytorch
  - jupyter workspace named "analysis" with 1 GPU
```

**When to Use Batch Submission:**
- Submitting multiple jobs to the same project
- Creating similar jobs with different configurations  
- Bulk provisioning for multiple users/teams
- Automated job creation from scripts or pipelines
- Parallel experimentation with different hyperparameters
- Multi-stage ML pipelines requiring multiple workloads

### 🛡️ Configuration

**By default, the agent has full access to all projects and resources.** Safety features like dry-run and confirmation are enabled to prevent accidents.

To add restrictions (optional), edit `runai-agent/configs/workflow.yaml`:

```yaml
runai_submit_workload:
  _type: runai_submit_workload
  dry_run_default: true           # Always preview first (recommended)
  require_confirmation: true      # Require explicit approval (recommended)
  # Optional restrictions (uncomment to enable):
  # allowed_projects: ["project-01", "project-02"]  # Limit to specific projects
  # max_gpus: 8                                     # Cap GPU requests per job

runai_submit_distributed_workload:
  _type: runai_submit_distributed_workload
  dry_run_default: true
  require_confirmation: true
  # Optional restrictions:
  # allowed_projects: ["project-01"]
  # max_gpus_per_worker: 8

runai_submit_workspace:
  _type: runai_submit_workspace
  dry_run_default: true
  require_confirmation: true
  # Optional restrictions:
  # allowed_projects: ["project-01"]
  # max_gpus: 8

runai_submit_batch:
  _type: runai_submit_batch
  dry_run_default: true
  require_confirmation: true
  # Optional restrictions:
  # allowed_projects: ["project-01"]
  # max_gpus_per_job: 8
  # max_batch_size: 20

runai_template_executor:
  _type: runai_template_executor
  require_confirmation: true
  dry_run_default: true
  debug_mode: false  # Enable via RUNAI_TEMPLATE_DEBUG=true env var
  # Optional restrictions:
  # allowed_projects: ["project-01"]
  # allowed_resource_types: ["nfs", "pvc", "git", "s3", "hostpath", "project", "department"]
```

**Recommended Practice:**
- Keep `dry_run_default: true` and `require_confirmation: true` enabled
- Only add project/resource restrictions if needed for your security requirements
- By default, users have full access with safety confirmations

### ⚠️ Important Notes

1. **Authentication Required**: Ensure `RUNAI_CLIENT_ID`, `RUNAI_CLIENT_SECRET`, and `RUNAI_BASE_URL` are set
2. **Project Access**: You can only submit to whitelisted projects
3. **Resource Limits**: GPU requests are capped at `max_gpus`
4. **Confirmation**: Set `confirmed=true` to bypass interactive approval

### 🔍 Troubleshooting Job Submission

**Project Not Found:**
```
❌ Project Not Found

The project "my-project" was not found in your Run:AI cluster.

Available projects:
  • project-01
  • project-02

Please use one of the available projects.
```

**Exceeded GPU Limit:**
```
❌ Validation Failed

GPU request (16) exceeds maximum allowed (8)
Please reduce GPU count or contact your administrator.
```

**Missing Authentication:**
```
⚠️ Run:AI SDK is not installed

To submit jobs directly, install the Run:AI SDK:
pip install runapy==1.223.0
```

---

## 🔄 Job Lifecycle Management

The agent provides comprehensive workload management through a unified lifecycle tool that handles suspend, resume, and delete operations for all workload types (training, workspace, distributed).

### 📊 Check Job Status

Query the status of any running or completed job:

```
Check the status of job "my-training-job" in project-01
```

**Agent Response:**
```
✅ Job Status: my-training-job

📋 Basic Information:
  • ID: f7326e42-f587-4a0d-b70b-7a89a19b19dd
  • Status: Running
  • Type: Run:AI Workload
  • Project: project-01

🔍 Pod Details:
  • Pod Name: my-training-job-0-0
  • Node: gpu-node-01
  • Phase: Running
  • GPUs Allocated: 4

⏱️ Timing:
  • Started: 2025-11-20 10:30:00
  • Running for: 2h 15m
```

### ⏸️ Suspend a Job

Pause a running job to free up resources (can be resumed later):

```
Suspend the job "my-training-job" in project-01
```

**Agent Response:**
```
✅ The job 'my-training-job' in project-01 has been successfully suspended.

The job is now in a paused state with workload ID `f7326e42-f587-4a0d-b70b-7a89a19b19dd`.
To resume the job later, you can use: "Resume job my-training-job in project-01"
```

### ▶️ Resume a Job

Restart a previously suspended job:

```
Resume the job "my-training-job" in project-01
```

**Agent Response:**
```
✅ The job 'my-training-job' in project-01 has been successfully resumed.

The workload ID is f7326e42-f587-4a0d-b70b-7a89a19b19dd.
You can monitor its status with: "Check status of job my-training-job in project-01"
```

### 🗑️ Delete a Job

**⚠️ Note:** Deletion requires **two-step confirmation** in conversational UI mode:

**Step 1 - Initial Request:**
```
Delete the job "old-training-job" from project-01
```

**Agent Response:**
```
⚠️ **WARNING: Permanent Action**

You are about to delete the job 'old-training-job' in project 'project-01'.
This action is irreversible and will permanently remove all associated resources and data.

To proceed, please explicitly confirm by saying 'yes', 'confirm', or 'proceed'.
```

**Step 2 - User Confirms:**
```
yes, delete it
```

**Agent Response:**
```
✅ The job 'old-training-job' from project 'project-01' has been successfully deleted.

The workload type was Training with ID f7326e42-f587-4a0d-b70b-7a89a19b19dd.
All associated resources have been permanently removed from the cluster.
```

**Note:** To cancel deletion, simply respond with "no", "cancel", or "nevermind" and the agent will not proceed.

### 🛡️ Safety Features

- **Project Whitelist**: Can only manage jobs in allowed projects
- **Two-Step Confirmation**: Deletion requires explicit user confirmation (in UI mode)
- **Validation**: All operations validate job existence before proceeding
- **Error Handling**: Clear feedback for missing jobs or permission issues
- **Status Checks**: Prevents invalid operations (e.g., resuming a running job)

---

## 🔔 Proactive Monitoring & Auto-Troubleshooting

The agent can **continuously monitor** your Run:AI workloads and automatically troubleshoot failures in real-time, with optional Slack notifications.

### ✨ Key Features

- 🔄 **Continuous Polling** - Check job status at configurable intervals (default: 60s)
- 🔍 **Failure Detection** - Automatically detects Failed, Error, ImagePullBackOff, OOMKilled, and Unknown states
- 🔧 **Auto-Troubleshooting** - Runs kubectl diagnostics (logs, events, pod status) when failures are detected
- 🔔 **Smart Alerts** - Sends formatted alerts to console and Slack with troubleshooting reports
- 🚫 **Anti-Spam** - Configurable alert limits per job to prevent notification flooding
- 🎯 **Project Filtering** - Monitor all projects or specific ones
- ⏱️ **Flexible Duration** - Run continuously or for a specified time period

### 📊 Usage Examples

**Start Monitoring All Jobs:**
```
Start monitoring all jobs in the cluster
```

The agent will:
1. Poll all workloads every 60 seconds
2. Detect failures (Failed, Error, ImagePullBackOff, OOMKilled, Unknown phases)
3. Auto-troubleshoot with kubectl (pod status, logs, events)
4. Send formatted alerts with diagnostic information
5. Continue monitoring until stopped or duration expires

**Monitor Specific Project:**
```
Monitor jobs in project ml-team
```

**Time-Limited Monitoring:**
```
Monitor all jobs for 30 minutes
```

**Check Monitoring Status:**
```
What is the monitoring status?
```

### 🔔 Alert Example

When a failure is detected, you'll see alerts like this:

```
🔴 Job Failure Alert: my-training-job

**Project:** ml-team
**Job Name:** my-training-job
**Type:** Training
**Status:** OOMKilled
**Time:** 2025-12-04 13:46:05
**UUID:** fbe3b7a8-37a0-4e9a-8ef1-067a25a73ad1

**Auto-Troubleshoot Report:**
🔍 Auto-Troubleshoot Report for my-training-job

## Pod Status:
NAME                 READY   STATUS      RESTARTS   AGE
my-training-job-0-0  0/1     OOMKilled   0          5h42m

## Logs (last 50 lines):
[Container logs showing memory allocation errors...]

## Events:
[Kubernetes events showing OOM kills and memory limits...]
```

### 🔧 Slack Integration (Optional)

To enable Slack notifications, configure a webhook in `runai-agent/configs/workflow.yaml`:

```yaml
runai_proactive_monitor:
  slack_webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
  poll_interval_seconds: 60
  enable_auto_troubleshoot: true
  max_alerts_per_job: 1
```

### 🛡️ Configuration Options

Edit `runai-agent/configs/workflow.yaml` to customize monitoring behavior:

```yaml
runai_proactive_monitor:
  # Projects to monitor (* = all)
  monitored_projects: ["*"]
  
  # Check interval (seconds)
  poll_interval_seconds: 60
  
  # Auto-troubleshoot failures
  enable_auto_troubleshoot: true
  
  # Monitor all jobs or only failures
  monitor_only_failed: false
  
  # Prevent alert spam
  max_alerts_per_job: 1
  
  # Optional Slack webhook
  slack_webhook_url: "https://hooks.slack.com/services/..."
```

### 📈 Benefits

**Before Proactive Monitoring:**
- ❌ Manual job status checks
- ❌ Delayed failure detection (hours/days)
- ❌ Manual troubleshooting for each failure
- ❌ No overnight/weekend coverage

**After Proactive Monitoring:**
- ✅ Automatic failure detection (seconds/minutes)
- ✅ Instant troubleshooting reports
- ✅ Slack alerts for immediate awareness
- ✅ 24/7 monitoring without manual intervention

**Perfect for:**
- Production ML training pipelines
- Multi-project environments
- Teams needing fast incident response
- Overnight and weekend job monitoring

📚 **Full Documentation:** [docs/PROACTIVE_MONITORING.md](docs/PROACTIVE_MONITORING.md)

---

## 🔬 Advanced Failure Analysis

The agent includes **intelligent failure analysis** that goes beyond logs to provide pattern recognition, cross-job correlation, and automated remediation suggestions.

### 🧪 Quick Test Prompts

**Get Started (Basic Queries):**
```
Show me failure statistics
What failure patterns have been detected?
Analyze recent job failures
How many failures have been recorded?
```

**Deep Analysis:**
```
What are the top failure types and how can I fix them?
Show me problematic nodes from the last 7 days
Analyze failures for project ml-team
Give me remediation suggestions for OOMKilled errors
```

**Specific Troubleshooting:**
```
What's the failure rate for gpu-node-03?
Which container images are causing the most failures?
Show me correlation between failure types and time of day
Get solutions that worked for ImagePullBackOff errors
```

### ✨ Key Capabilities

**Pattern Recognition:**
- "This is the 5th OOMKilled in project-01 today"
- "Failures spike between 2-4pm (resource contention)"
- Detects repeated failures across jobs and projects

**Cross-Job Correlation:**
- "Node gpu-node-03 has 90% failure rate across 15 jobs"
- "Container image pytorch:2.0 failed 8 times in the last hour"
- Identifies systemic issues before they become critical

**Automated Remediation:**
- Rule-based solutions for common issues
- Historical solutions: "3 other users fixed this by increasing memory 2x"
- Success rate tracking: Solutions ranked by effectiveness

**Knowledge Graph:**
- Persistent database of failure → solution mappings
- Builds institutional knowledge over time
- Community learning from successful fixes

### 📊 Usage Examples

**Analyze Patterns:**
```
Analyze failures from the last 7 days
```

**Agent Response:**
```
📊 Advanced Failure Analysis Report

## 📈 Summary
- Total Failures: 23
- Projects Affected: 4
- Unique Failure Types: 5

## 🔍 Detected Patterns

🔴 Project: ml-team
   - Failures: 8
   - Top failure types: {'OOMKilled': 5, 'ImagePullBackOff': 3}

## 🔥 Problematic Nodes

🔴 Node: gpu-node-03
   - Failures: 12 across 8 jobs
   - Failure Rate: 75.0%

## 💡 Recommendations

⚠️ Node 'gpu-node-03' has 75% failure rate. Consider cordoning for maintenance.
🐳 Image 'pytorch:2.0' is associated with 5 failures. Verify compatibility.
```

**Get Remediation Suggestions:**
```
How do I fix OOMKilled failures?
```

**Agent Response:**
```
🔧 Automated Remediation Suggestions

Failure Type: OOMKilled
Description: Out of Memory - Pod exceeded memory limit

## 🎯 Rule-Based Solutions

1. Increase memory request/limit by 2x
2. Optimize application memory usage

## 📊 Historical Solutions (Community Knowledge)

1. Increase memory limit from 8Gi to 16Gi
   ✅ Success Rate: 85.7% (6 successes, 1 failure)

2. Enable gradient checkpointing to reduce memory usage
   ✅ Success Rate: 75.0% (3 successes, 1 failure)
```

**Get Statistics:**
```
Show me failure statistics for the last 30 days
```

### 🔄 Automatic Integration

The failure analyzer **automatically integrates** with proactive monitoring:

- ✅ Every failure is recorded to the database
- ✅ Patterns are analyzed in real-time
- ✅ Remediation suggestions improve over time
- ✅ Knowledge graph builds automatically

**No manual setup required!** Just enable proactive monitoring:

```
Start monitoring all jobs
```

### 🎯 Benefits

**Before:**
- ❌ Manual investigation of each failure
- ❌ No visibility into systemic issues
- ❌ Repeated mistakes across teams
- ❌ Knowledge loss when team members leave

**After:**
- ✅ Automatic pattern detection
- ✅ Proactive identification of problematic nodes/images
- ✅ Institutional knowledge preservation
- ✅ Fast remediation with proven solutions

### 🛠️ Configuration

Edit `runai-agent/configs/workflow.yaml`:

```yaml
runai_failure_analyzer:
  _type: runai_failure_analyzer
  db_path: "/tmp/runai_failure_history.db"  # Failure history database
  lookback_days: 7  # Days of history to analyze
  pattern_threshold: 3  # Min occurrences to identify pattern
  enable_auto_remediation: false  # Enable automatic fixes (with confirmation)
```

**For production:** Mount a persistent volume to preserve failure history across restarts.

📚 **Documentation:**
- **[FAILURE_ANALYSIS.md](docs/FAILURE_ANALYSIS.md)** - Complete user guide
- **[FAILURE_ANALYSIS_QUICKSTART.md](docs/FAILURE_ANALYSIS_QUICKSTART.md)** - 5-minute quick start

---

## 🧠 Template-Based Datasource Management

The agent provides **fast, deterministic datasource and project management** through template-based execution - 20-50x faster than LLM generation.

📚 **Quick Start Guide:** [QUICKSTART_TEMPLATES.md](docs/QUICKSTART_TEMPLATES.md) - 5-minute testing guide with debug mode

### Architecture

**Template-Based Approach: Deterministic Jinja2 Templates**
- **Fast Execution** - 20-50x faster than LLM generation (< 1 second vs 2-5 seconds)
- **Deterministic** - Same input always produces same output
- **Debuggable** - Debug mode shows all API calls and responses
- **Proven** - Validated across NFS, PVC, Git, S3 datasources and project operations

### Features

- ✅ **Full CRUD Operations**: Create, list, and delete for NFS, PVC, Git datasources and projects
- ✅ **Natural Language**: No need to specify tool names - just ask naturally
- ✅ **Teaching Examples**: 5 core patterns (org-unit, flat spec, nested spec, list, delete)
- ✅ **Dynamic Adaptation**: LLM generalizes patterns to new resource types
- ✅ **Swagger Integration**: Endpoint discovery and schema validation
- ✅ **OAuth Authentication**: Secure authentication with Run:AI API
- ✅ **SSL Verification**: Proper certificate validation (verify=True enforced)
- ✅ **Dry-Run Mode**: Preview generated code before execution
- ✅ **Wildcard Validation**: Support for ["*"] to allow all projects by default

### Project & Department Operations (Pattern 1: Org-Unit Resources)

**Create Department:**
```
Create a department named test-dept with 8 GPU quota
```
✅ **Tested & Working** - Demonstrates org-unit resource creation with cluster lookup

**Create Project:**
```
Create a project named test-project with 4 GPU quota
Create a project named ml-team in department test-dept with 8 GPU quota
```
✅ **Tested & Working** - Shows project hierarchy and resource allocation

### NFS Operations (Pattern 2: Flat Spec Datasources)

**Create NFS:**
```
Create an NFS datasource named ml-datasets in test-project with server 192.168.1.100 and path /data/ml
```
✅ **Tested & Working** - Demonstrates flat spec datasource pattern

**List NFS:**
```
List all NFS datasources
Show me NFS storage in test-project
```
✅ **Tested & Working** - Pattern 4 (GET operations)

**Delete NFS:**
```
Delete the NFS datasource named ml-datasets from test-project
```
✅ **Tested & Working** - Pattern 5 (DELETE operations)

### PVC Operations (Pattern 3: Nested Spec Datasources)

**Create PVC:**
```
Create a PVC named test-pvc-storage with 10Gi storage in test-project with storage class ebs-csi
Create a 50Gi volume named training-data in test-project
```
✅ **Tested & Working** - Complex nested claimInfo structure handled perfectly!

**List PVCs:**
```
List all PVC datasources
Show me all PVC datasources
```
✅ **Tested & Working** - Universal list pattern with proper routing

**Delete PVC:**
```
Delete the PVC named test-pvc-storage from test-project
```
✅ **Tested & Working** - Clean deletion with confirmation

### Git Datasource Operations (Pattern 2: Flat Spec)

**Create Git:**
```
Create a Git datasource named code-repo with repository https://github.com/nvidia/nemo branch main in test-project
```
✅ **Tested & Working** - Git repository integration

**List Git:**
```
List all Git datasources
Show me Git storage in test-project
```
✅ **Ready to Use** - Same pattern as NFS/PVC list

**Delete Git:**
```
Delete the Git datasource named code-repo from project-01
```
✅ **Tested & Working** - Clean deletion with confirmation

### S3 Datasource Operations (Pattern 2: Flat Spec)

**Create S3:**
```
Create an S3 storage datasource named ml-s3-bucket in project-01 with S3 bucket name my-datasets and endpoint https://s3.amazonaws.com
```
✅ **Tested & Working** - S3 bucket integration

**Important for S3 prompts:**
- Use explicit phrasing: "**S3 storage datasource**" (not just "S3 datasource")
- Specify "**S3 bucket name**" (not just "bucket")
- This helps the agent correctly route to template executor instead of project creation

**List S3:**
```
List all S3 datasources in project-01
Show me S3 storage in project-01
```
✅ **Tested & Working** - Fast retrieval of S3 configurations

**Delete S3:**
```
Delete the S3 datasource named ml-s3-bucket from project-01
```
✅ **Tested & Working** - Clean deletion with confirmation

### How It Works

1. **Natural Language Input**: User asks in plain English
2. **Template Selection**: Agent selects appropriate Jinja2 template based on resource type and action
3. **Code Generation**: Template renders Python code with user parameters
4. **Preview (Dry-Run)**: Shows generated code for review (optional)
5. **Execution**: Runs code after confirmation
6. **Result**: Returns success/failure with details

**Debug Mode** (recommended for testing):
```bash
export RUNAI_TEMPLATE_DEBUG=true  # See all parameters, API calls, and responses
```

**Example Generated Code:**
```python
import requests

# Step 1: Authenticate with Run:AI API
token_response = requests.post(
    f"{base_url}/api/v1/token",
    json={"grantType": "client_credentials", "clientId": client_id, "clientSecret": client_secret},
    verify=True
)
# Access token retrieved from authentication response
headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}

# Step 2: Get project ID
projects_response = requests.get(f"{base_url}/api/v1/org-unit/project", headers=headers, verify=True)
project_obj = next(p for p in projects_response.json() if p["name"] == "project-01")
project_id = project_obj["id"]

# Step 3: Create NFS datasource
response = requests.post(
    f"{base_url}/api/v1/asset/datasource/nfs",
    headers=headers,
    json={
        "meta": {"name": "ml-datasets", "scope": "project", "projectId": project_id, "clusterId": cluster_id},
        "spec": {"server": "192.168.1.100", "path": "/data/ml", "readOnly": False}
    },
    verify=True
)
result = response.json()
```

### Architecture

The executor uses **deterministic Jinja2 templates**:
- Pre-built templates for common operations (NFS, PVC, Git, S3, Projects, Departments)
- Template patterns: auth, project lookup, flat spec, nested spec, list, delete
- Zero LLM overhead - instant code generation
- Debug mode for troubleshooting API calls

### Safety & Security

- ✅ **Project Whitelist**: Only allowed projects can be modified
- ✅ **SSL Certificate Verification**: No insecure requests
- ✅ **Confirmation Required**: Destructive operations need approval
- ✅ **Dry-Run Default**: Preview before execution
- ✅ **Error Handling**: Clear feedback on failures

---

## 🏗️ Architecture

### Simplified Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Combined Container                         │
│                                                             │
│  ┌──────────┐                                              │
│  │  Nginx   │  ← Entry point (port 3000)                   │
│  │  :3000   │    Static configuration                      │
│  └────┬─────┘                                              │
│       │                                                     │
│       ├─────→ /generate ──→ ┌──────────────┐             │
│       │       /docs         │  NAT Agent   │             │
│       │                     │    :8000     │             │
│       │                     └──────────────┘             │
│       │                                                    │
│       └─────→ /* ──────→   ┌──────────────┐             │
│                              │   Next.js    │             │
│                              │    :3001     │             │
│                              └──────────────┘             │
└─────────────────────────────────────────────────────────────┘

Access via Ingress/Service or Direct Connection
```

**Components:**
- **Nginx** (port 3000): Static reverse proxy configuration
  - Routes API requests (`/generate`, `/docs`) → Backend (8000)
  - Routes UI requests (`/*`) → Frontend (3001)
  - No dynamic configuration or path rewrites
- **Next.js UI** (port 3001): Modern web interface with SSE streaming
  - Pre-built at container build time (no runtime builds)
  - Fast startup (< 10 seconds)
- **NAT Agent** (port 8000): FastAPI backend with LangChain/LangGraph agent
  - Handles agent reasoning and tool execution
- **Supervisord**: Process manager for all services

**Key Improvements:**
- ✅ Static Nginx configuration (no dynamic generation)
- ✅ Pre-built frontend (12x faster startup)
- ✅ Standard reverse proxy patterns
- ✅ Simplified deployment (33% less code)

See [`deploy/SIMPLIFICATION_SUMMARY.md`](deploy/SIMPLIFICATION_SUMMARY.md) for full details.

## 🔧 Configuration

### Environment Variables

**Required:**
- `NVIDIA_API_KEY` - NVIDIA API key ([get here](https://build.nvidia.com))

**Run:AI Integration (Required for full functionality):**
- `RUNAI_CLIENT_ID` - Run:AI client ID for authentication
- `RUNAI_CLIENT_SECRET` - Run:AI client secret for authentication
- `RUNAI_BASE_URL` - Run:AI cluster URL (e.g., `https://your-cluster.run.ai`)
  - **Note:** This URL is automatically used in `workflow.yaml` for API documentation search
  - Set this to your actual Run:AI cluster URL - no code changes needed!

**Optional:**
- `GITHUB_TOKEN` - GitHub token (avoids API rate limits for fetching code examples)
- `RUNAI_FAILURE_DB_PATH` - Custom path for failure analysis database (default: `/tmp` for local, `/data` for K8s)
- `RUNAI_TEMPLATE_DEBUG` - Enable verbose logging for template executor (`true`/`false`, default: `false`)

**Auto-Detected (Run:Ai):**
- `RUNAI_PROJECT` - Automatically set by Run:Ai
- `RUNAI_JOB_NAME` - Automatically set by Run:Ai

### Agent Configuration

Edit `runai-agent/configs/workflow.yaml`:

```yaml
workflow:
  _type: react              # ReAct agent type
  llm_name: nvidia_nim      # Use NVIDIA NIM
  tool_names:
    - runailabs_environment_info
    - runai_submit_workload           # Direct job submission
    - runai_submit_distributed_workload # Distributed training jobs
    - runai_submit_workspace          # Interactive workspaces (Jupyter, VSCode)
    - runai_submit_batch              # Batch submission (multiple jobs)
    - runai_job_status                # Check job status
    - runai_manage_workload           # Unified lifecycle: suspend, resume, delete
    - runai_proactive_monitor         # Proactive monitoring & auto-troubleshooting
    - runai_failure_analyzer          # Advanced failure analysis
    - runai_template_executor         # Template-based datasource management (fast!)
    - runai_kubectl_troubleshoot      # Deep troubleshooting with kubectl
    - runailabs_job_generator         # Generate Python code
```

## 📚 Documentation

### Deployment Guides
- **[Helm Chart README](deploy/helm/runai-agent/README.md)** - ⭐ Recommended: One-command deployment with all features
- **[QUICKSTART.md](docs/QUICKSTART.md)** - Get started in 5 minutes
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Complete deployment guide
- **[SIDECAR_DEPLOYMENT.md](docs/SIDECAR_DEPLOYMENT.md)** - Production deployment with monitoring sidecar

### Feature Documentation
- **[QUICKSTART_TEMPLATES.md](docs/QUICKSTART_TEMPLATES.md)** - ⚡ Template-based datasource management (5-minute guide)
- **[PROACTIVE_MONITORING.md](docs/PROACTIVE_MONITORING.md)** - Proactive monitoring guide
- **[FAILURE_ANALYSIS.md](docs/FAILURE_ANALYSIS.md)** - Advanced failure analysis & pattern recognition
- **[FAILURE_ANALYSIS_QUICKSTART.md](docs/FAILURE_ANALYSIS_QUICKSTART.md)** - Quick start guide for failure analysis

### Reference
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and updates

## 🧪 Development

### Initial Setup

```bash
# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install the agent
cd runai-agent
pip install -e .

# 3. Install webpage_query plugin (required)
pip install "git+https://github.com/NVIDIA/NeMo-Agent-Toolkit.git@v1.3.1#subdirectory=examples/getting_started/simple_web_query"

# 4. Set environment variables
export NVIDIA_API_KEY="[YOUR_NVIDIA_API_KEY]"
export RUNAI_CLIENT_ID="[YOUR_CLIENT_ID]"
export RUNAI_CLIENT_SECRET="[YOUR_CLIENT_SECRET]"
export RUNAI_BASE_URL="https://your-cluster.example.com"
```

### Run Backend Only

```bash
source .venv/bin/activate
./deploy/start-local.sh
```

### Run with Hot Reload (Development)

```bash
# Terminal 1: Backend
source .venv/bin/activate
cd runai-agent
nat serve --config_file configs/workflow.yaml --reload

# Terminal 2: Frontend
cd apps/runai-agent-test-frontend
npm run dev
```

### Build Custom Image

```bash
# Backend only
# Quick build (recommended)
./deploy/build-docker.sh

# Or manually:
docker build -t runai-agent-ui:latest -f Dockerfile .
```

## 🐛 Troubleshooting

See [DEPLOYMENT.md](DEPLOYMENT.md#troubleshooting) for comprehensive troubleshooting guide.

**Quick Checks:**

```bash
# Check if environment variables are set (without displaying values)
printenv | grep -E "NVIDIA_API_KEY|RUNAI"

# Test backend
curl http://localhost:8000/docs

# View logs
docker logs <container_id>

# Check agent functions
nat info components --types function
```

### Enable Agent Reasoning Steps (Advanced)

By default, the agent provides clean, concise output. To see the agent's internal reasoning and tool usage (useful for debugging):

**For Local Development:**
```bash
docker run -p 3000:3000 -p 8000:8000 \
  -e NVIDIA_API_KEY="[YOUR_NVIDIA_API_KEY]" \
  -e NEXT_PUBLIC_ENABLE_INTERMEDIATE_STEPS=true \
  ghcr.io/runai-professional-services/runai-agent:latest
```

**For Helm Deployment:**

Add to your Helm values or use `--set` flag:
```bash
helm install runai-agent ./deploy/helm/runai-agent \
  --namespace runai-agent \
  --set frontend.env.NEXT_PUBLIC_ENABLE_INTERMEDIATE_STEPS="true"
```

Or add to a `values.yaml` file:
```yaml
frontend:
  env:
    NEXT_PUBLIC_ENABLE_INTERMEDIATE_STEPS: "true"
```

This will show the agent's thought process, tool calls, and intermediate results.

## 🤝 Contributing

This project uses:
- **Backend**: Python 3.11+, FastAPI, NeMo Agent Toolkit, LangChain
- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS
- **Infrastructure**: Docker, Kubernetes, Run:AI

See our [Contributing Guide](.github/PULL_REQUEST_TEMPLATE.md) and [Cursor Rules](.cursorrules) for development guidelines.

## 📊 CI/CD Pipeline

This project uses GitHub Actions for automated testing, building, and deployment.

### 🔄 Automated Workflows

#### 🧪 Testing & Validation
- **Continuous Testing**: Runs on every push and PR
  - Python tests (pytest) on Python 3.11 & 3.12
  - Frontend build and tests (Next.js)
  - CLI build and tests (TypeScript)
  - Code linting (ruff, black, isort)
  - Security scanning (bandit, safety, Trivy)
  - Helm chart validation

#### 🐳 Docker Images
- **Automated Builds**: On every push to `main` and version tags
- **Registry**: GitHub Container Registry (ghcr.io)
- **Multi-platform**: linux/amd64, linux/arm64
- **Tags**: `latest`, `v*.*.*`, `main-sha`

**Pull the latest image:**
```bash
docker pull ghcr.io/runai-professional-services/runai-agent:latest
```

#### 🚀 Releases
- **Automated Releases**: Triggered on merge to `main`
- **Version Management**: Auto-increments patch version
- **Changelog**: Automatically updated from commits
- **GitHub Releases**: Created with release notes

**Manual release:**
```bash
# Go to: Actions → Release → Run workflow
# Specify version (e.g., 0.2.0) and type (patch/minor/major)
```

#### ⎈ Helm Chart Publishing
- **Automated Publishing**: On version tags
- **Repository**: GitHub Pages
- **URL**: https://runai-professional-services.github.io/runai-agent

**Add Helm repository:**
```bash
helm repo add runai-agent https://runai-professional-services.github.io/runai-agent
helm repo update
helm install runai-agent runai-agent/runai-agent
```

#### 🔍 PR Validation
Every pull request is automatically validated:
- ✅ Full test suite
- 🔍 Breaking change detection
- 📝 CHANGELOG.md validation
- 🎨 Code quality checks
- 📚 Documentation checks
- 📊 PR size analysis

#### 🤖 Dependency Management
- **Dependabot**: Automated dependency updates
- **Auto-merge**: Patch and minor updates auto-merged after tests pass
- **Coverage**: Python, npm, GitHub Actions, Docker

### 📈 Status & Monitoring

- **Actions Dashboard**: [View all workflows](https://github.com/runai-professional-services/runai-agent/actions)
- **Security Alerts**: [View security findings](https://github.com/runai-professional-services/runai-agent/security)
- **Container Registry**: [View published images](https://github.com/orgs/runai-professional-services/packages?repo_name=runai-agent)
- **Helm Repository**: [View published charts](https://runai-professional-services.github.io/runai-agent)

### 🛠️ For Developers

**Before submitting a PR:**
1. Update `CHANGELOG.md` under `[Unreleased]` section
2. Run tests locally: `cd runai-agent && pytest tests/`
3. Format code: `black . && isort .`
4. Lint code: `ruff check .`
5. Build Docker image: `./deploy/build-docker.sh`
6. Test Helm chart: `helm lint ./deploy/helm/runai-agent`

**Creating a new release:**
1. Merge PR to `main` (auto-creates patch release)
2. Or manually trigger release workflow for specific version

See [.github/workflows/README.md](.github/workflows/README.md) for detailed CI/CD documentation.

## 📄 License

See [LICENSE.md](LICENSE.md) for details.

## 👥 Maintainers

- Vivek Kolasani
- Brad Soper

For support, please open an issue on GitHub.

---

**Built with ❤️ using NVIDIA NeMo Agent Toolkit**
