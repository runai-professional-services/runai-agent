# 🚀 Deployment Guide

Complete guide for deploying NAT Agent with Web UI to Docker, Kubernetes, and Run:ai.

## Table of Contents

- [Overview](#overview)
- [Build & Push](#build--push)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## Overview

### 🎯 Recommended: Use Official Images

**For most users, we recommend using the official pre-built images from GitHub Container Registry:**

```bash
# Pull the latest release
docker pull ghcr.io/runai-professional-services/runai-agent:latest

# Or a specific version
docker pull ghcr.io/runai-professional-services/runai-agent:v0.1.37
```

**Benefits:**
- ✅ Pre-built and tested
- ✅ Automated security scanning
- ✅ Multi-platform support (amd64, arm64)
- ✅ Matches Helm chart versions

**Skip to:** [Docker Deployment](#docker-deployment) or [Kubernetes Deployment](#kubernetes-deployment)

---

### Custom Builds (Advanced)

The instructions below are for users who need to build custom images with modifications.

### Deployment Options

1. **Helm Chart (Recommended)** - Production-ready deployment with monitoring, persistence, and RBAC
   - See [Helm Chart README](../deploy/helm/runai-agent/README.md) for full documentation
2. **Kubernetes Manifests** - Manual deployment with kubectl (for GitOps or custom setups)
3. **Docker** - Local development and testing

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Combined Container                         │
│                                                             │
│  ┌──────────┐      ┌───────┐      ┌──────────────┐        │
│  │  Nginx   │  →   │Next.js│  →   │  NAT Agent   │        │
│  │  :3000   │      │ :3001 │      │    :8000     │        │
│  └──────────┘      └───────┘      └──────────────┘        │
│       ↑                                    ↑                │
└───────┼────────────────────────────────────┼────────────────┘
        │                                    │
   User Browser                        Direct API
   (OAuth Proxy)                       (Internal)
```

**Components:**
- **Nginx**: Routes requests and handles path rewrites
- **Next.js UI**: Web interface on internal port 3001, exposed via Nginx on 3000
- **NAT Backend**: FastAPI server on port 8000
- **Supervisord**: Manages all processes

### Recommended Deployment Method

For production deployments, use the **Helm Chart** which includes:
- ✅ Monitoring sidecar for continuous failure detection
- ✅ Persistent failure database (configurable PVC)
- ✅ RBAC for kubectl access
- ✅ Secure credential management
- ✅ Easy upgrades and rollbacks

See the [Helm Chart README](../deploy/helm/runai-agent/README.md) for installation instructions.

## Build & Push

### Build the Combined Image

```bash
# Build with default tag
docker build -t nat-agent-ui:latest \
  -f Dockerfile \
  --platform linux/amd64 \
  .
```

**Note:** For custom path configurations, you can set `NEXT_PUBLIC_BASE_PATH` at build time if needed.

### Tag for Your Registry

```bash
# Tag with your registry
docker tag nat-agent-ui:latest your-registry.com/nat-agent-ui:v1.0.0

# Or use your Docker Hub username
docker tag nat-agent-ui:latest yourusername/nat-agent-ui:v1.0.0
```

### Push to Registry

```bash
# Push to your registry
docker push your-registry.com/nat-agent-ui:v1.0.0

# Or Docker Hub
docker push yourusername/nat-agent-ui:v1.0.0
```

### Automated Build Script

```bash
# Use the provided script
./BUILD_UI.sh your-registry.com

# Follow prompts to build and push
```

## Docker Deployment

### Running Locally with Docker

```bash
# Set required environment variables
export NVIDIA_API_KEY="[YOUR_NVIDIA_API_KEY]"
export RUNAI_CLIENT_ID="[YOUR_CLIENT_ID]"
export RUNAI_CLIENT_SECRET="[YOUR_CLIENT_SECRET]"

# Run the container
docker run -d \
  --name nat-agent-ui \
  -p 3000:3000 \
  -p 8000:8000 \
  -e NVIDIA_API_KEY="$NVIDIA_API_KEY" \
  -e RUNAI_CLIENT_ID="$RUNAI_CLIENT_ID" \
  -e RUNAI_CLIENT_SECRET="$RUNAI_CLIENT_SECRET" \
  -e RUNAI_BASE_URL="https://your-cluster.com" \
  your-registry.com/nat-agent-ui:v1.0.0

# View logs
docker logs -f nat-agent-ui

# Stop container
docker stop nat-agent-ui
docker rm nat-agent-ui
```

### Health Checks

```bash
# Check if services are running
docker ps | grep nat-agent-ui

# Test backend
curl http://localhost:8000/docs

# Test frontend
curl http://localhost:3000
```

## Kubernetes Deployment

### Prerequisites

1. Kubernetes cluster with kubectl configured
2. Docker image pushed to accessible registry
3. NVIDIA API key stored as secret

### Create Secrets

```bash
# Create NVIDIA API key secret
kubectl create secret generic nvidia-api-key \
  --from-literal=key="[YOUR_NVIDIA_API_KEY]"

# Create Run:ai credentials secret
kubectl create secret generic runai-credentials \
  --from-literal=client-id="[YOUR_CLIENT_ID]" \
  --from-literal=client-secret="[YOUR_CLIENT_SECRET]"
```

### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nat-agent-ui
  namespace: default
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
        image: your-registry.com/nat-agent-ui:v1.0.0
        ports:
        - containerPort: 3000
          name: http-ui
          protocol: TCP
        env:
        - name: NVIDIA_API_KEY
          valueFrom:
            secretKeyRef:
              name: nvidia-api-key
              key: key
        - name: RUNAI_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: runai-credentials
              key: client-id
        - name: RUNAI_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: runai-credentials
              key: client-secret
        - name: RUNAI_BASE_URL
          value: "https://your-cluster.com"
        resources:
          requests:
            memory: "2Gi"
            cpu: "1"
          limits:
            memory: "4Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 3000
          initialDelaySeconds: 10
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: nat-agent-ui
spec:
  selector:
    app: nat-agent-ui
  ports:
  - name: http-ui
    port: 3000
    targetPort: 3000
    protocol: TCP
  type: LoadBalancer
```

### Deploy

```bash
# Apply the manifests
kubectl apply -f k8s/deployment.yaml

# Check deployment status
kubectl get pods -l app=nat-agent-ui

# View logs
kubectl logs -f deployment/nat-agent-ui

# Get service endpoint
kubectl get service nat-agent-ui
```

**For Helm-based deployments (recommended)**, see the [Helm Chart README](../deploy/helm/runai-agent/README.md) for comprehensive deployment options with monitoring, persistence, and RBAC.

## Configuration

### Environment Variables

#### Required
- `NVIDIA_API_KEY` - Your NVIDIA API key

#### Optional - Run:ai Configuration
- `RUNAI_CLIENT_ID` - Run:ai client ID (default: "test")
- `RUNAI_CLIENT_SECRET` - Run:ai client secret
- `RUNAI_BASE_URL` - Run:ai cluster URL

#### Auto-Detected (Run:ai Only)
- `RUNAI_PROJECT` - Auto-set by Run:ai
- `RUNAI_JOB_NAME` - Auto-set by Run:ai

#### Manual Override
- `ROOT_PATH` - Manually set path prefix (overrides auto-detection)

### Agent Configuration

Edit `runai-agent/configs/workflow.yaml`:

```yaml
general:
  use_uvloop: true
  logging:
    console:
      _type: console
      level: INFO
  front_end:
    _type: fastapi
    host: "0.0.0.0"
    port: 8000
    # root_path set via environment variables

workflow:
  _type: react
  llm_name: nvidia_nim
  tool_names:
    - runailabs_environment_info
    - runailabs_generate_yaml_job
    # ... add more tools
```

### Resource Limits

Recommended Kubernetes resources:

```yaml
resources:
  requests:
    memory: "2Gi"
    cpu: "1"
  limits:
    memory: "4Gi"
    cpu: "2"
```

For GPU support (optional):
```yaml
resources:
  limits:
    nvidia.com/gpu: 1
```

## Troubleshooting

### Common Issues

#### 404 Errors

**Symptom:** Getting 404 on `/generate` endpoint

**Solutions:**
1. Check `RUNAI_PROJECT` and `RUNAI_JOB_NAME` are set correctly
2. Verify `NEXT_PUBLIC_BASE_PATH` matches your deployment path
3. Check nginx configuration in container

```bash
# View environment variables
kubectl exec nat-ui-0-0 -n runai-project-01 -c nat-ui -- env | grep RUNAI

# Check nginx config
kubectl exec nat-ui-0-0 -n runai-project-01 -c nat-ui -- cat /etc/nginx/nginx.conf
```

#### UI Shows Blank Page

**Symptom:** UI loads but shows blank page

**Solutions:**
1. Check browser console for errors
2. Verify `__ENV.js` is loaded
3. Check frontend logs

```bash
# Check __ENV.js
kubectl exec nat-ui-0-0 -n runai-project-01 -c nat-ui -- \
  cat /app/frontend/public/__ENV.js

# View frontend logs
kubectl logs nat-ui-0-0 -n runai-project-01 -c nat-ui | grep "nat-frontend"
```

#### API Returns 500 Error

**Symptom:** Chat requests fail with 500 Internal Server Error

**Solutions:**
1. Check backend is running
2. Verify NVIDIA_API_KEY is valid
3. Check backend logs for errors

```bash
# Check backend logs
kubectl logs nat-ui-0-0 -n runai-project-01 -c nat-ui | grep "nat-backend"

# Test backend directly
kubectl exec nat-ui-0-0 -n runai-project-01 -c nat-ui -- \
  curl -X POST http://127.0.0.1:8000/generate \
  -H "Content-Type: application/json" \
  -d '{"input_message": "test"}'
```

#### Container Crashes

**Symptom:** Pod keeps restarting

**Solutions:**
1. Check if NVIDIA_API_KEY is set
2. Review container logs
3. Check resource limits

```bash
# View crash logs
kubectl logs nat-ui-0-0 -n runai-project-01 -c nat-ui --previous

# Check events
kubectl get events -n runai-project-01 | grep nat-ui

# Describe pod for resource issues
kubectl describe pod nat-ui-0-0 -n runai-project-01
```

### Debug Commands

```bash
# Get shell access
kubectl exec -it nat-ui-0-0 -n runai-project-01 -c nat-ui -- /bin/bash

# Check all processes
kubectl exec nat-ui-0-0 -n runai-project-01 -c nat-ui -- ps aux

# Test internal connectivity
kubectl exec nat-ui-0-0 -n runai-project-01 -c nat-ui -- \
  curl http://127.0.0.1:8000/docs

# Check nginx logs
kubectl exec nat-ui-0-0 -n runai-project-01 -c nat-ui -- \
  tail -f /var/log/nginx/access.log
```

### Performance Tuning

#### Increase Resources

```yaml
resources:
  requests:
    memory: "4Gi"
    cpu: "2"
  limits:
    memory: "8Gi"
    cpu: "4"
```

#### Scale Replicas

```bash
# Scale up
kubectl scale deployment nat-agent-ui --replicas=3

# Check status
kubectl get pods -l app=nat-agent-ui
```

## Best Practices

### Security

1. **Use Secrets** - Never hardcode API keys in manifests
2. **RBAC** - Configure proper Kubernetes RBAC
3. **Network Policies** - Restrict pod-to-pod communication
4. **Image Scanning** - Scan images for vulnerabilities

### Monitoring

1. **Add Prometheus Metrics** - Monitor agent performance
2. **Set up Alerts** - Alert on pod crashes or high error rates
3. **Log Aggregation** - Use ELK or similar for centralized logs

### Updates

1. **Version Tags** - Always tag images with version numbers
2. **Rolling Updates** - Use Kubernetes rolling updates
3. **Health Checks** - Configure liveness and readiness probes

## Multi-Environment Deployments

### Development

```bash
# See Docker Deployment section above for running locally
docker run -p 3000:3000 -p 8000:8000 \
  -e NVIDIA_API_KEY="$NVIDIA_API_KEY" \
  your-registry.com/nat-agent-ui:v1.0.0
```

### Staging

```yaml
metadata:
  name: nat-ui-staging
  namespace: project-staging
```

### Production

```yaml
metadata:
  name: nat-ui
  namespace: project-prod
spec:
  replicas: 3
  resources:
    requests:
      memory: "4Gi"
      cpu: "2"
```

## Summary

✅ **Zero Configuration** - Auto-detects Run:ai environment  
✅ **Multi-Environment** - Same image for dev/staging/prod  
✅ **Scalable** - Easy to scale horizontally  
✅ **Observable** - Built-in health checks and logging  
✅ **Secure** - Secrets management and RBAC support  

---

**Need more help?** Check the logs, review the configuration, and ensure all environment variables are set correctly!

