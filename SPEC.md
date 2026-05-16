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

### 4.1 Replicar lógica MATLAB
- Recorrer imagen térmica píxel a píxel
- Comparar valor central con vecinos (derecho, superior, izquierdo, inferior)
- Aplicar umbral de sensibilidad T = 0.56
- Marcar posición cuando se detecta patrón caliente

### 4.2 Pipeline mejorado (scikit-image)
1. Normalizar imagen térmica a rango [0, 1]
2. Aplicar umbral adaptable o fijo (valor inicial: percentil 90)
3. Operaciones morfológicas (apertura/cierre) para eliminar ruido
4. Etiquetar componentes conectados con `label()`
5. Calcular centroides con `regionprops()`
6. Filtrar por área mínima/máxima (evitar ruido y blobs grandes)

### 4.3 Parámetros ajustables
- `threshold`: Umbral de detección (default: 0.56)
- `min_area`: Área mínima del blob (pixels)
- `max_area`: Área máxima del blob (pixels)
- `morph_kernel`: Tamaño del kernel morfológico

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