@echo off
REM Run Docker stage with GPU fallback
REM
REM Usage:
REM   run-docker-stage.bat asr --movie-dir out/Movie_Name --try-gpu
REM   run-docker-stage.bat asr --movie-dir out/Movie_Name --no-gpu

setlocal

python scripts\run_docker_stage.py %*

endlocal
exit /b %ERRORLEVEL%
