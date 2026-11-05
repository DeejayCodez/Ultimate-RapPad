@echo off
title Building The Ultimate RapPad v2.0
cd /d "%~dp0"
echo [1/4] Installing dependencies...
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
if errorlevel 1 goto failed

echo [2/4] Building main Windows application...
py -m PyInstaller --noconfirm --clean --onefile --windowed --name UltimateRapPad main.py
if errorlevel 1 goto failed

echo [3/4] Building background updater helper...
py -m PyInstaller --noconfirm --clean --onefile --windowed --name RapPadUpdater update_helper.py
if errorlevel 1 goto failed

echo [4/4] Preparing release folder...
if not exist release mkdir release
copy /Y dist\UltimateRapPad.exe release\UltimateRapPad.exe >nul
copy /Y dist\RapPadUpdater.exe release\RapPadUpdater.exe >nul
copy /Y update_config.json release\update_config.json >nul
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Path 'release\UltimateRapPad.exe','release\RapPadUpdater.exe','release\update_config.json' -DestinationPath 'release\UltimateRapPad-Windows.zip' -Force"
if errorlevel 1 goto failed
echo.
echo BUILD COMPLETE
echo App:     dist\UltimateRapPad.exe
echo Updater: dist\RapPadUpdater.exe
echo Release files are in the release folder.
echo To publish an update, zip the app EXE as UltimateRapPad-Windows.zip and attach it to a GitHub Release.
pause
exit /b 0

:failed
echo.
echo BUILD FAILED. Review the error above.
pause
exit /b 1
