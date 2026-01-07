# Sidecar Deployment Guide

This guide explains how to deploy the Run:AI agent with a monitoring sidecar for continuous failure analysis.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Pod                           │
│                                                             │
│  ┌──────────────────┐         ┌────────────────────┐      │
│  │  Main Container  │         │ Sidecar Container  │      │
│  │  (NAT Agent)     │         │  (Monitoring)      │      │
│  │                  │         │                    │      │
│  │  - Web UI :3000  │         │  - Polls every 60s │      │
│  │  - API :8000     │         │  - Records failures│      │
│  │  - Chat queries  │         │  - Auto-troubleshoot│     │
│  └────────┬─────────┘         └─────────┬──────────┘      │
│           │                             │                  │
│           └──────────┬──────────────────┘                  │
│                      │                                     │
│            ┌─────────▼─────────┐                          │
│            │  Shared Volume    │                          │
│            │  /data/           │                          │
│            │  failure_history  │                          │
│            │  .db              │                          │
│            └───────────────────┘                          │
│                      │                                     │
└──────────────────────┼─────────────────────────────────────┘
                       │
              ┌────────▼────────┐
              │ PersistentVolume│
              │  (2Gi NFS/EFS)  │
              └─────────────────┘
```

## 🎯 Benefits

### Why Sidecar Pattern?

1. **Single Deployment** - One workload, easier to manage
2. **Tight Coupling** - Monitoring and chat always together
3. **Automatic Scaling** - Both containers scale together
4. **Shared State** - Same database, instant access to latest failures
5. **Fault Tolerance** - If one crashes, Kubernetes restarts both

### Main Container (NAT Agent)
- **Purpose**: Interactive chat interface
- **Ports**: 3000 (UI), 8000 (API)
- **Function**: Queries failure database, provides analysis
- **Resources**: 2 CPU, 4Gi RAM

### Sidecar Container (Monitor)
- **Purpose**: Continuous workload monitoring
- **Function**: Polls cluster, detects failures, records to DB
- **Interval**: Every 60 seconds (configurable)
- **Resources**: 0.5 CPU, 1Gi RAM

## 📋 Prerequisites

1. **Kubernetes cluster** with Run:AI installed
2. **Storage class** (any type - EBS, EFS, NFS, etc.)
3. **Run:AI credentials** (client ID, secret)
4. **NVIDIA API key** for the LLM
5. **Container image** with the agent built

## 🚀 Deployment Steps

### Step 1: Set Environment Variables

```bash
export NVIDIA_API_KEY="[YOUR_NVIDIA_API_KEY]"
export RUNAI_CLIENT_ID="[YOUR_CLIENT_ID]"
export RUNAI_CLIENT_SECRET="[YOUR_CLIENT_SECRET]"
export RUNAI_BASE_URL="https://your-runai-cluster.example.com"
export RUNAI_PROJECT="project-01"
export RUNAI_JOB_NAME="runai-agent"
```

### Step 2: Create the PersistentVolumeClaim

```bash
# Edit the PVC to set your storage class
nano deploy/k8s/failure-analysis-pvc.yaml

# Apply the PVC
envsubst < deploy/k8s/failure-analysis-pvc.yaml | kubectl apply -f -

# Verify it's created
kubectl get pvc -n runai-${RUNAI_PROJECT}
```

**Expected output:**
```
NAME                    STATUS   VOLUME     CAPACITY   ACCESS MODES   STORAGECLASS
failure-analysis-pvc    Bound    pvc-xxx    2Gi        RWO            gp3
```

### Step 3: Deploy the Agent with Sidecar

```bash
# Deploy the agent
envsubst < deploy/k8s/runai-agent-with-sidecar.yaml | kubectl apply -f -

# Watch the pods start
kubectl get pods -n runai-${RUNAI_PROJECT} -w
```

### Step 4: Verify Both Containers Are Running

```bash
# Check pod status
kubectl get pods -n runai-${RUNAI_PROJECT}

# Expected: 2/2 containers ready
NAME                    READY   STATUS    RESTARTS   AGE
runai-agent-0-0         2/2     Running   0          2m
```

### Step 5: Check Logs

**Main container (agent):**
```bash
kubectl logs -n runai-${RUNAI_PROJECT} runai-agent-0-0 -c nat-agent
```

**Sidecar container (monitoring):**
```bash
kubectl logs -n runai-${RUNAI_PROJECT} runai-agent-0-0 -c monitor-sidecar -f
```

**Expected sidecar output:**
```
================================================================================
Run:AI Monitoring Sidecar Starting
================================================================================
Configuration:
  - Poll Interval: 60 seconds
  - Project Filter: All projects
  - Database: /data/runai_failure_history.db
  - Start Time: 2025-12-05 14:30:00
================================================================================
✓ Run:AI credentials configured
✓ Cluster: https://runcluster.example.com
🚀 Starting continuous monitoring...
```

### Step 6: Access the Agent UI

```bash
# Get the external URL from Run:AI UI
# Or port-forward locally for testing
kubectl port-forward -n runai-${RUNAI_PROJECT} runai-agent-0-0 3000:3000
```

Open http://localhost:3000 and test:

```
Show me failure statistics
Analyze failures from the last 7 days
```

## 🔧 Configuration

### Adjust Polling Interval

Edit `deploy/k8s/runai-agent-with-sidecar.yaml`:

```yaml
# Change from 60 seconds to 30 seconds
python scripts/monitor_sidecar.py --poll-interval 30
```

### Monitor Specific Project Only

```yaml
# Monitor only project-01
python scripts/monitor_sidecar.py --project project-01
```

### Increase Database Storage

Edit `deploy/k8s/failure-analysis-pvc.yaml`:

```yaml
resources:
  requests:
    storage: 10Gi  # Increase from 2Gi to 10Gi
