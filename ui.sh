#!/usr/bin/env sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
export UV_PROJECT_ENVIRONMENT="$root/.local/ui-venv-linux"
export UV_CACHE_DIR="$root/.local/uv-cache"
export UV_PYTHON_INSTALL_DIR="$root/.local/python"
exec uv run --locked --project "$root/sw/ui" python "$root/sw/ui/main.py" "$@"
