# Combined Dockerfile for NAT Agent + UI Frontend
# 
# Architecture:
# - Nginx reverse proxy (port 3000) - Entry point for all requests
# - FastAPI backend (port 8000) - Handles /generate, /docs, /openapi.json
# - Next.js UI (port 3001) - Handles all other requests
# 
# Simplified version - no Run:AI workload path prefix support
# Designed for: Helm deployment, Docker deployment, local development

# ============================================
# Stage 1: Build Next.js Frontend
# ============================================
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend source
COPY apps/runai-agent-test-frontend/package*.json ./
RUN npm install --legacy-peer-deps

COPY apps/runai-agent-test-frontend/ ./

# Build Next.js for production (no basePath)
ENV NODE_ENV=production
ENV NEXT_PUBLIC_BASE_PATH=""
RUN npm run build

# ============================================
# Stage 2: Python Backend + Runtime
# ============================================
FROM python:3.13-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    git-lfs \
    curl \
    supervisor \
    nginx \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Install kubectl for Run:AI job status checks
RUN curl -L -s https://dl.k8s.io/release/stable.txt -o /tmp/kubectl-version.txt && \
    KUBECTL_VERSION=$(cat /tmp/kubectl-version.txt) && \
    curl -LO "https://dl.k8s.io/release/${KUBECTL_VERSION}/bin/linux/amd64/kubectl" && \
    chmod +x kubectl && \
    mv kubectl /usr/local/bin/kubectl && \
    rm /tmp/kubectl-version.txt

# Set up working directory
WORKDIR /app

# ============================================
# Python Backend Setup
# ============================================

# Install uv for Python package management
RUN pip install --no-cache-dir uv

# Create virtual environment and install NAT from PyPI
RUN uv venv .venv && \
    . .venv/bin/activate && \
    uv pip install "nvidia-nat[langchain]==1.3.1" && \
    GIT_LFS_SKIP_SMUDGE=1 uv pip install "git+https://github.com/NVIDIA/NeMo-Agent-Toolkit.git@v1.3.1#subdirectory=examples/getting_started/simple_web_query"

# Copy and install custom RunAI agent
COPY runai-agent/ /app/runai-agent/
RUN . .venv/bin/activate && \
    cd /app/runai-agent && \
    uv pip install -e .

# ============================================
# Frontend Setup
# ============================================

# Copy built Next.js from builder stage
COPY --from=frontend-builder /app/frontend/.next/standalone /app/frontend/
COPY --from=frontend-builder /app/frontend/.next/static /app/frontend/.next/static
COPY --from=frontend-builder /app/frontend/public /app/frontend/public

# ============================================
# Configure Nginx
# ============================================

# Copy static nginx configuration
COPY deploy/nginx.conf /etc/nginx/nginx.conf

# Create nginx log directory
RUN mkdir -p /var/log/nginx

# ============================================
# Configure Supervisord
# ============================================

RUN echo '[supervisord]\n\
nodaemon=true\n\
user=root\n\
logfile=/var/log/supervisor/supervisord.log\n\
pidfile=/var/run/supervisord.pid\n\
\n\
[program:nginx]\n\
command=/usr/sbin/nginx -g "daemon off;"\n\
autostart=true\n\
autorestart=true\n\
stderr_logfile=/var/log/supervisor/nginx.err.log\n\
stdout_logfile=/var/log/supervisor/nginx.out.log\n\
priority=10\n\
\n\
[program:backend]\n\
command=/bin/bash -c "cd /app && . .venv/bin/activate && exec nat serve --config_file /app/runai-agent/configs/workflow.yaml --host 0.0.0.0 --port 8000"\n\
autostart=true\n\
autorestart=true\n\
stderr_logfile=/var/log/supervisor/backend.err.log\n\
stdout_logfile=/var/log/supervisor/backend.out.log\n\
priority=20\n\
\n\
[program:frontend]\n\
command=/bin/bash /app/start-frontend.sh\n\
autostart=true\n\
autorestart=true\n\
stderr_logfile=/var/log/supervisor/frontend.err.log\n\
stdout_logfile=/var/log/supervisor/frontend.out.log\n\
priority=30\n\
' > /etc/supervisor/conf.d/supervisord.conf

# Create supervisor log directory
RUN mkdir -p /var/log/supervisor

