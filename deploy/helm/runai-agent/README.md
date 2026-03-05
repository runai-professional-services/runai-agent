# Run:AI Agent Helm Chart

Helm chart for deploying the intelligent Run:AI conversational agent. Includes
`mcp-server-runai` as a bundled subchart so a single `helm install` deploys the
full working stack.

## Architecture

```
┌─────────────────────────────────────┐
│           runai-agent               │
│  ┌───────────────┐                  │
│  │  nat-agent    │──── MCP HTTP ───►│  mcp-server-runai (subchart)
│  │  (this chart) │                  │  └─ connects to Run:AI API
│  └───────────────┘                  │
└─────────────────────────────────────┘
```

The agent uses `mcp-server-runai` for all Run:AI platform operations (workloads,
projects, assets, etc.). The subchart is enabled by default and auto-configured —
no extra URL wiring needed.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.8+ (OCI support required for subchart pull)
- Run:AI cluster v2.x with API access
- Run:AI OAuth2 credentials (client ID + secret)
- NVIDIA API key (for the LLM)

## Quick Start

### Install with inline credentials (development)

```bash
helm upgrade -i runai-agent \
  oci://ghcr.io/runai-professional-services/charts/runai-agent \
  --namespace runai-agent --create-namespace \
  --set mcp-server-runai.runai.baseUrl="https://myorg.run.ai" \
  --set mcp-server-runai.runai.credentials.clientId="<client-id>" \
  --set mcp-server-runai.runai.credentials.clientSecret="<client-secret>" \
  --set runai.baseUrl="https://myorg.run.ai" \
  --set runai.clientId="<client-id>" \
  --set runai.clientSecret="<client-secret>" \
  --set nvidia.apiKey="<nvidia-api-key>"
```

### Install with existing Secrets (recommended for production)

```bash
# 1. Create namespace
kubectl create namespace runai-agent

# 2. Create Run:AI credentials secret
#    Used by both the MCP server (subchart) and the agent's monitoring functions.
#    Secret keys must be: clientId, clientSecret  (for the subchart)
#                         RUNAI_CLIENT_ID, RUNAI_CLIENT_SECRET, RUNAI_BASE_URL  (for the agent)
kubectl create secret generic runai-creds \
  --namespace runai-agent \
  --from-literal=clientId="<client-id>" \
  --from-literal=clientSecret="<client-secret>" \
  --from-literal=RUNAI_CLIENT_ID="<client-id>" \
  --from-literal=RUNAI_CLIENT_SECRET="<client-secret>" \
  --from-literal=RUNAI_BASE_URL="https://myorg.run.ai"

# 3. Create NVIDIA API key secret
kubectl create secret generic nvidia-key \
  --namespace runai-agent \
  --from-literal=NVIDIA_API_KEY="<nvidia-api-key>"

# 4. Install
helm upgrade -i runai-agent \
  oci://ghcr.io/runai-professional-services/charts/runai-agent \
  --namespace runai-agent \
  --set mcp-server-runai.runai.baseUrl="https://myorg.run.ai" \
  --set mcp-server-runai.runai.credentials.existingSecret="runai-creds" \
  --set runai.existingSecret="runai-creds" \
  --set nvidia.existingSecret="nvidia-key"
```

### Install from local chart

```bash
# Fetch subchart dependencies first
helm dependency update ./deploy/helm/runai-agent

helm upgrade -i runai-agent ./deploy/helm/runai-agent \
  --namespace runai-agent --create-namespace \
  --set mcp-server-runai.runai.baseUrl="https://myorg.run.ai" \
  --set mcp-server-runai.runai.credentials.existingSecret="runai-creds" \
  --set runai.existingSecret="runai-creds" \
  --set nvidia.existingSecret="nvidia-key"
```

## Using an Existing MCP Server Deployment

If you already have `mcp-server-runai` deployed in your cluster, disable the
subchart and point the agent at the existing service:

```bash
helm upgrade -i runai-agent \
  oci://ghcr.io/runai-professional-services/charts/runai-agent \
  --namespace runai-agent --create-namespace \
  --set mcp-server-runai.enabled=false \
  --set mcpServer.url="http://mcp-server-runai.runai-mcp.svc.cluster.local:8080" \
  --set runai.existingSecret="runai-creds" \
  --set nvidia.existingSecret="nvidia-key"
```

## Configuration

### MCP Server (subchart)

| Parameter | Description | Default |
|-----------|-------------|---------|
| `mcp-server-runai.enabled` | Deploy MCP server as a subchart | `true` |
| `mcp-server-runai.runai.baseUrl` | Run:AI cluster URL | `""` |
| `mcp-server-runai.runai.credentials.clientId` | OAuth2 client ID | `""` |
| `mcp-server-runai.runai.credentials.clientSecret` | OAuth2 client secret | `""` |
| `mcp-server-runai.runai.credentials.existingSecret` | Pre-existing Secret name | `""` |
| `mcp-server-runai.replicaCount` | MCP server replicas | `1` |
| `mcpServer.url` | Override MCP URL (leave empty when subchart enabled) | `""` |

