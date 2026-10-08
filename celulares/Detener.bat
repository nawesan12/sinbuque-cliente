@echo off
chcp 65001 >nul
echo Deteniendo SOLO las ventanas de los celulares (NO toca la app SinBuque de la PC)...
rem Mis ventanas se llaman "Celulares ..." -> este filtro NO puede alcanzar a SinBuque.exe,
rem que empieza con "SinBuque" y ademas es otro programa.
taskkill /f /fi "windowtitle eq Celulares*" >nul 2>&1
rem scrcpy.exe es exclusivo de esta herramienta; matarlo por nombre no afecta a SinBuque.exe.
taskkill /f /im scrcpy.exe >nul 2>&1
echo Listo. La sesion remota de SinBuque sigue intacta.
timeout /t 3 >nul
