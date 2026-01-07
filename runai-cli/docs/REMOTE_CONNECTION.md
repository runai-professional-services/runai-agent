# RunAI CLI - Remote Agent Connection Guide

## Overview

The `runai-cli` is a TypeScript command-line interface that can connect to remote agent deployments (Helm, Docker, etc.) for team collaboration.

## Installation

```bash
cd runai-cli
npm install
npm run build
npm link
```

## Quick Start

### Connect to Remote Agent

```bash
# Connect to Helm/Kubernetes deployment
runai-cli connect https://your-agent-url.com

# Or with IP address
runai-cli connect http://192.168.1.100:3000

# Verify connection
runai-cli server status
```

### Use the CLI

```bash
# Ask questions
runai-cli ask "Show me all projects"

# Submit jobs
runai-cli submit "Create a training job with 2 GPUs"

# Interactive mode
runai-cli chat

# Job operations
runai-cli job list
runai-cli job status my-job
```

## Connecting to Helm Deployment

If you deployed the agent with Helm:

```bash
# Your ingress exposes port 3000
runai-cli connect https://runai-agent.your-domain.com

# Check status
runai-cli server status
# Output: ✓ Agent server is running
#         ℹ Mode: Remote Agent
```

**Note:** The ingress on port 3000 is correct. Nginx internally routes API requests (`/generate`, `/docs`) to the backend on port 8000.

## Switching Between Agents

```bash
# Connect to production
runai-cli connect https://prod-agent.company.com

# Switch to staging
runai-cli connect https://staging-agent.company.com

# Switch to local mode
runai-cli connect local
```

## Configuration

View current settings:

```bash
runai-cli config show
```

Set timeout for slow networks:

```bash
runai-cli config set timeout 120000  # 2 minutes
```

## Available Commands

### Remote Mode (Connected to Remote Agent)

| Command | Available | Notes |
|---------|-----------|-------|
| `connect` | ✅ | Connect to remote/local agent |
| `ask` | ✅ | Send queries |
| `submit` | ✅ | Natural language job submission |
| `chat` | ✅ | Interactive REPL |
| `job *` | ✅ | All job operations |
| `env *` | ✅ | All environment operations |
| `server status` | ✅ | Check agent health |
| `server start` | ❌ | Cannot start remote servers |
| `server stop` | ❌ | Cannot stop remote servers |

## Troubleshooting

### Cannot Connect

```bash
# Test with curl
curl https://your-agent-url.com/docs

# If curl works, try CLI without verification
runai-cli connect https://your-agent-url.com --no-verify
```

### Check Deployment

```bash
# Kubernetes
kubectl get pods -n runai-agent
kubectl logs -n runai-agent deployment/runai-agent

# Check ingress
kubectl get ingress -n runai-agent
```

### Common Issues

**404 on /generate:**
- Check Nginx config in container: `kubectl exec -n runai-agent <pod> -- cat /etc/nginx/nginx.conf`
- Should route `/generate` to port 8000

**Connection refused:**
- Verify agent is running: `kubectl get pods -n runai-agent`
- Check service: `kubectl get svc -n runai-agent`
- Verify ingress: `kubectl get ingress -n runai-agent`

## Port-Forward (Development)

For local testing with Kubernetes:

```bash
# Terminal 1: Port-forward
kubectl port-forward -n runai-agent service/runai-agent 8000:3000

# Terminal 2: Connect CLI
runai-cli connect http://localhost:8000
```

## Best Practices

1. **Use HTTPS in production** - Configure SSL in your ingress
2. **Document team agent URL** - Share connection instructions
3. **Set appropriate timeouts** - Increase for complex queries
4. **Monitor the agent** - Use `runai-cli server status` in CI/CD

## Architecture

```
CLI Request
    ↓
https://your-agent-url.com/generate
    ↓
Ingress (SSL termination)
    ↓
Service (port 3000)
    ↓
Nginx (port 3000)
    ├─→ /generate → Backend (port 8000)
    └─→ /* → Frontend (port 3001)
```

The CLI only needs access to port 3000. Nginx handles internal routing.

## Complete CLI Documentation

For full CLI documentation including natural language submission and all commands:
- See [README.md](../README.md)
- See [NATURAL_LANGUAGE_GUIDE.md](NATURAL_LANGUAGE_GUIDE.md)

