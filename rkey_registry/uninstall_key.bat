@echo off
SETLOCAL ENABLEEXTENSIONS

echo ========= Enhanced FileOrg Registry Uninstaller =========
echo.

echo This will remove the FileOrg submenu from the right-click context menu.
echo.
choice /C YN /M "Are you sure you want to uninstall the registry keys?"
IF ERRORLEVEL 2 (
    echo Uninstall cancelled.
    pause
    exit /b 0
)

echo.
echo [1/3] Removing context menu registry keys...

:: Remove main FileOrg menu items
reg delete "HKCU\Software\Classes\Directory\shell\FileOrg" /f >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo [OK] Removed FileOrg cascading menu
)
reg delete "HKCU\Software\Classes\Directory\shell\fileorg" /f >nul 2>&1

:: Remove individual menu items (if they exist)
reg delete "HKCU\Software\Classes\Directory\shell\FileOrgPreview" /f >nul 2>&1
reg delete "HKCU\Software\Classes\Directory\shell\FileOrgOrganize" /f >nul 2>&1
reg delete "HKCU\Software\Classes\Directory\shell\FileOrgRestore" /f >nul 2>&1

:: Remove background context menu
reg delete "HKCU\Software\Classes\Directory\Background\shell\FileOrg" /f >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo [OK] Removed background FileOrg cascading menu
)
reg delete "HKCU\Software\Classes\Directory\Background\shell\FileOrgPreview" /f >nul 2>&1
reg delete "HKCU\Software\Classes\Directory\Background\shell\FileOrgOrganize" /f >nul 2>&1
reg delete "HKCU\Software\Classes\Directory\Background\shell\FileOrgRestore" /f >nul 2>&1

:: Remove CommandStore definitions
reg delete "HKCU\Software\Classes\FileOrg.Preview" /f >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo [OK] Removed FileOrg.Preview command
)
reg delete "HKCU\Software\Classes\FileOrg.Organize" /f >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo [OK] Removed FileOrg.Organize command
)
reg delete "HKCU\Software\Classes\FileOrg.Restore" /f >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo [OK] Removed FileOrg.Restore command
)

:: Remove any MuiCache entries
reg delete "HKCU\Software\Classes\Local Settings\MuiCache\CommandStore\shell\FileOrgPreview" /f >nul 2>&1
reg delete "HKCU\Software\Classes\Local Settings\MuiCache\CommandStore\shell\FileOrgOrganize" /f >nul 2>&1
reg delete "HKCU\Software\Classes\Local Settings\MuiCache\CommandStore\shell\FileOrgRestore" /f >nul 2>&1

:: Try to remove from HKCR if exists (requires admin)
echo.
echo [2/3] Checking for system-wide keys...
reg query "HKCR\Directory\shell\FileOrg" >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo [INFO] Found HKCR registry keys (requires admin to remove)
    reg delete "HKCR\Directory\shell\FileOrg" /f >nul 2>&1
    IF %ERRORLEVEL% EQU 0 (
        echo [OK] Removed HKCR registry keys successfully
    ) ELSE (
        echo [WARNING] Could not remove HKCR keys (may need admin rights)
        echo To remove manually, run as administrator:
        echo   reg delete "HKCR\Directory\shell\FileOrg" /f
    )
) ELSE (
    echo [OK] No system-wide registry keys found
)

echo.
echo [3/3] Verifying removal...

:: Verify removal
set KEYS_FOUND=0

:: Check main menu
reg query "HKCU\Software\Classes\Directory\shell\FileOrg" >nul 2>&1
IF %ERRORLEVEL% EQU 0 set KEYS_FOUND=1

:: Check individual menus
reg query "HKCU\Software\Classes\Directory\shell\FileOrgPreview" >nul 2>&1
IF %ERRORLEVEL% EQU 0 set KEYS_FOUND=1

reg query "HKCU\Software\Classes\Directory\shell\FileOrgOrganize" >nul 2>&1
IF %ERRORLEVEL% EQU 0 set KEYS_FOUND=1

reg query "HKCU\Software\Classes\Directory\shell\FileOrgRestore" >nul 2>&1
IF %ERRORLEVEL% EQU 0 set KEYS_FOUND=1

:: Check command definitions
reg query "HKCU\Software\Classes\FileOrg.Preview" >nul 2>&1
IF %ERRORLEVEL% EQU 0 set KEYS_FOUND=1

reg query "HKCU\Software\Classes\FileOrg.Organize" >nul 2>&1
IF %ERRORLEVEL% EQU 0 set KEYS_FOUND=1

reg query "HKCU\Software\Classes\FileOrg.Restore" >nul 2>&1
IF %ERRORLEVEL% EQU 0 set KEYS_FOUND=1

:: Check HKCR
reg query "HKCR\Directory\shell\FileOrg" >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo [WARNING] Some HKCR keys may still exist (need admin to remove)
    set KEYS_FOUND=1
)

IF %KEYS_FOUND% EQU 0 (
    echo [OK] All registry keys successfully removed
) ELSE (
    echo [ERROR] Some FileOrg keys may still exist
)

echo.
echo ========= Uninstall Complete =========
echo FileOrg has been removed from the context menu.
echo.
echo [INFO] To reinstall, run: install_key.bat
echo =====================================
pause