param([ValidateRange(1,65535)][int]$Port = 8080, [switch]$Setup, [switch]$Check)
$ErrorActionPreference = 'Stop'
$uv = Join-Path $PSScriptRoot '.local/tools/uv-windows/uv.exe'
if (-not (Test-Path -LiteralPath $uv)) {
    $installed = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $installed) { throw 'Run ./setup-ui.ps1 first to install the workbench tools.' }
    $uv = $installed.Source
}
$saved = @{}
$settings = @{
    UV_PROJECT_ENVIRONMENT = (Join-Path $PSScriptRoot '.local/ui-venv')
    UV_CACHE_DIR = (Join-Path $PSScriptRoot '.local/uv-cache')
    UV_PYTHON_INSTALL_DIR = (Join-Path $PSScriptRoot '.local/python')
}
try {
    foreach ($name in $settings.Keys) {
        $saved[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
        [Environment]::SetEnvironmentVariable($name, $settings[$name], 'Process')
    }
    $project = Join-Path $PSScriptRoot 'sw/ui'
    if ($Setup) {
        & $uv sync --locked --project $project
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
    if ($Check) {
        & $uv run --locked --project $project python (Join-Path $project 'check.py')
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        & $uv run --locked --project $project python -m unittest discover -s $project -p 'test_*.py'
        exit $LASTEXITCODE
    }
    if ($Setup) { Write-Host 'Setup complete. Run ./ui.ps1, then open http://127.0.0.1:8080'; exit 0 }
    Write-Host "Starting workbench: http://127.0.0.1:$Port (Ctrl+C stops it)"
    & $uv run --locked --project $project python (Join-Path $project 'main.py') --port $Port
    exit $LASTEXITCODE
} finally {
    foreach ($name in $saved.Keys) { [Environment]::SetEnvironmentVariable($name, $saved[$name], 'Process') }
}
