@echo off
setlocal ENABLEDELAYEDEXPANSION

rem Construye el ejecutable "Reduccion de imagenes de Arquinnova S.L. y creado por Marco Salguero Rissiotti.exe" con PyInstaller
pushd %~dp0

if not exist "%SystemRoot%\System32\where.exe" goto nowhere
where python >nul 2>&1
if errorlevel 1 (
    echo No se encontro Python en el PATH. Instala Python 3.10 o superior y vuelve a ejecutar este script.
    goto end
)

if exist .venv\Scripts\python.exe (
    echo Activando el entorno virtual .venv...
    call .venv\Scripts\activate
)

echo Instalando dependencias...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install pyinstaller

echo.
set "APP_NAME=Reduccion de imagenes de Arquinnova S.L. y creado por Marco Salguero Rissiotti"
echo Construyendo ejecutable %APP_NAME%.exe ...
pyinstaller --noconsole --onefile --name "%APP_NAME%" reduce_images_gui.py
if errorlevel 1 (
    echo.
    echo Ocurrio un error al generar el ejecutable.
    goto end
)

echo.
echo ¡Listo! Encontraras el ejecutable en "dist\%APP_NAME%.exe"

goto end

:nowhere
echo No se encontro la utilidad WHERE; este script requiere Windows 7 o superior.

goto end

:end
popd
pause
endlocal
