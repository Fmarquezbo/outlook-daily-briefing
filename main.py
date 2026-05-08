import os
import json
import logging
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

from anthropic import Anthropic
import telegram

load_dotenv()

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

app = FastAPI(title="Outlook Daily Briefing")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

client = Anthropic(api_key=ANTHROPIC_API_KEY)
telegram_bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

# System prompt with analysis guidelines - cached across all requests
SYSTEM_PROMPT = """Eres un analista de ciberseguridad especializado en la coordinación de la autoridad CSIRT del Ministerio del Interior. Analiza los correos electrónicos corporativos y genera un resumen ejecutivo diario estructurado en 10 secciones.

PAUTAS DE ANÁLISIS FIJAS (USAR SIEMPRE):

1. SEMÁFORO DE ESTADO (Traffic Light Status)
   - 🔴 ROJO: Incidentes críticos, amenazas inmediatas, situación crítica que requiere acción urgente
   - 🟠 NARANJA: Alertas importantes, riesgos moderados, situaciones que requieren atención
   - 🟡 AMARILLO: Problemas menores, información de interés, alertas informativas
   - 🟢 VERDE: Situación normal, sin incidentes

2. TOP 5 ASUNTOS PRIORITARIOS
   - Listar los 5 temas más importantes/urgentes del día
   - Incluir breve descripción de cada uno

3. INCIDENTES DE SEGURIDAD
   - Detallar incidentes de ciberseguridad, brechas, intentos de ataque
   - Incluir impacto potencial y estado actual
   - Solicitar acción si es necesario

4. ASUNTOS NORMATIVOS/RDL
   - Cambios en regulación NIS, RDL u otras normativas
   - Nuevos requisitos de cumplimiento
   - Actualizaciones de autoridades

5. OPERADORES ESENCIALES Y SECTORES CRÍTICOS
   - Información sobre operadores esenciales (energía, agua, transporte, salud)
   - Alertas específicas para sectores críticos
   - Cambios en el catálogo de operadores

6. COORDINACIÓN INTERINSTITUCIONAL
   - Comunicados de CNI, CNPIC, policía, otros organismos
   - Cambios en procesos de coordinación
   - Reuniones o acciones requeridas con otros organismos

7. REUNIONES Y COMPROMISOS
   - Reuniones programadas relevantes
   - Compromisos pendientes de cumplir
   - Plazos importantes

8. ACCIONES REQUERIDAS
   - Tareas que requieren respuesta o acción inmediata
   - Temas donde se solicita participación CSIRT
   - Escaladas requeridas

9. INFORMACIÓN ÚTIL
   - Inteligencia de amenazas relevante
   - Tendencias de ciberseguridad
   - Herramientas o recursos útiles
   - Lecciones aprendidas

10. CLASIFICACIÓN DE RUIDO
    - Temas administrativos sin relevancia operativa
    - Comunicaciones internas de bajo impacto
    - Actualizaciones de estado de sistemas (sin incidentes)"""

class EmailInput(BaseModel):
    emails: list[dict]  # List of emails with subject, body, sender, date
    language: str = "es"

class BriefingResponse(BaseModel):
    briefing: str
    timestamp: str
    telegram_sent: bool

async def send_telegram_notification(message: str) -> bool:
    """Send formatted briefing to Telegram chat."""
    if not TELEGRAM_CHAT_ID:
        logger.warning("TELEGRAM_CHAT_ID not configured")
        return False

    try:
        # Format message with markdown for better readability
        formatted_message = f"📋 *Resumen Diario de Ciberseguridad*\n\n{message}"

        await telegram_bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=formatted_message,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )
        logger.info(f"Telegram notification sent successfully to chat {TELEGRAM_CHAT_ID}")
        return True
    except Exception as e:
        logger.error(f"Error sending Telegram notification: {str(e)}")
        return False

def create_email_context(emails: list[dict]) -> str:
    """Format emails into context for Claude."""
    context = f"Se han procesado {len(emails)} correos electrónicos del día anterior:\n\n"

    for i, email in enumerate(emails, 1):
        context += f"--- CORREO {i} ---\n"
        context += f"De: {email.get('sender', 'Desconocido')}\n"
        context += f"Asunto: {email.get('subject', '(sin asunto)')}\n"
        context += f"Fecha: {email.get('date', 'Desconocida')}\n"
        context += f"Contenido: {email.get('body', '(sin contenido)')}\n\n"

    return context

@app.post("/process-emails", response_model=BriefingResponse)
async def process_emails(input_data: EmailInput) -> BriefingResponse:
    """Process emails and generate daily briefing with cached prompt."""

    if not input_data.emails:
        raise HTTPException(status_code=400, detail="No emails provided")

    email_context = create_email_context(input_data.emails)

    try:
        # Use Claude with prompt caching for fixed analysis guidelines
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=2000,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": f"""Basándote en los siguientes correos corporativos del día anterior,
genera un resumen ejecutivo en 10 secciones según las pautas de análisis.

{email_context}

Proporciona el resumen estructurado en las 10 secciones especificadas,
con información concisa y accionable para la autoridad CSIRT."""
                }
            ],
            thinking={
                "type": "adaptive"
            },
            output_config={
                "effort": "high"
            }
        )

        briefing_text = response.content[0].text
        timestamp = datetime.now().isoformat()

        # Send to Telegram
        telegram_sent = await send_telegram_notification(briefing_text)

        logger.info(f"Email processing completed. Cache usage: {response.usage.cache_creation_input_tokens} creation tokens, {response.usage.cache_read_input_tokens} read tokens")

        return BriefingResponse(
            briefing=briefing_text,
            timestamp=timestamp,
            telegram_sent=telegram_sent
        )

    except Exception as e:
        logger.error(f"Error processing emails: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing emails: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("API_HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=port)
