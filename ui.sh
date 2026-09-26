#!/usr/bin/env sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
uv="$root/.local/tools/uv-unix/uv"
if [ ! -x "$uv" ]; then
    uv=$(command -v uv) || { echo 'Run sh ./setup-ui.sh first to install the workbench tools.' >&2; exit 1; }
fi
export UV_PROJECT_ENVIRONMENT="$root/.local/ui-venv-linux"
export UV_CACHE_DIR="$root/.local/uv-cache"
export UV_PYTHON_INSTALL_DIR="$root/.local/python"
if [ "${1:-}" = '--setup' ]; then
    shift
    "$uv" sync --locked --project "$root/sw/ui"
    if [ "$#" -eq 0 ]; then
        echo 'Setup complete. Run sh ./ui.sh, then open http://127.0.0.1:8080'
        exit 0
    fi
fi
if [ "${1:-}" = '--check' ]; then
    "$uv" run --locked --project "$root/sw/ui" python "$root/sw/ui/check.py"
    exec "$uv" run --locked --project "$root/sw/ui" python -m unittest discover -s "$root/sw/ui" -p 'test_*.py'
fi
echo 'Starting workbench (default http://127.0.0.1:8080; Ctrl+C stops it)'
exec "$uv" run --locked --project "$root/sw/ui" python "$root/sw/ui/main.py" "$@"
