@echo off
setlocal
cd /d "%~dp0"
py c_drive_cleaner.py %*
if errorlevel 1 (
  echo.
  echo Failed to start. Make sure Python Launcher is installed and available as "py".
  echo You can also run: python c_drive_cleaner.py
  pause
)
