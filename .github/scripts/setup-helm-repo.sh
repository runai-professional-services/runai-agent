#!/bin/bash
set -e

echo "=========================================="
echo "Setting up GitHub Pages for Helm Repository"
echo "=========================================="
echo ""

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "Current branch: $CURRENT_BRANCH"

# Check if gh-pages branch already exists
if git show-ref --verify --quiet refs/heads/gh-pages; then
    echo "✅ gh-pages branch already exists"
    echo ""
    echo "To update the Helm repository, just push a new tag:"
    echo "  git tag v0.1.37"
    echo "  git push origin v0.1.37"
    exit 0
fi

echo ""
echo "Creating gh-pages branch for Helm repository..."
echo ""

# Create orphan gh-pages branch
git checkout --orphan gh-pages

# Remove all files from staging
git rm -rf . > /dev/null 2>&1 || true

# Create index.html
cat > index.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RunAI Agent Helm Repository</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            line-height: 1.6;
        }
        h1 { color: #76b900; }
        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
        pre {
            background: #f4f4f4;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }
        .badge {
            display: inline-block;
            margin: 5px;
        }
    </style>
</head>
<body>
    <h1>⎈ RunAI Agent Helm Repository</h1>
    
    <p>
        <img src="https://img.shields.io/badge/Helm-v3-blue" alt="Helm v3" class="badge">
        <img src="https://img.shields.io/badge/Kubernetes-1.24%2B-blue" alt="Kubernetes 1.24+" class="badge">
    </p>

    <h2>📦 Installation</h2>
    
    <h3>Add the Helm repository:</h3>
    <pre><code>helm repo add runai-agent https://runai-professional-services.github.io/runai-agent
helm repo update</code></pre>

    <h3>Install the chart:</h3>
    <pre><code>helm install runai-agent runai-agent/runai-agent \
  --namespace runai-agent \
  --create-namespace \
  --set nvidia.apiKey="YOUR_NVIDIA_API_KEY" \
  --set runai.clientId="YOUR_RUNAI_CLIENT_ID" \
  --set runai.clientSecret="YOUR_RUNAI_CLIENT_SECRET" \
  --set runai.baseUrl="https://your-cluster.run.ai"</code></pre>

    <h3>Search for available charts:</h3>
    <pre><code>helm search repo runai-agent</code></pre>

    <h2>📚 Documentation</h2>
    <ul>
        <li><a href="https://github.com/runai-professional-services/runai-agent">GitHub Repository</a></li>
        <li><a href="https://github.com/runai-professional-services/runai-agent/blob/main/README.md">README</a></li>
        <li><a href="https://github.com/runai-professional-services/runai-agent/blob/main/deploy/helm/runai-agent/README.md">Helm Chart Documentation</a></li>
    </ul>

    <h2>🔗 Resources</h2>
    <ul>
        <li><a href="index.yaml">Chart Repository Index</a></li>
        <li><a href="https://github.com/runai-professional-services/runai-agent/releases">Releases</a></li>
        <li><a href="https://github.com/runai-professional-services/runai-agent/actions">CI/CD Status</a></li>
    </ul>

    <hr>
    <p><small>Built with ❤️ using NVIDIA NeMo Agent Toolkit</small></p>
</body>
</html>
EOF

# Create README
cat > README.md << 'EOF'
# RunAI Agent Helm Repository

This is the Helm chart repository for the RunAI Agent project.

## Usage

Add the repository:
```bash
helm repo add runai-agent https://runai-professional-services.github.io/runai-agent
helm repo update
```

Install the chart:
```bash
helm install runai-agent runai-agent/runai-agent --namespace runai-agent
```

See the [main repository](https://github.com/runai-professional-services/runai-agent) for full documentation.
EOF

# Create initial index.yaml
cat > index.yaml << 'EOF'
apiVersion: v1
entries: {}
generated: "2026-01-14T00:00:00Z"
EOF

# Add files
git add index.html README.md index.yaml

# Commit
git commit -m "Initialize Helm repository on GitHub Pages"

echo ""
echo "✅ gh-pages branch created successfully!"
echo ""
echo "Next steps:"
echo "1. Push the gh-pages branch:"
echo "   git push origin gh-pages"
echo ""
echo "2. Enable GitHub Pages in repository settings:"
echo "   - Go to Settings → Pages"
echo "   - Source: Deploy from a branch"
echo "   - Branch: gh-pages"
echo "   - Folder: / (root)"
echo "   - Save"
echo ""
echo "3. Return to your main branch:"
echo "   git checkout $CURRENT_BRANCH"
echo ""
echo "4. Create and push a tag to publish your first chart:"
echo "   git tag v0.1.36"
echo "   git push origin v0.1.36"
echo ""
echo "The Helm repository will be available at:"
echo "https://runai-professional-services.github.io/runai-agent"
echo ""
