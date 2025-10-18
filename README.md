# Reducción masiva de imágenes

Este repositorio contiene herramientas para reducir el tamaño de imágenes sin
cambiar su formato original. Incluye:

- Un script de línea de comandos (`reduce_image.py`) capaz de procesar una
  imagen suelta o carpetas completas con subcarpetas y múltiples formatos.
- Una interfaz gráfica moderna (`reduce_images_gui.py`) pensada para usuarios de
  Windows que prefieran trabajar con una ventana interactiva.
- Un guion (`build_windows_exe.bat`) para generar fácilmente un ejecutable de
  Windows con la interfaz gráfica usando [PyInstaller](https://pyinstaller.org/).

## Requisitos

1. [Python 3.10 o superior](https://www.python.org/downloads/).
2. Dependencias de Python instalables con:

   ```bash
   pip install -r requirements.txt
   ```

   > Esto instalará la librería [Pillow](https://python-pillow.org/) necesaria
   > para manipular imágenes. En Windows, Tkinter viene incluido con las
   > distribuciones oficiales de Python, por lo que no requiere instalaciones
   > adicionales.

## Uso desde la línea de comandos

El script puede trabajar con imágenes individuales o carpetas enteras. Cuando
se le pasa una carpeta, explora todas las subcarpetas de forma recursiva y
reduce únicamente los archivos de imagen, dejando intactos los demás.

### Ejemplos

Reducir todas las imágenes de una carpeta (y sus subcarpetas) al 60 % del tamaño
original:

```bash
python reduce_image.py ruta/a/carpeta --scale 0.6
```

Establecer un ancho máximo para todas las imágenes dentro de un directorio. La
altura se ajustará automáticamente manteniendo la proporción y nunca se
superará el tamaño original:

```bash
python reduce_image.py ruta/a/carpeta --width 1280
```

Indicar límites máximos de ancho y alto para una imagen individual (se evita
ampliarla aunque se introduzcan valores mayores):

```bash
python reduce_image.py ruta/a/imagen.jpg --width 800 --height 600
```

> Si sólo se indica el ancho o el alto, la otra dimensión se calcula de forma
> proporcional. Para usar el script es obligatorio especificar al menos una de
> las opciones (`--scale`, `--width` o `--height`).

Tras completar el proceso, el script mostrará en la terminal la lista de
archivos que se modificaron.

## Interfaz gráfica (Windows, macOS y Linux)

La aplicación gráfica ofrece controles intuitivos para elegir la carpeta o la
imagen a procesar, seleccionar entre un porcentaje de reducción o límites de
ancho/alto y revisar un registro en tiempo real del proceso.

Ejecuta la interfaz con:

```bash
python reduce_images_gui.py
```

### Características destacadas

- **Diseño moderno** inspirado en aplicaciones de productividad, con colores
  suaves y tipografías legibles.
- **Registro de actividad en vivo** que detalla cada archivo procesado y marca
  los errores si se presentaran.
- **Procesamiento en segundo plano** para mantener la ventana siempre
  responsive, incluso con lotes grandes de imágenes.
- **Modo porcentaje o límites máximos**, con controles habilitados según la
  opción elegida.

## Generar un ejecutable para Windows

Para crear un `.exe` que puedas distribuir o ejecutar sin abrir la terminal,
utiliza el guion incluido `build_windows_exe.bat` desde una consola de Windows
(PowerShell o CMD). El script instala las dependencias necesarias, ejecuta
PyInstaller y deja el ejecutable en `dist/ReduceImagesGUI.exe`.

```bat
build_windows_exe.bat
```

Si prefieres hacerlo manualmente, estos son los comandos clave:

```bat
python -m pip install -r requirements.txt
python -m pip install pyinstaller
pyinstaller --noconsole --onefile --name ReduceImagesGUI reduce_images_gui.py
```

Una vez finalizado, encontrarás el archivo listo para usar dentro de la carpeta
`dist` que genera PyInstaller. Puedes crear un acceso directo al ejecutable para
que tu equipo lo utilice con doble clic.

## Consejos adicionales

- Mantén una copia de seguridad antes de ejecutar el proceso si necesitas
  conservar las imágenes originales sin cambios.
- Si tienes archivos muy grandes, considera ejecutar la reducción en lotes más
  pequeños para evaluar el resultado antes de procesar toda la colección.
- PyInstaller permite personalizar el icono del ejecutable con el parámetro
  `--icon=tu_icono.ico`.

¡Listo! Con estas herramientas podrás optimizar grandes volúmenes de imágenes
de manera rápida y sin complicaciones.
