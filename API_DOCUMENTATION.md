# API de YouTube Downloader

## Endpoints Disponibles

La API está corriendo en el puerto 5000. Puedes hacer peticiones a los siguientes endpoints:

### 1. Descargar Video por URL
**Endpoint:** `/api/download/video`  
**Método:** `GET`  
**Parámetro:** `url` - URL del video de YouTube

**Ejemplo:**
```bash
curl "http://localhost:5000/api/download/video?url=https://www.youtube.com/watch?v=VIDEO_ID" -o video.mp4
```

**Desde otra aplicación:**
```
http://localhost:5000/api/download/video?url=https://www.youtube.com/watch?v=VIDEO_ID
```

---

### 2. Descargar Audio por URL
**Endpoint:** `/api/download/audio`  
**Método:** `GET`  
**Parámetro:** `url` - URL del video de YouTube

**Ejemplo:**
```bash
curl "http://localhost:5000/api/download/audio?url=https://www.youtube.com/watch?v=VIDEO_ID" -o audio.mp3
```

**Desde otra aplicación:**
```
http://localhost:5000/api/download/audio?url=https://www.youtube.com/watch?v=VIDEO_ID
```

---

### 3. Buscar y Descargar Video (1 resultado)
**Endpoint:** `/api/download/search/video`  
**Método:** `GET`  
**Parámetro:** `q` - Término de búsqueda

**Ejemplo:**
```bash
curl "http://localhost:5000/api/download/search/video?q=musica+relajante" -o video.mp4
```

**Desde otra aplicación:**
```
http://localhost:5000/api/download/search/video?q=musica%20relajante
```

---

### 4. Buscar y Descargar Audio (1 resultado)
**Endpoint:** `/api/download/search/audio`  
**Método:** `GET`  
**Parámetro:** `q` - Término de búsqueda

**Ejemplo:**
```bash
curl "http://localhost:5000/api/download/search/audio?q=musica+relajante" -o audio.mp3
```

**Desde otra aplicación:**
```
http://localhost:5000/api/download/search/audio?q=musica%20relajante
```

---

## Respuestas

### Exitosa
- **Código:** 200
- **Contenido:** Archivo descargado (MP4 o MP3)

### Error
- **Código:** 400 (Bad Request) - Parámetro faltante
- **Código:** 404 (Not Found) - No se encontraron resultados de búsqueda
- **Código:** 500 (Internal Server Error) - Error en la descarga

**Formato de error:**
```json
{
  "error": "Descripción del error"
}
```

---

## Notas Importantes

1. **Búsqueda:** Los endpoints de búsqueda (`/search/video` y `/search/audio`) devuelven solo **1 resultado** (el primero encontrado).

2. **Formatos:** 
   - Video: MP4
   - Audio: MP3 (192 kbps)

3. **URL del servidor:** Si estás en Replit, usa el dominio proporcionado por Replit en lugar de localhost.

4. **Codificación de URL:** Recuerda codificar los parámetros de URL correctamente (espacios = `%20` o `+`).

---

## Ejemplo de Uso en JavaScript

```javascript
// Descargar video por URL
fetch('http://localhost:5000/api/download/video?url=https://www.youtube.com/watch?v=VIDEO_ID')
  .then(response => response.blob())
  .then(blob => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'video.mp4';
    a.click();
  });

// Buscar y descargar audio
fetch('http://localhost:5000/api/download/search/audio?q=música relajante')
  .then(response => response.blob())
  .then(blob => {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'audio.mp3';
    a.click();
  });
```

## Ejemplo de Uso en Python

```python
import requests

# Descargar video por URL
url = "http://localhost:5000/api/download/video?url=https://www.youtube.com/watch?v=VIDEO_ID"
response = requests.get(url)
with open('video.mp4', 'wb') as f:
    f.write(response.content)

# Buscar y descargar audio
url = "http://localhost:5000/api/download/search/audio?q=música relajante"
response = requests.get(url)
with open('audio.mp3', 'wb') as f:
    f.write(response.content)
```
