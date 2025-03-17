# SoulDown - S3RGI09

**SoulDown** es una aplicación de escritorio en Python que permite descargar álbumes completos o canciones individuales desde YouTube. Ofrece opciones de calidad de audio y organiza automáticamente las descargas en carpetas estructuradas por artista y álbum. Además, permite gestionar una cola de descargas con seguimiento del progreso individual y total.

## Características Principales

- **Descarga de álbumes completos**: Ingresa la URL de una playlist o álbum de YouTube para descargar todas las canciones.
- **Descarga de canciones individuales**: Selecciona canciones específicas de un álbum para su descarga.
- **Opciones de calidad de audio**: Elige entre baja (96kbps), media (128kbps) y alta calidad (320kbps).
- **Organización automática**: Las canciones se guardan en una estructura de carpetas `Artista/Álbum/Canción.mp3`.
- **Descarga de carátulas**: Descarga y asigna automáticamente la carátula del álbum a cada canción.
- **Gestión de cola de descargas**: Añade múltiples álbumes a una cola y descárgalos secuencialmente.
- **Barras de progreso**: Visualiza el progreso de la descarga actual y el progreso total de la cola.
- **Interfaz personalizable**: Interfaz gráfica basada en colores azules y negros para una experiencia visual agradable.

## Requisitos del Sistema

- **Sistema Operativo**: Windows, macOS o Linux con soporte para Python 3.x.
- **Python**: Versión 3.6 o superior.
- **Dependencias**: Las bibliotecas necesarias se detallan en el archivo `requirements.txt`.

## Instalación

1. **Clona o descarga el repositorio**: Obtén el código fuente de SoulDown desde el repositorio oficial.
2. **Navega al directorio del proyecto**:
   - Abre una terminal o línea de comandos.
   - Dirígete al directorio donde se encuentra el proyecto.
3. **Instala las dependencias**:
   - Asegúrate de tener `pip` instalado.
   - Ejecuta el comando `pip install -r requirements.txt` para instalar todas las dependencias necesarias.

## Uso

1. **Ejecuta la aplicación**:
   - En la terminal, dentro del directorio del proyecto, ejecuta `python souldown.py`.
2. **Añadir álbum a la cola**:
   - En la interfaz gráfica, ingresa la URL del álbum o playlist de YouTube en el campo correspondiente.
   - Selecciona la calidad de audio deseada.
   - Haz clic en "Agregar a la cola" para añadir el álbum a la lista de descargas pendientes.
3. **Gestionar la cola**:
   - Visualiza la lista de álbumes en cola en la sección designada.
   - Reordena la lista arrastrando los elementos según tu preferencia.
4. **Descargar cola**:
   - Haz clic en "Descargar cola" para iniciar las descargas.
   - Observa las barras de progreso para el seguimiento de las descargas individuales y del progreso total de la cola.

## Licencia

Este proyecto está bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.
