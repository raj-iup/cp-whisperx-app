@echo off
REM Common logging functions for Windows batch scripts
REM Usage: call scripts\common-logging.bat :function_name "message"
REM Example: call scripts\common-logging.bat :log_info "Starting build"

if "%1"=="" goto :show_usage
goto %1

:log_debug
if /i "%LOG_LEVEL%"=="DEBUG" (
    echo [%date% %time%] [DEBUG] %~2
    if not "%LOG_FILE%"=="" echo [%date% %time%] [DEBUG] %~2 >> "%LOG_FILE%"
)
goto :eof

:log_info
echo [%date% %time%] [INFO] %~2
if not "%LOG_FILE%"=="" echo [%date% %time%] [INFO] %~2 >> "%LOG_FILE%"
goto :eof

:log_warn
echo [%date% %time%] [WARN] %~2
if not "%LOG_FILE%"=="" echo [%date% %time%] [WARN] %~2 >> "%LOG_FILE%"
goto :eof

:log_error
echo [%date% %time%] [ERROR] %~2 1>&2
if not "%LOG_FILE%"=="" echo [%date% %time%] [ERROR] %~2 >> "%LOG_FILE%"
goto :eof

:log_critical
echo [%date% %time%] [CRITICAL] %~2 1>&2
if not "%LOG_FILE%"=="" echo [%date% %time%] [CRITICAL] %~2 >> "%LOG_FILE%"
goto :eof

:log_success
echo [%date% %time%] [SUCCESS] %~2
if not "%LOG_FILE%"=="" echo [%date% %time%] [SUCCESS] %~2 >> "%LOG_FILE%"
goto :eof

:log_failure
echo [%date% %time%] [FAILURE] %~2 1>&2
if not "%LOG_FILE%"=="" echo [%date% %time%] [FAILURE] %~2 >> "%LOG_FILE%"
goto :eof

:log_section
echo ======================================================================
echo %~2
echo ======================================================================
if not "%LOG_FILE%"=="" (
    echo ====================================================================== >> "%LOG_FILE%"
    echo %~2 >> "%LOG_FILE%"
    echo ====================================================================== >> "%LOG_FILE%"
)
goto :eof

:show_usage
echo Common Logging Functions for Windows Batch Scripts
echo.
echo Usage:
echo   call scripts\common-logging.bat :function_name "message"
echo.
echo Functions:
echo   :log_debug     - Debug message (only if LOG_LEVEL=DEBUG)
echo   :log_info      - Info message
echo   :log_warn      - Warning message
echo   :log_error     - Error message (to stderr)
echo   :log_critical  - Critical error (to stderr)
echo   :log_success   - Success message
echo   :log_failure   - Failure message
echo   :log_section   - Section header
echo.
echo Environment Variables:
echo   LOG_LEVEL - Set to DEBUG to see debug messages (default: INFO)
echo   LOG_FILE  - Set to file path to enable file logging
echo.
echo Examples:
echo   call scripts\common-logging.bat :log_info "Starting build process"
echo   call scripts\common-logging.bat :log_error "Build failed"
echo   call scripts\common-logging.bat :log_success "Build completed"
goto :eof
