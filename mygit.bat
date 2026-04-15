@echo off
if "%~1"=="" (
    echo Usage: git.bat "your commit message"
    exit /b 1
)

git add .
git commit -m "%~1"
git push origin main
git status