### Agent Image

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.repository` | Container image | `ghcr.io/runai-professional-services/runai-agent` |
| `image.tag` | Image tag (defaults to `appVersion`) | `""` |
| `image.pullPolicy` | Pull policy | `Always` |

### Run:AI Credentials (agent-side)

Used by the agent's built-in monitoring functions (`proactive_monitor`,
`job_analytics`, `kubectl_troubleshoot`).

| Parameter | Description | Default |
|-----------|-------------|---------|
| `runai.clientId` | OAuth2 client ID | `""` |
| `runai.clientSecret` | OAuth2 client secret | `""` |
| `runai.baseUrl` | Run:AI cluster URL | `""` |
| `runai.existingSecret` | Pre-existing Secret name (keys: `RUNAI_CLIENT_ID`, `RUNAI_CLIENT_SECRET`, `RUNAI_BASE_URL`) | `""` |

### NVIDIA API

| Parameter | Description | Default |
|-----------|-------------|---------|
| `nvidia.apiKey` | NVIDIA API key for the LLM | `""` |
| `nvidia.existingSecret` | Pre-existing Secret name (key: `NVIDIA_API_KEY`) | `""` |

### Monitoring Sidecar

| Parameter | Description | Default |
|-----------|-------------|---------|
| `monitoring.enabled` | Enable proactive monitoring sidecar | `true` |
| `monitoring.pollInterval` | Poll interval in seconds | `60` |
| `monitoring.slackWebhookUrl` | Slack webhook for alerts | `""` |

### Failure Analysis

| Parameter | Description | Default |
|-----------|-------------|---------|
| `failureAnalysis.persistence.enabled` | Persist failure history to PVC | `true` |
| `failureAnalysis.persistence.size` | PVC size | `2Gi` |
| `failureAnalysis.persistence.storageClassName` | Storage class | `""` |
| `failureAnalysis.persistence.existingClaim` | Use an existing PVC | `""` |
| `failureAnalysis.database.path` | Database file path | `/data/runai_failure_history.db` |

### Resources

| Parameter | Description | Default |
|-----------|-------------|---------|
| `resources.requests.cpu` | CPU request | `2` |
| `resources.requests.memory` | Memory request | `4Gi` |
| `resources.limits.cpu` | CPU limit | `4` |
| `resources.limits.memory` | Memory limit | `8Gi` |

## Accessing the Agent

```bash
# Port-forward the UI
kubectl port-forward -n runai-agent deployment/runai-agent 3000:3000

# Open browser
open http://localhost:3000
```

## Upgrading

```bash
helm upgrade runai-agent \
  oci://ghcr.io/runai-professional-services/charts/runai-agent \
  --namespace runai-agent \
  --reuse-values \
  --version <new-version>
```

## Uninstalling

```bash
helm uninstall runai-agent --namespace runai-agent

# Remove PVC if you want to wipe the failure history database
kubectl delete pvc -n runai-agent -l app.kubernetes.io/name=runai-agent
```

## Troubleshooting

```bash
# Check all pods (agent + MCP server)
kubectl get pods -n runai-agent

# Agent logs
kubectl logs -n runai-agent deployment/runai-agent -c nat-agent -f

# MCP server logs
kubectl logs -n runai-agent deployment/runai-agent-mcp-server-runai -f

# Check MCP server is reachable from the agent pod
kubectl exec -n runai-agent deployment/runai-agent -c nat-agent -- \
  curl -s http://runai-agent-mcp-server-runai:8080/health
```

### Common Issues

**Subchart not pulled (`Error: no cached repo found`)**
```bash
helm dependency update ./deploy/helm/runai-agent
```

**MCP server unreachable**
- Verify `kubectl get svc -n runai-agent` shows `runai-agent-mcp-server-runai`
- Check MCP server pod logs for credential errors

**Secrets not found**
```bash
kubectl get secrets -n runai-agent
```

## Development

```bash
# Pull subchart dependencies
helm dependency update ./deploy/helm/runai-agent

# Lint
helm lint ./deploy/helm/runai-agent

# Dry-run
helm install runai-agent ./deploy/helm/runai-agent \
  --namespace test --dry-run --debug \
  --set mcp-server-runai.runai.baseUrl=https://test.run.ai \
  --set mcp-server-runai.runai.credentials.clientId=test \
  --set mcp-server-runai.runai.credentials.clientSecret=test \
  --set runai.clientId=test \
  --set runai.clientSecret=test \
  --set runai.baseUrl=https://test.run.ai \
  --set nvidia.apiKey=test
```
