@echo off
SETLOCAL ENABLEEXTENSIONS
SETLOCAL ENABLEDELAYEDEXPANSION

echo ========= FileOrg Right-Click Installer =========
echo.

:: 1. Check if Python is installed
echo [1/5] Checking Python installation...
where python >nul 2>nul
IF ERRORLEVEL 1 (
    echo [ERROR] Python not detected, please install Python first
    pause
    exit /b 1
) ELSE (
    echo [OK] Python detected successfully
)

:: 2. Check if pipx is installed
echo [2/5] Checking pipx installation...
where pipx >nul 2>nul
IF ERRORLEVEL 1 (
    echo [INFO] Installing pipx...
    python -m pip install --upgrade pip
    python -m pip install pipx
    python -m pipx ensurepath
) ELSE (
    echo [OK] pipx detected successfully
)

:: 3. Install fileorg tool
echo [3/5] Installing fileorg tool...

:: Check if fileorg is already installed
pipx list | findstr "fileorg" >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo [INFO] fileorg already installed, reinstalling with --force...
    pipx install --force git+https://github.com/leoliu5550/QualcommHackathon.git
) ELSE (
    pipx install git+https://github.com/leoliu5550/QualcommHackathon.git
)

IF NOT %ERRORLEVEL% EQU 0 (
    echo [ERROR] fileorg installation failed!
    pause
    exit /b 1
)
echo [OK] fileorg installed successfully

:: 4. Find fileorg.exe location from pipx
echo [4/5] Locating fileorg.exe from pipx installation...

set "EXE_PATH="

:: Check standard pipx venv locations
IF EXIST "%USERPROFILE%\pipx\venvs\fileorg\Scripts\fileorg.exe" (
    set "EXE_PATH=%USERPROFILE%\pipx\venvs\fileorg\Scripts\fileorg.exe"
    echo [OK] Found fileorg at: %USERPROFILE%\pipx\venvs\fileorg\Scripts\
) ELSE IF EXIST "%USERPROFILE%\.local\pipx\venvs\fileorg\Scripts\fileorg.exe" (
    set "EXE_PATH=%USERPROFILE%\.local\pipx\venvs\fileorg\Scripts\fileorg.exe"
    echo [OK] Found fileorg at: %USERPROFILE%\.local\pipx\venvs\fileorg\Scripts\
) ELSE IF EXIST "%LOCALAPPDATA%\pipx\venvs\fileorg\Scripts\fileorg.exe" (
    set "EXE_PATH=%LOCALAPPDATA%\pipx\venvs\fileorg\Scripts\fileorg.exe"
    echo [OK] Found fileorg at: %LOCALAPPDATA%\pipx\venvs\fileorg\Scripts\
)

:: Also check pipx global bin location
IF "%EXE_PATH%"=="" (
    IF EXIST "%USERPROFILE%\.local\bin\fileorg.exe" (
        set "EXE_PATH=%USERPROFILE%\.local\bin\fileorg.exe"
        echo [OK] Found fileorg at: %USERPROFILE%\.local\bin\
    )
)

:: Check if exe exists
IF NOT EXIST "%EXE_PATH%" (
    echo [ERROR] fileorg.exe not found in pipx installation!
    echo.
    echo Checked pipx locations:
    echo   - %USERPROFILE%\pipx\venvs\fileorg\Scripts\
    echo   - %USERPROFILE%\.local\pipx\venvs\fileorg\Scripts\
    echo   - %LOCALAPPDATA%\pipx\venvs\fileorg\Scripts\
    echo   - %USERPROFILE%\.local\bin\
    echo.
    echo Please ensure fileorg was installed successfully with pipx.
    echo Try running: pipx list
    echo to verify the installation.
    pause
    exit /b 1
)

:: Display found path for debugging
echo [DEBUG] Using EXE_PATH: %EXE_PATH%

:: 5. Register cascading context menu using CommandStore (User-level, no admin required)
echo [5/5] Registering cascading context menu...
echo.

:: Remove old menus if exist
echo Removing old menu entries...
reg delete "HKCU\Software\Classes\Directory\shell\fileorg" /f >nul 2>&1
reg delete "HKCU\Software\Classes\Directory\shell\FileOrg" /f >nul 2>&1
reg delete "HKCU\Software\Classes\Directory\shell\FileOrgPreview" /f >nul 2>&1
reg delete "HKCU\Software\Classes\Directory\shell\FileOrgOrganize" /f >nul 2>&1
reg delete "HKCU\Software\Classes\Directory\shell\FileOrgRestore" /f >nul 2>&1
reg delete "HKCU\Software\Classes\Directory\Background\shell\FileOrg" /f >nul 2>&1
reg delete "HKCU\Software\Classes\Directory\Background\shell\FileOrgPreview" /f >nul 2>&1
reg delete "HKCU\Software\Classes\Directory\Background\shell\FileOrgOrganize" /f >nul 2>&1
reg delete "HKCU\Software\Classes\Directory\Background\shell\FileOrgRestore" /f >nul 2>&1

