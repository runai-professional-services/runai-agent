# GitHub Actions Workflows

This directory contains automated CI/CD workflows for the RunAI Agent project.

## 📋 Workflows Overview

### 🧪 `test.yml` - Test Suite
**Triggers:** Push to main/develop, Pull Requests

Runs comprehensive test suite including:
- **Python Tests**: pytest across Python 3.11 and 3.12
- **Python Linting**: ruff, black, isort
- **Security Scanning**: bandit, safety
- **Frontend Tests**: Next.js build and tests
- **CLI Tests**: TypeScript build and tests
- **Docker Build Test**: Validates Dockerfile builds
- **Helm Linting**: Validates Helm chart

**Status Badge:**
```markdown
![Tests](https://github.com/runai-professional-services/runai-agent/workflows/Test%20Suite/badge.svg)
```

---

### 🐳 `docker.yml` - Build and Push Docker Image
**Triggers:** Push to main, Version tags (`v*.*.*`), Manual dispatch

Builds and publishes Docker images to GitHub Container Registry:
- Multi-platform builds (amd64, arm64)
- Automated tagging (latest, version, sha)
- Security scanning with Trivy
- Results uploaded to GitHub Security tab

**Images Published:**
- `ghcr.io/runai-professional-services/runai-agent:latest`
- `ghcr.io/runai-professional-services/runai-agent:v0.1.36`
- `ghcr.io/runai-professional-services/runai-agent:main-sha`

**Status Badge:**
```markdown
![Docker](https://github.com/runai-professional-services/runai-agent/workflows/Build%20and%20Push%20Docker%20Image/badge.svg)
```

---

### 🚀 `release.yml` - Automated Release
**Triggers:** Push to main (auto-patch), Manual dispatch (specify version)

Automated release workflow:
1. ✅ Runs full test suite
2. 📦 Calculates next version (auto-increment patch or manual)
3. 📝 Generates changelog from commits
4. 🔖 Updates `pyproject.toml`, `Chart.yaml`, and `CHANGELOG.md`
5. 🏷️ Creates Git tag
6. 📢 Creates GitHub Release with notes
7. 🐳 Triggers Docker image build
8. ⎈ Publishes Helm chart

**Manual Release:**
```bash
# Go to GitHub Actions → Release → Run workflow
# Choose version and release type (patch/minor/major)
```

**Status Badge:**
```markdown
![Release](https://github.com/runai-professional-services/runai-agent/workflows/Release/badge.svg)
```

---

### ⎈ `helm-publish.yml` - Publish Helm Chart
**Triggers:** Version tags, Release workflow, Manual dispatch

Publishes Helm chart to GitHub Pages:
- Packages Helm chart
- Updates Helm repository index
- Publishes to `gh-pages` branch
- Accessible at: `https://runai-professional-services.github.io/runai-agent`

**Usage:**
```bash
# Add Helm repository
helm repo add runai-agent https://runai-professional-services.github.io/runai-agent

# Update repository cache
helm repo update

# Install chart
helm install runai-agent runai-agent/runai-agent --version 0.1.0
```

**Status Badge:**
```markdown
![Helm](https://github.com/runai-professional-services/runai-agent/workflows/Publish%20Helm%20Chart/badge.svg)
```

---

### ✅ `pr-validation.yml` - Pull Request Validation
**Triggers:** Pull Requests to main/develop

Comprehensive PR validation:
- ✅ Full test suite
- 🔍 Breaking change detection
- 📝 CHANGELOG.md validation
- 🎨 Code quality checks (black, isort, ruff)
- 📚 Documentation checks for new functions
- 📊 PR size analysis
- 📋 Summary report in PR

**Automated Checks:**
- Function signature changes
- Workflow configuration changes
- New functions without documentation
- Code formatting issues
- Import sorting

---

### 🤖 `dependabot-auto-merge.yml` - Dependabot Auto-Merge
**Triggers:** Dependabot Pull Requests

Automatically merges Dependabot PRs for:
- Patch version updates
- Minor version updates

Major version updates require manual review.

---

