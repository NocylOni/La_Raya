@echo off
REM Build a standalone .exe for Windows. Run this from the patient_management folder.
cd /d "%~dp0"

python -m venv .buildenv
call .buildenv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
pyinstaller PatientManagement.spec --noconfirm

echo.
echo Build complete: dist\PatientManagement.exe
pause
