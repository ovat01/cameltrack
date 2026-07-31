# DJ CamelTrack

DJ CamelTrack es una aplicación de escritorio para Windows desarrollada en Python y PyQt6 que realiza un análisis avanzado (DSP) de bibliotecas musicales para DJs. Detecta automáticamente BPM, tono musical, clave Camelot, LUFS, y más.

## Requisitos Previos (Windows)

1. **Instalar Python:**
   - Descarga e instala Python 3.10 o superior desde la página oficial: [python.org/downloads/windows/](https://www.python.org/downloads/windows/).
   - **IMPORTANTE:** Durante la instalación, asegúrate de marcar la casilla que dice **"Add Python to PATH"** (Agregar Python al PATH).

2. **Instalar FFmpeg:**
   - FFmpeg es necesario para analizar formatos de audio.
   - Puedes instalarlo fácilmente a través del módulo de Python que ya hemos incluido, o instalarlo manualmente en Windows si es necesario para librosa.

## Instrucciones de Instalación

1. **Descargar el código:**
   Descarga o clona este repositorio en tu computadora y descomprímelo en una carpeta (por ejemplo, en `C:\DJ_CamelTrack`).

2. **Abrir la terminal:**
   - Presiona `Win + R`, escribe `cmd` y presiona Enter para abrir el Símbolo del sistema.
   - Navega a la carpeta donde guardaste el proyecto usando el comando `cd`. Por ejemplo:
     ```bash
     cd C:\DJ_CamelTrack
     ```

3. **Crear un entorno virtual (Recomendado):**
   Es buena práctica instalar las librerías en un entorno aislado. Ejecuta:
   ```bash
   python -m venv venv
   ```
   Luego, actívalo con:
   ```bash
   venv\Scripts\activate
   ```
   *(Verás que la terminal ahora empieza con `(venv)`).*

4. **Instalar las dependencias:**
   Con el entorno virtual activado (o directamente en tu sistema), instala todas las librerías necesarias ejecutando:
   ```bash
   pip install -r requirements.txt
   ```

5. **Ejecutar la aplicación (Modo Desarrollo):**
   Una vez instaladas todas las dependencias sin errores, puedes iniciar la aplicación directamente ejecutando:
   ```bash
   python main.py
   ```

## Generar un Archivo Ejecutable (.exe)

Si prefieres tener un único archivo `.exe` para no tener que abrir la consola de comandos cada vez, puedes compilar la aplicación utilizando `PyInstaller`.

### Opción A: Usar el script automático (Más fácil)
1. Simplemente haz doble clic en el archivo **`build.bat`** que se encuentra en la carpeta del proyecto.
2. Esto abrirá una consola, descargará lo necesario y creará el ejecutable automáticamente.

### Opción B: Modo Manual desde la Terminal
1. Abre tu terminal (Asegúrate de tener el entorno virtual activado si creaste uno).
2. Ejecuta el siguiente comando:
   ```bash
   pyinstaller --noconfirm --onedir --windowed --name "DJ CamelTrack" main.py
   ```
   - `--onedir`: Crea una carpeta con el `.exe` y todas sus dependencias (recomendado para aplicaciones grandes y rápidas de abrir).
   - `--windowed`: Evita que se abra la fea consola negra de Windows detrás de la aplicación.
3. Espera a que el proceso termine (puede tardar unos minutos).

### ¿Dónde encuentro mi `.exe`?
Una vez finalizado, verás una nueva carpeta llamada **`dist`** en tu proyecto.
Entra a `dist \ DJ CamelTrack \` y allí encontrarás el archivo **`DJ CamelTrack.exe`**.
Puedes crear un acceso directo de ese archivo y ponerlo en tu Escritorio.

¡Listo! Ya deberías ver la interfaz gráfica de DJ CamelTrack y comenzar a analizar tu música de forma fácil y profesional.