```

### Adjust Resource Requests

Edit `deploy/k8s/runai-agent-with-sidecar.yaml`:

```yaml
# Sidecar resources
resources:
  requests:
    cpu: "1"        # Increase CPU
    memory: "2Gi"   # Increase memory
```

## 🐛 Troubleshooting

### Sidecar Not Starting

**Check logs:**
```bash
kubectl logs -n runai-${RUNAI_PROJECT} runai-agent-0-0 -c monitor-sidecar
```

**Common issues:**

1. **Missing credentials:**
   ```
   ERROR: Missing required environment variables: RUNAI_CLIENT_SECRET
   ```
   **Fix:** Set all environment variables in the YAML

2. **Database path not writable:**
   ```
   ERROR: Permission denied: /data/runai_failure_history.db
   ```
   **Fix:** Check PVC is mounted correctly

3. **Python environment not found:**
   ```
   ERROR: No module named 'runai_agent'
   ```
   **Fix:** Ensure virtual environment is activated in startup script

### PVC Not Binding

**Check PVC status:**
```bash
kubectl describe pvc failure-analysis-pvc -n runai-${RUNAI_PROJECT}
```

**Common issues:**

1. **No default storage class**
   ```
   Events:
     Warning  ProvisioningFailed  no volume plugin matched
   ```
   **Fix:** Install NFS provisioner or use EFS (AWS)

2. **Storage class doesn't exist**
   ```
   StorageClass "nfs-client" not found
   ```
   **Fix:** Update PVC with correct storage class name

### Database Not Shared

**Verify both containers can access the database:**

```bash
# Check main container
kubectl exec -n runai-${RUNAI_PROJECT} runai-agent-0-0 -c nat-agent -- ls -la /data/

# Check sidecar
kubectl exec -n runai-${RUNAI_PROJECT} runai-agent-0-0 -c monitor-sidecar -- ls -la /data/
```

Both should show the same database file.

### Monitoring Not Detecting Failures

**Check sidecar logs for errors:**
```bash
kubectl logs -n runai-${RUNAI_PROJECT} runai-agent-0-0 -c monitor-sidecar -f
```

**Look for:**
```
🔄 Monitoring check #X at HH:MM:SS
   Found Y workload(s)
   Checking: job-name (project=project-01, phase=Running)
```

If you don't see workloads, check Run:AI API connectivity.

## 📊 Monitoring Health

### Check Sidecar is Running

```bash
# Get pod status
kubectl get pods -n runai-${RUNAI_PROJECT} -l job-name=runai-agent

# Should show 2/2 containers ready
```

### View Monitoring Activity

```bash
# Tail sidecar logs
kubectl logs -n runai-${RUNAI_PROJECT} runai-agent-0-0 -c monitor-sidecar -f --tail=50
```

### Check Database Size

```bash
kubectl exec -n runai-${RUNAI_PROJECT} runai-agent-0-0 -c nat-agent -- du -h /data/runai_failure_history.db
```

### Test Database Access

```bash
# From main container
kubectl exec -it -n runai-${RUNAI_PROJECT} runai-agent-0-0 -c nat-agent -- sqlite3 /data/runai_failure_history.db "SELECT COUNT(*) FROM failure_events;"
```

## 🔄 Updates and Maintenance

### Update Agent Image

```bash
# Update image in YAML
# Then apply changes
envsubst < deploy/k8s/runai-agent-with-sidecar.yaml | kubectl apply -f -

# Restart pod
kubectl delete pod -n runai-${RUNAI_PROJECT} runai-agent-0-0
```

### Backup Database

```bash
# Copy database locally
kubectl cp runai-${RUNAI_PROJECT}/runai-agent-0-0:/data/runai_failure_history.db ./failure_history_backup.db -c nat-agent

# Restore database
kubectl cp ./failure_history_backup.db runai-${RUNAI_PROJECT}/runai-agent-0-0:/data/runai_failure_history.db -c nat-agent
```

### Clean Old Data

```bash
# Delete failures older than 90 days
kubectl exec -it -n runai-${RUNAI_PROJECT} runai-agent-0-0 -c nat-agent -- sqlite3 /data/runai_failure_history.db "DELETE FROM failure_events WHERE timestamp < datetime('now', '-90 days'); VACUUM;"
```

## 🎯 Production Best Practices

1. **Use Persistent Storage**: Ensure PVC uses reliable storage (NFS, EFS, etc.)
2. **Set Resource Limits**: Prevent sidecar from consuming too many resources
3. **Monitor Logs**: Set up log aggregation for both containers
4. **Regular Backups**: Schedule database backups
5. **Health Checks**: Monitor that both containers stay running
6. **Retention Policy**: Clean old failure data periodically

## 📚 Related Documentation

- [FAILURE_ANALYSIS.md](FAILURE_ANALYSIS.md) - Complete feature guide
- [FAILURE_ANALYSIS_QUICKSTART.md](FAILURE_ANALYSIS_QUICKSTART.md) - Quick start
- [PROACTIVE_MONITORING.md](PROACTIVE_MONITORING.md) - Monitoring details
- [DEPLOYMENT.md](DEPLOYMENT.md) - General deployment guide

---

**Questions?** Check the main README or open an issue on the repository.

