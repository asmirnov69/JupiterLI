#!/bin/sh
set -e

TAG="podman-jupiterli-ready"
REMOTE="origin"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"

echo "Current branch: $BRANCH"
echo "Creating/updating tag: $TAG at HEAD"

# Create or move the tag locally
git tag -f "$TAG"

# Push tag to remote (force update if it already exists)
git push -f "$REMOTE" "refs/tags/$TAG"

echo "Tag '$TAG' now points to HEAD and is pushed to $REMOTE"
