param([int]$Port = 8080)
$ErrorActionPreference = 'Stop'
$env:UV_PROJECT_ENVIRONMENT = Join-Path $PSScriptRoot '.local/ui-venv'
$env:UV_CACHE_DIR = Join-Path $PSScriptRoot '.local/uv-cache'
$env:UV_PYTHON_INSTALL_DIR = Join-Path $PSScriptRoot '.local/python'
uv run --locked --project (Join-Path $PSScriptRoot 'sw/ui') python (Join-Path $PSScriptRoot 'sw/ui/main.py') --port $Port
exit $LASTEXITCODE
