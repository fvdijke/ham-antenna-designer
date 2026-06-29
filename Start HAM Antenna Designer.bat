@echo off
REM Double-click this file to launch the HAM Antenna Designer GUI on Windows.
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python gui.py
pause
