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
echo [1/3] Removing enhanced context menu registry keys...

:: Remove enhanced submenu from HKCU (current user)
reg delete "HKCU\Software\Classes\Directory\shell\FileOrg" /f >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo [OK] Removed enhanced FileOrg submenu successfully
) ELSE (
    echo [INFO] Enhanced FileOrg submenu not found or already removed
)

:: Also remove old single-option menu if exists
reg delete "HKCU\Software\Classes\Directory\shell\fileorg" /f >nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo [OK] Removed old single-option menu
)

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
reg query "HKCU\Software\Classes\Directory\shell\FileOrg" >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    reg query "HKCU\Software\Classes\Directory\shell\fileorg" >nul 2>&1
    IF %ERRORLEVEL% NEQ 0 (
        reg query "HKCR\Directory\shell\FileOrg" >nul 2>&1
        IF %ERRORLEVEL% NEQ 0 (
            echo [OK] All registry keys successfully removed
        ) ELSE (
            echo [WARNING] Some HKCR keys may still exist (need admin to remove)
        )
    ) ELSE (
        echo [ERROR] Failed to remove old fileorg keys
    )
) ELSE (
    echo [ERROR] Failed to remove FileOrg submenu keys
)

echo.
echo ========= Uninstall Complete =========
echo FileOrg has been removed from the context menu.
echo.
echo [INFO] To reinstall, run: r_key_registry_enhanced.bat
echo =====================================
pause