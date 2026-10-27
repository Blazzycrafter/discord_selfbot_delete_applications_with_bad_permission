@echo off
chcp 65001 >nul
title Discord Apps Cleaner
mode con cols=90 lines=40
color 0F
cd /d "%~dp0"
python main.py
if errorlevel 1 pause
