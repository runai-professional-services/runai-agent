# Run:AI Agent Helm Chart

Helm chart for deploying the intelligent Run:AI conversational agent with advanced failure analysis and optional monitoring sidecar.

## Features

- 🤖 **Interactive Chat Interface** - Natural language control of Run:AI clusters
- 🔬 **Advanced Failure Analysis** - ML-driven root cause analysis with persistent database
- 📊 **Continuous Monitoring** - Optional sidecar for proactive failure detection
- 🔒 **Security First** - Kubernetes secrets for sensitive credentials
- 🎯 **Production Ready** - Configurable resources, RBAC, and storage

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- Run:AI cluster v2.18+
- Storage class (any type - EBS, EFS, NFS, etc.)
- Run:AI API credentials
- NVIDIA API key (for LLM)

## Quick Start

### 1. Install with Minimum Configuration

```bash
# Install with inline credentials (development only)
helm upgrade -i runai-agent ./deploy/helm/runai-agent \
  --namespace runai-agent \
  --create-namespace \
  --set runai.clientId="[YOUR_CLIENT_ID]" \
  --set runai.clientSecret="[YOUR_CLIENT_SECRET]" \
  --set runai.baseUrl="https://your-cluster.run.ai" \
  --set nvidia.apiKey="[YOUR_NVIDIA_API_KEY]"
```

### 2. Install with Existing Secrets (Production)

```bash
# Create secrets first
kubectl create namespace runai-agent

kubectl create secret generic runai-creds \
  --namespace runai-agent \
  --from-literal=RUNAI_CLIENT_ID="[YOUR_CLIENT_ID]" \
  --from-literal=RUNAI_CLIENT_SECRET="[YOUR_CLIENT_SECRET]" \
  --from-literal=RUNAI_BASE_URL="https://your-cluster.run.ai"

kubectl create secret generic nvidia-key \
  --namespace runai-agent \
  --from-literal=NVIDIA_API_KEY="[YOUR_NVIDIA_API_KEY]"

# Install using existing secrets
helm upgrade -i runai-agent ./deploy/helm/runai-agent \
  --namespace runai-agent \
  --set runai.existingSecret="runai-creds" \
  --set nvidia.existingSecret="nvidia-key"
```

### 3. Install with Custom Values

```bash
# Create custom values file
cat > my-values.yaml <<EOF
global:
  project: "my-project"
  jobName: "my-agent"

runai:
  existingSecret: "runai-creds"
  
nvidia:
  existingSecret: "nvidia-key"

monitoring:
  enabled: true
  pollInterval: 30

failureAnalysis:
  persistence:
    size: 5Gi
    storageClassName: "nfs-client"

resources:
  requests:
    cpu: "4"
    memory: "8Gi"
EOF

# Install with custom values
helm upgrade -i runai-agent ./deploy/helm/runai-agent \
  --namespace runai-my-project \
  --create-namespace \
  -f my-values.yaml
```

## Installing from GitHub Packages

The Run:AI Agent Helm chart and Docker images are published to GitHub Packages with each release.

### Add Helm Repository

```bash
# Add the Helm repository
helm repo add runai-agent https://runai-professional-services.github.io/runai-agent

# Update repository index
helm repo update
```

### Install Latest Version

```bash
# Install from the published chart
helm upgrade -i runai-agent runai-agent/runai-agent \
  --namespace runai-agent \
  --create-namespace \
  --set runai.clientId="[YOUR_CLIENT_ID]" \
  --set runai.clientSecret="[YOUR_CLIENT_SECRET]" \
  --set runai.baseUrl="https://your-cluster.run.ai" \
  --set nvidia.apiKey="[YOUR_NVIDIA_API_KEY]"
```

### Install Specific Version

```bash
# List available versions
helm search repo runai-agent/runai-agent --versions

# Install specific version
helm upgrade -i runai-agent runai-agent/runai-agent \
  --version 0.1.27 \
  --namespace runai-agent \
  --create-namespace \
  --set runai.existingSecret="runai-creds" \
  --set nvidia.existingSecret="nvidia-key"
```

