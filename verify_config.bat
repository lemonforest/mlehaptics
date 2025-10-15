@echo off
REM PlatformIO ESP-IDF Configuration Verification Script v2
REM EMDR Bilateral Stimulation Device
REM
REM This script verifies platformio.ini configuration and builds test firmware

echo ========================================
echo ESP-IDF Configuration Verification v2
echo ========================================
echo.

echo Checking PlatformIO installation...
pio --version
if errorlevel 1 (
    echo ERROR: PlatformIO not found in PATH
    echo Please install PlatformIO first
    pause
    exit /b 1
)
echo.

echo ========================================
echo Step 1: Cleaning previous build...
echo ========================================
pio run --target clean
echo.

echo ========================================
echo Step 2: Building configuration test firmware...
echo ========================================
echo This will download ESP-IDF on first run (may take 5-10 minutes)
echo.
pio run --verbose > build_output.log 2>&1
if errorlevel 1 (
    echo.
    echo BUILD FAILED - Check build_output.log for details
    echo.
    echo Common issues:
    echo   1. Board definition not found - FIXED in v2
    echo   2. ESP-IDF download in progress - Check build_output.log
    echo   3. Missing dependencies - Run: pio pkg install
    echo.
    type build_output.log
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo BUILD SUCCESSFUL!
echo ========================================
echo.

echo ========================================
echo Checking for ESP-IDF version in build output...
echo ========================================
findstr /C:"ESP-IDF" build_output.log
echo.

echo ========================================
echo Checking for ESP32-C6 target...
echo ========================================
findstr /C:"esp32c6" build_output.log
echo.

echo ========================================
echo Build Statistics:
echo ========================================
findstr /C:"RAM:" build_output.log
findstr /C:"Flash:" build_output.log
echo.

echo ========================================
echo Verification Complete!
echo ========================================
echo.
echo Full build output saved to: build_output.log
echo.
echo ✓ Configuration is verified if you see:
echo   - ESP-IDF v5.x.x in output above
echo   - esp32c6 target confirmed
echo   - BUILD SUCCESSFUL message
echo.
echo Next Steps:
echo   1. Review build_output.log for ESP-IDF version
echo   2. Connect ESP32-C6 device via USB
echo   3. Run: pio run --target upload
echo   4. Run: pio device monitor
echo   5. Check console output for configuration details
echo.
echo Update docs\platformio_verification.md with your results!
echo.

pause
