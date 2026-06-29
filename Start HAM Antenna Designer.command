#!/bin/bash
# Double-click this file to launch the HAM Antenna Designer GUI.
cd "$(dirname "$0")"
source .venv/bin/activate
python3 gui.py
