param([string]$Port)

$ErrorActionPreference = 'Stop'
$venvPath = Join-Path $PSScriptRoot '.venv'
$pythonPath = Join-Path $venvPath 'Scripts\python.exe'

if (!(Test-Path -LiteralPath $pythonPath)) {
    try {
        & py -3.12 -m venv $venvPath
        if ($LASTEXITCODE -ne 0) { throw 'Could not create .venv' }
    } catch {
        $codexPython = Join-Path $env:USERPROFILE '.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
        if (!(Test-Path -LiteralPath $codexPython)) {
            throw 'Install Python 3.12 with the Windows py launcher, then retry.'
        }
        & $codexPython -m venv $venvPath
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
    }
}

& $pythonPath -B -c 'import importlib.util, sys; sys.exit(not all(map(importlib.util.find_spec, sys.argv[1:])))' matplotlib numpy serial
if ($LASTEXITCODE -ne 0) {
    & $pythonPath -m pip install -r (Join-Path $PSScriptRoot 'pc_app\requirements.txt')
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$webPath = Join-Path $PSScriptRoot 'pc_app\imu_web.py'
if ($Port) {
    & $pythonPath -B $webPath --port $Port
} else {
    & $pythonPath -B $webPath --demo
}
exit $LASTEXITCODE
