set dotenv-load := true

# Lists all available commands
help:
    just --list

# ---------------------------------------------- #
# Script to rule them all recipes.               #
# ---------------------------------------------- #

# Install pre-commit hooks
_install-pre-commit: _check-pre-commit
    pre-commit install

# Downloads and installs rye on your system. If on Windows, download an official release from https://rye-up.com instead.
rye-install:
    #!/usr/bin/env bash
    set -euo pipefail
    if ! command -v rye &> /dev/null;
    then
      echo "Rye is not found on path! Starting install..."
      curl -sSf https://rye-up.com/get | bash
    else
      rye self update
    fi

# Update Rye
rye-update:
    rye self update

# Uninstall Rye
rye-uninstall:
    rye self uninstall

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
bootstrap: rye-install _install-pre-commit _check-env
    rye sync
    rye run django-admin migrate

# Checks that project is ready for development.
check: _check-env _check-pre-commit
    #!/usr/bin/env bash
    if ! command -v rye &> /dev/null; then
      echo "Rye is not installed!"
      exit 1
    fi
    if [[ ! -f ".venv/bin/python" ]]; then
      echo "Virtualenv is not installed! Run 'just bootstrap' to complete setup."
      exit 1
    fi

# Run just formatter and rye formatter.
fmt: check
    just --fmt --unstable
    rye fmt

# Run ruff linting
lint: check
    rye check

# Run the test suite
test *ARGS: check
    rye run pytest {{ ARGS }}

# Runs bandit safety checks.
safety: check
    rye run python -m bandit -c pyproject.toml -r src

# Access Django management commands.
manage *ARGS: check
    #!/usr/bin/env bash
    DJANGO_SETTINGS_MODULE="tests.settings" PYTHONPATH="$PYTHONPATH:$(pwd)" rye run django-admin {{ ARGS }}

# Run tests in CI.
citest:
    # TODO

# Check types
check-types: check
    rye run pyright

# Access mike commands
docs *ARGS: check
    rye run mike {{ ARGS }}

# Build Python package
build *ARGS: check
    rye build {{ ARGS }}

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
