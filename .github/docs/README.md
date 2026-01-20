# GitHub Documentation

This directory contains documentation for CI/CD, workflows, and development tooling.

## 📚 Documentation Files

### [CI_CD_SUMMARY.md](./CI_CD_SUMMARY.md)
**CI/CD Implementation Overview**

High-level overview of the complete CI/CD implementation:
- What was built and why
- Architecture and design decisions
- Workflow descriptions
- Feature highlights
- Best practices applied

**When to use:** Understanding the overall CI/CD system architecture and capabilities.

---

### [CI_CD_SETUP.md](./CI_CD_SETUP.md)
**Complete CI/CD Setup Guide**

Comprehensive guide covering:
- Initial setup and configuration
- Workflow architecture and design
- Security and permissions
- Troubleshooting common issues
- Advanced configuration

**When to use:** Setting up CI/CD from scratch or understanding the complete system.

---

### [ACT_TESTING.md](./ACT_TESTING.md)
**Local Workflow Testing with `act`**

Guide for testing GitHub Actions workflows locally before pushing:
- Installation and setup
- Testing commands and patterns
- Debugging failed workflows
- Best practices

**When to use:** Before pushing workflow changes, to validate syntax and behavior locally.

---

### [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)
**CI/CD Quick Reference**

Quick reference for common CI/CD tasks:
- Creating releases
- Building Docker images
- Publishing Helm charts
- Running tests
- Troubleshooting commands

**When to use:** Quick lookup for everyday CI/CD tasks.

---

### [ORGANIZATION_SUMMARY.md](./ORGANIZATION_SUMMARY.md)
**Documentation Organization Summary**

Details about how the `.github/` directory is organized:
- Before/after structure
- Organization principles
- Maintenance guidelines

**When to use:** Understanding the repository organization or planning to add new documentation.

---

## 🔗 Related Documentation

### In `.github/` (Root Level)
- **[CONTRIBUTING.md](../CONTRIBUTING.md)** - Contribution guidelines
- **[PULL_REQUEST_TEMPLATE.md](../PULL_REQUEST_TEMPLATE.md)** - PR template
- **[workflows/README.md](../workflows/README.md)** - Detailed workflow documentation

### In Project Root
- **[README.md](../../README.md)** - Main project documentation
- **[CHANGELOG.md](../../CHANGELOG.md)** - Version history
- **[docs/](../../docs/)** - Feature-specific documentation

---

## 🎯 Quick Start

**New to the project?**
1. Read [CI_CD_SUMMARY.md](./CI_CD_SUMMARY.md) for overall understanding
2. Follow [CI_CD_SETUP.md](./CI_CD_SETUP.md) for complete setup
3. Use [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) for daily tasks
4. Reference [../workflows/README.md](../workflows/README.md) for workflow details

**Testing workflow changes?**
1. Read [ACT_TESTING.md](./ACT_TESTING.md)
2. Test locally with `act`
3. Push with confidence

**Looking for something specific?**
- **Releases:** [QUICK_REFERENCE.md](./QUICK_REFERENCE.md#create-a-release)
- **Docker:** [QUICK_REFERENCE.md](./QUICK_REFERENCE.md#build-docker-image)
- **Helm:** [QUICK_REFERENCE.md](./QUICK_REFERENCE.md#publish-helm-chart)
- **Workflows:** [../workflows/README.md](../workflows/README.md)
- **Contributing:** [../CONTRIBUTING.md](../CONTRIBUTING.md)

---

## 📖 Documentation Organization

```
.github/
├── docs/                           # ← You are here
│   ├── README.md                  # This file
│   ├── CI_CD_SETUP.md            # Complete setup guide
│   ├── ACT_TESTING.md            # Local workflow testing
│   └── QUICK_REFERENCE.md        # Quick reference
├── workflows/                      # Workflow files
│   ├── README.md                 # Workflow documentation
│   ├── release.yml               # Release workflow
│   ├── test.yml                  # Test suite
│   ├── docker.yml                # Docker build
│   ├── helm-publish.yml          # Helm publishing
│   └── pr-validation.yml         # PR validation
├── scripts/                        # Automation scripts
│   ├── create-release.sh         # Release helper
│   └── setup-helm-repo.sh        # Helm repo setup
├── ISSUE_TEMPLATE/                # Issue templates
├── CONTRIBUTING.md                # Contribution guide
├── PULL_REQUEST_TEMPLATE.md      # PR template
└── dependabot.yml                # Dependabot config
```

---

## 🤝 Contributing to Documentation

When updating documentation:

1. **Keep it accurate** - Test commands before documenting
2. **Use examples** - Show, don't just tell
3. **Update cross-references** - Keep links up to date
4. **Follow formatting** - Use emojis, headers, code blocks consistently
5. **Update this README** - If adding new docs, add them here

---

## 📝 Documentation Style Guide

### Headers
- Use emojis in main headers for visual scanning
- Keep headers concise and descriptive

### Code Blocks
- Always specify language for syntax highlighting
- Include comments for complex commands
- Show both input and expected output when relevant

### Links
- Use relative links within the repository
- Use descriptive link text, not "click here"
- Verify links work after reorganizing files

### Examples
- Provide real-world examples
- Show common use cases first
- Include troubleshooting for common issues

---

**Need help?** Open an issue or reach out to the team!
