# PulsarLab

## Descripción

**PulsarLab** es una herramienta científica de análisis y visualización de la evolución rotacional de los púlsares, desarrollada para facilitar la inspección de modelos de temporización, el estudio de glitches, el análisis de fase, el diagnóstico de residuos y la comparación de modelos.

La aplicación permite cargar datos observacionales y parámetros de temporización de púlsares mediante archivos `.dat` y `.par`, analizar matemáticamente su comportamiento rotacional y visualizar su evolución a través del tiempo.

PulsarLab considera tanto la evolución regular del púlsar como las modificaciones producidas por eventos de tipo **glitch**, permitiendo comparar gráficamente el comportamiento del modelo con y sin estos eventos.

## Funcionalidades principales

### Carga y análisis de archivos

PulsarLab permite:

* Cargar archivos de parámetros `.par`.
* Cargar archivos observacionales `.dat`.
* Trabajar con archivos que contienen parámetros asociados a glitches.
* Gestionar los parámetros del modelo mediante una configuración predeterminada editable.
* Cargar hasta dos conjuntos de datos para realizar comparaciones.

### Análisis de la fase rotacional

La aplicación permite estudiar matemáticamente la evolución de la fase rotacional del púlsar a partir de parámetros contenidos en los archivos de entrada, entre ellos:

* `F0`: frecuencia rotacional.
* `F1`: primera derivada de la frecuencia.
* `F2`: segunda derivada de la frecuencia.
* `F3`: tercera derivada de la frecuencia.

Los cálculos pueden incorporar las modificaciones provocadas por glitches, permitiendo estudiar cómo estos eventos afectan la evolución rotacional del púlsar.

### Análisis de glitches

PulsarLab permite:

* Identificar glitches presentes en los modelos de temporización.
* Incorporar sus efectos dentro de los cálculos de fase.
* Analizar su evolución respecto del tiempo de observación.
* Comparar el comportamiento del modelo considerando o ignorando los glitches.
* Examinar parámetros asociados a la recuperación posterior a un glitch.

### Visualización de resultados

La aplicación genera representaciones gráficas que permiten:

* Analizar la evolución rotacional del púlsar a través del tiempo.
* Visualizar la fase y sus derivadas.
* Comparar resultados con y sin glitches.
* Representar temporalmente los glitches presentes durante el período de observación.
* Analizar residuos del modelo.
* Comparar diferentes conjuntos de datos.
* Preparar figuras para análisis y publicaciones científicas.

## Flujo de trabajo desde la terminal local

Desde la raíz del proyecto, instala PulsarLab mediante:

```powershell
pip install -e .
```

Luego ejecuta:

```powershell
plab glitAD.par allVF.dat
```

Este comando inicia automáticamente la interfaz de Streamlit y precarga el modelo de temporización `.par` y el conjunto de datos observacionales `.dat`.

Puedes encontrar información adicional sobre la instalación en:

[`INSTALL_LOCAL.md`](INSTALL_LOCAL.md)

## Inicio rápido

También es posible preparar manualmente el entorno de ejecución mediante Conda:

```powershell
conda create -n pulsarlab python=3.11
conda activate pulsarlab
pip install -r requirements.txt
streamlit run run_app.py
```

Una vez iniciada la aplicación, la interfaz permite cargar los archivos correspondientes al púlsar, modificar la configuración del modelo y generar los análisis y gráficos disponibles.

## Estructura del proyecto

```text
app/        Interfaz de Streamlit y gestión del estado
core/       Parsers, modelo de spin, modelo de fase, glitches, residuos y ajuste
plotting/   Utilidades de gráficos mediante Plotly y matplotlib
exports/    Módulos reservados para futuras funciones de informes y exportación
data/       Almacenamiento local opcional para archivos .par y .dat
notebooks/  Notebooks opcionales para análisis y trabajo exploratorio
```

## Comparación de conjuntos de datos

La barra lateral de PulsarLab dispone de dos espacios para cargar conjuntos de datos.

Cada espacio permite cargar:

* Un archivo `.par` con los parámetros del modelo de temporización.
* Un archivo `.dat` con los datos observacionales.

Después de cargar ambos conjuntos, las casillas de visibilidad permiten seleccionar cuáles serán representados en los gráficos, facilitando la comparación entre diferentes modelos, observaciones o configuraciones.
