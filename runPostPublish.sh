#!/bin/bash

VERSION="$(cat ./version).$BUILD_NUMBER"
TAG="v$VERSION"

if [[ "$GIT_BRANCH" == 'origin/master' ]]; then
    git tag $TAG && git push origin --tags
fi
