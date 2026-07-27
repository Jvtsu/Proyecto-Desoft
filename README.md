# PulsarLab

## PulsarLab es una herramienta de analisis y visualizacion de la evolución rotacional de los pulsares.
La interfaz del proyecto se encuentra implementada dentro del archivo etapa3_pulsar.ipynb, desarrollado para ejecutarse en un entorno con Jupyter Notebook. A través de esta interfaz es posible cargar parámetros de púlsares, modificar configuraciones del modelo y analizar gráficamente el comportamiento de la fase rotacional tomando en cuenta la presencia de glitches.

## Funcionalidades principales
Nuestra interfaz permite:
- Carga y analisis de archivos de entrada:
  -Implementar archivos .dat y .par
  -Soporte para archivos con glitches
  -Manejo de parametros en funcion de una configuracion predeterminada editable

- Analisis matematico de la fase rotacional del pulsar:
  -Se calcula la evolución de la fase en base a los siguientes parametros de los archivos:
    -F0 / F1 / F2 / F3
  -Consideracion de modificaciones provocadas por el glitch incluidos en los calculos
- Visualización de resultados:
  -Generar graficos para analizar la evolucion a traves del tiempo del púlsar
  -Comparacion del comportamiento de los calculos con y sin glitches
  -Muestreo de glitches en funcion del tiempo de toma de datos del pulsar.

## Ejecución
Para utilizar la interfaz de PulsarLab se requiere:
- Entorno con Python y Jupyter Notebook instalado
- Descargar o clonar este repositorio
- Instalar dependencias
- Ejecutar el archivo etapa3_pulsar.ipynb

Una vez ejecutado el notebook, la interfaz permitirá cargar los archivos del púlsar, modificar la configuración del modelo y generar los graficos correspondientes.
