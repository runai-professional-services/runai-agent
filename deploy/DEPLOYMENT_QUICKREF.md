# 🚀 Deployment Quick Reference

Quick reference for deploying the Run:AI Agent with different methods.

## 🎯 Recommended: Helm Chart (Production)

**Best for:** Production deployments, full features, easy management

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

# 2. Deploy with Helm
helm install runai-agent ./deploy/helm/runai-agent \
  --namespace runai-agent \
  --set runai.existingSecret="runai-creds" \
  --set nvidia.existingSecret="nvidia-key" \
  --set failureAnalysis.persistence.storageClassName="your-storage-class"

# 3. Access
kubectl port-forward -n runai-agent deployment/runai-agent 3000:3000
```

**What you get:**
- ✅ Main agent (chat UI + API)
- ✅ Monitoring sidecar (continuous failure detection)
- ✅ Persistent failure database (2Gi PVC)
- ✅ RBAC for kubectl access
- ✅ Easy upgrades with `helm upgrade`

**Documentation:** [deploy/helm/runai-agent/README.md](helm/runai-agent/README.md)

---

## 📝 Alternative: kubectl Manifests

**Best for:** Manual control, GitOps workflows, no Helm available

### Option A: With Monitoring Sidecar (Recommended)

```bash
# 1. Create PVC for failure database
kubectl apply -f deploy/k8s/failure-analysis-pvc.yaml

# 2. Deploy agent with sidecar
kubectl apply -f deploy/k8s/runai-agent-with-sidecar.yaml

# 3. Verify
kubectl get pods -n runai-<your-project>
# Should show: 2/2 Running (depends on your project namespace)
```

### Option B: Single Container (Minimal)

For a minimal deployment without monitoring, edit `deploy/k8s/runai-agent-with-sidecar.yaml` and remove the sidecar container section, or use Helm with `monitoring.enabled=false`.

**Documentation:** [docs/SIDECAR_DEPLOYMENT.md](../docs/SIDECAR_DEPLOYMENT.md)

---

## 💻 Local Development

**Best for:** Testing, development, debugging

```bash
# Quick start
export NVIDIA_API_KEY="[YOUR_NVIDIA_API_KEY]"
export RUNAI_CLIENT_ID="[YOUR_CLIENT_ID]"
export RUNAI_CLIENT_SECRET="[YOUR_CLIENT_SECRET]"
export RUNAI_BASE_URL="https://your-cluster.run.ai"

./deploy/start-local.sh

# Access: http://localhost:3000
```

**Documentation:** [docs/QUICKSTART.md](../docs/QUICKSTART.md)

---

## 🐳 Docker (Standalone)

**Best for:** Quick testing, demos, non-Kubernetes environments

```bash
# Build
./deploy/build-docker.sh

# Run
docker run -p 3000:3000 -p 8000:8000 \
  -e NVIDIA_API_KEY="$NVIDIA_API_KEY" \
  -e RUNAI_CLIENT_ID="$RUNAI_CLIENT_ID" \
  -e RUNAI_CLIENT_SECRET="$RUNAI_CLIENT_SECRET" \
  -e RUNAI_BASE_URL="$RUNAI_BASE_URL" \
  ghcr.io/runai-professional-services/runai-agent:latest

