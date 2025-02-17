@echo off

pip show pyinstaller >nul 2>nul
if %errorlevel% neq 0 (
    echo Try to install PyInstaller...
    pip install pyinstaller
) else (
    echo PyInstaller already exist...
)

pyinstaller --onefile --windowed --icon=static/cokeserver.ico .\main.py

pause
