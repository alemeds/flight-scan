"""
Script para monitoreo automático de vuelos
Puede ejecutarse con cron o GitHub Actions

Lee las alertas de precio activas de la planilla de Google Sheets, consulta
precios actuales en Sky Scrapper y envía un email al alcanzar el objetivo.

Variables de entorno requeridas:
    GCP_SERVICE_ACCOUNT_FILE (path al JSON de la service account)
    SHEET_NAME (opcional, default: flight-scan-db) o SHEET_ID
    RAPIDAPI_KEY
    SMTP_HOST, SMTP_PORT (default 587), SMTP_USER, SMTP_PASSWORD
    ALERT_EMAIL_TO (opcional, default: SMTP_USER)
"""

from sheets_db import SheetsDatabase, DEFAULT_SPREADSHEET_NAME
from skyscrapper_client import SkyScrapperClient
from config import get_gcp_credentials
import os
import smtplib
from email.message import EmailMessage
from datetime import datetime, date
from typing import Dict


def send_alert_email(alert: Dict, price: float, offer: Dict) -> bool:
    """Envía el email de alerta. Retorna True si se envió correctamente."""
    smtp_host = os.getenv('SMTP_HOST')
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    recipient = os.getenv('ALERT_EMAIL_TO', smtp_user)

    if not all([smtp_host, smtp_user, smtp_password, recipient]):
        print("   ⚠️  SMTP no configurado (SMTP_HOST/SMTP_USER/SMTP_PASSWORD). "
              "No se envía email; la alerta queda activa para el próximo chequeo.")
        return False

    route = f"{alert['origin']} → {alert['destination']}"

    msg = EmailMessage()
    msg['Subject'] = (
        f"✈️ Flight Scan: {route} a ${price:.2f} "
        f"(objetivo ${alert['target_price']:.2f})"
    )
    msg['From'] = smtp_user
    msg['To'] = recipient
    msg.set_content(
        f"¡Precio objetivo alcanzado!\n\n"
        f"Ruta: {route}\n"
        f"Salida: {alert['departure_date']}\n"
        f"Regreso: {alert['return_date'] or 'Solo ida'}\n"
        f"Adultos: {alert['adults']}\n\n"
        f"Precio encontrado: ${price:.2f} {offer.get('currency', 'USD')}\n"
        f"Precio objetivo:   ${alert['target_price']:.2f}\n"
        f"Aerolínea: {offer.get('airline', 'N/A')}\n"
        f"Escalas: {offer.get('stops', 'N/A')}\n"
        f"Duración: {offer.get('duration', 'N/A')}\n\n"
        f"Chequeado: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    )

    try:
        with smtplib.SMTP(smtp_host, int(os.getenv('SMTP_PORT', 587))) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"   ❌ Error enviando email: {type(e).__name__}")
        return False


def monitor_flights():
    """Ejecuta el monitoreo de las alertas de precio activas"""

    print(f"🚀 Iniciando monitoreo de vuelos - {datetime.now()}")

    # Inicializar conexiones
    try:
        db = SheetsDatabase(
            credentials_info=get_gcp_credentials(),
            spreadsheet_name=os.getenv('SHEET_NAME', DEFAULT_SPREADSHEET_NAME),
            spreadsheet_id=os.getenv('SHEET_ID')
        )

        flight_client = SkyScrapperClient(api_key=os.getenv('RAPIDAPI_KEY'))

        print("✅ Conexiones inicializadas correctamente")

    except Exception as e:
        print(f"❌ Error inicializando conexiones: {str(e)}")
        return

    alerts = db.get_active_alerts()

    if not alerts:
        print("ℹ️  No hay alertas de precio activas. Nada que monitorear.")
        return

    print(f"📋 {len(alerts)} alerta(s) activa(s)")

    total_saved = 0

    for alert in alerts:
        route = f"{alert['origin']} → {alert['destination']}"

        try:
            # Desactivar alertas con fecha de salida ya pasada
            if alert['departure_date'] <= date.today():
                print(f"\n⏰ {route}: fecha de salida pasada. Alerta desactivada.")
                db.deactivate_alert(alert['id'])
                continue

            print(f"\n🔍 {route} (objetivo ${alert['target_price']:.2f})")

            offers = flight_client.search_flights(
                origin=alert['origin'],
                destination=alert['destination'],
                departure_date=alert['departure_date'].strftime('%Y-%m-%d'),
                return_date=alert['return_date'].strftime('%Y-%m-%d') if alert['return_date'] else None,
                adults=alert['adults'],
                max_results=10
            )

            if not offers:
                print("   ⚠️  Sin ofertas para esta ruta")
                continue

            # Guardar ofertas en la planilla (una sola llamada por lote)
            try:
                saved_count = db.insert_flight_offers(
                    origin=alert['origin'],
                    destination=alert['destination'],
                    departure_date=alert['departure_date'].strftime('%Y-%m-%d'),
                    return_date=alert['return_date'].strftime('%Y-%m-%d') if alert['return_date'] else None,
                    adults=alert['adults'],
                    offers=offers
                )
            except Exception as e:
                saved_count = 0
                print(f"   ⚠️  Error guardando ofertas: {str(e)}")

            total_saved += saved_count
            print(f"   ✅ {saved_count} ofertas guardadas")

            # Comparar el precio más bajo contra el objetivo
            cheapest = min(offers, key=lambda o: o['price'])
            db.update_alert_price(alert['id'], cheapest['price'])

            if cheapest['price'] <= float(alert['target_price']):
                print(f"   🎯 ¡Objetivo alcanzado! Precio más bajo: ${cheapest['price']:.2f}")

                if send_alert_email(alert, cheapest['price'], cheapest):
                    db.mark_alert_triggered(alert['id'])
                    print("   📧 Email enviado y alerta desactivada")

        except Exception as e:
            print(f"   ❌ Error procesando alerta {route}: {str(e)}")

    print(f"\n🎉 Monitoreo completado: {total_saved} ofertas guardadas en total")
    print(f"⏰ Finalizado: {datetime.now()}")


if __name__ == "__main__":
    monitor_flights()
