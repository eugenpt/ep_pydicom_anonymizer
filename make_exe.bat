@echo off
REM =============================================================
REM make_exe.bat - QUICK LOCAL BUILD FOR TESTING
REM
REM - For local debugging only
REM - Full release = GitHub Actions
REM =============================================================

echo.
echo [LOCAL TEST BUILD] DICOM_Anonymizer.exe
echo.

REM --- Check deps ---
python -c "import PyInstaller" >nul 2>&1 || (
    echo [ERROR] Install PyInstaller: pip install pyinstaller
    pause
    exit /b 1
)

REM --- Build ---
pyinstaller --onefile --console ^
    --add-data "anonymizer.py;." ^
    --name DICOM_Anonymizer ^
    batch.py

if %errorlevel% neq 0 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

REM --- Copy config for testing ---
copy /Y config.txt dist\config.txt >nul 2>&1

echo.
echo [SUCCESS] Test build ready:
echo   dist\DICOM_Anonymizer.exe
echo   dist\config.txt
echo.
echo For release: git tag + push -> GitHub Actions
pause