#!/bin/bash
# Usage:
## Deploys to dev only, by pushing a release-dev-* tag.
## preprod and prod both deploy automatically on merge to main (see
## deploy-main.yml), and can also be deployed manually via workflow_dispatch in
## GitHub Actions, referencing a published release tag.
BRANCH=$(git rev-parse --abbrev-ref HEAD)
CURRENT_USER=$(whoami)
TIMESTAMP=$(date +%d-%m-%y--%H%M%S)
TAG_NAME="release-dev-$BRANCH-$CURRENT_USER-$TIMESTAMP"

echo "Current branch name is" "$BRANCH"
echo "Deploying to dev"
echo "Timestamp assigned will be $TIMESTAMP"
echo "New tag name will be " "$TAG_NAME"

##
echo "Removing Local tags"
git tag -d $(git tag -l)

# Command to run
echo "Applying local tag" && \
git tag "$TAG_NAME" && \
echo "Pushing tag" && \
git push origin $TAG_NAME
