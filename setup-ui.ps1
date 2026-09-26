param([switch]$Check)
$ErrorActionPreference = 'Stop'
# Official, versioned installer; no administrator rights or persistent PATH changes.
$toolDir = Join-Path $PSScriptRoot '.local/tools/uv-windows'
$uv = Join-Path $toolDir 'uv.exe'
if (-not (Test-Path -LiteralPath $uv)) {
    New-Item -ItemType Directory -Force -Path $toolDir | Out-Null
    $installer = Join-Path $toolDir 'install.ps1'
    Write-Host 'Installing uv 0.11.2 inside .local/ (network required)...'
    Invoke-WebRequest 'https://astral.sh/uv/0.11.2/install.ps1' -UseBasicParsing -OutFile $installer
    $previous = $env:UV_UNMANAGED_INSTALL
    try {
        $env:UV_UNMANAGED_INSTALL = $toolDir
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer
        if ($LASTEXITCODE -ne 0) { throw 'uv installation failed. Check the download error above and rerun setup.' }
    } finally { $env:UV_UNMANAGED_INSTALL = $previous }
}
& (Join-Path $PSScriptRoot 'ui.ps1') -Setup -Check:$Check
exit $LASTEXITCODE
