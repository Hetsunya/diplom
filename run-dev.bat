@echo off
REM === Backend ===
start "emeeting-backend" cmd /k ^
cd /d "%~dp0code\emeeting-backend" ^&^& go run .\cmd\server\main.go

REM === Frontend ===
start "emeeting-ui" cmd /k ^
cd /d "%~dp0code\emeeting-ui" ^&^& npm run dev
