@echo off
REM Launches the Dota Coach: the context GUI and the coach server, each in its
REM own window. Run this from anywhere; it uses its own folder as the project.

cd /d "%~dp0"

start "Dota Context" cmd /k uv run dota-context
start "Dota Coach" cmd /k uv run dota-coach