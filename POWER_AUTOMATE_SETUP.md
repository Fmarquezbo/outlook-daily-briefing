# Configuración de Power Automate - Outlook Daily Briefing

## Pasos para crear el flujo automático

### 1. Acceder a Power Automate
- Ve a https://powerautomate.microsoft.com
- Inicia sesión con tu cuenta corporativa

### 2. Crear nuevo flujo planificado
```
Crear → Flujo en la nube → Flujo planificado
Nombre: "Outlook Daily Briefing"
```

### 3. Configurar la programación
```
Frecuencia: Día
Cada: 1 día
Hora de inicio: 07:45
Zona horaria: Zona Europea de Hora de Invierno (UTC+1)
```

### 4. Agregar acción: Obtener correos

En el diseñador del flujo:

```
Acción: Office 365 Outlook → Obtener eventos (versión 2)

Parámetros:
- Buzón: Tu correo corporativo
- Carpeta: Bandeja de entrada
- Filtro de búsqueda: receivedDateTime ge '@{addDays(utcNow(), -1)}'
```

### 5. Agregar acción: Construir JSON

```
Acción: Datos → Crear objeto JSON

Entrada:
{
  "emails": [
    {
      "sender": "De",
      "subject": "Asunto",
      "body": "Vista previa del cuerpo",
      "date": "Fecha recibida"
    }
  ]
}
```

Mapa dinámico los campos del correo con los campos JSON.

### 6. Agregar acción: HTTP POST

```
Acción: HTTP

Método: POST
URI: https://tu-dominio.com/process-emails
        (o http://localhost:8000 si es local)

Encabezados:
{
  "Content-Type": "application/json"
}

Cuerpo: (Salida del paso anterior)
```

### 7. Guardar y activar el flujo

Una vez configurado:
1. Haz clic en "Guardar"
2. El flujo se activará automáticamente
3. Se ejecutará cada día a las 07:45 CET
4. Enviará los correos al API
5. El API procesará y enviará a Telegram a las 07:50

## Validar funcionamiento

Después de activar:
1. Espera a las 07:45 del próximo día, O
2. Haz clic en "Probar" para ejecutar manualmente
3. Revisa los logs del API en el servidor
4. Confirma que recibiste el mensaje en Telegram

## Troubleshooting en Power Automate

Si el flujo falla:
1. Haz clic en el flujo ejecutado
2. Revisa el paso que falló
3. Comprueba que la URL del API es accesible
4. Verifica que el formato JSON es válido
5. Revisa los logs del servidor

---

**PRÓXIMO PASO**: Una vez que proporciones tu API key de Anthropic,
configuraré el .env y probaré que todo funciona.
