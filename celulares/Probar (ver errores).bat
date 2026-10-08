@echo off
chcp 65001 >nul
cd /d "%~dp0"
title SinBuque - probar un celu

echo ============================================
echo   SinBuque - Probar un celu (para ver errores^)
echo ============================================
echo.
adb.exe start-server >nul 2>&1
echo Celulares conectados:
adb.exe devices
echo.
set "S="
set /p S=Pega el SERIAL del celu que falla y Enter:
if "%S%"=="" (
  echo No escribiste ningun serial.
  pause
  exit /b
)
echo.
echo Abriendo %S% una sola vez (sin audio^). Si falla, el error queda abajo.
echo.
scrcpy.exe -s %S% --window-title "SinBuque %S%" --stay-awake --no-audio --force-adb-forward
echo.
echo ===== scrcpy termino. Si hay un error arriba, mandamelo tal cual. =====
pause