:: Remove old CommandStore entries if exist
reg delete "HKCU\Software\Classes\FileOrg.Preview" /f >nul 2>&1
reg delete "HKCU\Software\Classes\FileOrg.Organize" /f >nul 2>&1
reg delete "HKCU\Software\Classes\FileOrg.Restore" /f >nul 2>&1

echo Creating FileOrg cascading menu...

:: Main cascading menu entry for Directory
echo Adding main FileOrg menu...
reg add "HKCU\Software\Classes\Directory\shell\FileOrg" /v "MUIVerb" /d "FileOrg" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\shell\FileOrg" /v "Icon" /d "%EXE_PATH%" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\shell\FileOrg" /v "SubCommands" /d "" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\shell\FileOrg" /v "Position" /d "Top" /f >nul 2>&1

:: Main cascading menu entry for Directory Background
reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg" /v "MUIVerb" /d "FileOrg" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg" /v "Icon" /d "%EXE_PATH%" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg" /v "SubCommands" /d "" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg" /v "Position" /d "Top" /f >nul 2>&1

:: Setup shell subkeys for cascading menu
echo Setting up submenu options...

:: Shell subkeys for Directory
reg add "HKCU\Software\Classes\Directory\shell\FileOrg\shell\Preview" /ve /d "Preview" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\shell\FileOrg\shell\Preview" /v "Icon" /d "%EXE_PATH%" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\shell\FileOrg\shell\Preview\command" /ve /d "cmd.exe /c \"cd /d \"\"%%1\"\" && \"\"%EXE_PATH%\"\" \"\"%%1\"\" --preview && pause\"" /f >nul 2>&1

reg add "HKCU\Software\Classes\Directory\shell\FileOrg\shell\Start" /ve /d "Start" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\shell\FileOrg\shell\Start" /v "Icon" /d "%EXE_PATH%" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\shell\FileOrg\shell\Start\command" /ve /d "cmd.exe /c \"cd /d \"\"%%1\"\" && \"\"%EXE_PATH%\"\" \"\"%%1\"\" && pause\"" /f >nul 2>&1

reg add "HKCU\Software\Classes\Directory\shell\FileOrg\shell\Restore" /ve /d "Restore" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\shell\FileOrg\shell\Restore" /v "Icon" /d "%EXE_PATH%" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\shell\FileOrg\shell\Restore\command" /ve /d "cmd.exe /c \"cd /d \"\"%%1\"\" && \"\"%EXE_PATH%\"\" \"\"%%1\"\" --restore && pause\"" /f >nul 2>&1

:: Shell subkeys for Background
reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg\shell\Preview" /ve /d "Preview" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg\shell\Preview" /v "Icon" /d "%EXE_PATH%" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg\shell\Preview\command" /ve /d "cmd.exe /c \"cd /d \"\"%%V\"\" && \"\"%EXE_PATH%\"\" \"\"%%V\"\" --preview && pause\"" /f >nul 2>&1

reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg\shell\Start" /ve /d "Start" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg\shell\Start" /v "Icon" /d "%EXE_PATH%" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg\shell\Start\command" /ve /d "cmd.exe /c \"cd /d \"\"%%V\"\" && \"\"%EXE_PATH%\"\" \"\"%%V\"\" && pause\"" /f >nul 2>&1

reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg\shell\Restore" /ve /d "Restore" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg\shell\Restore" /v "Icon" /d "%EXE_PATH%" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg\shell\Restore\command" /ve /d "cmd.exe /c \"cd /d \"\"%%V\"\" && \"\"%EXE_PATH%\"\" \"\"%%V\"\" --restore && pause\"" /f >nul 2>&1

echo.
echo ========= Installation Complete! =========
echo.
echo FileOrg has been successfully installed!
echo.
echo Right-click on any folder to see "FileOrg" menu
echo Click the arrow to see 3 options:
echo    - Preview - See what will be organized
echo    - Start - Organize files with AI
echo    - Restore - Restore files to original locations
echo.
echo [DEBUG] Executable path: %EXE_PATH%
echo.
echo [INFO] Registry keys: HKCU\Software\Classes\Directory\shell\FileOrg
echo [INFO] To uninstall: Run uninstall_key.bat
echo ==========================================
pause