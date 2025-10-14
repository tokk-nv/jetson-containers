#---
# name: python
# group: build
# depends: [build-essential, pip_cache]
# notes: installs core `python3` packages and `pip`
#---
ARG BASE_IMAGE
FROM ${BASE_IMAGE}

ARG PYTHON_VERSION \
    PIP_CONSTRAINT_PATH \
    TMP=/tmp/python

ENV PYTHON_VERSION=${PYTHON_VERSION} \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=true \
    PIP_CACHE_PURGE=true \
    PIP_ROOT_USER_ACTION=ignore \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_WHEEL_DIR=/opt/wheels \
    PIP_VERBOSE=1 \
    TWINE_NON_INTERACTIVE=1 \
    DEBIAN_FRONTEND=noninteractive \
    PATH=/opt/venv/bin:$PATH \
    PIP_CONSTRAINT=${PIP_CONSTRAINT_PATH} \
    UV_CONSTRAINT=${PIP_CONSTRAINT_PATH} \
    UV_BUILD_CONSTRAINT=${PIP_CONSTRAINT_PATH} \
    PIP_APPEND_CONSTRAINT=${TMP}/pip-append-constraint.sh \
    UV_PYTHON=/opt/venv/bin/python

# uv constraints are not 100% aligned with pip, sow we need to set
# UV_CONSTRAINT and UV_BUILD_CONSTRAINT: https://docs.astral.sh/uv/pip/compatibility/#build-constraints
# Usage:
# ${PIP_APPEND_CONSTRAINT} <pip-pkg-name>

COPY *.sh $TMP/

RUN $TMP/install.sh
