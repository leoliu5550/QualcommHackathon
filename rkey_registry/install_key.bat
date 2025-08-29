@echo off
SETLOCAL ENABLEEXTENSIONS
SETLOCAL ENABLEDELAYEDEXPANSION

echo ========= Enhanced FileOrg Installer (3 Options) =========
echo.

:: Optional: Check if running in r_key_venv virtual environment
IF DEFINED VIRTUAL_ENV (
    echo %VIRTUAL_ENV% | findstr /C:".rkey_venv" >nul
    IF ERRORLEVEL 1 (
        echo [WARNING] Different virtual environment detected: %VIRTUAL_ENV%
        echo [INFO] Recommended: r_key_venv for testing
    ) ELSE (
        echo [OK] Running in r_key_venv virtual environment
    )
) ELSE (
    echo [INFO] No virtual environment detected
)
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

:: 4. Find fileorg.exe location
echo [4/5] Locating fileorg.exe...

:: Try multiple possible pipx installation paths
set "EXE_PATH="

:: Check pipx venvs location
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

:: Also check global bin location
IF "%EXE_PATH%"=="" (
    IF EXIST "%USERPROFILE%\.local\bin\fileorg.exe" (
        set "EXE_PATH=%USERPROFILE%\.local\bin\fileorg.exe"
        echo [OK] Found fileorg at: %USERPROFILE%\.local\bin\
    )
)

:: Check if exe exists
IF NOT EXIST "%EXE_PATH%" (
    echo [ERROR] fileorg.exe not found!
    echo Checked locations:
    echo   - %USERPROFILE%\pipx\venvs\fileorg\Scripts\
    echo   - %USERPROFILE%\.local\pipx\venvs\fileorg\Scripts\
    echo   - %LOCALAPPDATA%\pipx\venvs\fileorg\Scripts\
    pause
    exit /b 1
)

:: 5. Register context menu with THREE options (User-level, no admin required)
echo [5/5] Registering context menu with 3 options...
echo.

:: Remove old menus if exist
reg delete "HKCU\Software\Classes\Directory\shell\fileorg" /f >nul 2>&1
reg delete "HKCU\Software\Classes\Directory\shell\FileOrg" /f >nul 2>&1
reg delete "HKCU\Software\Classes\Directory\Background\shell\FileOrg" /f >nul 2>&1

:: Create cascading menu with 3 options using shell submenu structure
echo Creating FileOrg cascading menu...

:: Main menu entry with MUIVerb for cascading
reg add "HKCU\Software\Classes\Directory\shell\FileOrg" /ve /d "FileOrg Operations" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\shell\FileOrg" /v "MUIVerb" /d "FileOrg Operations" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\shell\FileOrg" /v "Icon" /d "%EXE_PATH%" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\shell\FileOrg" /v "SubCommands" /d "" /f >nul 2>&1

:: Option 1: Preview (子選單項目)
echo Adding Preview option...
reg add "HKCU\Software\Classes\Directory\shell\FileOrg\shell\01preview" /ve /d "📋 Preview Organization" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\shell\FileOrg\shell\01preview" /v "Icon" /d "%EXE_PATH%" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\shell\FileOrg\shell\01preview\command" /ve /d "cmd.exe /c \"cd /d \"\"%%1\"\" && \"\"%EXE_PATH%\"\" \"\"%%1\"\" --preview && pause\"" /f >nul 2>&1

:: Option 2: Organize (子選單項目)
echo Adding Organize option...
reg add "HKCU\Software\Classes\Directory\shell\FileOrg\shell\02organize" /ve /d "🗂️ Start Organizing" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\shell\FileOrg\shell\02organize" /v "Icon" /d "%EXE_PATH%" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\shell\FileOrg\shell\02organize\command" /ve /d "cmd.exe /c \"cd /d \"\"%%1\"\" && \"\"%EXE_PATH%\"\" \"\"%%1\"\" && pause\"" /f >nul 2>&1

:: Option 3: Restore (子選單項目)
echo Adding Restore option...
reg add "HKCU\Software\Classes\Directory\shell\FileOrg\shell\03restore" /ve /d "↩️ Restore Original" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\shell\FileOrg\shell\03restore" /v "Icon" /d "%EXE_PATH%" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\shell\FileOrg\shell\03restore\command" /ve /d "cmd.exe /c \"cd /d \"\"%%1\"\" && \"\"%EXE_PATH%\"\" \"\"%%1\"\" --restore && pause\"" /f >nul 2>&1

:: Also add to background context menu (right-click on empty space in folder)
echo Adding background context menu...
reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg" /ve /d "FileOrg Operations" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg" /v "MUIVerb" /d "FileOrg Operations" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg" /v "Icon" /d "%EXE_PATH%" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg" /v "SubCommands" /d "" /f >nul 2>&1

:: Background menu - Option 1: Preview
reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg\shell\01preview" /ve /d "📋 Preview Organization" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg\shell\01preview" /v "Icon" /d "%EXE_PATH%" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg\shell\01preview\command" /ve /d "cmd.exe /c \"cd /d \"\"%%V\"\" && \"\"%EXE_PATH%\"\" \"\"%%V\"\" --preview && pause\"" /f >nul 2>&1

:: Background menu - Option 2: Organize
reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg\shell\02organize" /ve /d "🗂️ Start Organizing" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg\shell\02organize" /v "Icon" /d "%EXE_PATH%" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg\shell\02organize\command" /ve /d "cmd.exe /c \"cd /d \"\"%%V\"\" && \"\"%EXE_PATH%\"\" \"\"%%V\"\" && pause\"" /f >nul 2>&1

:: Background menu - Option 3: Restore
reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg\shell\03restore" /ve /d "↩️ Restore Original" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg\shell\03restore" /v "Icon" /d "%EXE_PATH%" /f >nul 2>&1
reg add "HKCU\Software\Classes\Directory\Background\shell\FileOrg\shell\03restore\command" /ve /d "cmd.exe /c \"cd /d \"\"%%V\"\" && \"\"%EXE_PATH%\"\" \"\"%%V\"\" --restore && pause\"" /f >nul 2>&1

echo.
echo ========= Installation Complete! =========
echo.
echo ✅ FileOrg has been successfully installed with 3 options:
echo    1. 📋 Preview Organization - See what will be organized
echo    2. 🗂️ Start Organizing - Organize files with AI
echo    3. ↩️ Restore Original - Restore files to original locations
echo.
echo 📁 Right-click on any folder to see "FileOrg Operations" menu
echo.
echo [INFO] Registry keys: HKCU\Software\Classes\Directory\shell\FileOrg
echo [INFO] To uninstall: Run uninstall_registry_enhanced.bat
echo ==========================================
pause