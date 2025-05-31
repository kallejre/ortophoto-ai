@echo off
setlocal

set VENV_DIR=.ortho-venv

python -m venv %VENV_DIR%
call %VENV_DIR%\Scripts\activate.bat
python -m pip install --upgrade pip

if exist requirements.txt (
    pip install -r requirements.txt
) else (
    echo requirements.txt not found, skipping dependency install.
)

endlocal