# Access: http://localhost:3000
```

**Documentation:** [README.md](../README.md#docker-deployment)

---

## 📊 Feature Comparison

| Feature | Helm | kubectl (Sidecar) | Local Dev | Docker |
|---------|------|-------------------|-----------|--------|
| **Chat UI** | ✅ | ✅ | ✅ | ✅ |
| **Job Management** | ✅ | ✅ | ✅ | ✅ |
| **Continuous Monitoring** | ✅ | ✅ | ❌ | ❌ |
| **Failure Analysis DB** | ✅ (Persistent) | ✅ (Persistent) | ✅ (In-memory) | ✅ (In-memory) |
| **kubectl Access** | ✅ | ✅ | ✅ (Local) | ⚠️ (Manual) |
| **Easy Updates** | ✅ | ⚠️ | ✅ | ⚠️ |
| **Production Ready** | ✅ | ✅ | ❌ | ❌ |

**Legend:**
- ✅ Fully supported
- ⚠️ Requires manual setup
- ❌ Not available

---

## 🎯 Which Method Should I Use?

### Use **Helm** if:
- ✅ You want production deployment
- ✅ You need all features (monitoring, persistence, RBAC)
- ✅ You want easy upgrades and management
- ✅ You're comfortable with Helm

### Use **kubectl (Sidecar)** if:
- ✅ You want production deployment
- ✅ You prefer raw manifests (GitOps)
- ✅ You don't have/want Helm
- ⚠️ You're comfortable manually updating manifests


### Use **Local Dev** if:
- 🧪 You're developing features
- 🧪 You need hot reload
- 🧪 Testing locally before deployment

### Use **Docker** if:
- 🎯 Quick demos
- 🎯 Non-Kubernetes environment
- 🎯 Personal laptop testing

---

## 🔧 Common Post-Deployment Tasks

### Access the UI

```bash
# Port forward to local machine
kubectl port-forward -n runai-agent deployment/runai-agent 3000:3000

# Open browser
open http://localhost:3000
```

### View Logs

```bash
# Main agent logs
kubectl logs -n runai-agent deployment/runai-agent -c nat-agent -f

# Monitoring sidecar logs (if enabled)
kubectl logs -n runai-agent deployment/runai-agent -c monitor-sidecar -f
```

### Check Database

```bash
# Connect to database (if persistent storage enabled)
POD_NAME=$(kubectl get pods -n runai-agent -l app.kubernetes.io/name=runai-agent -o jsonpath='{.items[0].metadata.name}')
kubectl exec -it -n runai-agent $POD_NAME -c nat-agent -- \
  sqlite3 /data/runai_failure_history.db

# Query failures
sqlite> SELECT COUNT(*) FROM failure_events;
sqlite> SELECT * FROM failure_events ORDER BY timestamp DESC LIMIT 5;
```

### Upgrade (Helm only)

```bash
# Upgrade to new version
helm upgrade runai-agent ./deploy/helm/runai-agent \
  --namespace runai-agent \
  -f my-values.yaml

# Rollback if needed
helm rollback runai-agent --namespace runai-agent
```

---

## 📚 Full Documentation

- **Helm Chart:** [deploy/helm/runai-agent/README.md](helm/runai-agent/README.md)
- **Sidecar Deployment:** [docs/SIDECAR_DEPLOYMENT.md](../docs/SIDECAR_DEPLOYMENT.md)
- **Quick Start:** [docs/QUICKSTART.md](../docs/QUICKSTART.md)
- **Complete Deployment:** [docs/DEPLOYMENT.md](../docs/DEPLOYMENT.md)
- **Failure Analysis:** [docs/FAILURE_ANALYSIS.md](../docs/FAILURE_ANALYSIS.md)

---

## 🆘 Troubleshooting

### Pod not starting?
```bash
kubectl describe deployment -n runai-agent runai-agent
kubectl logs -n runai-agent deployment/runai-agent -c nat-agent
```

### PVC pending?
```bash
kubectl describe pvc -n runai-agent runai-agent-failure-db
# Check available storage classes
kubectl get storageclass
```

### Can't access UI?
```bash
# Check pod is running
kubectl get pods -n runai-agent

# Check port forward
kubectl port-forward -n runai-agent deployment/runai-agent 3000:3000
```

### Database not persisting?
```bash
# Check PVC is bound
kubectl get pvc -n runai-agent

# Check volume mounts
kubectl describe deployment -n runai-agent runai-agent
```

**Need more help?** See full troubleshooting guide: [docs/DEPLOYMENT.md#troubleshooting](../docs/DEPLOYMENT.md#troubleshooting)

