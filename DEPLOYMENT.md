# Guía de Despliegue - Outlook Daily Briefing

## 📌 Opciones de Despliegue

### Opción 1: Desarrollo Local (Recomendado para pruebas)

#### 1.1 Requisitos
- Python 3.9+
- pip
- Git

#### 1.2 Instalación

```bash
# Clonar repositorio
cd /home/user/outlook-daily-briefing

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores
```

#### 1.3 Ejecutar API

```bash
python main.py
```

El API estará disponible en `http://localhost:8000`

Documentación interactiva: `http://localhost:8000/docs`

#### 1.4 Probar API

```bash
# En otra terminal
python test_api.py
```

---

### Opción 2: Docker Local

#### 2.1 Requisitos
- Docker
- Docker Compose

#### 2.2 Instalación

```bash
# Copiar archivo de configuración
cp .env.example .env
# Editar .env con tus valores

# Construir y ejecutar imagen Docker
docker-compose up --build
```

El API estará disponible en `http://localhost:8000`

#### 2.3 Detener servicio

```bash
docker-compose down
```

---

### Opción 3: Servidor Linux (Producción)

#### 3.1 Requisitos
- Servidor Linux (Ubuntu 22.04 recomendado)
- Python 3.9+
- systemd
- Acceso a internet para Claude API y Telegram

#### 3.2 Preparación del servidor

```bash
# Actualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependencias del sistema
sudo apt install -y python3 python3-pip python3-venv git curl

# Crear usuario de servicio (opcional pero recomendado)
sudo useradd -m -s /bin/bash briefing-api
sudo su - briefing-api
```

#### 3.3 Instalación de la aplicación

```bash
# Clonar repositorio
git clone <repositorio-url> outlook-daily-briefing
cd outlook-daily-briefing

# Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Crear directorio de logs
mkdir -p logs

# Copiar configuración
cp .env.example .env
# Editar .env con tus valores
```

#### 3.4 Configurar como servicio systemd

```bash
# Crear archivo de servicio
sudo tee /etc/systemd/system/outlook-briefing.service > /dev/null << 'EOF'
[Unit]
Description=Outlook Daily Briefing API
After=network.target

[Service]
Type=simple
User=briefing-api
WorkingDirectory=/home/briefing-api/outlook-daily-briefing
Environment="PATH=/home/briefing-api/outlook-daily-briefing/venv/bin"
EnvironmentFile=/home/briefing-api/outlook-daily-briefing/.env
ExecStart=/home/briefing-api/outlook-daily-briefing/venv/bin/python main.py
Restart=always
RestartSec=10
StandardOutput=append:/home/briefing-api/outlook-daily-briefing/logs/api.log
StandardError=append:/home/briefing-api/outlook-daily-briefing/logs/error.log

[Install]
WantedBy=multi-user.target
EOF

# Recargar systemd
sudo systemctl daemon-reload

# Habilitar servicio al iniciar
sudo systemctl enable outlook-briefing.service

# Iniciar servicio
sudo systemctl start outlook-briefing.service

# Verificar estado
sudo systemctl status outlook-briefing.service
```

#### 3.5 Configurar Nginx como reverse proxy (HTTPS)

```bash
# Instalar Nginx
sudo apt install -y nginx certbot python3-certbot-nginx

# Crear configuración Nginx
sudo tee /etc/nginx/sites-available/outlook-briefing > /dev/null << 'EOF'
upstream briefing_api {
    server localhost:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://briefing_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Habilitar sitio
sudo ln -s /etc/nginx/sites-available/outlook-briefing /etc/nginx/sites-enabled/

# Verificar sintaxis
sudo nginx -t

# Recargar Nginx
sudo systemctl reload nginx

# Obtener certificado SSL (reemplazar your-domain.com)
sudo certbot --nginx -d your-domain.com
```

#### 3.6 Monitoreo con logrotate

```bash
# Crear configuración de rotación de logs
sudo tee /etc/logrotate.d/outlook-briefing > /dev/null << 'EOF'
/home/briefing-api/outlook-daily-briefing/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 briefing-api briefing-api
    sharedscripts
    postrotate
        systemctl reload outlook-briefing.service > /dev/null 2>&1 || true
    endscript
}
EOF
```

---

### Opción 4: Heroku (Cloud hosting)

#### 4.1 Requisitos
- Cuenta de Heroku
- Heroku CLI instalado

