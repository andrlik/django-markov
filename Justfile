set dotenv-load := true

# Lists all available commands
help:
    just --list

# ---------------------------------------------- #
# Script to rule them all recipes.               #
# ---------------------------------------------- #

# Install pre-commit hooks
_install-pre-commit: _check-pre-commit
    #!/usr/bin/env bash
    if [[ ! -f .git/hooks/pre-commit ]]; then
      echo "Pre-commit hooks are not installed yet! Doing so now."
      pre-commit install
    fi
    exit 0

# Downloads and installs uv on your system. If on Windows, follow the directions at https://docs.astral.sh/uv/getting-started/installation/ instead.
uv-install:
    #!/usr/bin/env bash
    set -euo pipefail
    if ! command -v uv &> /dev/null;
    then
      echo "uv is not found on path! Starting install..."
      curl -LsSf https://astral.sh/uv/install.sh | sh
    else
      uv self update
    fi

# Update uv
uv-update:
    uv self update

# Uninstall uv
uv-uninstall:
    uv self uninstall

_check-pre-commit:
    #!/usr/bin/env bash
    if ! command -v pre-commit &> /dev/null; then
      echo "Pre-commit is not installed!"
      exit 1
    fi

_check-env:
    #!/usr/bin/env bash
    if [[ -z "$DJANGO_DEBUG" ]]; then
      echo "DJANGO_DEBUG is not set and application will run in production mode." >&2
    fi

# Setup the project and update dependencies.
bootstrap: uv-install _install-pre-commit _check-env
    #!/usr/bin/env bash
    uv sync
    DJANGO_SETTINGS_MODULE="tests.settings" PYTHONPATH="$PYTHONPATH:$(pwd)" uv run django-admin migrate

# Checks that project is ready for development.
check: _check-pre-commit
    #!/usr/bin/env bash
    if ! command -v uv &> /dev/null; then
      echo "uv is not installed!"
      exit 1
    fi
    if [[ ! -f ".venv/bin/python" ]]; then
      echo "Virtualenv is not installed! Run 'just bootstrap' to complete setup."
      exit 1
    fi

# Run just formatter and rye formatter.
fmt: check
    just --fmt --unstable
    uv run -m ruff format

# Run ruff linting
lint: check
    uv run -m ruff check

# Run the test suite
test *ARGS: check
    uv run -m pytest {{ ARGS }}

# Run tox for code style, type checking, and multi-python tests. Uses run-parallel.
tox *ARGS: check
    uvx --python 3.12 --with tox-uv tox run-parallel {{ ARGS }}

# Runs bandit safety checks.
safety: check
    uv run -m bandit -c pyproject.toml -r src

# Access Django management commands.
manage *ARGS: check
    #!/usr/bin/env bash
    DJANGO_SETTINGS_MODULE="tests.settings" PYTHONPATH="$PYTHONPATH:$(pwd)" uv run django-admin {{ ARGS }}

# Run tests in CI.
citest:
    # TODO

# Check types
check-types: check
    uv run -m pyright

# Access mike commands
docs *ARGS: check
    uv run mike {{ ARGS }}

# Build Python package
build *ARGS: check
    uv build {{ ARGS }}

# Deletes pycache directories and files
_pycache-remove:
    find . | grep -E "(__pycache__|\.pyc|\.pyo$$)" | xargs rm -rf

# Removes any build artifacts
_build-remove:
    rm -rf dist/*

# Removes any built docs
_docs-clean:
    rm -rf site/*

# Removes build artifacts
clean: _pycache-remove _build-remove _docs-clean
