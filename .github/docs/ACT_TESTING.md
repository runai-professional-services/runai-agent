# Testing GitHub Workflows Locally with `act`

## Overview
`act` allows you to test GitHub Actions workflows locally using Docker before pushing to GitHub.

## Installation
Already installed at: `/opt/homebrew/bin/act`

## Basic Commands

### List All Workflows and Jobs
```bash
act --list
```

### Dry Run (See what would run)
```bash
# Dry run for push events (default)
act --dryrun

# Dry run for specific workflow
act -W .github/workflows/release.yml --dryrun

# Dry run for specific event
act workflow_dispatch -W .github/workflows/release.yml --dryrun
```

### Run Workflows

#### Test the Release Workflow
```bash
# Test with workflow_dispatch event (manual trigger)
act workflow_dispatch -W .github/workflows/release.yml

# Test specific job only
act workflow_dispatch -W .github/workflows/release.yml -j test

# Test with verbose output
act workflow_dispatch -W .github/workflows/release.yml -v
```

#### Test the Test Suite
```bash
# Run all tests (triggered by push)
act push -W .github/workflows/test.yml

# Run specific test job
act push -W .github/workflows/test.yml -j python-tests
```

#### Test Docker Build
```bash
# Test docker workflow
act push -W .github/workflows/docker.yml

# Test with specific tag
act push -W .github/workflows/docker.yml --env GITHUB_REF=refs/tags/v1.0.0
```

#### Test PR Validation
```bash
# Simulate pull request event
act pull_request -W .github/workflows/pr-validation.yml

# Test specific PR check
act pull_request -W .github/workflows/pr-validation.yml -j tests
```

## Using Secrets

Create a `.secrets` file in the project root (already in .gitignore):

```bash
# .secrets file format
GITHUB_TOKEN=ghp_your_token_here
NVIDIA_API_KEY=nvapi_your_key_here
DOCKERHUB_USERNAME=your_username
DOCKERHUB_TOKEN=your_token
```

Then run with secrets:
```bash
act workflow_dispatch -W .github/workflows/release.yml --secret-file .secrets
```

## Common Options

```bash
# Use specific container architecture (for M-series Macs)
act --container-architecture linux/amd64

# Run in interactive mode (useful for debugging)
act -W .github/workflows/release.yml -j test --interactive

# Reuse containers (faster for repeated runs)
act push -W .github/workflows/test.yml --reuse

# Run only specific job
act push -j python-tests

# Set environment variables
act push --env GITHUB_SHA=abc123 --env GITHUB_REF=refs/heads/main

# Verbose output for debugging
act workflow_dispatch -W .github/workflows/release.yml -v

# Use specific event payload
act workflow_dispatch -W .github/workflows/release.yml --eventpath event.json
```

## Event Types

Common event types you can trigger:
- `push` - Simulates pushing to a branch
- `pull_request` - Simulates creating/updating a PR
- `workflow_dispatch` - Simulates manual workflow trigger
- `release` - Simulates creating a release
- `schedule` - Simulates scheduled workflows

## Workflow-Specific Testing

### Release Workflow
```bash
# Test the entire release process
act workflow_dispatch -W .github/workflows/release.yml --secret-file .secrets

# Test only the test stage
act workflow_dispatch -W .github/workflows/release.yml -j test

# Test release preparation
act workflow_dispatch -W .github/workflows/release.yml -j prepare-release

# Simulate pushing a tag
act push -W .github/workflows/release.yml --env GITHUB_REF=refs/tags/v1.0.0
```

### Test Suite
```bash
# Run all tests
act push -W .github/workflows/test.yml --secret-file .secrets

# Run specific test suites
act push -W .github/workflows/test.yml -j python-tests
act push -W .github/workflows/test.yml -j frontend-tests
act push -W .github/workflows/test.yml -j cli-tests
act push -W .github/workflows/test.yml -j helm-lint
```

### Docker Build
```bash
# Test docker build
act push -W .github/workflows/docker.yml --secret-file .secrets

# Test with tag
act push -W .github/workflows/docker.yml \
  --env GITHUB_REF=refs/tags/v1.0.0 \
  --secret-file .secrets
```

### PR Validation
```bash
# Test all PR checks
act pull_request -W .github/workflows/pr-validation.yml

# Test specific checks
act pull_request -W .github/workflows/pr-validation.yml -j tests
act pull_request -W .github/workflows/pr-validation.yml -j code-quality
act pull_request -W .github/workflows/pr-validation.yml -j changelog-check
```

## Limitations

1. **Some GitHub-specific features won't work:**
   - GitHub API calls may need mocking
   - Some actions might not work exactly as on GitHub
   - Secrets management is simplified

2. **Performance:**
   - First run downloads Docker images (can be slow)
   - Use `--reuse` flag for faster subsequent runs

3. **Context differences:**
   - Local environment vs GitHub runners
   - File permissions may differ
   - Some paths may need adjustment

## Debugging Failed Workflows

```bash
# Run with verbose logging
act workflow_dispatch -W .github/workflows/release.yml -v

# Run in interactive mode to inspect
act workflow_dispatch -W .github/workflows/release.yml --interactive

# Check specific step
act workflow_dispatch -W .github/workflows/release.yml -v 2>&1 | grep "specific-step-name"

# Use shell access
act workflow_dispatch -W .github/workflows/release.yml --container-architecture linux/amd64 -v
```

## Before Pushing to GitHub

### Recommended Test Sequence

1. **Test the workflows you changed:**
```bash
# If you changed release.yml
act workflow_dispatch -W .github/workflows/release.yml --dryrun

# If you changed test.yml
act push -W .github/workflows/test.yml -j python-tests
```

2. **Test with secrets (if needed):**
```bash
echo "GITHUB_TOKEN=your_token" > .secrets
act workflow_dispatch -W .github/workflows/release.yml --secret-file .secrets
rm .secrets  # Clean up
```

3. **Verify syntax:**
```bash
# Use GitHub's action validator
act --list  # Will show syntax errors
```

4. **Test critical paths:**
```bash
# Test release workflow without actually releasing
act workflow_dispatch -W .github/workflows/release.yml -j test -j prepare-release
```

## Quick Reference Card

| Task | Command |
|------|---------|
| List all workflows | `act --list` |
| Dry run everything | `act --dryrun` |
| Test release workflow | `act workflow_dispatch -W .github/workflows/release.yml` |
| Test specific job | `act push -j python-tests` |
| Use secrets | `act --secret-file .secrets` |
| Verbose mode | `act -v` |
| Reuse containers | `act --reuse` |
| M-series Mac fix | `act --container-architecture linux/amd64` |

## Tips

1. **Speed up testing:** Use `--reuse` flag to keep containers between runs
2. **Focus testing:** Use `-j job-name` to test only specific jobs
3. **Dry run first:** Always do a `--dryrun` before full execution
4. **Check syntax:** Run `act --list` to validate workflow syntax
5. **Mock secrets:** Use dummy values for testing non-critical workflows

## Resources

- act documentation: https://github.com/nektos/act
- GitHub Actions docs: https://docs.github.com/en/actions
