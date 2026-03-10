# Run:AI Agent with NeMo Agent Toolkit

[![Tests](https://github.com/runai-professional-services/runai-agent/workflows/Test%20Suite/badge.svg)](https://github.com/runai-professional-services/runai-agent/actions/workflows/test.yml)
[![Docker](https://github.com/runai-professional-services/runai-agent/workflows/Build%20and%20Push%20Docker%20Image/badge.svg)](https://github.com/runai-professional-services/runai-agent/actions/workflows/docker.yml)
[![Release](https://github.com/runai-professional-services/runai-agent/workflows/Release/badge.svg)](https://github.com/runai-professional-services/runai-agent/actions/workflows/release.yml)
[![Helm](https://github.com/runai-professional-services/runai-agent/workflows/Publish%20Helm%20Chart/badge.svg)](https://github.com/runai-professional-services/runai-agent/actions/workflows/helm-publish.yml)

An intelligent conversational agent built with NVIDIA's NeMo Agent Toolkit (NAT), featuring a modern web UI and specialized tools for Run:AI cluster management. All Run:AI platform operations — job submission, project management, workload lifecycle, datasources, and more — are handled by the **`mcp-server-runai` MCP server**, which the agent communicates with over the Model Context Protocol.

## 📑 Table of Contents

- [🎯 Features](#-features)
- [📋 Prerequisites](#-prerequisites)
- [🚀 Quick Start](#-quick-start)
  - [Deploy to Kubernetes with Helm](#deploy-to-kubernetes-with-helm-)
  - [Deploy the MCP Server Standalone](#deploy-the-mcp-server-standalone-claude-cli--external-mcp-clients)
  - [Local Development](#local-development)
- [📁 Project Structure](#-project-structure)
- [🤖 What Can the Agent Do?](#-what-can-the-agent-do)
- [🚀 Submitting Jobs with the Agent](#-submitting-jobs-with-the-agent)
  - [🤖 NVIDIA NIM Inference Deployment](#example-4-nvidia-nim-inference-endpoint)
- [🔄 Job Lifecycle Management](#-job-lifecycle-management)
- [🔔 Proactive Monitoring & Auto-Troubleshooting](#-proactive-monitoring--auto-troubleshooting)
- [🔬 Advanced Failure Analysis](#-advanced-failure-analysis)
- [📊 Job Performance Analytics](#-job-performance-analytics)
- [🗄️ Datasource Operations](#️-datasource-operations)
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

- 🤖 **Intelligent Agent** - Powered by `nvidia/nemotron-3-nano-30b-a3b` via NVIDIA NIM with ReAct reasoning
- 💬 **Web UI** - Beautiful, responsive chat interface with real-time streaming
- 🔧 **Run:AI Integration via MCP Server** - All platform operations (projects, workloads, node pools, departments, users, access rules, datasources) via `mcp-server-runai`
- 🚀 **Job Submission** - Submit training, inference, and workspace workloads directly from natural language
- 🔄 **Unified Lifecycle Management** - Suspend, resume, and delete any workload type
- 🔔 **Proactive Monitoring** - Continuously monitor jobs and auto-troubleshoot failures with optional Slack alerts
- 🔬 **Advanced Failure Analysis** - Pattern recognition, cross-job correlation, and automated remediation suggestions
- 📊 **Job Performance Analytics** - Execution time trends, failure rates by project/image, recommendations, anomaly detection
- 📊 **Cluster Resource Summary** - GPU quota and utilization per project, cluster totals
- 🩺 **Deep Troubleshooting** - Pod logs, events, and AI-powered diagnosis via kubectl
- 🤖 **NIM Inference Deployment** - Deploy NVIDIA NIM inference endpoints with correct defaults — NGC API key, port 8000, and NIM env vars auto-configured
- 🚀 **NIM LLM Benchmarking** - Run GPU benchmarks on H100, H200, A100 using NIM inference
- 📚 **Documentation Search** - Ask questions about Run:AI features and get answers from official docs
- 🧠 **Code Generation** - Generate Python job submission code from real GitHub examples
- 🌙 **Dark/Light Theme** - Choose your preferred appearance

## 📋 Prerequisites

- NVIDIA API Key for NIMs. [NVIDIA Build](https://build.nvidia.com)
- Run:AI environment with a provisioned `Application` for API access. [How to Create a Run:AI Application](https://run-ai-docs.nvidia.com/self-hosted/2.22/infrastructure-setup/authentication/applications)
- Docker Registry
- Docker CLI

**macOS Users:** If running locally and you encounter OpenMP library conflicts, set this environment variable:
```bash
export KMP_DUPLICATE_LIB_OK=TRUE
# Add to your ~/.zshrc or ~/.bashrc to make it permanent
```

## 🚀 Quick Start

### Deploy to Kubernetes with Helm 🎯

Deploy the agent with all features enabled using Helm (recommended deployment method). The Helm chart includes `mcp-server-runai` as an optional subchart — enabled by default.

```bash
# 1. Add the Helm repo
helm repo add runai-agent https://runai-professional-services.github.io/runai-agent
helm repo update
```

#### Option 1 — Existing Secrets (recommended for production)

```bash
# Create namespace
kubectl create namespace runai-agent

# Create a combined secret for Run:AI credentials
# Keys clientId/clientSecret are used by the MCP server subchart;
# RUNAI_CLIENT_ID/RUNAI_CLIENT_SECRET/RUNAI_BASE_URL are used by the agent.
kubectl create secret generic runai-creds \
  --namespace runai-agent \
  --from-literal=clientId="<client-id>" \
  --from-literal=clientSecret="<client-secret>" \
  --from-literal=RUNAI_CLIENT_ID="<client-id>" \
  --from-literal=RUNAI_CLIENT_SECRET="<client-secret>" \
  --from-literal=RUNAI_BASE_URL="https://myorg.run.ai"

# Create NVIDIA API key secret
kubectl create secret generic nvidia-key \
  --namespace runai-agent \
  --from-literal=NVIDIA_API_KEY="<nvidia-api-key>"

# Install
helm upgrade -i runai-agent runai-agent/runai-agent \
  --namespace runai-agent --create-namespace \
  --set mcp-server-runai.runai.baseUrl="https://myorg.run.ai" \
  --set mcp-server-runai.runai.credentials.existingSecret="runai-creds" \
  --set runai.existingSecret="runai-creds" \
  --set nvidia.existingSecret="nvidia-key"
```

#### Option 2 — Inline credentials (quick start / development)

```bash
helm upgrade -i runai-agent runai-agent/runai-agent \
  --namespace runai-agent --create-namespace \
  --set mcp-server-runai.runai.baseUrl="https://myorg.run.ai" \
  --set mcp-server-runai.runai.credentials.clientId="<client-id>" \
  --set mcp-server-runai.runai.credentials.clientSecret="<client-secret>" \
  --set runai.baseUrl="https://myorg.run.ai" \
  --set runai.clientId="<client-id>" \
  --set runai.clientSecret="<client-secret>" \
  --set nvidia.apiKey="<nvidia-api-key>"
```

#### Option 3 — Values file

```bash
# Export default values, edit, then install
helm show values runai-agent/runai-agent > values.yaml
# Edit values.yaml with your settings
helm upgrade -i runai-agent runai-agent/runai-agent \
  --namespace runai-agent --create-namespace \
  -f values.yaml
```

#### Upgrade

```bash
helm upgrade runai-agent runai-agent/runai-agent \
  --namespace runai-agent \
  --reuse-values \
  --version <new-version>
```

#### Uninstall

```bash
helm uninstall runai-agent --namespace runai-agent
# Optional: remove PVC to wipe the failure history database
kubectl delete pvc -n runai-agent -l app.kubernetes.io/name=runai-agent
```

See [Helm Chart README](deploy/helm/runai-agent/README.md) for advanced configuration options.

---

### Deploy the MCP Server Standalone (Claude CLI / External MCP Clients)

If you want to connect an external MCP client — such as **Claude Desktop** or the **Claude CLI** — directly to your Run:AI cluster, you can deploy `mcp-server-runai` on its own without the full agent stack.

```bash
# 1. Create namespace and secret
kubectl create namespace runai-mcp

kubectl create secret generic runai-creds \
  --namespace runai-mcp \
  --from-literal=clientId="[YOUR_CLIENT_ID]" \
  --from-literal=clientSecret="[YOUR_CLIENT_SECRET]"

# 2. Install only the MCP server subchart
helm install mcp-server-runai \
  oci://ghcr.io/runai-professional-services/charts/mcp-server-runai \
  --namespace runai-mcp \
  --set runai.baseUrl="https://your-cluster.run.ai" \
  --set runai.credentials.existingSecret="runai-creds" \
  --set ingress.enabled=true \
  --set ingress.className=nginx \
  --set ingress.host="mcp-runai.example.com" \
  --set mcp.allowedHosts[0]="mcp-runai.example.com"
```

> ⚠️ **Security:** Always set `mcp.allowedHosts` to your ingress hostname when exposing the MCP server externally. Leaving it empty disables host-header validation, which makes the server vulnerable to DNS rebinding attacks.

Once deployed, add it to your Claude config (`~/.claude.json` or Claude Desktop settings):

```json
{
  "mcpServers": {
    "runai": {
      "type": "http",
      "url": "https://mcp-runai.example.com/mcp"
    }
  }
}
```

You can then ask Claude directly: *"List my Run:AI projects"*, *"Submit a training job…"*, etc.

---

### Local Development

#### Quick Start Script (Recommended)

```bash
# 1. Set required environment variables
export NVIDIA_API_KEY="[YOUR_NVIDIA_API_KEY]"
export RUNAI_CLIENT_ID="[YOUR_CLIENT_ID]"
export RUNAI_CLIENT_SECRET="[YOUR_CLIENT_SECRET]"
export RUNAI_BASE_URL="https://your-cluster.run.ai"
export MCP_SERVER_URL="http://localhost:8080"  # Point to a running mcp-server-runai instance

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
  -e MCP_SERVER_URL="[YOUR_MCP_SERVER_URL]" \
  -e RUNAI_FAILURE_DB_PATH="/tmp/runai_failure_history.db" \
  ghcr.io/runai-professional-services/runai-agent:latest
```

**Access the UI:** http://localhost:3000

**Check container logs:**
```bash
docker ps

# All output (nginx + backend + frontend)
docker logs <container_id> 2>&1

# Backend (NAT agent) logs only
docker exec <container_id> tail -n 200 /var/log/supervisor/backend.out.log
docker exec <container_id> tail -n 200 /var/log/supervisor/backend.err.log
```

#### With kubectl Troubleshooting (Optional)

To enable kubectl troubleshooting features, mount your kubeconfig:

```bash
docker run -p 3000:3000 -p 8000:8000 \
  -e NVIDIA_API_KEY="[YOUR_NVIDIA_API_KEY]" \
  -e RUNAI_CLIENT_ID="[YOUR_CLIENT_ID]" \
  -e RUNAI_CLIENT_SECRET="[YOUR_CLIENT_SECRET]" \
  -e RUNAI_BASE_URL="[YOUR_RUNAI_BASE_URL]" \
  -e MCP_SERVER_URL="[YOUR_MCP_SERVER_URL]" \
  -e RUNAI_FAILURE_DB_PATH="/tmp/runai_failure_history.db" \
  -e KUBECONFIG="/root/.kube/config" \
  -v "$HOME/.kube/config:/root/.kube/config:ro" \
  ghcr.io/runai-professional-services/runai-agent:latest
```

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

### Ingress Configuration

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
├── runai-agent/                      # NAT agent (nvidia-nat>=1.3.0)
│   ├── configs/
│   │   └── workflow.yaml             # Agent configuration, LLM, tool definitions
│   └── src/
│       └── runai_agent/
│           ├── functions/            # Agent-side tool modules
│           │   ├── environment_info.py    # Cluster overview & project listing
│           │   ├── failure_analyzer.py    # Pattern recognition & remediation
│           │   ├── job_analytics.py       # Execution trends & anomaly detection
│           │   ├── job_generator.py       # Python code generation from GitHub
│           │   ├── kubectl_troubleshoot.py # Deep kubectl diagnostics
│           │   ├── list_resources.py      # Wrapper for all MCP list operations
│           │   ├── nim_benchmark.py       # NIM LLM GPU benchmarking
│           │   ├── nim_inference.py       # NIM inference deployment with correct defaults
│           │   ├── proactive_monitor.py   # Proactive monitoring & auto-troubleshoot
│           │   └── runai_docs_helper.py   # Direct links to Run:AI documentation
│           ├── middleware/            # Request middleware
│           ├── security/              # Security utilities
│           ├── utils/                 # Shared utilities
│           ├── query_classifier.py    # Query routing and classification
│           └── register.py            # Function registration with NAT
├── deploy/
│   ├── Dockerfile                    # Combined container (Nginx + NAT + Next.js)
│   ├── nginx.conf                    # Nginx reverse proxy config
│   ├── build-docker.sh              # Docker build script
│   ├── start-local.sh               # Quick start script for local development
│   └── helm/
│       └── runai-agent/             # Production Helm chart
│           └── charts/
│               └── mcp-server-runai/ # MCP server subchart dependency
├── docs/                             # Documentation
│   ├── QUICKSTART.md
│   ├── DEPLOYMENT.md
│   ├── SIDECAR_DEPLOYMENT.md
│   ├── PROACTIVE_MONITORING.md
│   ├── FAILURE_ANALYSIS.md
│   ├── FAILURE_ANALYSIS_QUICKSTART.md
│   └── BATCH_SUBMISSION.md
├── runai-cli/                        # TypeScript CLI for remote agent connection
│   ├── docs/
│   │   ├── REMOTE_CONNECTION.md
│   │   ├── NATURAL_LANGUAGE_GUIDE.md
│   │   └── QUICKSTART_EXAMPLES.md
│   └── README.md
└── CHANGELOG.md
```

**Key Dependencies:**
- **NVIDIA NeMo Agent Toolkit 1.3.1** (`nvidia-nat>=1.3.0`) - Agent framework, ReAct agent, tool management
- **nvidia-nat-mcp>=1.3.0** - MCP client support for NAT (`mcp_client` function group type)
- **nat_simple_web_query plugin** - Installed from NAT GitHub for `webpage_query` tool (docs search)
- **mcp-server-runai** - Separate service (deployed as Helm subchart) exposing all Run:AI platform operations as MCP tools

---

## 🤖 What Can the Agent Do?

### Run:AI Operations (via MCP Server)
- **List & manage projects** — view GPU quotas, create/delete projects
- **Submit training jobs** — single-node, distributed (PyTorch, TensorFlow, MPI)
- **Submit interactive workspaces** — Jupyter, VSCode, custom environments
- **Submit inference workloads** — model serving with autoscaling
- **Deploy NIM inference endpoints** — NVIDIA NIM models with NGC API key, env vars, and port auto-configured
- **Workload lifecycle** — suspend, resume, delete any workload type
- **Cluster resource summary** — GPU quota and utilization per project and node pool
- **Department management** — create/list/delete departments with GPU resource allocation
- **User & access rule management** — list users, manage roles and access rules
- **Datasource listing** — view PVCs, S3, NFS, and Git data source assets
- **Node pool information** — list node pools, view metrics

### Agent Tools
- **Deep troubleshooting** — kubectl logs, events, and AI-powered diagnosis
- **Proactive monitoring** — continuously detect failures and auto-troubleshoot
- **Advanced failure analysis** — pattern recognition, remediation suggestions, knowledge graph
- **Job performance analytics** — execution trends, failure rates, anomaly detection
- **NIM inference deployment** — deploy NIM endpoints with correct defaults (port 8000, env vars, NGC API key from K8s Secret)
- **NIM benchmarking** — run GPU inference benchmarks (H100, H200, A100)
- **Documentation search** — answers from official Run:AI docs
- **Code generation** — Python job submission code using real GitHub examples

### Example Queries

**General Operations:**
```
"Show me the current status of the environment"
"Show me cluster resource summary"
"List all departments"
```

**Documentation Search:**
```
"What is a nodePool in Run:AI?"
"How do I configure GPU fractions?"
"Explain Run:AI environments"
"How does the Run:AI scheduler work?"
```

**Job Submission:**
```
"Submit a training job with 2 GPUs to project-01"
"Submit a distributed PyTorch job with 2 workers and 1 GPU per worker"
"Create a Jupyter workspace with 1 GPU in project-01"
```

**Workspace Submission:**
```
"Create a Jupyter workspace with 1 GPU in project-01"
"Submit a VSCode workspace named 'my-workspace' with 0.5 GPU"
```

**NIM Inference Deployment:**
```
"Deploy a NIM inference called llama-8b in project-01 using image nvcr.io/nim/meta/llama-3.1-8b-instruct:latest with NGC API key from secret ngc-api-key-secret"
"Start a NIM embedding model nim-embed in project-01 using image nvcr.io/nim/nvidia/llama-nemotron-embed-300m-v2 with NGC API key from secret ngc-creds"
```

**Code Generation:**
```
"Generate Python code for a distributed training job with 4 GPUs"
"What is an example of submitting a training job with the Python runapy SDK?"
```

**Status & Troubleshooting:**
```
"Troubleshoot job broken-job in project-01"
"Show me logs and events for failed-job"
"What's wrong with my job that keeps failing?"
```

**Proactive Monitoring:**
```
"Start monitoring all jobs in the cluster"
"Monitor project-01 for failures"
"What's the monitoring status?"
```

**Analytics:**
```
"Show me job performance analytics"
"Show me failure rate by project for the last 7 days"
"Any jobs running longer than usual?"
```

---

## 🚀 Submitting Jobs with the Agent

The agent submits workloads directly to your Run:AI cluster via the MCP server's `submit_training`, `submit_inference`, and `submit_workspace` tools. Jobs are submitted immediately — no confirmation step required.

### 📝 Job Submission Examples

#### Example 1: Simple Training Job

```
Submit a training job called my-training-job to project-01 with image pytorch/pytorch:latest and 2 GPUs
```

**Agent Response:**
```
✅ Training job submitted successfully!

Job ID: f7326e42-f587-4a0d-b70b-7a89a19b19dd
Name: my-training-job
Project: project-01
Status: Creating
```

#### Example 2: Distributed Training Job (PyTorch)

```
Submit a distributed PyTorch job: name pytorch-dist, project project-01,
image kubeflow/pytorch-dist-mnist:latest, 2 workers, 1 GPU per worker
```

**Agent Response:**
```
✅ Distributed job submitted successfully!

Job ID: 4650f48a-6705-435c-8cfe-046bdea40917
Name: pytorch-dist
Project: project-01
Framework: PyTorch
Workers: 2 × 1 GPU
Status: Creating
```

#### Example 3: Interactive Workspace (Jupyter)

```
Submit a Jupyter workspace named my-jupyter in project-01 with image jupyter/scipy-notebook and 1 GPU
```

**Agent Response:**
```
✅ Workspace submitted successfully!

Workspace ID: 462b67de-353f-4f8e-b3e2-73aeab837c01
Name: my-jupyter
Project: project-01
Image: jupyter/scipy-notebook
GPU: 1
Status: Creating
```

#### Example 4: NVIDIA NIM Inference Endpoint

Deploy a NIM model with a single natural language prompt. The agent automatically configures port 8000, NIM environment variables, and wires your NGC API key from a Kubernetes Secret — no manual spec required.

```
Deploy a NIM inference called llama-8b in project-01 using image
nvcr.io/nim/meta/llama-3.1-8b-instruct:latest with NGC API key from secret ngc-api-key-secret
```

**Agent Response:**
```
✅ NIM Inference Submitted

| Parameter     | Value                                              |
|---------------|----------------------------------------------------|
| Workload      | llama-8b                                           |
| Project       | project-01                                         |
| Image         | nvcr.io/nim/meta/llama-3.1-8b-instruct:latest      |
| Serving Port  | 8000                                               |
| GPUs          | 1 × 1.0                                            |
| Replicas      | 1–1                                                |
| Workload ID   | e1eca348-b33b-4c9a-925b-100b42e7cab1               |

🔑 Credentials: NGC API key sourced from secret `ngc-api-key-secret` (key: `NGC_API_KEY`)

🌐 Internal URL: http://llama-8b.runai-project-01.svc.cluster.local

📋 NIM Environment Variables Set:
- NIM_SERVER_PORT=8000
- NIM_JSONL_LOGGING=1
- NIM_LOG_LEVEL=INFO
- OUTLINES_CACHE_DIR=/tmp/outlines
```

**Before submitting**, create the NGC API key secret in the project namespace:

```bash
kubectl create secret generic ngc-api-key-secret \
  --namespace runai-project-01 \
  --from-literal=NGC_API_KEY="<your-ngc-api-key>"
```

> **Note:** The secret must exist in the Run:AI project namespace (`runai-<project-name>`) before submitting the NIM workload.

---

## 🔄 Job Lifecycle Management

The agent provides full workload lifecycle management via MCP tools.

### 📊 Check Job Status

```
What is the status of my-training-job in project-01?
```

### ⏸️ Suspend a Job

```
Suspend the job "my-training-job" in project-01
```

**Agent Response:**
```
✅ Job 'my-training-job' in project-01 has been successfully suspended.

To resume: "Resume job my-training-job in project-01"
```

### ▶️ Resume a Job

```
Resume the job "my-training-job" in project-01
```

### 🗑️ Delete a Job

```
Delete the job "old-training-job" from project-01
```

**Agent Response:**
```
✅ Job 'old-training-job' deleted successfully.
```

---

## 🔔 Proactive Monitoring & Auto-Troubleshooting

The agent can **continuously monitor** your Run:AI workloads and automatically troubleshoot failures, with optional Slack notifications.

### ✨ Key Features

- 🔄 **Continuous Polling** - Check job status at configurable intervals (default: 60s)
- 🔍 **Failure Detection** - Detects Failed, Error, ImagePullBackOff, OOMKilled, and Unknown states
- 🔧 **Auto-Troubleshooting** - Runs kubectl diagnostics when failures are detected
- 🔔 **Smart Alerts** - Console and Slack notifications with troubleshooting reports
- 🚫 **Anti-Spam** - Configurable alert limits per job
- 🎯 **Project Filtering** - Monitor all projects or specific ones

### 📊 Usage Examples

```
Start monitoring all jobs in the cluster
Monitor jobs in project ml-team
Monitor all jobs for 30 minutes
What is the monitoring status?
```

### 🔔 Alert Example

```
🔴 Job Failure Alert: my-training-job

Project: ml-team
Status: OOMKilled
Time: 2026-01-15 13:46:05

Auto-Troubleshoot Report:
Pod Status: OOMKilled (0/1 Ready)
Logs: [Memory allocation errors...]
Events: [OOM kills and memory limit exceeded...]
```

### 🔧 Slack Integration (Optional)

Configure a webhook in `runai-agent/configs/workflow.yaml`:

```yaml
runai_proactive_monitor:
  slack_webhook_url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
  poll_interval_seconds: 60
  enable_auto_troubleshoot: true
  max_alerts_per_job: 1
```

### 🛡️ Configuration Options

```yaml
runai_proactive_monitor:
  monitored_projects: ["*"]        # * = all projects
  poll_interval_seconds: 60
  enable_auto_troubleshoot: true
  monitor_only_failed: false       # true = only failures, false = all jobs
  max_alerts_per_job: 1
  # slack_webhook_url: "https://hooks.slack.com/services/..."
```

📚 **Full Documentation:** [docs/PROACTIVE_MONITORING.md](docs/PROACTIVE_MONITORING.md)

---

## 🔬 Advanced Failure Analysis

Intelligent failure analysis with pattern recognition, cross-job correlation, and automated remediation suggestions.

### 🧪 Example Prompts

```
Show me failure statistics
What failure patterns have been detected?
Analyze recent job failures
What are the top failure types and how can I fix them?
Show me problematic nodes from the last 7 days
Give me remediation suggestions for OOMKilled errors
```

### ✨ Key Capabilities

- **Pattern Recognition** — "This is the 5th OOMKilled in project-01 today"
- **Cross-Job Correlation** — "Node gpu-node-03 has 90% failure rate across 15 jobs"
- **Automated Remediation** — Rule-based solutions + historical fixes with success rates
- **Knowledge Graph** — Persistent database of failure → solution mappings

### 📊 Example Output

```
📊 Advanced Failure Analysis Report

Summary:
- Total Failures: 23
- Projects Affected: 4

Detected Patterns:
🔴 Project ml-team: 8 failures (OOMKilled: 5, ImagePullBackOff: 3)

Problematic Nodes:
🔴 gpu-node-03: 12 failures across 8 jobs (75% failure rate)

Recommendations:
⚠️ Node 'gpu-node-03' has 75% failure rate. Consider cordoning for maintenance.
🐳 Image 'pytorch:2.0' associated with 5 failures. Verify compatibility.
```

### 🛠️ Configuration

```yaml
runai_failure_analyzer:
  db_path: "${RUNAI_FAILURE_DB_PATH:-/tmp/runai_failure_history.db}"
  lookback_days: 7
  pattern_threshold: 3       # Min occurrences to identify a pattern
  enable_auto_remediation: false
```

📚 **Documentation:** [docs/FAILURE_ANALYSIS.md](docs/FAILURE_ANALYSIS.md)

---

## 📊 Job Performance Analytics

Historical performance insights from the same database used for failure analysis. Populated automatically when proactive monitoring is running.

**Example prompts:**
```
Show me job performance analytics
How long do my training jobs usually take?
Show me failure rate by project for the last 7 days
Any jobs running longer than usual?
Job performance analytics for project ml-team
```

**What you get:**
- Execution time trends (average by project/image)
- Failure rates by project and image
- Recommendations (e.g. "Training jobs in project-01 typically take ~2h")
- Anomaly detection for jobs running 3× longer than their usual duration

---

## 🗄️ Datasource Operations

The agent can list all datasource assets via the MCP server.

**List operations (available now):**
```
List all PVC datasources
List all NFS assets
Show me S3 datasources
List Git datasources
```

**Create/delete operations** are not yet available in the MCP server and will be added in a future release.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                       runai-agent Pod                            │
│                                                                  │
│  ┌──────────┐                                                    │
│  │  Nginx   │  ← Entry point (port 3000)                         │
│  │  :3000   │    Static reverse proxy                            │
│  └────┬─────┘                                                    │
│       │                                                          │
│       ├──→ /generate, /docs ──→ ┌──────────────────────────┐   │
│       │                          │      NAT Agent            │   │
│       │                          │       :8000               │   │
│       └──→ /* ──→ ┌──────────┐  │  (ReAct + MCP client)    │   │
│                    │ Next.js  │  └────────────┬─────────────┘   │
│                    │  :3001   │               │ MCP              │
│                    └──────────┘               │ streamable-http  │
└───────────────────────────────────────────────┼──────────────────┘
                                                │
                ┌───────────────────────────────▼──────────────────┐
                │              mcp-server-runai Pod                  │
                │                    :8080                           │
                │                                                    │
                │  MCP Tools: list/create/delete projects,           │
                │  submit/suspend/resume/delete workloads,           │
                │  departments, node pools, users, access rules,     │
                │  PVC/S3/NFS/Git asset listing                      │
                └───────────────────────────────┬──────────────────┘
                                                │
                                        Run:AI Cluster API
```

**Components:**
- **Nginx** (port 3000): Static reverse proxy
  - Routes `/generate`, `/docs` → NAT Agent (8000)
  - Routes `/*` → Next.js frontend (3001)
- **Next.js UI** (port 3001): Modern web interface with SSE streaming, pre-built at image build time
- **NAT Agent** (port 8000): FastAPI backend — ReAct agent with MCP client connecting to `mcp-server-runai`
- **mcp-server-runai** (port 8080): Separate pod — exposes all Run:AI platform operations as MCP tools
- **Supervisord**: Process manager inside the agent container (Nginx + NAT + Next.js)

**Agent init flow:** An initContainer in the agent pod polls `mcp-server-runai/ready` before the agent starts, ensuring the MCP server is authenticated and ready before NAT registers tools.

---

## 🔧 Configuration

### Environment Variables

**Required:**
- `NVIDIA_API_KEY` — NVIDIA API key ([get here](https://build.nvidia.com))
- `MCP_SERVER_URL` — URL of the `mcp-server-runai` service (auto-derived from subchart when using Helm)

**Run:AI Integration (Required for full functionality):**
- `RUNAI_CLIENT_ID` — Run:AI client ID for authentication
- `RUNAI_CLIENT_SECRET` — Run:AI client secret for authentication
- `RUNAI_BASE_URL` — Run:AI cluster URL (e.g., `https://your-cluster.run.ai`)

**Optional:**
- `GITHUB_TOKEN` — GitHub token (avoids API rate limits for code generation examples)
- `RUNAI_FAILURE_DB_PATH` — Path for failure analysis database (default: `/tmp` locally, `/data` in K8s)

### Agent Configuration

Edit `runai-agent/configs/workflow.yaml` to change the model, add tools, or customize behavior:

```yaml
llms:
  demo_llm:
    _type: nim
    model_name: nvidia/nemotron-3-nano-30b-a3b
    temperature: 0.1
    max_tokens: 4096

function_groups:
  mcp_runai:
    _type: mcp_client
    server:
      transport: streamable-http
      url: ${MCP_SERVER_URL}/mcp

workflow:
  _type: react_agent
  tool_names:
    - runailabs_environment_info    # Cluster overview
    - runai_kubectl_troubleshoot    # Deep kubectl diagnostics
    - runai_proactive_monitor       # Continuous monitoring
    - runai_failure_analyzer        # Pattern analysis & remediation
    - runai_job_analytics           # Performance analytics
    - runailabs_job_generator       # Python code generation
    - runai_nim_benchmark           # NIM GPU benchmarking
    - runai_docs_helper             # Direct doc links (fast)
    - runai_docs_search             # Semantic doc search
    - runai_api_docs                # API documentation search
    - mcp_runai                     # All Run:AI platform operations
  llm_name: demo_llm
  max_iterations: 15
  max_tool_calls: 15
  parse_agent_response_max_retries: 3
```

### Monitoring Sidecar (Kubernetes)

Enable the monitoring sidecar in Helm values for continuous background monitoring:

```yaml
monitoring:
  enabled: true
  pollInterval: 60
  slackWebhookUrl: ""   # Optional Slack webhook
```

---

## 📚 Documentation

### Deployment Guides
- **[Helm Chart README](deploy/helm/runai-agent/README.md)** - ⭐ Recommended: One-command deployment with all features
- **[QUICKSTART.md](docs/QUICKSTART.md)** - Get started in 5 minutes
- **[DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Complete deployment guide
- **[SIDECAR_DEPLOYMENT.md](docs/SIDECAR_DEPLOYMENT.md)** - Production deployment with monitoring sidecar

### Feature Documentation
- **[PROACTIVE_MONITORING.md](docs/PROACTIVE_MONITORING.md)** - Proactive monitoring guide
- **[FAILURE_ANALYSIS.md](docs/FAILURE_ANALYSIS.md)** - Advanced failure analysis & pattern recognition
- **[FAILURE_ANALYSIS_QUICKSTART.md](docs/FAILURE_ANALYSIS_QUICKSTART.md)** - Quick start guide for failure analysis

### Reference
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and updates

---

## 🧪 Development

### Initial Setup

```bash
# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install the agent
cd runai-agent
pip install -e .

# 3. Install webpage_query plugin (required for docs search)
pip install "git+https://github.com/NVIDIA/NeMo-Agent-Toolkit.git@v1.3.1#subdirectory=examples/getting_started/simple_web_query"

# 4. Set environment variables
export NVIDIA_API_KEY="[YOUR_NVIDIA_API_KEY]"
export RUNAI_CLIENT_ID="[YOUR_CLIENT_ID]"
export RUNAI_CLIENT_SECRET="[YOUR_CLIENT_SECRET]"
export RUNAI_BASE_URL="https://your-cluster.example.com"
export MCP_SERVER_URL="http://localhost:8080"  # Running mcp-server-runai instance
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
./deploy/build-docker.sh
# Or manually:
docker build -t runai-agent:latest -f deploy/Dockerfile .
```

---

## 🐛 Troubleshooting

See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for a comprehensive troubleshooting guide.

**Quick Checks:**

```bash
# Check environment variables (without displaying values)
printenv | grep -E "NVIDIA_API_KEY|RUNAI|MCP_SERVER"

# Test backend
curl http://localhost:8000/docs

# View logs
docker logs <container_id>

# List NAT components
nat info components --types function
```

### Kubernetes: Check MCP Server Readiness

```bash
kubectl get pods -n runai-agent
kubectl logs -n runai-agent deployment/runai-agent-mcp-server-runai
```

If the MCP server is restarting repeatedly, check that `RUNAI_CLIENT_ID`, `RUNAI_CLIENT_SECRET`, and `RUNAI_BASE_URL` are correctly set in the secret referenced by the deployment.

### Enable Agent Reasoning Steps (Advanced)

By default the agent provides clean output. To see internal reasoning and tool calls:

**Docker:**
```bash
docker run -p 3000:3000 -p 8000:8000 \
  -e NVIDIA_API_KEY="[YOUR_NVIDIA_API_KEY]" \
  -e NEXT_PUBLIC_ENABLE_INTERMEDIATE_STEPS=true \
  ghcr.io/runai-professional-services/runai-agent:latest
```

**Helm:**
```bash
helm install runai-agent ./deploy/helm/runai-agent \
  --namespace runai-agent \
  --set frontend.env.NEXT_PUBLIC_ENABLE_INTERMEDIATE_STEPS="true"
```

---

## 🤝 Contributing

This project uses:
- **Backend**: Python 3.11+, FastAPI, NeMo Agent Toolkit, LangChain
- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS
- **Infrastructure**: Docker, Kubernetes, Run:AI, Helm

See our [Contributing Guide](.github/PULL_REQUEST_TEMPLATE.md) for development guidelines.

---

## 📊 CI/CD Pipeline

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
- **Tags**: `latest`, `0.1.39`, `main-sha`

```bash
# Pull latest image
docker pull ghcr.io/runai-professional-services/runai-agent:latest

# Pull a specific version (recommended for production)
docker pull ghcr.io/runai-professional-services/runai-agent:0.1.39
```

**Version Convention:**
- Git tags: `v0.1.39` (with `v` prefix)
- Docker image tags: `0.1.39`, `latest` (no `v` prefix)
- Helm chart versions: `0.1.39` (no `v` prefix)

#### 🚀 Releases
- **Automated Releases**: Triggered on merge to `main`
- **Version Management**: Auto-increments patch version
- **Changelog**: Automatically updated from commits

```bash
# Manual release: Actions → Release → Run workflow
# Specify version (e.g., 0.2.0) and type (patch/minor/major)
```

#### ⎈ Helm Chart Publishing
- **Automated Publishing**: On version tags
- **Repository**: GitHub Pages

```bash
helm repo add runai-agent https://runai-professional-services.github.io/runai-agent
helm repo update
helm install runai-agent runai-agent/runai-agent
```

#### 🔍 PR Validation
- ✅ Full test suite
- 🔍 Breaking change detection
- 📝 CHANGELOG.md validation
- 🎨 Code quality checks
- 📊 PR size analysis

#### 🤖 Dependency Management
- **Dependabot**: Automated dependency updates (Python, npm, GitHub Actions, Docker)

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

See [.github/workflows/README.md](.github/workflows/README.md) for detailed CI/CD documentation.

---

## 📄 License

See [LICENSE.md](LICENSE.md) for details.

## 👥 Maintainers

- Vivek Kolasani
- Brad Soper

For support, please open an issue on GitHub.

---

**Built with ❤️ using NVIDIA NeMo Agent Toolkit**