### 🧹 `stale.yml` - Stale Issue Management
**Triggers:** Daily at midnight, Manual dispatch

Automatically manages stale issues and PRs:
- Marks issues stale after 30 days of inactivity
- Closes stale issues after 7 more days
- Exempts `pinned` and `security` labels

---

## 🔧 Configuration Files

### `.github/dependabot.yml`
Automated dependency updates for:
- Python dependencies (`/runai-agent`)
- Frontend dependencies (`/apps/runai-agent-test-frontend`)
- CLI dependencies (`/runai-cli`)
- GitHub Actions
- Docker base images

### `.github/PULL_REQUEST_TEMPLATE.md`
PR template with comprehensive checklist for:
- Change description
- Type of change
- Testing verification
- Documentation updates
- New function checklist

### `.github/ISSUE_TEMPLATE/`
Issue templates for:
- Bug reports
- Feature requests

---

## 📊 Setting Up CI/CD

### 1. Enable GitHub Pages for Helm Repository

1. Go to **Settings** → **Pages**
2. Set **Source** to "Deploy from a branch"
3. Select **Branch**: `gh-pages` (will be created automatically)
4. Save

### 2. Required Secrets

No additional secrets required! The workflows use:
- `GITHUB_TOKEN` (automatically provided)
- GitHub Container Registry (automatic with `packages: write` permission)

### 3. Initial Helm Repository Setup

Run this once to create the `gh-pages` branch:

```bash
# Create orphan gh-pages branch
git checkout --orphan gh-pages
git rm -rf .
echo "# RunAI Agent Helm Repository" > index.html
echo "Repository URL: https://runai-professional-services.github.io/runai-agent" >> index.html
git add index.html
git commit -m "Initialize Helm repository"
git push origin gh-pages
git checkout main
```

---

## 🚀 Usage Examples

### Creating a Release

#### Automatic (Patch Version)
```bash
# Just merge PR to main - automatically increments patch version
git checkout main
git merge feature-branch
git push
# → Creates release v0.1.37 (if current is v0.1.36)
```

#### Manual (Specific Version)
```bash
# Go to GitHub Actions → Release → Run workflow
# Inputs:
#   - version: 0.2.0
#   - release_type: minor
```

### Building Docker Image Manually
```bash
# Go to GitHub Actions → Build and Push Docker Image → Run workflow
# Input:
#   - tag: custom-tag
```

### Updating CHANGELOG

Before merging PR, update `CHANGELOG.md`:

```markdown
## [Unreleased]

### Added
- New feature: proactive monitoring with Slack alerts

### Fixed
- Bug in job status parsing
```

The release workflow will automatically:
1. Move unreleased changes to new version section
2. Add release date
3. Update version comparison links

---

## 🐛 Troubleshooting

### Docker Build Fails
- Check `deploy/Dockerfile` syntax
- Verify all COPY paths exist
- Review build logs in Actions tab

### Helm Chart Fails to Publish
- Ensure `gh-pages` branch exists
- Check GitHub Pages is enabled in Settings
- Verify Chart.yaml has correct version

### Tests Fail
- Run tests locally first: `cd runai-agent && pytest tests/`
- Check for missing dependencies
- Review test logs in Actions artifacts

### Release Workflow Fails
- Ensure CHANGELOG.md exists and is valid
- Check version format in pyproject.toml
- Verify no uncommitted changes

---

## 📈 Monitoring

### GitHub Actions Dashboard
View all workflow runs: https://github.com/runai-professional-services/runai-agent/actions

### Security Alerts
View security findings: https://github.com/runai-professional-services/runai-agent/security

### Container Registry
View published images: https://github.com/orgs/runai-professional-services/packages?repo_name=runai-agent

### Helm Repository
View published charts: https://runai-professional-services.github.io/runai-agent

---

## 🔒 Security

All workflows run in GitHub's secure environment:
- Secrets are encrypted
- Limited permissions (least privilege)
- Audit logs available
- Dependabot security updates

---

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Build Documentation](https://docs.docker.com/build/ci/github-actions/)
- [Helm Chart Repository Guide](https://helm.sh/docs/topics/chart_repository/)
- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
