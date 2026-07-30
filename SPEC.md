# Especificación Técnica: Detector de Roedores en Cultivos

## 1. Visión del Proyecto

Aplicación de escritorio en Python para detectar roedores en cultivos mediante análisis de imagen térmica, proyectando resultados sobre imagen visible del dron.

## 2. Alcance Funcional

### 2.1 Entradas
- Imagen térmica en formato `.tif`
- Imagen visible del dron en formato `.png`
- Ambas imágenes con mismo encuadre y resolución

### 2.2 Procesos
1. **Lectura de imágenes**: Cargar y validar formatos de entrada
2. **Detección térmica**: Identificar regiones de calor con umbral configurable
3. **Análisis de blobs**: Extraer componentes conectados y calcular centroides
4. **Conteo**: Contar roedores detectados
5. **Proyección**: Mapear coordenadas sobre imagen del dron
6. **Visualización**: Mostrar imagen con círculos en posiciones detectadas
7. **Exportación**: Guardar imagen anotada y reporte CSV/JSON

### 2.3 Salidas
- Imagen `.png` con círculos dibujados sobre detecciones
- Archivo CSV con coordenadas (x, y) y conteo total
- Archivo JSON con metadata y parámetros usados

## 3. Arquitectura de Módulos

```
deteccion_roedores/
├── core/
│   ├── __init__.py
│   ├── image_loader.py      # Lectura de imágenes
│   ├── detector.py          # Lógica de detección térmica
│   ├── blob_analyzer.py     # Análisis de componentes conectados
│   └── projector.py         # Mapeo de coordenadas
├── ui/
│   ├── __init__.py
│   ├── main_window.py       # Ventana principal
│   └── widgets.py           # Componentes UI
├── utils/
│   ├── __init__.py
│   ├── exporter.py          # Exportación de resultados
│   └── logger.py            # Logging de la aplicación
├── app.py                   # Punto de entrada
├── requirements.txt        # Dependencias
└── main.spec               # PyInstaller config
```

## 4. Algoritmo de Detección v1

### 4.1 Replicar lógica MATLAB (implementado)

Para cada píxel interior (`x = 2..W-1`, `y = 2..H-1`, índices MATLAB 1-based):

```
B  = Q(y, x)      bd = Q(y, x+1)    ba = Q(y-1, x)
bi = Q(y, x-1)    bb = Q(y+1, x)

b_k = abs(abs(B) - abs(vecino_k))          para k = derecha, arriba, izquierda, abajo
c   = #{ k : B > vecino_k  y  b_k < 1000  y  b_k > T }

detección  <=>  c > 2
```

Puntos críticos a respetar:
- Las 4 comparaciones son **independientes**; no se promedian los vecinos.
- `abs(abs(B) - abs(n))` no equivale a `abs(B - n)` cuando los signos difieren.
- `b < 1000` es lo que excluye el fondo (`-32767`); no hace falta máscara aparte.
- El umbral `T` es un delta de temperatura en unidades de la imagen, **no** un valor
  normalizado en [0,1].
- Equivalencia en numpy 0-based: centro `img[1:-1, 1:-1]`, derecha `img[1:-1, 2:]`,
  arriba `img[:-2, 1:-1]`, izquierda `img[1:-1, :-2]`, abajo `img[2:, 1:-1]`.

### 4.2 Post-proceso: agrupamiento (opcional)

El original cuenta un roedor por cada píxel que dispara, así que un animal repartido
en píxeles contiguos se cuenta varias veces. `BlobAnalyzer.cluster_points()` une por
union-find las detecciones separadas por <= `merge_radius` y deja un centroide por grupo.

Medido sobre `Or17-18.tif` con T=0.56: 227 píxeles → 217 grupos. Los blobs promedian
1.03 px, así que la inflación del conteo original es baja (~4%).

**Descartado**: el pipeline morfológico con `opening`/`closing` + `remove_small_objects`
que planteaba la versión inicial de este documento. Con detecciones de un solo píxel —
que son la mayoría — una apertura las elimina todas.

### 4.3 Parámetros ajustables
- `threshold` (T): Delta mínimo de temperatura contra un vecino (default: 0.56)
- `min_neighbors`: Vecinos que deben cumplir, de 4 (default: 3, equivale a `c > 2`)
- `max_delta`: Cota superior que descarta el fondo (default: 1000, constante del original)
- `merge_radius`: Radio para agrupar detecciones contiguas (default: 3, opcional)

## 5. Interfaz de Usuario

### 5.1 Layout
```
┌─────────────────────────────────────────────────────────────┐
│  [Cargar TIF] [Cargar PNG]  │  Umbral: [0.56] [Detectar]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    Área de Visualización                    │
│                  (imagen con círculos)                      │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│  Roedores detectados: 5  │  [Exportar IMG] [Exportar CSV] │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Componentes PySide6
- QMainWindow como contenedor principal
- QWidget central con QHBoxLayout/QVBoxLayout
- QLabel para previsualización de imagen
- QLineEdit para ajuste de umbral
- QPushButton para acciones principales
- QStatusBar para información de estado

### 5.3 Flujo de usuario
1. Cargar imagen térmica (.tif)
2. Cargar imagen visible (.png)
3. Ajustar umbral de detección
4. Click en "Detectar"
5. Ver resultados en área de visualización
6. Exportar imagen y/o datos

## 6. Criterios de Aceptación

### 6.1 Funcionales
- [ ] Cargar archivo .tif sin errores
- [ ] Cargar archivo .png sin errores
- [ ] Ejecutar detección con umbral configurable
- [ ] Mostrar círculos sobre imagen visible
- [ ] Contar correctamente roedores (vs MATLAB baseline)
- [ ] Exportar imagen con anotaciones
- [ ] Exportar CSV con coordenadas

### 6.2 No funcionales
- UI responsiva durante procesamiento
- Mensajes de error claros para archivos inválidos
- Logging de operaciones para debugging

## 7. Dependencias

```
opencv-python>=4.8.0
numpy>=1.24.0
scikit-image>=0.21.0
tifffile>=2023.7.10
PySide6>=6.5.0
```

## 8. Próximos Pasos

1. Crear estructura de directorios
2. Implementar módulo de carga de imágenes
3. Implementar detector térmico v1
4. Implementar análisis de blobs
5. Implementar visualización
6. Construir UI completa
7. Integrar y probar
8. Empaquetar con PyInstaller