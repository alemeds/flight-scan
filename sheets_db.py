import gspread
from gspread.utils import rowcol_to_a1, ValueRenderOption
from google.oauth2.service_account import Credentials
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple
import logging
import uuid

logger = logging.getLogger(__name__)

SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

DEFAULT_SPREADSHEET_NAME = 'flight-scan-db'

SEARCHES_SHEET = 'busquedas'
ALERTS_SHEET = 'alertas_precio'

# Headers en español porque la planilla es de revisión manual para la familia.
# La interfaz pública de esta clase traduce a las keys en inglés que consume app.py.
SEARCHES_HEADERS = [
    'timestamp', 'origen', 'destino', 'fecha_salida', 'fecha_regreso',
    'adultos', 'precio', 'moneda', 'aerolinea', 'simulado'
]
ALERTS_HEADERS = [
    'id', 'origen', 'destino', 'fecha_salida', 'fecha_regreso', 'adultos',
    'precio_objetivo', 'ultimo_precio', 'activa', 'ultima_revision',
    'disparada_en', 'creada_en'
]

TIMESTAMP_FORMAT = '%Y-%m-%d %H:%M:%S'


class DatabaseError(Exception):
    """Error de acceso a la planilla de Google Sheets"""
    pass


def _to_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().upper() in ('TRUE', '1', 'SI', 'YES')


def _parse_date(value) -> Optional[date]:
    if isinstance(value, date):
        return value
    try:
        return datetime.strptime(str(value).strip(), '%Y-%m-%d').date()
    except ValueError:
        return None


