@echo off
rem Vigia de UN celular. Lo lanza "Ver celulares.bat".
rem %1 = serial del celular. %2 = puerto o rango (opcional).
cd /d "%~dp0"
set SERIAL=%~1
set PORT=%~2
if "%PORT%"=="" set PORT=27183:27299
rem Titulo que empieza con "Celulares" (NO "SinBuque") para que Detener no roce el control remoto.
title Celulares %SERIAL%

:loop
rem Esperar a que el celu este presente (aguanta reinicios y reconexiones de USB).
adb.exe -s %SERIAL% wait-for-device >nul 2>&1

rem Abrir scrcpy; BLOQUEA hasta que se cierra la ventana o se cae el celu.
rem --no-audio: en Android 14 la captura de audio crashea scrcpy al arrancar.
rem --force-adb-forward: MIUI/Xiaomi bloquea el 'adb reverse' por defecto (Connection refused).
rem --port RANGO: scrcpy elige un puerto libre solo; asi NO chocan varios celus a la vez.
scrcpy.exe -s %SERIAL% --port %PORT% --window-title "SinBuque %SERIAL%" --stay-awake --no-audio --force-adb-forward

rem Si llegamos aca, la sesion termino. Esperar un toque y reintentar.
timeout /t 3 >nul
goto loop
