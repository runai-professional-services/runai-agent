# CI/CD Setup Guide

This guide will help you set up the complete CI/CD pipeline for the RunAI Agent project.

## 🎯 Overview

The CI/CD pipeline provides:
- ✅ Automated testing on every push and PR
- 🐳 Docker image building and publishing
- 🚀 Automated releases with changelog generation
- ⎈ Helm chart publishing to GitHub Pages
- 🔍 PR validation and code quality checks
- 🤖 Automated dependency updates

## 📋 Prerequisites

- GitHub repository with admin access
- Git installed locally
- Docker (optional, for local testing)
- Helm (optional, for local testing)

## 🚀 Quick Setup (5 minutes)

### Step 1: Enable GitHub Pages

1. Go to your repository on GitHub
2. Navigate to **Settings** → **Pages**
3. Under **Source**, select:
   - **Deploy from a branch**
   - **Branch**: `gh-pages` (will be created automatically)
   - **Folder**: `/ (root)`
4. Click **Save**

### Step 2: Initialize Helm Repository

Run the setup script to create the `gh-pages` branch:

```bash
./.github/scripts/setup-helm-repo.sh
```

This will:
- Create an orphan `gh-pages` branch
- Add initial Helm repository files
- Provide instructions for pushing

Follow the script's instructions to push the branch:

```bash
git push origin gh-pages
git checkout main
```

### Step 3: Verify Workflows

All workflows are already configured! They will automatically run on:
- Push to `main` or `develop`
- Pull requests
- Tag creation
- Manual trigger

### Step 4: Create Your First Release

Option A: **Automatic (Recommended)**
```bash
# Just merge to main - automatically creates patch release
git checkout main
git merge your-feature-branch
git push origin main
# → Creates v0.1.37 (if current is v0.1.36)
```

Option B: **Manual Script**
```bash
./.github/scripts/create-release.sh 0.2.0 minor
```

Option C: **GitHub Actions UI**
1. Go to **Actions** → **Release**
2. Click **Run workflow**
3. Enter version and type
4. Click **Run workflow**

## 📊 What Gets Automated

### On Every Push/PR
- ✅ Python tests (pytest on 3.11 & 3.12)
- ✅ Frontend build and tests
- ✅ CLI build and tests
- ✅ Code linting (ruff, black, isort)
- ✅ Security scanning (bandit, safety)
- ✅ Docker build test
- ✅ Helm chart validation

### On Push to Main
- 🐳 Docker image built and pushed to `ghcr.io`
- 🚀 Automatic patch release created
- 📝 CHANGELOG.md updated
- 🏷️ Git tag created
- 📢 GitHub Release published

### On Tag Push (v*.*.*)
- 🐳 Docker image with version tag
- ⎈ Helm chart packaged and published
- 📦 Multi-platform builds (amd64, arm64)
- 🔒 Security scan with Trivy

### On Pull Requests
- ✅ Full test suite
- 🔍 Breaking change detection
- 📝 CHANGELOG validation
- 🎨 Code quality checks
- 📚 Documentation checks
- 📊 PR size analysis

### Daily
- 🧹 Stale issue management
- 🤖 Dependabot checks

## 🔧 Configuration

### No Secrets Required!

The workflows use built-in GitHub tokens:
- `GITHUB_TOKEN` - Automatically provided by GitHub
- GitHub Container Registry - Automatic with `packages: write` permission

### Optional: Custom Docker Registry

To use a different registry (e.g., Docker Hub):

1. Add registry credentials as secrets:
   - Go to **Settings** → **Secrets and variables** → **Actions**
   - Add `DOCKER_USERNAME` and `DOCKER_PASSWORD`

2. Update `.github/workflows/docker.yml`:
   ```yaml
   env:
     REGISTRY: docker.io  # or your registry
     IMAGE_NAME: your-org/runai-agent
   ```

## 📈 Monitoring

### View Workflow Status

- **All Workflows**: https://github.com/YOUR_ORG/runai-agent/actions
- **Security Alerts**: https://github.com/YOUR_ORG/runai-agent/security
- **Packages**: https://github.com/orgs/YOUR_ORG/packages

### Status Badges

Add to your README (already included):

```markdown
[![Tests](https://github.com/YOUR_ORG/runai-agent/workflows/Test%20Suite/badge.svg)](https://github.com/YOUR_ORG/runai-agent/actions/workflows/test.yml)
[![Docker](https://github.com/YOUR_ORG/runai-agent/workflows/Build%20and%20Push%20Docker%20Image/badge.svg)](https://github.com/YOUR_ORG/runai-agent/actions/workflows/docker.yml)
```

## 🎨 Customization

### Adjust Test Requirements

Edit `.github/workflows/test.yml`:

```yaml
strategy:
  matrix:
    python-version: ['3.11', '3.12']  # Add more versions
```

### Change Release Behavior

Edit `.github/workflows/release.yml`:

