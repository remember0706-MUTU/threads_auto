@echo off
chcp 65001 > nul
title 쓰레드 테스트 포스팅
cd /d %~dp0
echo 테스트 포스팅 실행 중...
python -X utf8 main.py test
pause
