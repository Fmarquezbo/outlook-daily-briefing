#!/usr/bin/env python3
"""
Test script for the Outlook Daily Briefing API.
Use this to test the API locally before integrating with Power Automate.
"""

import requests
import json
from datetime import datetime, timedelta

# API configuration
API_BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint."""
    print("Testing health check...")
    response = requests.get(f"{API_BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}\n")
    return response.status_code == 200

def test_process_emails_simple():
    """Test with a simple email set."""
    print("Testing email processing with simple example...")

    yesterday = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday.isoformat()

    emails = [
        {
            "sender": "seguridad@ministerio.interior",
            "subject": "Alerta: Intento de acceso no autorizado detectado",
            "body": "Se detectó un intento de acceso no autorizado al servidor CRITICAL-001 desde IP 192.168.1.100. El sistema de detección de intrusiones bloqueó la actividad. Requiere investigación inmediata.",
            "date": yesterday_str
        },
        {
            "sender": "normativa@ministerio.interior",
            "subject": "Actualización RDL - Nuevos requisitos de cumplimiento",
            "body": "Se han publicado nuevos requisitos en el Real Decreto Legislativo sobre protección de operadores esenciales. Plazo de cumplimiento: 90 días.",
            "date": yesterday_str
        },
        {
            "sender": "coordinacion@cnpic.es",
            "subject": "Reunión coordinación CSIRT - 2026-05-15",
            "body": "Confirmar asistencia a reunión de coordinación del CSIRT. Orden del día: análisis de amenazas actuales y nuevos procedimientos de reporte.",
            "date": yesterday_str
        }
    ]

    payload = {
        "emails": emails,
        "language": "es"
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/process-emails",
            json=payload,
            timeout=60
        )
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\nBriefing:\n{result['briefing']}")
            print(f"\nTimestamp: {result['timestamp']}")
            print(f"Telegram Sent: {result['telegram_sent']}")
            return True
        else:
            print(f"Error: {response.text}")
            return False

    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def test_process_emails_comprehensive():
    """Test with a comprehensive email set simulating real scenario."""
    print("\nTesting email processing with comprehensive example...")

    yesterday = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday.isoformat()

    emails = [
        {
            "sender": "incidentes@csirt.gov",
            "subject": "CRÍTICO: Botnet detectada en red ministerial",
            "body": """Reporte de incidente crítico:
            - Detección de 47 máquinas comprometidas
            - C2 comunicándose con servidor externo
            - Potencial exfiltración de datos
            - Requiere activación de protocolo de incidente crítico
            - Notificar a operadores esenciales potencialmente afectados""",
            "date": yesterday_str
        },
        {
            "sender": "normativa@interior.es",
            "subject": "NIS - Nuevos operadores esenciales catalogados",
            "body": "Se han añadido 12 nuevos operadores esenciales al catálogo oficial. Requiere envío de notificación a todos los organismos coordinadores.",
            "date": yesterday_str
        },
        {
            "sender": "cni@cni.es",
            "subject": "Inteligencia de amenazas - APT Grupo 28",
            "body": "Inteligencia sobre nueva campaña de APT Group 28 dirigida al sector energético español. Incluye indicadores de compromiso y técnicas observadas.",
            "date": yesterday_str
        },
        {
            "sender": "rrhh@ministerio.interior",
            "subject": "Cambio de horario en cafetería",
            "body": "La cafetería cambiará su horario de atención a partir del próximo lunes.",
            "date": yesterday_str
        },
        {
            "sender": "infraestructura@ministerio.interior",
            "subject": "Mantenimiento programado sistemas",
            "body": "Mantenimiento programado del servidor DNS principal. Ventana: 02:00-04:00 CET. Sin impacto esperado en servicios críticos.",
            "date": yesterday_str
        }
    ]

    payload = {
        "emails": emails,
        "language": "es"
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/process-emails",
            json=payload,
            timeout=60
        )
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print(f"\nBriefing:\n{result['briefing']}")
            print(f"\nTimestamp: {result['timestamp']}")
            print(f"Telegram Sent: {result['telegram_sent']}")
            return True
        else:
            print(f"Error: {response.text}")
            return False

    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("=" * 80)
    print("Outlook Daily Briefing API - Test Suite")
    print("=" * 80 + "\n")

    print("Make sure the API is running: python main.py\n")

    # Test health check
    health_ok = test_health_check()
    if not health_ok:
        print("❌ Health check failed. Make sure the API is running.")
        return

    print("✅ Health check passed\n")

    # Test simple example
    simple_ok = test_process_emails_simple()
    if simple_ok:
        print("✅ Simple email processing test passed\n")
    else:
        print("❌ Simple email processing test failed\n")

    # Test comprehensive example
    comprehensive_ok = test_process_emails_comprehensive()
    if comprehensive_ok:
        print("✅ Comprehensive email processing test passed\n")
    else:
        print("❌ Comprehensive email processing test failed\n")

    print("=" * 80)
    if health_ok and simple_ok:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed. Check the output above.")
    print("=" * 80)

if __name__ == "__main__":
    main()