```yaml
# Auto-increment behavior
- name: Calculate next version
  run: |
    # Modify version calculation logic
```

### Modify Helm Repository URL

Update in `.github/workflows/helm-publish.yml`:

```yaml
helm repo index . --url https://YOUR_ORG.github.io/runai-agent
```

## 🐛 Troubleshooting

### Workflow Fails

1. **Check the logs**:
   - Go to Actions tab
   - Click on failed workflow
   - Review error messages

2. **Common issues**:
   - **Docker build fails**: Check Dockerfile syntax
   - **Tests fail**: Run locally first
   - **Helm publish fails**: Ensure gh-pages branch exists

### GitHub Pages Not Working

1. Verify branch exists: `git branch -r | grep gh-pages`
2. Check Settings → Pages is configured
3. Wait 5-10 minutes for initial deployment
4. Visit: https://YOUR_ORG.github.io/runai-agent

### Docker Image Not Pushing

1. Check package permissions:
   - Go to package settings
   - Ensure repository has write access
2. Verify GITHUB_TOKEN has `packages: write` permission

### Release Not Created

1. Check if version already exists: `git tag -l`
2. Verify CHANGELOG.md format is correct
3. Check workflow logs for errors

## 📚 Workflow Details

### Test Suite (`test.yml`)
- **Triggers**: Push, PR
- **Duration**: ~5-10 minutes
- **Artifacts**: Test results, coverage reports

### Docker Build (`docker.yml`)
- **Triggers**: Push to main, tags
- **Duration**: ~15-20 minutes
- **Output**: Multi-platform images in ghcr.io

### Release (`release.yml`)
- **Triggers**: Push to main, manual
- **Duration**: ~20-30 minutes
- **Output**: GitHub Release, Docker images, Helm chart

### Helm Publish (`helm-publish.yml`)
- **Triggers**: Tags, release workflow
- **Duration**: ~2-3 minutes
- **Output**: Updated Helm repository

### PR Validation (`pr-validation.yml`)
- **Triggers**: Pull requests
- **Duration**: ~10-15 minutes
- **Output**: Validation report in PR

## 🔒 Security

### Automated Security Scanning

- **Bandit**: Python code security
- **Safety**: Python dependency vulnerabilities
- **Trivy**: Docker image vulnerabilities
- **Dependabot**: Automated dependency updates

### Security Alerts

View in: **Security** tab → **Code scanning alerts**

### Dependabot Configuration

Edit `.github/dependabot.yml` to customize:
- Update frequency
- Number of open PRs
- Auto-merge rules

## 📖 Best Practices

### Before Merging PR

1. ✅ Update CHANGELOG.md under `[Unreleased]`
2. ✅ All tests pass
3. ✅ Code is formatted and linted
4. ✅ Documentation is updated
5. ✅ PR template checklist completed

### Creating Releases

1. **Patch** (0.0.x): Bug fixes, minor improvements
2. **Minor** (0.x.0): New features, non-breaking changes
3. **Major** (x.0.0): Breaking changes

### Versioning Strategy

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Breaking changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes (backwards compatible)

## 🚀 Advanced Usage

### Manual Docker Build

```bash
# Trigger workflow manually
gh workflow run docker.yml -f tag=custom-tag
```

### Manual Release

```bash
# Using script
./.github/scripts/create-release.sh 1.0.0 major

# Using GitHub CLI
gh workflow run release.yml -f version=1.0.0 -f release_type=major
```

### Skip CI for Commits

Add to commit message:
```bash
git commit -m "docs: update README [skip ci]"
```

### Test Workflows Locally

Using [act](https://github.com/nektos/act):
```bash
# Install act
brew install act  # macOS

# Run test workflow
act -j python-tests
```

## 📞 Getting Help

- **Workflow Issues**: Check [workflow README](.github/workflows/README.md)
- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **Project Issues**: https://github.com/YOUR_ORG/runai-agent/issues

## ✅ Verification Checklist

After setup, verify:

- [ ] GitHub Pages is enabled and accessible
- [ ] `gh-pages` branch exists
- [ ] Test workflow runs on PR
- [ ] Docker workflow runs on push to main
- [ ] Helm repository is accessible
- [ ] Status badges appear in README
- [ ] Dependabot is creating PRs
- [ ] Security scanning is active

## 🎉 You're All Set!

Your CI/CD pipeline is now fully automated. Every push, PR, and release will be automatically tested, built, and deployed.

### Quick Reference

```bash
# Create feature
git checkout -b feature/my-feature
# ... make changes ...
git commit -m "feat: add my feature"
git push origin feature/my-feature
# → Creates PR, runs tests

# Merge to main
git checkout main
git merge feature/my-feature
git push origin main
# → Creates release, builds Docker, publishes Helm

# Use Helm chart
helm repo add runai-agent https://YOUR_ORG.github.io/runai-agent
helm install runai-agent runai-agent/runai-agent
```

---

**Questions?** Open an issue or check the [workflows README](.github/workflows/README.md).
