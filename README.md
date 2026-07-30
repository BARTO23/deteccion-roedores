# Detector de Roedores en Cultivos

Aplicación de escritorio para detectar roedores en cultivos mediante análisis de imagen térmica, inspirándose en un script original de MATLAB.

## Descripción

El programa recibe dos imágenes:
- **Imagen térmica (.tif)**: Imagen infrarroja donde aparecen rastros de calor de roedores
- **Imagen visible (.jpg/.png)**: Fotografía del mismo cultivo tomada por dron

El sistema detecta la presencia de roedores en la imagen térmica, estima su posición, cuenta cuántos hay, y proyecta esos puntos sobre la imagen del dron para visualización y exportación.

## Algoritmo

Replica exactamente el script MATLAB original (`identificación de roedores.txt`).

Para cada píxel interior de la imagen térmica (`x = 2..W-1`, `y = 2..H-1` en índices
MATLAB) se compara el píxel central `B` contra sus 4 vecinos ortogonales **de forma
independiente** (no contra su promedio):

```
b = abs(abs(B) - abs(vecino))
cuenta si:  B > vecino   y   T < b < 1000
```

Se marca detección cuando **al menos 3 de los 4 vecinos** cumplen (`c > 2` en el
original). La cota superior `b < 1000` es la que descarta el fondo de la imagen
(valor `-32767`): la diferencia contra el fondo es enorme y nunca pasa el filtro.

Diferencias deliberadas respecto al original:

- **Escalado de coordenadas**: MATLAB dibujaba en coordenadas de la térmica sobre la
  figura de la visible. Como las imágenes no tienen el mismo tamaño (9992×8835 vs
  9750×8511), eso desplazaba los puntos hasta ~300 px en los bordes. Aquí se reescalan.
- **Agrupamiento opcional**: el original cuenta un roedor por cada píxel que dispara,
  así que un animal repartido en píxeles contiguos se contaba varias veces. La opción
  "Agrupar píxeles contiguos" une las detecciones vecinas en un solo punto.
- **Vectorizado por bloques de filas**: mismo resultado que el doble ciclo píxel a
  píxel, pero procesa una térmica de 88 M de píxeles en ~3 s en vez de horas.

## Requisitos

- Python 3.12 o superior
- Windows 10/11 (el código está optimizado para Windows)

## Instalación

### 1. Clonar o descargar el proyecto

```powershell
cd C:\Users\juanp\Dev\deteccion-roedores
```

### 2. Crear entorno virtual

```powershell
python -m venv venv --without-pip
.\venv\Scripts\python.exe -m pip install --upgrade pip
```

### 3. Instalar dependencias

```powershell
.\venv\Scripts\pip.exe install -r requirements.txt
```

### 4. Ejecutar la aplicación

```powershell
.\venv\Scripts\python.exe app.py
```

## Uso

1. **Ejecutar la app**: `python app.py`
2. **Cargar imagen térmica**: Click en "Cargar TIF Térmico" y selecciona tu archivo `.tif`
3. **Cargar imagen visible**: Click en "Cargar PNG Visible" y selecciona tu archivo `.jpg` o `.png`
4. **Ajustar umbral**: El valor por defecto es 0.56, el mismo `T` del script MATLAB
   - Valores menores = más detecciones
   - Valores mayores = menos detecciones
5. **Detectar**: Click en "Detectar" para ejecutar el algoritmo
6. **Ver resultados**: La imagen con círculos rojos aparece en el panel central
7. **Exportar**:
   - "Exportar Imagen": Guarda la imagen con los círculos dibujados
   - "Exportar CSV": Guarda las coordenadas (x, y) de cada detección

## Parámetros de detección

| Parámetro | Default | Descripción |
|-----------|---------|-------------|
| `T` (umbral) | 0.56 | Delta mínimo de temperatura contra un vecino. Es el `T` del original |
| Vecinos mínimos | 3 | Cuántos de los 4 vecinos deben cumplir (`c > 2` en el original) |
| Delta máximo | 1000 | Cota superior que descarta el fondo. Constante del original |

Conteos medidos sobre `img-test/Or17-18.tif` (8835×9992) con el algoritmo fiel:

| Umbral T | Píxeles detectados | Agrupados (radio 3) |
|----------|--------------------|---------------------|
| 0.50     | 798                | ~760                |
| 0.54     | 339                | ~324                |
| 0.56     | **227**            | **217**             |
| 0.58     | 156                | ~148                |
| 0.60     | 97                 | —                   |
| 0.64     | 47                 | —                   |

Con el valor original **T = 0.56** el resultado es **227 píxeles / 217 roedores agrupados**.

> Nota: versiones anteriores de este README citaban ~194 detecciones con T=0.58. Ese
> número venía de una implementación que promediaba los 4 vecinos — un algoritmo
> distinto al del script MATLAB. Las cifras de la tabla son del algoritmo fiel.
> Si tu corrida de MATLAB da otro conteo, calibrá `T` contra ese valor de referencia.

## Estructura del proyecto

```
deteccion_roedores/
├── core/
│   ├── image_loader.py      # Lectura de imágenes TIF/JPG/PNG
│   ├── detector.py          # Detección térmica (réplica del MATLAB)
│   ├── blob_analyzer.py     # Agrupamiento de detecciones contiguas
│   └── projector.py         # Proyección de puntos sobre imagen visible
├── ui/
│   ├── main_window.py       # Interfaz gráfica con PySide6
│   ├── styles.py            # Paleta y hoja de estilos QSS
│   └── worker.py            # Detección en QThread (no bloquea la UI)
├── utils/
│   ├── logger.py            # Logging de la aplicación
│   └── exporter.py         # Exportación de resultados
├── img-test/                # Imágenes de prueba
│   ├── Or17-18.tif         # Imagen térmica
│   └── Or17-18-foto1.jpg  # Imagen visible
├── app.py                   # Punto de entrada
├── requirements.txt        # Dependencias
└── SPEC.md                # Especificación técnica
```

## Tecnologías utilizadas

- **OpenCV**: Procesamiento de imágenes y dibujo
- **NumPy**: Manejo de matrices
- **scikit-image**: Análisis de componentes conectados
- **tifffile**: Lectura de imágenes TIFF
- **PySide6**: Interfaz gráfica de escritorio

## Notas

- Las dos imágenes deben corresponder a la misma zona (mismo vuelo)
- El programa escala automáticamente las coordenadas si las imágenes tienen diferentes tamaños
- Los puntos fuera de los límites de la imagen visible se descartan automáticamente

## Licencia

Proyecto de uso interno - Detección de roedores en cultivos