@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

rem ARRANQUE LIMPIO: matar escaneres y vigias de corridas anteriores, para no duplicar.
rem Los titulos de MIS ventanas empiezan con "Celulares" (NO con "SinBuque"), asi que estos
rem filtros NO pueden tocar la app de control remoto SinBuque. scrcpy.exe es exclusivo nuestro.
rem (Esta ventana todavia NO tiene titulo "Celulares...", asi que no se mata a si misma.)
taskkill /f /fi "windowtitle eq Celulares*" >nul 2>&1
taskkill /f /im scrcpy.exe >nul 2>&1

title Celulares (escaner)

echo ============================================
echo   SinBuque - Ver y controlar celulares
echo ============================================
echo.

if not exist "%~dp0adb.exe" (
  echo ERROR: no encuentro adb.exe en esta carpeta.
  echo Abriste el .bat SIN extraer el ZIP.
  echo   1^) Clic derecho en el ZIP ^> Extraer todo.
  echo   2^) Entra a la carpeta ya extraida.
  echo   3^) Recien ahi corre este archivo.
  echo.
  pause
  exit /b
)

echo Vigilando. Enchufa los celulares que quieras, cuando quieras:
echo cada uno autorizado se abre solo y agarra un puerto libre.
echo Para detener todo: corre "Detener.bat". Esta ventana podes minimizarla.
echo.
adb.exe start-server >nul 2>&1

:scan
for /f "skip=1 tokens=1,2" %%a in ('adb.exe devices') do (
  if "%%b"=="device" (
    if not defined seen_%%a (
      set "seen_%%a=1"
      echo [%time%] Abriendo celu %%a
      start "Celulares %%a" "%~dp0vigia-un-celu.bat" %%a
      timeout /t 1 >nul
    )
  ) else (
    if not defined warned_%%a (
      set "warned_%%a=1"
      echo [%time%] Celu %%a conectado pero SIN LISTO ^(estado: %%b^). Autorizalo en el telefono.
    )
  )
)
timeout /t 5 >nul
goto scan