def _to_float(value) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class SheetsDatabase:
    """
    Persistencia en Google Sheets, con la misma interfaz pública que la
    antigua capa PostgreSQL para no romper app.py ni monitor_script.py.

    La planilla debe existir y estar compartida (rol Editor) con el email
    de la service account. Las hojas y sus encabezados se crean solos.
    """

    def __init__(
        self,
        credentials_info: Dict,
        spreadsheet_name: str = DEFAULT_SPREADSHEET_NAME,
        spreadsheet_id: Optional[str] = None
    ):
        try:
            creds = Credentials.from_service_account_info(credentials_info, scopes=SCOPES)
            self._client = gspread.authorize(creds)

            if spreadsheet_id:
                self._spreadsheet = self._client.open_by_key(spreadsheet_id)
            else:
                self._spreadsheet = self._client.open(spreadsheet_name)

        except gspread.SpreadsheetNotFound:
            raise DatabaseError(
                f"No se encontró la planilla '{spreadsheet_name}'. "
                "Creala en Google Sheets y compartila (rol Editor) con el email "
                "de la service account."
            )
        except DatabaseError:
            raise
        except Exception as e:
            raise DatabaseError(f"Error conectando a Google Sheets: {type(e).__name__}")

        self._ensure_worksheets()

    def _ensure_worksheets(self) -> None:
        """Crea las hojas con sus encabezados si no existen"""
        for sheet_name, headers in (
            (SEARCHES_SHEET, SEARCHES_HEADERS),
            (ALERTS_SHEET, ALERTS_HEADERS)
        ):
            try:
                ws = self._spreadsheet.worksheet(sheet_name)
            except gspread.WorksheetNotFound:
                ws = self._spreadsheet.add_worksheet(
                    title=sheet_name, rows=1000, cols=len(headers)
                )
                ws.append_row(headers)
                continue

            if not ws.row_values(1):
                ws.append_row(headers)

    def _worksheet(self, name: str):
        return self._spreadsheet.worksheet(name)

    # ------------------------------------------------------------------
    # Búsquedas (hoja "busquedas")
    # ------------------------------------------------------------------

    def _searches_records(self) -> List[Dict]:
        """Lee la hoja de búsquedas y traduce a las keys que consume la app"""
        try:
            # UNFORMATTED: el valor real de la celda, no el string formateado
            # según el locale de la planilla (que corrompe los decimales)
            rows = self._worksheet(SEARCHES_SHEET).get_all_records(
                expected_headers=SEARCHES_HEADERS,
                value_render_option=ValueRenderOption.unformatted
            )
        except gspread.exceptions.GSpreadException as e:
            logger.error(f"Error leyendo búsquedas: {type(e).__name__}")
            return []

        records = []
        for row in rows:
            price = _to_float(row.get('precio'))
            if price is None:
                continue

            records.append({
                'search_timestamp': str(row.get('timestamp', '')),
                'origin': str(row.get('origen', '')),
                'destination': str(row.get('destino', '')),
                'departure_date': str(row.get('fecha_salida', '')),
                'return_date': str(row.get('fecha_regreso', '')),
                'adults': int(row.get('adultos') or 1),
                'price': price,
                'currency': str(row.get('moneda', 'USD')),
                'airline': str(row.get('aerolinea', 'N/A')),
                'is_simulated': _to_bool(row.get('simulado'))
            })
        return records

    def insert_flight_offers(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str],
        adults: int,
        offers: List[Dict],
        is_simulated: bool = False
    ) -> int:
        """
        Inserta un lote de ofertas en una sola llamada a la API de Sheets
        (una fila por oferta). Devuelve la cantidad de filas guardadas.
        """
        if not offers:
            return 0

        timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
        rows = [
            [
                timestamp,
                origin,
                destination,
                departure_date,
                return_date or '',
                adults,
                float(offer['price']),
                offer.get('currency', 'USD'),
                offer.get('airline', 'N/A'),
                'TRUE' if is_simulated else 'FALSE'
            ]
            for offer in offers
        ]

        try:
            # RAW: evita que Sheets reinterprete números/fechas según el locale
            # de la planilla (con USER_ENTERED, "390.18" se vuelve 39018 en es-AR)
            self._worksheet(SEARCHES_SHEET).append_rows(
                rows, value_input_option='RAW'
            )
            return len(rows)
        except gspread.exceptions.GSpreadException as e:
            raise DatabaseError(f"Error guardando ofertas: {type(e).__name__}")

    def get_recent_searches(self, limit: int = 100, simulated: bool = False) -> List[Dict]:
        """Búsquedas más recientes del modo indicado (reales o simuladas)"""
        limit = min(int(limit), 1000)
        records = [r for r in self._searches_records() if r['is_simulated'] == simulated]
        # Timestamp ISO: el orden lexicográfico es cronológico
        records.sort(key=lambda r: r['search_timestamp'], reverse=True)
        return records[:limit]

    def get_unique_routes(self, simulated: bool = False) -> List[Tuple[str, str]]:
        """Rutas únicas (origen, destino) del modo indicado"""
        routes = {
            (r['origin'], r['destination'])
            for r in self._searches_records()
            if r['is_simulated'] == simulated
        }
        return sorted(routes)

    def get_searches_by_route(
        self,
        origin: str,
        destination: str,
        days: int = 30,
        simulated: bool = False
    ) -> List[Dict]:
        """Búsquedas de una ruta en los últimos N días"""
        days = min(int(days), 365)
        cutoff = datetime.now() - timedelta(days=days)

        results = []
        for record in self._searches_records():
            if record['is_simulated'] != simulated:
                continue
            if record['origin'] != origin or record['destination'] != destination:
                continue
            try:
                ts = datetime.strptime(record['search_timestamp'], TIMESTAMP_FORMAT)
            except ValueError:
                continue
            if ts >= cutoff:
                results.append(record)

        results.sort(key=lambda r: r['search_timestamp'], reverse=True)
        return results

    # ------------------------------------------------------------------
    # Alertas de precio (hoja "alertas_precio")
    # ------------------------------------------------------------------

    def create_price_alert(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str],
        adults: int,
        target_price: float,
        last_price: Optional[float] = None
    ) -> str:
        """Crea una alerta de precio y devuelve su ID"""
        alert_id = uuid.uuid4().hex[:8]
        row = [
            alert_id,
            origin,
            destination,
            departure_date,
            return_date or '',
            adults,
            float(target_price),
            float(last_price) if last_price is not None else '',
            'TRUE',
            '',
            '',
            datetime.now().strftime(TIMESTAMP_FORMAT)
        ]

        try:
            self._worksheet(ALERTS_SHEET).append_row(
                row, value_input_option='RAW'
            )
            return alert_id
        except gspread.exceptions.GSpreadException as e:
            raise DatabaseError(f"Error creando alerta: {type(e).__name__}")

    def get_active_alerts(self) -> List[Dict]:
        """Alertas activas, con las keys que consumen app.py y el monitor"""
        try:
            rows = self._worksheet(ALERTS_SHEET).get_all_records(
                expected_headers=ALERTS_HEADERS,
                value_render_option=ValueRenderOption.unformatted
            )
        except gspread.exceptions.GSpreadException as e:
            logger.error(f"Error leyendo alertas: {type(e).__name__}")
            return []

        alerts = []
        for row in rows:
            if not _to_bool(row.get('activa')):
                continue

            departure = _parse_date(row.get('fecha_salida'))
            target_price = _to_float(row.get('precio_objetivo'))
            if departure is None or target_price is None:
                logger.warning(f"Alerta {row.get('id')} con datos inválidos, ignorada")
                continue

            alerts.append({
                'id': str(row.get('id')),
                'origin': str(row.get('origen', '')),
                'destination': str(row.get('destino', '')),
                'departure_date': departure,
                'return_date': _parse_date(row.get('fecha_regreso')),
                'adults': int(row.get('adultos') or 1),
                'target_price': target_price,
                'last_price': _to_float(row.get('ultimo_precio')),
                'created_at': str(row.get('creada_en', ''))
            })
        return alerts

    def _find_alert_row(self, alert_id: str) -> int:
        cell = self._worksheet(ALERTS_SHEET).find(str(alert_id), in_column=1)
        if cell is None:
            raise DatabaseError(f"Alerta {alert_id} no encontrada")
        return cell.row

    def _update_alert_cells(self, alert_id: str, values: Dict[str, object]) -> None:
        """Actualiza columnas puntuales de una alerta (por nombre de header)"""
        try:
            ws = self._worksheet(ALERTS_SHEET)
            row = self._find_alert_row(alert_id)
            for header, value in values.items():
                # update con raw=True (update_cell usa USER_ENTERED y el locale
                # de la planilla rompe los decimales)
                cell = rowcol_to_a1(row, ALERTS_HEADERS.index(header) + 1)
                ws.update([[value]], cell)
        except gspread.exceptions.GSpreadException as e:
            raise DatabaseError(f"Error actualizando alerta: {type(e).__name__}")

    def update_alert_price(self, alert_id: str, price: float) -> None:
        """Actualiza el último precio conocido de una alerta"""
        self._update_alert_cells(alert_id, {
            'ultimo_precio': float(price),
            'ultima_revision': datetime.now().strftime(TIMESTAMP_FORMAT)
        })

    def mark_alert_triggered(self, alert_id: str) -> None:
        """
        Marca una alerta como disparada y la desactiva
        (evita notificaciones repetidas por el mismo objetivo)
        """
        self._update_alert_cells(alert_id, {
            'activa': 'FALSE',
            'disparada_en': datetime.now().strftime(TIMESTAMP_FORMAT)
        })

    def deactivate_alert(self, alert_id: str) -> None:
        """Desactiva una alerta (eliminada por el usuario)"""
        self._update_alert_cells(alert_id, {'activa': 'FALSE'})

    def test_connection(self) -> bool:
        """Prueba el acceso a la planilla"""
        try:
            self._worksheet(SEARCHES_SHEET)
            return True
        except Exception as e:
            logger.error(f"Error de conexión a Sheets: {type(e).__name__}")
            return False
