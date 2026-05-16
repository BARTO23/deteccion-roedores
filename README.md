# Detector de Roedores en Cultivos

Aplicación de escritorio para detectar roedores en cultivos mediante análisis de imagen térmica, inspirándose en un script original de MATLAB.

## Descripción

El programa recibe dos imágenes:
- **Imagen térmica (.tif)**: Imagen infrarroja donde aparecen rastros de calor de roedores
- **Imagen visible (.jpg/.png)**: Fotografía del mismo cultivo tomada por dron

El sistema detecta la presencia de roedores en la imagen térmica, estima su posición, cuenta cuántos hay, y proyecta esos puntos sobre la imagen del dron para visualización y exportación.

## Algoritmo

El método de detección replica la lógica del script MATLAB original:
1. Recorre la imagen térmica píxel a píxel
2. Compara el valor central con el promedio de sus 4 vecinos (arriba, abajo, izquierda, derecha)
3. Aplica un umbral de sensibilidad T (por defecto 0.58)
4. Marca como detección cuando la diferencia supera el umbral
5. Escala las coordenadas para proyectarlas sobre la imagen visible

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
4. **Ajustar umbral**: El valor por defecto es 0.58 (aproximadamente 194 detecciones para imágenes de prueba)
   - Valores menores = más detecciones
   - Valores mayores = menos detecciones
5. **Detectar**: Click en "Detectar" para ejecutar el algoritmo
6. **Ver resultados**: La imagen con círculos rojos aparece en el panel central
7. **Exportar**:
   - "Exportar Imagen": Guarda la imagen con los círculos dibujados
   - "Exportar CSV": Guarda las coordenadas (x, y) de cada detección

## Parámetros de detección

| Umbral | Detecciones aproximadas |
|--------|-------------------------|
| 0.50   | ~845                    |
| 0.54   | ~393                    |
| 0.58   | ~194                    |
| 0.60   | ~144                    |
| 0.64   | ~83                     |

El valor recomendado es **0.58** que se aproxima a los 198 roedores del script MATLAB original.

## Estructura del proyecto

```
deteccion_roedores/
├── core/
│   ├── image_loader.py      # Lectura de imágenes TIF/JPG/PNG
│   ├── detector.py          # Algoritmo de detección térmica
│   ├── blob_analyzer.py     # Análisis de componentes (no usado en v1)
│   └── projector.py         # Proyección de puntos sobre imagen visible
├── ui/
│   └── main_window.py       # Interfaz gráfica con PySide6
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