**Note:** Docker images are automatically pulled from `ghcr.io/runai-professional-services/runai-agent` and versioned to match the chart release.

## Configuration

### Global Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.namespace` | Kubernetes namespace for agent deployment | `runai-agent` |
| `global.deploymentName` | Name for the agent deployment | `runai-agent` |

### Image Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.repository` | Container image repository | `ghcr.io/runai-professional-services/runai-agent` |
| `image.tag` | Image tag (defaults to Chart.appVersion if empty) | `""` |
| `image.pullPolicy` | Image pull policy | `Always` |

**Note:** The image tag defaults to the chart's `appVersion` (from `Chart.yaml`) when not specified. This ensures version-pinned deployments that match the chart version. Override with `--set image.tag=<version>` if you need a specific version.

### Run:AI Credentials

| Parameter | Description | Default |
|-----------|-------------|---------|
| `runai.clientId` | Run:AI API client ID | `""` |
| `runai.clientSecret` | Run:AI API client secret | `""` |
| `runai.baseUrl` | Run:AI cluster URL | `https://your-cluster.run.ai` |
| `runai.existingSecret` | Use existing Kubernetes secret | `""` |

### NVIDIA API

| Parameter | Description | Default |
|-----------|-------------|---------|
| `nvidia.apiKey` | NVIDIA API key for LLM | `""` |
| `nvidia.existingSecret` | Use existing secret | `""` |

### Monitoring Sidecar

| Parameter | Description | Default |
|-----------|-------------|---------|
| `monitoring.enabled` | Enable monitoring sidecar | `true` |
| `monitoring.pollInterval` | Poll interval in seconds | `60` |
| `monitoring.resources.requests.cpu` | CPU request | `0.5` |
| `monitoring.resources.requests.memory` | Memory request | `1Gi` |
| `monitoring.slackWebhookUrl` | Slack webhook for alerts | `""` |

### Failure Analysis

| Parameter | Description | Default |
|-----------|-------------|---------|
| `failureAnalysis.persistence.enabled` | Enable persistent storage | `true` |
| `failureAnalysis.persistence.size` | PVC size | `2Gi` |
| `failureAnalysis.persistence.storageClassName` | Storage class name | `""` |
| `failureAnalysis.persistence.accessModes` | PVC access modes | `[ReadWriteOnce]` |
| `failureAnalysis.persistence.existingClaim` | Use existing PVC | `""` |
| `failureAnalysis.database.path` | Database file path | `/data/runai_failure_history.db` |

### Resources

| Parameter | Description | Default |
|-----------|-------------|---------|
| `resources.requests.cpu` | CPU request | `2` |
| `resources.requests.memory` | Memory request | `4Gi` |
| `resources.requests.gpu` | GPU devices | `0` |
| `resources.limits.cpu` | CPU limit | `4` |
| `resources.limits.memory` | Memory limit | `8Gi` |

### RBAC

| Parameter | Description | Default |
|-----------|-------------|---------|
| `rbac.create` | Create RBAC resources | `true` |
| `rbac.serviceAccountName` | ServiceAccount name | `default` |

### Kubeconfig

| Parameter | Description | Default |
|-----------|-------------|---------|
| `kubeconfig.existingSecret` | Secret with kubeconfig file | `""` |
| `kubeconfig.key` | Key in secret | `config` |

## Examples

### Minimal Deployment (No Monitoring)

```yaml
# values-minimal.yaml
global:
  namespace: "runai-agent-dev"

monitoring:
  enabled: false

failureAnalysis:
  persistence:
    enabled: false

runai:
  existingSecret: "runai-creds"

nvidia:
  existingSecret: "nvidia-key"
```

```bash
helm upgrade -i runai-agent ./deploy/helm/runai-agent \
  --namespace runai-agent-dev --create-namespace \
  -f values-minimal.yaml
```

### Full Production Deployment

