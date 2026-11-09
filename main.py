"""
Entry point for Griductive Solver NiceGUI application.
CSC14003 - Project 2
"""
import os
import sys

# Ensure project root is in python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from nicegui import ui
from ui.app import create_ui

if __name__ in {"__main__", "__mp_main__"}:
    create_ui()
    print("Starting Griductive Solver Web UI on http://127.0.0.1:8080 ...")
    ui.run(
        title="Griductive Solver - CSC14003",
        host="127.0.0.1",
        port=8080,
        reload=False,
        dark=True,
    )
