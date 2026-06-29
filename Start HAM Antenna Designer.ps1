# Double-click this file to launch the HAM Antenna Designer GUI on Windows (PowerShell).
# Right-click → Run with PowerShell

Push-Location $PSScriptRoot
& ".\.venv\Scripts\Activate.ps1"
python gui.py
Read-Host "Press Enter to exit"
