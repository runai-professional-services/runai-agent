# Contributing to RunAI Agent

Thank you for your interest in contributing to the RunAI Agent project! This document provides guidelines and instructions for contributing.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

## Code of Conduct

This project follows a standard code of conduct. Please be respectful and constructive in all interactions.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker
- Git
- NVIDIA API Key
- Run:AI cluster access (for integration testing)

### Development Setup

1. **Clone the repository:**
```bash
git clone https://github.com/runai-professional-services/runai-agent.git
cd runai-agent
```

2. **Set up Python environment:**
```bash
cd runai-agent
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

3. **Set up frontend:**
```bash
cd apps/runai-agent-test-frontend
npm install --legacy-peer-deps
```

4. **Set up CLI:**
```bash
cd runai-cli
npm install
```

5. **Configure environment variables:**
```bash
export NVIDIA_API_KEY="your-nvidia-api-key"
export RUNAI_CLIENT_ID="your-runai-client-id"
export RUNAI_CLIENT_SECRET="your-runai-client-secret"
export RUNAI_BASE_URL="https://your-cluster.run.ai"
```

## Development Workflow

### Branch Strategy

- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/*` - New features
- `bugfix/*` - Bug fixes
- `hotfix/*` - Urgent production fixes

### Creating a Feature

1. **Create a feature branch:**
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes** following the coding standards

3. **Update CHANGELOG.md:**
```markdown
## [Unreleased]

### Added
- Your new feature description
```

4. **Commit your changes:**
```bash
git add .
git commit -m "feat: add your feature description"
```

5. **Push and create PR:**
```bash
git push origin feature/your-feature-name
```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

Examples:
```
feat: add proactive monitoring with Slack alerts
fix: resolve job status parsing error
docs: update Helm chart installation guide
```

## Coding Standards

### Python

Follow the project's cursor rules (see `.cursorrules`):

- **Style**: PEP 8 compliant
- **Formatting**: Use `black` for code formatting
- **Import sorting**: Use `isort`
- **Linting**: Use `ruff`
- **Type hints**: Required for all functions
- **Docstrings**: Google style

**Format your code:**
```bash
cd runai-agent/src
black .
isort .
ruff check . --fix
```

### TypeScript

- **Style**: Follow ESLint rules
- **Formatting**: Use Prettier
- **Types**: Strict TypeScript

**Format your code:**
```bash
cd apps/runai-agent-test-frontend
npm run lint
npm run format
```

### Adding New Agent Functions

Follow the template pattern in `.cursorrules`. Every new function must:

1. ✅ Follow the function template structure
2. ✅ Include proper error handling
3. ✅ Use environment variables for credentials (never hardcode)
4. ✅ Implement project whitelisting
5. ✅ Return user-friendly formatted responses
6. ✅ Include comprehensive logging
7. ✅ Be registered in `functions/__init__.py`
8. ✅ Be added to `workflow.yaml`
9. ✅ Have tests written
10. ✅ Be documented in README.md

See `.cursorrules` for the complete function template.

## Testing

### Python Tests

```bash
cd runai-agent
pytest tests/ -v
```

**Test structure:**
- `tests/unit/` - Unit tests
- `tests/integration/` - Integration tests
- `tests/e2e/` - End-to-end tests

### Frontend Tests

```bash
cd apps/runai-agent-test-frontend
npm test
```

### CLI Tests

```bash
cd runai-cli
npm test
```

### Docker Build Test

```bash
./deploy/build-docker.sh
```

### Helm Chart Test

```bash
helm lint ./deploy/helm/runai-agent
helm template runai-agent ./deploy/helm/runai-agent \
  --set nvidia.apiKey="test" \
  --set runai.clientId="test" \
  --set runai.clientSecret="test" \
  --set runai.baseUrl="https://test.run.ai"
```

## Pull Request Process

### Before Submitting

1. ✅ All tests pass locally
2. ✅ Code is formatted and linted
3. ✅ CHANGELOG.md is updated
4. ✅ Documentation is updated
5. ✅ No linter errors or warnings
6. ✅ Docker image builds successfully
7. ✅ Helm chart lints successfully

### PR Checklist

Use the [PR template](.github/PULL_REQUEST_TEMPLATE.md) which includes:

- Description of changes
- Type of change
- Testing performed
- Documentation updates
- Checklist completion

### Review Process

1. **Automated checks** run on every PR:
   - Full test suite
   - Code quality checks
   - Security scanning
   - Docker build test
   - Helm chart validation

2. **Code review** by maintainers:
   - Code quality and style
   - Test coverage
   - Documentation completeness
   - Security considerations

3. **Approval** required before merge

### After Approval

- PRs to `main` trigger automatic release (patch version)
- PRs to `develop` are integrated for next release

## Release Process

### Automated Release (Recommended)

Merge to `main` automatically creates a patch release:

```bash
git checkout main
git merge feature/your-feature
git push origin main
# → Automatically creates v0.1.37 (if current is v0.1.36)
```

### Manual Release

For minor or major versions:

1. Go to **Actions** → **Release** → **Run workflow**
2. Enter version (e.g., `0.2.0`)
3. Select release type (`minor` or `major`)
4. Click **Run workflow**

### What Happens on Release

1. ✅ Full test suite runs
2. 📦 Version updated in `pyproject.toml` and `Chart.yaml`
3. 📝 CHANGELOG.md updated with release notes
4. 🏷️ Git tag created
5. 📢 GitHub Release created
6. 🐳 Docker image built and pushed
7. ⎈ Helm chart published

## Project Structure

```
runai-agent/
├── .github/              # GitHub Actions workflows and templates
├── apps/
│   └── runai-agent-test-frontend/  # Next.js frontend
├── deploy/
│   ├── Dockerfile        # Combined Docker image
│   ├── helm/
│   │   └── runai-agent/  # Helm chart
│   └── k8s/              # Kubernetes manifests
├── docs/                 # Documentation
├── runai-agent/
│   ├── configs/          # Agent configurations
│   ├── src/
│   │   └── runai_agent/
│   │       ├── functions/  # Agent functions/tools
│   │       └── utils/      # Utilities
│   └── tests/            # Python tests
└── runai-cli/            # TypeScript CLI
```

## Getting Help

- **Issues**: [GitHub Issues](https://github.com/runai-professional-services/runai-agent/issues)
- **Discussions**: [GitHub Discussions](https://github.com/runai-professional-services/runai-agent/discussions)
- **Documentation**: [docs/](../docs/)

## Additional Resources

- [Cursor Rules](.cursorrules) - Complete development guidelines
- [CI/CD Documentation](.github/workflows/README.md) - Workflow details
- [Helm Chart README](../deploy/helm/runai-agent/README.md) - Deployment guide
- [NVIDIA NAT Documentation](https://github.com/NVIDIA/NeMo-Agent-Toolkit) - Agent framework

---

Thank you for contributing to RunAI Agent! 🚀
