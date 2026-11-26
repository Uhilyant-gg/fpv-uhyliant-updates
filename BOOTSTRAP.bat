@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 tools\project_bootstrap.py --root "%~dp0"
) else (
  python tools\project_bootstrap.py --root "%~dp0"
)
exit /b %errorlevel%
