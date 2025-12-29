@echo off
REM UTLP C64 HAL - Windows Build Script
REM
REM Prerequisites:
REM   - cc65 toolchain installed (auto-detected in common locations)
REM   - VICE emulator (optional, for testing)
REM
REM Usage:
REM   build.bat          - Build utlp_c64.prg
REM   build.bat run      - Build and run in VICE
REM   build.bat clean    - Remove build artifacts

setlocal enabledelayedexpansion

REM Configuration
set TARGET=utlp_c64.prg
set CC=cl65
REM --standard cc65 enables extended features (relaxed C89 mode)
REM NOTE: cc65 does NOT support 64-bit types - we use utlp_time_t union instead
set CFLAGS=-t c64 -O -Oi -Or --standard cc65 -I. -I..\utlp_skeleton
set VICE=x64sc

REM Auto-detect cc65 in common locations (add to local PATH)
if exist "C:\cc65\bin\cl65.exe" set PATH=C:\cc65\bin;%PATH%
if exist "C:\Program Files\cc65\bin\cl65.exe" set PATH=C:\Program Files\cc65\bin;%PATH%
if exist "C:\Program Files (x86)\cc65\bin\cl65.exe" set PATH=C:\Program Files (x86)\cc65\bin;%PATH%
if exist "%USERPROFILE%\cc65\bin\cl65.exe" set PATH=%USERPROFILE%\cc65\bin;%PATH%
if exist "%LOCALAPPDATA%\cc65\bin\cl65.exe" set PATH=%LOCALAPPDATA%\cc65\bin;%PATH%

REM Auto-detect VICE in common locations
if exist "C:\VICE\bin\x64sc.exe" set PATH=C:\VICE\bin;%PATH%
if exist "C:\Program Files\VICE\bin\x64sc.exe" set PATH=C:\Program Files\VICE\bin;%PATH%
if exist "C:\Program Files\GTK3VICE\bin\x64sc.exe" set PATH=C:\Program Files\GTK3VICE\bin;%PATH%
if exist "%USERPROFILE%\VICE\bin\x64sc.exe" set PATH=%USERPROFILE%\VICE\bin;%PATH%

REM Check for cc65
where %CC% >nul 2>&1
if errorlevel 1 (
    echo ERROR: cc65 not found
    echo.
    echo Searched: C:\cc65, Program Files, %USERPROFILE%\cc65
    echo.
    echo Install cc65 from: https://cc65.github.io/
    echo Extract to C:\cc65 and re-run this script
    exit /b 1
)

REM Parse command line
if "%1"=="clean" goto clean
if "%1"=="run" goto build_and_run
goto build

:build
echo ============================================================
echo UTLP C64 HAL - Building for Commodore 64
echo ============================================================
echo.

REM Copy and transform source files for C89 compatibility
echo.
echo Step 1: Copying source files from main project...
copy /Y "..\utlp_skeleton\utlp_skeleton.c" "utlp_skeleton_c99.c" >nul
copy /Y "..\utlp_skeleton\utlp_hal.h" "utlp_hal_c99.h" >nul
if errorlevel 1 (
    echo ERROR: Failed to copy source files
    exit /b 1
)

echo Step 2: Transforming C99 to C89 for cc65 compatibility...
python c89_transform.py utlp_skeleton_c99.c utlp_skeleton.c
if errorlevel 1 (
    echo ERROR: Failed to transform utlp_skeleton.c
    echo Make sure Python is installed and in PATH
    exit /b 1
)
python c89_transform.py utlp_hal_c99.h utlp_hal.h
if errorlevel 1 (
    echo ERROR: Failed to transform utlp_hal.h
    exit /b 1
)

echo Step 3: Applying C64-specific patches...
echo If this builds, UTLP is truly Universal!
echo.

REM Compile each source file
echo Compiling utlp_skeleton.c...
%CC% %CFLAGS% -c utlp_skeleton.c -o utlp_skeleton.o
if errorlevel 1 goto compile_error

echo Compiling utlp_hal_c64.c...
%CC% %CFLAGS% -c utlp_hal_c64.c -o utlp_hal_c64.o
if errorlevel 1 goto compile_error

echo Compiling utlp_main_c64.c...
%CC% %CFLAGS% -c utlp_main_c64.c -o utlp_main_c64.o
if errorlevel 1 goto compile_error

REM Link
echo Linking %TARGET%...
%CC% %CFLAGS% -o %TARGET% utlp_skeleton.o utlp_hal_c64.o utlp_main_c64.o
if errorlevel 1 goto link_error

echo.
echo ============================================================
echo BUILD SUCCESSFUL: %TARGET%
echo ============================================================
echo.
echo To run in VICE: build.bat run
echo Or manually:    %VICE% %TARGET%
goto end

:build_and_run
call :build
if errorlevel 1 exit /b 1

echo.
echo Starting VICE emulator...
echo Press STOP+RESTORE in VICE to exit
%VICE% %TARGET%
goto end

:clean
echo Cleaning build artifacts...
del /q *.o 2>nul
del /q %TARGET% 2>nul
REM Transformed files
del /q utlp_skeleton.c 2>nul
del /q utlp_skeleton_c99.c 2>nul
del /q utlp_hal.h 2>nul
del /q utlp_hal_c99.h 2>nul
REM Build outputs
del /q *.map 2>nul
del /q *.lbl 2>nul
echo Done.
goto end

:compile_error
echo.
echo ERROR: Compilation failed!
exit /b 1

:link_error
echo.
echo ERROR: Linking failed!
exit /b 1

:end
endlocal
