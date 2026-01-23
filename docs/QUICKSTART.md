# 🚀 Quick Start Guide

Get your NAT Agent running locally or deployed to Kubernetes in minutes!

## Prerequisites

- Docker installed
- NVIDIA API key ([get one from build.nvidia.com](https://build.nvidia.com))
- (Optional) Kubernetes cluster access
- (Optional) Run:ai client credentials

## Local Development - Backend Only

The fastest way to test the agent locally:

### 1. Set Environment Variables

```bash
export NVIDIA_API_KEY="[YOUR_NVIDIA_API_KEY]"
export RUNAI_CLIENT_ID="[YOUR_CLIENT_ID]"       # Optional
export RUNAI_CLIENT_SECRET="[YOUR_CLIENT_SECRET]"      # Optional
export RUNAI_BASE_URL="https://your-cluster.com"    # Optional
```

### 2. Run with Docker

```bash
# Run backend in Docker
docker run -p 8000:8000 \
  -e NVIDIA_API_KEY="$NVIDIA_API_KEY" \
  -e RUNAI_CLIENT_ID="$RUNAI_CLIENT_ID" \
  -e RUNAI_CLIENT_SECRET="$RUNAI_CLIENT_SECRET" \
  ghcr.io/runai-professional-services/runai-agent:latest
```

**Backend API:** http://localhost:8000/docs

### 3. Or Run from Source

```bash
cd nemo-agent-toolkit
./START_AGENT.sh
```

**Backend API:** http://localhost:8000/docs

## Local Development - Full UI

Build and run the combined container locally:

```bash
# Build the combined image
docker build -t runai-agent-ui:latest \
  --build-arg NEXT_PUBLIC_BASE_PATH= \
  -f Dockerfile.combined .

# Run the container
docker run -p 3000:3000 -p 8000:8000 \
  -e NVIDIA_API_KEY="$NVIDIA_API_KEY" \
  -e RUNAI_CLIENT_ID="$RUNAI_CLIENT_ID" \
  -e RUNAI_CLIENT_SECRET="$RUNAI_CLIENT_SECRET" \
  runai-agent-ui:latest
```

**Access:**
- **UI:** http://localhost:3000
- **Backend API:** http://localhost:8000/docs

## First Steps

### Using the API

```bash
# Test the backend directly
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"input_message": "Show me the environment"}'
```

### Using the Web UI (if running combined container)

1. Open http://localhost:3000 in your browser
2. Try these example queries:
   - "Show me the current RunAI environment"
   - "Generate a Jupyter workspace job"
   - "What can you help me with?"
3. Enable "Intermediate Steps" in settings (⚙️) to see agent reasoning

## Configuration

### Agent Configuration

Edit `runai-agent/configs/workflow.yaml` to customize:
- LLM models and parameters
- Available tools and functions
- Logging and debugging

## Deploy to Kubernetes

### Quick Deploy

```bash
# 1. Build and tag image for your registry
docker build -t your-registry/nat-agent-ui:latest \
  --build-arg NEXT_PUBLIC_BASE_PATH=/project-01/nat-ui \
  -f Dockerfile.combined \
  --platform linux/amd64 .

# 2. Push to registry
docker push your-registry/nat-agent-ui:latest

# 3. Create secrets
kubectl create secret generic nvidia-api-key --from-literal=key="[YOUR_NVIDIA_API_KEY]"

# 4. Deploy
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nat-agent-ui
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nat-agent-ui
  template:
    metadata:
      labels:
        app: nat-agent-ui
    spec:
      containers:
      - name: nat-ui
        image: your-registry/nat-agent-ui:latest
        ports:
        - containerPort: 3000
        env:
        - name: NVIDIA_API_KEY
          valueFrom:
            secretKeyRef:
              name: nvidia-api-key
              key: key
---
apiVersion: v1
kind: Service
metadata:
  name: nat-agent-ui
spec:
  selector:
    app: nat-agent-ui
  ports:
  - port: 3000
    targetPort: 3000
  type: LoadBalancer
EOF
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment instructions.

## Troubleshooting

### Port Already in Use

```bash
# Kill processes on ports 3000/8000
lsof -ti:3000 | xargs kill -9
lsof -ti:8000 | xargs kill -9
```

### Container Won't Start

```bash
# Check if NVIDIA_API_KEY is set (without displaying value)
printenv | grep NVIDIA_API_KEY

# View container logs
docker logs <container_id>
```

### Backend Returns 404

```bash
# Check if running with path prefix
# For local development, no path prefix is needed
# For Kubernetes/Run:ai, paths are auto-configured

# Test backend directly
curl http://localhost:8000/generate -X POST \
  -H "Content-Type: application/json" \
  -d '{"input_message": "test"}'
```

### Build Fails

```bash
# Clean Docker cache
docker builder prune -a

# Rebuild from scratch
docker build --no-cache -t runai-agent-ui:latest -f Dockerfile.combined .
```

## What's Included

### Architecture

```
┌─────────────────────────────────────────────┐
│         Combined Docker Container           │
│                                             │
│  ┌──────────────┐         ┌──────────────┐ │
│  │   Nginx      │    →    │   Next.js    │ │
│  │   :3000      │         │    :3001     │ │
│  └──────────────┘         └──────────────┘ │
│         │                        ↓          │
│         └────────────→  ┌──────────────┐   │
│                         │  NAT Agent   │   │
│                         │   :8000      │   │
│                         └──────────────┘   │
└─────────────────────────────────────────────┘
```

### Features

- 🎨 **Modern Web UI** - Beautiful, responsive chat interface
- 🔄 **Real-time Streaming** - See responses as they're generated
- 🧠 **Agent Reasoning** - View intermediate steps and tool calls
- 🌙 **Dark/Light Theme** - Choose your preferred appearance
- 🔧 **Configurable** - Customize agent behavior via YAML
- 🚀 **Auto-Configuration** - Works in Run:ai without manual setup

## Example Queries

Try these to explore your agent's capabilities:

**RunAI Environment:**
- "Show me the current RunAI environment"
- "What RunAI cluster am I connected to?"

**Job Creation:**
- "Generate a Jupyter workspace job"
- "Create a distributed training job with 2 GPUs"
- "Submit a job using 4 workers"

**Documentation Search:**
- "How do I submit a job using the Runapy SDK?"
- "Search the Run:ai docs for GPU allocation best practices"

**General Help:**
- "What can you help me with?"
- "List all available tools"

## Next Steps

- **Customize**: Edit `runai-agent/configs/workflow.yaml`
- **Deploy**: See [DEPLOYMENT.md](DEPLOYMENT.md) for Kubernetes/Run:ai deployment
- **Develop**: Add custom functions and tools to your agent

## Need Help?

- Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment issues
- Review container logs: `docker logs <container_id>`
- Ensure your NVIDIA_API_KEY is valid and active

---

**Your NAT Agent is ready to use! 🎉**
