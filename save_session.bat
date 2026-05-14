@echo off
chcp 65001 > nul
title Threads 로그인 세션 저장
cd /d %~dp0
echo.
echo ======================================
echo  Threads 로그인 세션 저장 (최초 1회)
echo ======================================
echo 브라우저가 열리면 Threads에 로그인해주세요.
echo 로그인 완료되면 자동으로 세션이 저장됩니다.
echo.
python -X utf8 save_session.py
echo.
echo 완료! 이제 run_scheduler.bat을 실행하세요.
pause
