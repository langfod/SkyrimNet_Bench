@echo off
setlocal enabledelayedexpansion


:: === CONFIGURATION ===
set "skyrimnet_skse_log=C:\Users\langf\OneDrive\Smokey\Documents\My Games\Skyrim Special Edition\SKSE"
set "skyrim_game=D:\SteamLibrary\steamapps\common\Skyrim Special Edition"
set "skyrimnet_logs=%skyrim_game%\Data\skse\Plugins\SkyrimNet\logs"
set "logarchive_folder=D:\temp\skyrimnet_logarchive"


:: === GET LAST MODIFIED TIMESTAMP OF SkyrimNet.log ===
for %%F in ("%skyrimnet_skse_log%\SkyrimNet.log") do (
    set "filedate=%%~tF"
)

:: filedate format  into YYYYMMDDHHMM
for /f "tokens=1,2 delims= " %%a in ("!filedate!") do (
    set "datepart=%%a"
    set "timepart=%%b"
)

:: Split date (MM/DD/YYYY) and time (HH:MM)
for /f "tokens=1-3 delims=/" %%a in ("!datepart!") do (
    set "mm=%%a"
    set "dd=%%b"
    set "yyyy=%%c"
)

for /f "tokens=1,2 delims=:" %%a in ("!timepart!") do (
    set "hh=%%a"
    set "min=%%b"
)

:: Handle 12-hour clock AM/PM if present
echo !timepart! | findstr /i "PM" >nul
if !errorlevel! == 0 (
    if not "!hh!"=="12" set /a hh=hh+12
)
echo !timepart! | findstr /i "AM" >nul
if !errorlevel! == 0 (
    if "!hh!"=="12" set hh=00
)

:: Zero-pad hour if needed
if 1!hh! LSS 110 set hh=0!hh!


set "datetime=!yyyy!!mm!!dd!!hh!!min!"

:: === CREATE ARCHIVE FOLDER ===
set "target=%logarchive_folder%\!datetime!"
if not exist "%target%" mkdir "%target%"

:: === MOVE FILES ===
move "%skyrimnet_skse_log%\SkyrimNet.log" "%target%" >nul
move "%skyrimnet_logs%\*.log" "%target%" >nul

echo Logs archived to: %target%


cd /d %skyrim_game%


start skse64_loader.exe"


endlocal