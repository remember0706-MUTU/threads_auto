@echo off
chcp 65001 > nul
title 쓰레드 자동 포스팅 스케줄러
cd /d %~dp0
echo 쓰레드 자동 포스팅 스케줄러 시작 중...
python -X utf8 main.py
pause
