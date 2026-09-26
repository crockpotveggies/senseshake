#!/usr/bin/env sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
case "${1:-}" in
    '') check='' ;;
    --check) check='--check' ;;
    *) echo 'Usage: sh setup-ui.sh [--check]' >&2; exit 2 ;;
esac
tool_dir="$root/.local/tools/uv-unix"
if [ ! -x "$tool_dir/uv" ]; then
    command -v curl >/dev/null 2>&1 || { echo 'Install curl with your OS package manager, then rerun setup.' >&2; exit 1; }
    mkdir -p "$tool_dir"
    echo 'Installing uv 0.11.2 inside .local/ (network required)...'
    curl --fail --location --silent --show-error https://astral.sh/uv/0.11.2/install.sh -o "$tool_dir/install.sh"
    UV_UNMANAGED_INSTALL="$tool_dir" sh "$tool_dir/install.sh"
fi
if [ -n "$check" ]; then
    exec sh "$root/ui.sh" --setup --check
fi
exec sh "$root/ui.sh" --setup