#### 4.2 Instalación

```bash
# Crear archivo Procfile
echo "web: gunicorn -w 4 -b 0.0.0.0:\$PORT main:app" > Procfile

# Instalar gunicorn
pip install gunicorn
pip freeze > requirements.txt

# Iniciar sesión en Heroku
heroku login

# Crear aplicación
heroku create outlook-daily-briefing

# Configurar variables de entorno
heroku config:set ANTHROPIC_API_KEY=sk-ant-...
heroku config:set TELEGRAM_BOT_TOKEN=...
heroku config:set TELEGRAM_CHAT_ID=...

# Deploy
git push heroku main

# Ver logs
heroku logs --tail
```

---

## 🔧 Integración con Power Automate

### Pasos en Power Automate

1. **Crear nuevo flujo planificado**
   - Nombre: "Outlook Daily Briefing"
   - Frecuencia: Diariamente
   - Hora: 07:45 CET
   - Zona: W. Europe Standard Time

2. **Acción 1: Obtener eventos**
   - Usar conector "Office 365 Outlook"
   - Filtrar correos de las últimas 24 horas

3. **Acción 2: HTTP POST**
   - Método: POST
   - URI: `https://tu-dominio.com/process-emails`
   - Headers: `Content-Type: application/json`
   - Body: JSON con array de correos

Ejemplo de URI según opción de despliegue:
- Desarrollo: `http://localhost:8000/process-emails`
- Servidor Linux: `https://your-domain.com/process-emails`
- Heroku: `https://outlook-daily-briefing.herokuapp.com/process-emails`

---

## 📊 Monitoreo y Mantenimiento

### Verificar estado del servicio (Linux)

```bash
# Ver status
sudo systemctl status outlook-briefing.service

# Ver últimos logs
sudo tail -f /home/briefing-api/outlook-daily-briefing/logs/api.log

# Reiniciar servicio
sudo systemctl restart outlook-briefing.service
```

### Monitorear cache de Claude

Los logs mostrarán información de uso de cache:
```
Cache usage: 1200 creation tokens, 0 read tokens
```

- `creation tokens`: Primera solicitud (se cachea)
- `read tokens`: Solicitudes posteriores (reutilizan cache)

### Alertas recomendadas

Monitorear en logs/métricas:
- Errores en llamadas a Claude API
- Fallos en envío de Telegram
- Time-outs de conexión
- Cambios en velocidad de procesamiento

---

## 🔐 Seguridad

### Mejores prácticas

1. **Ambiente**
   - Usar `.env` para variables sensibles (nunca commitear)
   - Rotar API keys regularmente
   - Usar HTTPS en producción

2. **Acceso**
   - Limitar acceso al API (firewall, VPN)
   - Usar tokens de autenticación si es público
   - Auditar acceso a logs

3. **Datos**
   - No guardar correos en base de datos (procesar y descartar)
   - Encriptar variables sensibles
   - Respetar RGPD/normativa de datos

### Firewall (Linux)

```bash
# Permitir solo desde tu red
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```

---

## 🔄 Actualizar a nuevo release

```bash
# Obtener cambios
git pull origin main

# Actualizar dependencias
source venv/bin/activate
pip install -r requirements.txt

# Reiniciar servicio
sudo systemctl restart outlook-briefing.service

# Verificar que funciona
curl https://your-domain.com/health
```

---

## 🆘 Troubleshooting

### El API no inicia

```bash
# Ver error detallado
python main.py

# Verificar sintaxis Python
python -m py_compile main.py

# Verificar dependencias
pip list
```

### Power Automate no puede conectar

1. Verificar URL es correcta
2. Verificar firewall permite conexión
3. Verificar API está activo: `curl https://your-domain.com/health`
4. Ver logs: `sudo tail -f /var/log/syslog`

### Telegram no envía mensajes

1. Verificar `TELEGRAM_CHAT_ID` en `.env`
2. Verificar bot token es correcto
3. Verificar logs de error
4. Probar manualmente: `curl -X GET https://api.telegram.org/bot<TOKEN>/getMe`

---

## 📚 Documentación adicional

- [FastAPI Documentation](https://fastapi.tiangolo.com)
- [Anthropic Claude API](https://docs.anthropic.com)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Power Automate Documentation](https://docs.microsoft.com/power-automate)
