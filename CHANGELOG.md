# Changelog

All notable changes to the RunAI Agent project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.49] - 2026-03-11

### Changed
- Hotfix/workspaces (#80) (59ca437)


## [0.1.48] - 2026-03-10

### Changed
- Feature/nim inference (#79) (ffd5e14)


## [0.1.47] - 2026-03-09

### Changed
- Hotfix/require confirm (#78) (f662fa2)
- fix(ci): anchor grep to start of line in helm-publish version extraction (a569c90)


## [0.1.46] - 2026-03-05

### Changed
- Feature/mcp server (#77) (d87a565)


## [0.1.45] - 2026-02-10

### Changed
- feat: cluster resource summary tool + example prompts in next steps (#73) (2746449)
- fix: pass release ref to Docker build so image is tagged with release version (#72) (633240d)


## [0.1.44] - 2026-02-07

### Changed
- chore: add test script to package.json (4668ce0)
- feat: add NVIDIA NIM LLM benchmarking support (c20aa89)
- fix: scope buildx cache by commit SHA so image matches tag (#70) (80eefd4)


## [0.1.43] - 2026-02-06

### Changed
- Feature/job performance (#69) (70a33e4)
- chore: trigger Docker build for version 0.1.42 (5dc9fb8)


## [0.1.42] - 2026-02-03

### Changed
- fix: make kubectl installation more robust for docker/build-push-acti… (#68) (5787a65)
- build(deps): bump the github-actions group with 5 updates (#64) (cd91f04)


## [0.1.41] - 2026-01-31

### Changed
- Fix/dockerfile (#61) (216b6aa)


## [0.1.40] - 2026-01-29

### Changed
- Fix/helm image (#60) (987124d)


## [0.1.39] - 2026-01-29

### Changed
- fix: reduce Dependabot noise and workflow runs (#42) (6af834f)
- build(deps): bump actions/setup-node from 4 to 6 (#34) (623d3db)
- build(deps): bump next-i18next in /apps/runai-agent-test-frontend (#33) (59e502e)
- build(deps): bump actions/stale from 9 to 10 (#31) (0a75d72)
- build(deps): bump actions/upload-artifact from 4 to 6 (#29) (0acb6b9)
- build(deps): bump github/codeql-action from 3 to 4 (#28) (99699ae)
- build(deps): bump axios from 1.13.2 to 1.13.3 in /runai-cli (#38) (a5f2039)
- build(deps): bump python from 3.12-slim to 3.14-slim in /deploy (#30) (212e9af)
- fix: Ensure Helm chart publishes with correct version (#27) (fc9efcf)


## [0.1.38] - 2026-01-23

### Changed
- Fix/helm publish git config (#26) (5a58d43)


## [0.1.37] - 2026-01-23

### Changed
- Fix/workflow changelog (#25) (42c3f32)
- fix: GitHub Actions workflows and release pipeline improvements (329e8ac)
- build(deps-dev): bump prettier-plugin-tailwindcss (#17) (40fc75a)
- build(deps): bump python from 3.11-slim to 3.14-slim in /deploy (#5) (f8aee45)
- Feature/GitHub actions (#2) (5cb8227)
- feat: enhance failure statistics and add job listing capability (a301263)
- First Commit (1f4a509)
- Initial commit (4ae5063)


### Added
- CI/CD automation with GitHub Actions
- Automated Docker image building and publishing
- Automated Helm chart publishing to GitHub Pages
- Automated release workflow with changelog generation
- Comprehensive testing pipeline

## [0.1.36] - 2026-01-14

### Added
- 🤖 Intelligent agent powered by NVIDIA Llama 3.3 Nemotron Super (49B) with ReAct reasoning
- 💬 Modern web UI with real-time streaming responses
- 🔧 Run:AI cluster integration with specialized tools
- 🚀 Direct job submission with safety validations
- 📦 Batch job submission (training, distributed, workspace)
- 🔄 Unified lifecycle management (suspend, resume, delete)
- 🔔 Proactive monitoring with auto-troubleshooting and Slack alerts
- 🔬 Advanced failure analysis with pattern recognition
- 🗑️ Two-step confirmation for destructive operations
- ⚡ Template-based API executor for datasource management (20-50x faster)
- 🔍 Job status and kubectl diagnostics
- 🩺 Deep troubleshooting with pod logs and AI-powered diagnosis
- 📚 Documentation search for Run:AI features
- 🧠 Optional agent reasoning view for debugging
- 🔒 Auto-configuration for Run:AI environments
- 🌙 Dark/Light theme support

### Infrastructure
- Docker deployment with Nginx reverse proxy
- Helm chart for Kubernetes deployment
- TypeScript CLI for remote connections
- Python 3.11+ backend with FastAPI
- Next.js 14 frontend with TypeScript and Tailwind CSS

### Security
- Project whitelisting for access control
- Environment-based credential management
- SSL verification for API calls
- RBAC support for Kubernetes deployments

---

## Release Types

- **Major** (x.0.0): Breaking changes, major feature additions
- **Minor** (0.x.0): New features, non-breaking changes
- **Patch** (0.0.x): Bug fixes, minor improvements

## Sections

- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements or fixes
- **Infrastructure**: Deployment, CI/CD, or infrastructure changes

[0.1.36]: https://github.com/runai-professional-services/runai-agent/releases/tag/v0.1.36


[0.1.37]: https://github.com/runai-professional-services/runai-agent/releases/tag/v0.1.37

[0.1.38]: https://github.com/runai-professional-services/runai-agent/releases/tag/v0.1.38

[0.1.39]: https://github.com/runai-professional-services/runai-agent/releases/tag/v0.1.39

[0.1.40]: https://github.com/runai-professional-services/runai-agent/releases/tag/v0.1.40

[0.1.41]: https://github.com/runai-professional-services/runai-agent/releases/tag/v0.1.41

[0.1.42]: https://github.com/runai-professional-services/runai-agent/releases/tag/v0.1.42

[0.1.43]: https://github.com/runai-professional-services/runai-agent/releases/tag/v0.1.43

[0.1.44]: https://github.com/runai-professional-services/runai-agent/releases/tag/v0.1.44

[0.1.45]: https://github.com/runai-professional-services/runai-agent/releases/tag/v0.1.45

[0.1.46]: https://github.com/runai-professional-services/runai-agent/releases/tag/v0.1.46

[0.1.47]: https://github.com/runai-professional-services/runai-agent/releases/tag/v0.1.47

[0.1.48]: https://github.com/runai-professional-services/runai-agent/releases/tag/v0.1.48

[Unreleased]: https://github.com/runai-professional-services/runai-agent/compare/v0.1.49...HEAD
[0.1.49]: https://github.com/runai-professional-services/runai-agent/releases/tag/v0.1.49
