@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   SinBuque - Diagnostico de celulares
echo ============================================
echo.
adb.exe start-server >nul 2>&1
echo Celulares que ve esta PC por USB:
echo.
adb.exe devices -l
echo.
echo COMO LEERLO:
echo   device        = listo, se puede ver y controlar.
echo   unauthorized  = falta tocar "Permitir siempre..." en ESE telefono.
echo   offline       = cable/puerto flojo; probar otro cable u otro puerto USB.
echo   (no aparece^)  = falta Depuracion USB, driver, o modo USB en "Solo carga".
echo.
pause
