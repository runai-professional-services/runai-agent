# CI/CD Quick Reference

## 🚀 Common Tasks

### Create a Release

**Automatic (Recommended):**
```bash
git checkout main
git merge feature-branch
git push origin main
# → Auto-creates v0.1.37 (if current is v0.1.36)
```

**Manual:**
```bash
./.github/scripts/create-release.sh 0.2.0 minor
```

**GitHub UI:**
```
Actions → Release → Run workflow
```

---

### Build Docker Image

**Automatic:**
```bash
git push origin main  # Builds on every push
```

**Manual:**
```bash
gh workflow run docker.yml -f tag=custom-tag
```

---

### Publish Helm Chart

**Automatic:**
```bash
git tag v0.1.37
git push origin v0.1.37  # Auto-publishes
```

**Use Published Chart:**
```bash
helm repo add runai-agent https://runai-professional-services.github.io/runai-agent
helm install runai-agent runai-agent/runai-agent
```

---

### Update CHANGELOG

Before merging PR:
```markdown
## [Unreleased]

### Added
- New feature description

### Fixed
- Bug fix description
```

---

### Run Tests Locally

**Python:**
```bash
cd runai-agent
pytest tests/ -v
```

**Frontend:**
```bash
cd apps/runai-agent-test-frontend
npm test
```

**Linting:**
```bash
cd runai-agent/src
black .
isort .
ruff check .
```

---

### Check Workflow Status

**All Workflows:**
```
https://github.com/YOUR_ORG/runai-agent/actions
```

**Specific Workflow:**
```bash
gh run list --workflow=test.yml
gh run watch  # Watch latest run
```

---

### Pull Docker Image

```bash
docker pull ghcr.io/runai-professional-services/runai-agent:latest
docker pull ghcr.io/runai-professional-services/runai-agent:v0.1.36
```

---

### Skip CI

```bash
git commit -m "docs: update README [skip ci]"
```

---

## 📊 Workflow Triggers

| Workflow | Trigger | Duration |
|----------|---------|----------|
| Test Suite | Push, PR | ~5-10 min |
| Docker Build | Push to main, tags | ~15-20 min |
| Release | Push to main, manual | ~20-30 min |
| Helm Publish | Tags | ~2-3 min |
| PR Validation | PRs | ~10-15 min |

---

## 🔧 Setup Commands

**Initialize Helm Repo:**
```bash
./.github/scripts/setup-helm-repo.sh
git push origin gh-pages
```

**Enable GitHub Pages:**
```
Settings → Pages → gh-pages branch
```

---

## 📝 Version Bumping

**Semantic Versioning:**
- `0.0.x` - Patch (bug fixes)
- `0.x.0` - Minor (new features)
- `x.0.0` - Major (breaking changes)

**Auto-increment:**
- Merge to main → patch bump
- Manual release → specify version

---

## 🐛 Troubleshooting

**Tests fail:**
```bash
# Run locally first
cd runai-agent && pytest tests/ -v
```

**Docker build fails:**
```bash
# Test locally
./deploy/build-docker.sh
```

**Helm chart fails:**
```bash
# Lint locally
helm lint ./deploy/helm/runai-agent
```

**GitHub Pages not working:**
```bash
# Check branch exists
git branch -r | grep gh-pages

# Verify in Settings → Pages
```

---

## 📚 Documentation

- **Setup Guide**: `.github/CI_CD_SETUP.md`
- **Workflows**: `.github/workflows/README.md`
- **Contributing**: `.github/CONTRIBUTING.md`
- **Summary**: `CI_CD_SUMMARY.md`

---

## 🎯 PR Checklist

Before submitting PR:
- [ ] Update CHANGELOG.md
- [ ] Tests pass locally
- [ ] Code formatted (black, isort)
- [ ] Code linted (ruff)
- [ ] Documentation updated
- [ ] PR template filled out

---

## 🔒 Security

**View Security Alerts:**
```
Security tab → Code scanning alerts
```

**Update Dependencies:**
```bash
# Dependabot creates PRs automatically
# Or manually:
cd runai-agent && pip install -U -e ".[dev]"
```

---

## 📦 Artifacts

**Docker Images:**
```
ghcr.io/runai-professional-services/runai-agent:latest
ghcr.io/runai-professional-services/runai-agent:v*.*.*
ghcr.io/runai-professional-services/runai-agent:main-sha
```

**Helm Repository:**
```
https://runai-professional-services.github.io/runai-agent
```

**GitHub Releases:**
```
https://github.com/runai-professional-services/runai-agent/releases
```

---

## 🎨 Status Badges

```markdown
[![Tests](https://github.com/YOUR_ORG/runai-agent/workflows/Test%20Suite/badge.svg)](...)
[![Docker](https://github.com/YOUR_ORG/runai-agent/workflows/Build%20and%20Push%20Docker%20Image/badge.svg)](...)
[![Release](https://github.com/YOUR_ORG/runai-agent/workflows/Release/badge.svg)](...)
[![Helm](https://github.com/YOUR_ORG/runai-agent/workflows/Publish%20Helm%20Chart/badge.svg)](...)
```

---

**Need more help?** See `.github/CI_CD_SETUP.md`
