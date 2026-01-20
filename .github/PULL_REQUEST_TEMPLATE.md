# Pull Request

## Description
<!-- Provide a brief description of the changes in this PR -->

## Type of Change
<!-- Mark with an 'x' all that apply -->

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] 🔧 Configuration change
- [ ] ♻️ Code refactoring
- [ ] ⚡ Performance improvement
- [ ] ✅ Test update

## Changes Made
<!-- Describe the changes you've made in detail -->

## Related Issue
<!-- Link to the issue this PR addresses, if applicable -->
Fixes #(issue number)

## Testing
<!-- Describe the tests you ran to verify your changes -->

- [ ] Tested locally with `./deploy/start-local.sh`
- [ ] Python tests pass (`cd runai-agent && pytest tests/`)
- [ ] Frontend builds successfully (`cd apps/runai-agent-test-frontend && npm run build`)
- [ ] Docker image builds successfully
- [ ] Helm chart lints successfully (`helm lint ./deploy/helm/runai-agent`)

## Checklist
<!-- Mark with an 'x' all that you have completed -->

- [ ] My code follows the style guidelines of this project (see cursor rules)
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] I have updated the CHANGELOG.md file under `[Unreleased]`
- [ ] My changes generate no new warnings or errors
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## For New Agent Functions
<!-- If you added a new agent function, complete this section -->

- [ ] Function follows the template pattern in cursor rules
- [ ] Function is registered in `functions/__init__.py`
- [ ] Function is added to `workflow.yaml` with description
- [ ] Function has appropriate error handling and logging
- [ ] Function has security checks (credentials, project whitelisting)
- [ ] Function has user-friendly formatted responses with emojis
- [ ] Tests are written for the new function
- [ ] README.md is updated with usage examples
- [ ] Documentation created in `docs/` if complex

## Screenshots/Demo
<!-- If applicable, add screenshots or demo videos -->

## Additional Notes
<!-- Add any additional notes or context about the PR -->

## Deployment Notes
<!-- Any special deployment considerations? -->

---

**By submitting this pull request, I confirm that my contribution is made under the terms of the project's license.**