# ============================================
# Create Frontend Startup Script
# ============================================

RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "========================================"\n\
echo "Starting Next.js Frontend (port 3001)"\n\
echo "========================================"\n\
\n\
cd /app/frontend\n\
\n\
# Set runtime environment variables\n\
export PORT=3001\n\
export HOSTNAME="0.0.0.0"\n\
export NODE_ENV=production\n\
\n\
# Configure chat completion URL for streaming\n\
export NEXT_PUBLIC_HTTP_CHAT_COMPLETION_URL="/generate/stream"\n\
export NEXT_PUBLIC_ENABLE_INTERMEDIATE_STEPS="${NEXT_PUBLIC_ENABLE_INTERMEDIATE_STEPS:-false}"\n\
\n\
echo "  Chat completion URL: /generate/stream"\n\
echo "  Intermediate steps: $NEXT_PUBLIC_ENABLE_INTERMEDIATE_STEPS"\n\
echo ""\n\
\n\
# Generate runtime-env.js for client-side access to env vars\n\
cat > /app/frontend/public/runtime-env.js << EOF\n\
window.__RUNTIME_ENV = {\n\
  NEXT_PUBLIC_HTTP_CHAT_COMPLETION_URL: "/generate/stream",\n\
  NEXT_PUBLIC_ENABLE_INTERMEDIATE_STEPS: ${NEXT_PUBLIC_ENABLE_INTERMEDIATE_STEPS:-false}\n\
};\n\
EOF\n\
\n\
echo "Starting Next.js server..."\n\
exec node server.js\n\
' > /app/start-frontend.sh && chmod +x /app/start-frontend.sh

# ============================================
# Create Entrypoint Script
# ============================================

RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "========================================"\n\
echo "RunAI Agent with NeMo Agent Toolkit"\n\
echo "========================================"\n\
echo ""\n\
\n\
# Validate required environment variables\n\
if [ -z "$NVIDIA_API_KEY" ]; then\n\
    echo "⚠️  Warning: NVIDIA_API_KEY environment variable is not set"\n\
    echo ""\n\
    echo "Get your API key from: https://build.nvidia.com"\n\
    echo ""\n\
    echo "The agent will not be able to make LLM calls without a valid API key."\n\
    echo "Services will start but functionality will be limited."\n\
    echo ""\n\
fi\n\
\n\
# Set defaults for optional variables\n\
export RUNAI_CLIENT_ID="${RUNAI_CLIENT_ID:-test}"\n\
export RUNAI_CLIENT_SECRET="${RUNAI_CLIENT_SECRET:-test}"\n\
export RUNAI_BASE_URL="${RUNAI_BASE_URL:-https://test.run.ai}"\n\
\n\
echo "Configuration:"\n\
if [ -z "$NVIDIA_API_KEY" ]; then\n\
    echo "  NVIDIA_API_KEY: ❌ NOT SET"\n\
else\n\
    echo "  NVIDIA_API_KEY: ${NVIDIA_API_KEY:0:20}..."\n\
fi\n\
echo "  RUNAI_CLIENT_ID: $RUNAI_CLIENT_ID"\n\
echo "  RUNAI_BASE_URL: $RUNAI_BASE_URL"\n\
echo ""\n\
echo "Services:"\n\
echo "  ✓ Nginx (port 3000) - Entry point"\n\
echo "  ✓ Backend API (port 8000) - NAT agent"\n\
echo "  ✓ Frontend UI (port 3001) - Next.js"\n\
echo ""\n\
echo "Access:"\n\
echo "  🌐 UI: http://localhost:3000"\n\
echo "  📡 API: http://localhost:3000/docs"\n\
echo "  🔧 Direct API: http://localhost:8000/docs"\n\
echo ""\n\
echo "Starting services with supervisord..."\n\
echo "========================================"\n\
echo ""\n\
\n\
# Start supervisord\n\
exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf\n\
' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

# ============================================
# Expose Ports
# ============================================

# Port 3000: Main entry point (Nginx)
EXPOSE 3000

# Port 8000: Direct backend access (optional)
EXPOSE 8000

# ============================================
# Health Check
# ============================================

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# ============================================
# Start Services
# ============================================

ENTRYPOINT ["/app/entrypoint.sh"]
