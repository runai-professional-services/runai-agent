#!/bin/bash
set -e

# Script to manually create a release
# Usage: ./create-release.sh [version] [release_type]
# Example: ./create-release.sh 0.2.0 minor

VERSION=$1
RELEASE_TYPE=${2:-patch}

if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version> [release_type]"
    echo "Example: $0 0.2.0 minor"
    echo ""
    echo "Release types: patch, minor, major"
    exit 1
fi

echo "=========================================="
echo "Creating Release v$VERSION"
echo "=========================================="
echo ""

# Check if we're on main branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "⚠️  Warning: You are not on the main branch (current: $CURRENT_BRANCH)"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo "❌ Error: You have uncommitted changes"
    echo "Please commit or stash them before creating a release"
    exit 1
fi

# Pull latest changes
echo "Pulling latest changes..."
git pull origin $CURRENT_BRANCH

# Update version in pyproject.toml
echo "Updating version in pyproject.toml..."
sed -i.bak "s/version = \".*\"/version = \"$VERSION\"/" runai-agent/pyproject.toml
rm runai-agent/pyproject.toml.bak

# Update version in Chart.yaml
echo "Updating version in Chart.yaml..."
sed -i.bak "s/appVersion: \".*\"/appVersion: \"$VERSION\"/" deploy/helm/runai-agent/Chart.yaml
rm deploy/helm/runai-agent/Chart.yaml.bak

# Generate changelog entry
echo "Generating changelog..."
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")
if [ -z "$LAST_TAG" ]; then
    COMMITS=$(git log --pretty=format:"- %s (%h)" --no-merges)
else
    COMMITS=$(git log ${LAST_TAG}..HEAD --pretty=format:"- %s (%h)" --no-merges)
fi

CHANGELOG_ENTRY="## [$VERSION] - $(date +%Y-%m-%d)

### Changed
$COMMITS
"

# Update CHANGELOG.md
echo "Updating CHANGELOG.md..."
# Insert after [Unreleased] section
awk -v entry="$CHANGELOG_ENTRY" '
    /## \[Unreleased\]/ { print; print ""; print entry; next }
    { print }
' CHANGELOG.md > CHANGELOG.md.tmp
mv CHANGELOG.md.tmp CHANGELOG.md

# Commit changes
echo "Committing version bump..."
git add runai-agent/pyproject.toml deploy/helm/runai-agent/Chart.yaml CHANGELOG.md
git commit -m "chore: bump version to $VERSION"

# Create tag
echo "Creating tag v$VERSION..."
git tag -a "v$VERSION" -m "Release v$VERSION"

# Push changes
echo ""
echo "Ready to push changes!"
echo ""
echo "Run the following commands to complete the release:"
echo ""
echo "  git push origin $CURRENT_BRANCH"
echo "  git push origin v$VERSION"
echo ""
echo "This will trigger:"
echo "  - GitHub Release creation"
echo "  - Docker image build and push"
echo "  - Helm chart publishing"
echo ""
read -p "Push now? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push origin $CURRENT_BRANCH
    git push origin v$VERSION
    echo ""
    echo "✅ Release v$VERSION created successfully!"
    echo ""
    echo "View the release at:"
    echo "https://github.com/runai-professional-services/runai-agent/releases/tag/v$VERSION"
    echo ""
    echo "Monitor the workflows at:"
    echo "https://github.com/runai-professional-services/runai-agent/actions"
else
    echo ""
    echo "Changes committed and tagged locally but not pushed."
    echo "To push later, run:"
    echo "  git push origin $CURRENT_BRANCH"
    echo "  git push origin v$VERSION"
fi
