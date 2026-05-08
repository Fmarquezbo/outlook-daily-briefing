# Outlook Daily Briefing - Sistema Automático de Resumen de Ciberseguridad

Sistema automatizado para generar un resumen ejecutivo diario de correos corporativos de ciberseguridad y entregarlo vía Telegram cada mañana a las 07:50 CET.

## 🏗️ Arquitectura

```
Power Automate (07:45 CET)
        ↓ (extrae correos últimas 24h)
   FastAPI Backend
        ↓ (procesa con Claude + cache)
  Claude API (con prompt caching)
        ↓ (genera resumen 10 secciones)
  Telegram Bot API
        ↓
   Tu chat de Telegram
```

## 📋 Características

- **Análisis automático**: Procesa correos corporativos con Claude
- **Prompt caching**: Las pautas de análisis se cachean para optimizar tokens y costo
- **10 secciones estructuradas**:
  1. Semáforo de estado (🔴🟠🟡🟢)
  2. Top 5 asuntos prioritarios
  3. Incidentes de seguridad
  4. Asuntos normativos/RDL
  5. Operadores esenciales
  6. Coordinación interinstitucional
  7. Reuniones y compromisos
  8. Acciones requeridas
  9. Información útil
  10. Clasificación de ruido

- **Entrega por Telegram**: Notificación formateada cada mañana
- **API REST**: Endpoint para procesar correos bajo demanda

## 🚀 Instalación

### 1. Clonar y configurar entorno

```bash
cd /home/user/outlook-daily-briefing
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configurar variables de entorno

```bash
cp .env.example .env
```

Edita `.env` con tus valores:

```env
ANTHROPIC_API_KEY=sk-ant-... # Tu clave API de Anthropic
TELEGRAM_BOT_TOKEN=8254712869:AAHst64r31bht8WTi6-R5rDyPXuVFBR3GOY
TELEGRAM_CHAT_ID=123456789  # Tu Chat ID personal (ver abajo)
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

### 3. Obtener tu Telegram Chat ID

**Opción A**: Usar el bot para obtenerlo
```bash
# Inicia el bot primero, luego escribe /getchatid en Telegram
```

**Opción B**: Usar un ID conocido
- Si ya tienes un ID de Telegram, úsalo directamente

## 🔧 Configuración de Power Automate

### Pasos en Power Automate:

1. **Crear nuevo flujo planificado** (Scheduled Cloud Flow)
   - Nombre: "Outlook Daily Briefing"
   - Frecuencia: Diariamente
   - Hora: 07:45 CET
   - Zona horaria: W. Europe Standard Time

2. **Agregar acción: Obtener eventos (versión 2)**
   - Buzón: Tu correo corporativo
   - Carpeta: Inbox
   - Filtro: correos de las últimas 24 horas

3. **Agregar acción: HTTP POST**
   ```
   URI: http://your_server:8000/process-emails
   Método: POST
   Body: JSON con los correos formateados
   ```

Ver archivo `power_automate_flow.json` para detalles completos.

## 🏃 Ejecución

### Desarrollo local:

```bash
python main.py
```

Acceso a API: `http://localhost:8000`
Documentación: `http://localhost:8000/docs`

### Producción (con Gunicorn):

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 main:app
```

## 📡 Uso de la API

### Endpoint: POST /process-emails

**Solicitud:**
```bash
curl -X POST "http://localhost:8000/process-emails" \
  -H "Content-Type: application/json" \
  -d '{
    "emails": [
      {
        "sender": "seguridad@ministerio.interior",
        "subject": "Alerta de incidente de seguridad",
        "body": "Detectamos intentos de acceso no autorizados...",
        "date": "2026-05-08T14:30:00Z"
      }
    ],
    "language": "es"
  }'
```

**Respuesta:**
```json
{
  "briefing": "📋 RESUMEN DIARIO DE CIBERSEGURIDAD\n\n🔴 SEMÁFORO DE ESTADO: ROJO...",
  "timestamp": "2026-05-08T15:35:42.123456",
  "telegram_sent": true
}
```

### Endpoint: GET /health

```bash
curl http://localhost:8000/health
```

## 🔐 Optimización de tokens con Prompt Caching

El sistema utiliza **prompt caching** para las pautas de análisis fijas:

- **Primera solicitud**: Se cachea el sistema prompt (pautas de análisis) - ~1200 tokens
- **Solicitudes posteriores**: Reutilizan el cache - ahorro de ~1200 tokens por request

**Ahorro estimado** (100 correos al mes):
- Sin cache: 100 × 1200 = 120,000 tokens
- Con cache: 100 × 120 = 12,000 tokens
- **Ahorro: 90% en tokens del sistema prompt**

Ver documentación de Anthropic sobre [Prompt Caching](https://docs.anthropic.com/en/docs/build-a-system/prompt-caching) para más detalles.

## 📊 Monitoreo

El sistema genera logs en STDOUT:

```
INFO - Email processing completed. Cache usage: 1200 creation tokens, 0 read tokens
INFO - Telegram notification sent successfully to chat 123456789
```

**Métricas a monitorear**:
- Cache hit rate (cache_read_input_tokens)
- Error rate en envío de Telegram
- Tiempo de procesamiento

## 🐛 Troubleshooting

### El API no recibe correos de Power Automate

1. Verifica que la URL sea accesible desde Power Automate
2. Revisa logs del API para errores de conexión
3. Confirma que el formato JSON es válido

### Telegram no envía mensajes

1. Verifica que `TELEGRAM_CHAT_ID` esté configurado
2. Confirma que el bot tiene permisos para enviar mensajes
3. Revisa logs de errores de conexión

### Bajo rendimiento del cache

1. Asegúrate de que usas la misma API key
2. El cache dura máximo 5 minutos - solicitudes después de ese tiempo no reutilizan
3. Cada cambio en el system prompt invalida el cache

## 📝 Ejemplo de salida

```
📋 RESUMEN DIARIO DE CIBERSEGURIDAD

🔴 SEMÁFORO DE ESTADO
Estado: ROJO
Razón: Incidente de seguridad crítico en progreso

🔝 TOP 5 ASUNTOS PRIORITARIOS
1. Intento de acceso no autorizado a sistema CRITICAL-001
2. Nueva vulnerabilidad NVD en software de infraestructura
3. Cambio en normativa RDL sobre operadores esenciales
4. Reunión de coordinación CSIRT programada
5. Actualización de catálogo de operadores esenciales

... (resto de secciones)
```

## 📚 Referencias

- [Documentación Anthropic - Claude API](https://docs.anthropic.com)
- [Documentación FastAPI](https://fastapi.tiangolo.com)
- [Documentación Telegram Bot API](https://core.telegram.org/bots/api)
- [Power Automate Documentation](https://docs.microsoft.com/power-automate)

## ⚖️ Licencia

Repositorio interno del Ministerio del Interior. Uso no autorizado prohibido.
