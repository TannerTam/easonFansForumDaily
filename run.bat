@echo off
set LOGFILE=script_log.log
CALL conda activate easonForum
python login.py >> %LOGFILE% 2>&1
echo %date% %time%: Script execution completed >> %LOGFILE%
echo. >> %LOGFILE%
