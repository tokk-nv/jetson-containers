#!/usr/bin/env bash
set -ex

echo "Building diffusers ${DIFFUSERS_VERSION:-main} ${DIFFUSERS_COMMIT:+at commit $DIFFUSERS_COMMIT}"

# Handle different version formats:
# 1. DIFFUSERS_COMMIT set -> clone full repo and checkout specific commit
# 2. DIFFUSERS_VERSION set -> clone specific branch/tag (works for both)
# 3. Neither set -> clone main branch

if [ -n "${DIFFUSERS_COMMIT}" ]; then
    # Commit hash specified (either standalone or with tag for context)
    if [ -n "${DIFFUSERS_VERSION}" ]; then
        echo "Building from commit ${DIFFUSERS_COMMIT} (after ${DIFFUSERS_VERSION})"
    else
        echo "Building from commit ${DIFFUSERS_COMMIT}"
    fi
    # Clone the repo without depth limit to ensure we can checkout any commit
    git clone --recursive https://github.com/huggingface/diffusers /opt/diffusers
    cd /opt/diffusers
    git checkout ${DIFFUSERS_COMMIT}
    cd /
elif [ -n "${DIFFUSERS_VERSION}" ]; then
    # Branch or tag name specified
    echo "Building from ${DIFFUSERS_VERSION}"
    # Try to clone with specific branch/tag (works for both), fallback to main if not found
    git clone --branch=${DIFFUSERS_VERSION} --depth=1 --recursive https://github.com/huggingface/diffusers /opt/diffusers || \
    git clone --recursive https://github.com/huggingface/diffusers /opt/diffusers
else
    # Default: clone main branch
    echo "No version specified, cloning main branch"
    git clone --recursive https://github.com/huggingface/diffusers /opt/diffusers
fi

cd /opt/diffusers

DIFFUSERS_MORE_DETAILS=1 MAX_JOBS=$(nproc) \
python3 setup.py --verbose bdist_wheel --dist-dir /opt

ls /opt
cd /

uv pip install /opt/diffusers*.whl

twine upload --verbose /opt/diffusers*.whl || echo "failed to upload wheel to ${TWINE_REPOSITORY_URL}"

${PIP_APPEND_CONSTRAINT} diffusers
