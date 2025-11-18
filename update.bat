@echo off
git add .
set /p msg="Введите комментарий коммита: "
git commit -m "%msg%"
git push
pause