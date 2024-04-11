@echo off
set LOGFILE=script_log.log
echo %date:~0,10% %time:~0,8%  script start >> %LOGFILE%
CALL conda activate easonForum
python login.py >> %LOGFILE% 2>&1
echo. >> %LOGFILE%
