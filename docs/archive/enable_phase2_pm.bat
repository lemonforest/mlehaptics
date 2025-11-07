@echo off
REM Phase 2: Enable Tickless Idle and Light Sleep
REM Automatically updates sdkconfig for power management

echo ========================================
echo Phase 2: Power Management Configuration
echo ========================================
echo.

set SDKCONFIG=sdkconfig.single_device_battery_bemf_queued_test

echo Backing up current sdkconfig...
copy %SDKCONFIG% %SDKCONFIG%.backup >nul
if %errorlevel% neq 0 (
    echo ERROR: Could not create backup!
    exit /b 1
)
echo ✓ Backup created: %SDKCONFIG%.backup
echo.

echo Adding Power Management settings...

REM Find and replace the PM section
powershell -Command "(Get-Content %SDKCONFIG%) -replace '#\s*CONFIG_PM_ENABLE\s+is\s+not\s+set', 'CONFIG_PM_ENABLE=y' | Set-Content %SDKCONFIG%.tmp"
if exist %SDKCONFIG%.tmp (
    move /Y %SDKCONFIG%.tmp %SDKCONFIG% >nul
)

REM Add tickless idle after PM_ENABLE
powershell -Command "$content = Get-Content '%SDKCONFIG%'; $index = 0; foreach ($line in $content) { if ($line -match 'CONFIG_PM_ENABLE=y') { break } $index++ }; if ($index -lt $content.Length) { $newContent = @(); $newContent += $content[0..$index]; $newContent += 'CONFIG_FREERTOS_USE_TICKLESS_IDLE=y'; $newContent += 'CONFIG_PM_DFS_INIT_AUTO=y'; $newContent += 'CONFIG_PM_MIN_IDLE_TIME_DURATION_MS=20'; $newContent += $content[($index+1)..($content.Length-1)]; $newContent | Set-Content '%SDKCONFIG%' }"

echo ✓ Configuration updated!
echo.

echo Changes made:
echo   - CONFIG_PM_ENABLE=y
echo   - CONFIG_FREERTOS_USE_TICKLESS_IDLE=y  
echo   - CONFIG_PM_DFS_INIT_AUTO=y
echo   - CONFIG_PM_MIN_IDLE_TIME_DURATION_MS=20
echo.

echo ========================================
echo Next Steps:
echo ========================================
echo 1. Clean previous build:
echo    pio run -e single_device_battery_bemf_queued_test -t clean
echo.
echo 2. Rebuild with new config:
echo    pio run -e single_device_battery_bemf_queued_test -t upload
echo.
echo 3. Monitor output:
echo    pio device monitor
echo.
echo See PHASE_2_TICKLESS_IDLE_GUIDE.md for details
echo.

echo To restore original config:
echo    copy %SDKCONFIG%.backup %SDKCONFIG%
echo.

pause
