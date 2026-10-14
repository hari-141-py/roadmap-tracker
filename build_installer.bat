@echo off
REM Builds the app, then the installer. Needs Inno Setup 6 installed.
call build.bat
set ISCC="%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not exist %ISCC% set ISCC="%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
%ISCC% installer.iss
echo.
echo Installer: installer_output\DevOpsTracker-Setup.exe
pause
