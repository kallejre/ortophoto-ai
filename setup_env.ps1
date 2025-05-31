$venvDir = ".ortho-venv"

if (-not (Test-Path $venvDir)) {
    python -m venv $venvDir
}

$activate = Join-Path $venvDir "Scripts\Activate.ps1"
if (-not (Test-Path $activate)) {
    Write-Error "Cannot find activation script: $activate"
    exit 1
}
. $activate

if (-not (Test-Path "requirements.txt")) {
    Write-Error "requirements.txt not found"
    exit 1
}

pip install --upgrade pip
pip install -r requirements.txt
# Deactivate with $> deactivate