```yaml
# values-production.yaml
global:
  namespace: "runai-agent-prod"
  deploymentName: "runai-agent-prod"

image:
  repository: "ghcr.io/runai-professional-services/runai-agent"
  tag: ""  # Uses Chart.appVersion (recommended for version consistency)
  pullPolicy: IfNotPresent

monitoring:
  enabled: true
  pollInterval: 30
  slackWebhookUrl: "https://hooks.slack.com/services/xxx"
  resources:
    requests:
      cpu: "1"
      memory: "2Gi"

failureAnalysis:
  persistence:
    enabled: true
    size: 10Gi
    storageClassName: "nfs-client"

resources:
  requests:
    cpu: "4"
    memory: "8Gi"
  limits:
    cpu: "8"
    memory: "16Gi"

rbac:
  create: true

kubeconfig:
  existingSecret: "kubeconfig-secret"

nodeSelector:
  workload-type: "services"
```

```bash
helm upgrade -i runai-agent ./deploy/helm/runai-agent \
  --namespace runai-agent-prod --create-namespace \
  -f values-production.yaml
```

## Accessing the Agent

### Via Port Forward

```bash
# Forward UI port
kubectl port-forward -n runai-agent deployment/runai-agent 3000:3000

# Open browser
open http://localhost:3000
```

### Via Ingress

If ingress is enabled, access the agent at your configured hostname.

## Upgrading

```bash
# Upgrade to new version
helm upgrade runai-agent ./deploy/helm/runai-agent \
  --namespace runai-agent \
  -f my-values.yaml

# Rollback if needed
helm rollback runai-agent --namespace runai-agent
```

## Uninstalling

```bash
# Uninstall the chart
helm uninstall runai-agent --namespace runai-agent

# Optionally delete the PVC (if you want to remove data)
kubectl delete pvc -n runai-agent -l app.kubernetes.io/name=runai-agent

# Optionally delete the namespace
kubectl delete namespace runai-agent
```

## Troubleshooting

### Check Deployment Status

```bash
# List releases
helm list --namespace runai-agent

# Get deployment status
helm status runai-agent --namespace runai-agent

# Check pod status
kubectl get pods -n runai-agent -l app.kubernetes.io/name=runai-agent
```

### View Logs

```bash
# Main agent logs
kubectl logs -n runai-agent deployment/runai-agent -c nat-agent -f

# Monitoring sidecar logs (if enabled)
kubectl logs -n runai-agent deployment/runai-agent -c monitor-sidecar -f
```

### Common Issues

**PVC Pending**
```bash
# Check PVC status
kubectl describe pvc -n runai-agent runai-agent-failure-db

# Check available storage classes
kubectl get storageclass
```

**Secrets Not Found**
```bash
# Verify secrets exist
kubectl get secrets -n runai-agent

# Create missing secrets
kubectl create secret generic runai-creds \
  --namespace runai-agent \
  --from-literal=RUNAI_CLIENT_ID="xxx" \
  --from-literal=RUNAI_CLIENT_SECRET="xxx" \
  --from-literal=RUNAI_BASE_URL="https://xxx"
```

**Pod Not Starting**
```bash
# Describe deployment
kubectl describe deployment -n runai-agent runai-agent

# Check pod events
kubectl describe pod -n runai-agent -l app.kubernetes.io/name=runai-agent
```

## Development

### Validate Chart

```bash
# Lint the chart
helm lint ./deploy/helm/runai-agent

# Dry-run installation
helm install runai-agent ./deploy/helm/runai-agent \
  --namespace test \
  --dry-run --debug \
  --set runai.clientId=test \
  --set runai.clientSecret=test \
  --set runai.baseUrl=test \
  --set nvidia.apiKey=test
```

### Template Rendering

```bash
# Render templates locally
helm template runai-agent ./deploy/helm/runai-agent \
  --set runai.clientId=test \
  --set runai.clientSecret=test \
  --set runai.baseUrl=test \
  --set nvidia.apiKey=test \
  > rendered.yaml
```

## Support

- Documentation: `docs/`
- Issues: [GitLab Issues](https://gitlab-master.nvidia.com/ape-repo/astra-projects/runai-agent-test/issues)
- Slack: #runai-agent

## License

Copyright © 2024 NVIDIA Corporation

