"""Unit tests for the Google Sheets persistence layer."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import date, datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gspread
from sheets_db import (
    SheetsDatabase,
    DatabaseError,
    SEARCHES_HEADERS,
    ALERTS_HEADERS,
)

FAKE_CREDS = {'type': 'service_account', 'client_email': 'test@test.iam.gserviceaccount.com'}


def make_db(searches_ws=None, alerts_ws=None):
    """Construye una SheetsDatabase con gspread completamente mockeado."""
    searches_ws = searches_ws or MagicMock()
    alerts_ws = alerts_ws or MagicMock()
    searches_ws.row_values.return_value = SEARCHES_HEADERS
    alerts_ws.row_values.return_value = ALERTS_HEADERS

    spreadsheet = MagicMock()

    def get_worksheet(name):
        return {'busquedas': searches_ws, 'alertas_precio': alerts_ws}[name]

    spreadsheet.worksheet.side_effect = get_worksheet

    client = MagicMock()
    client.open.return_value = spreadsheet

    with patch('sheets_db.Credentials'), patch('sheets_db.gspread.authorize', return_value=client):
        db = SheetsDatabase(credentials_info=FAKE_CREDS)

    return db, searches_ws, alerts_ws


class TestConnection:
    def test_should_raise_database_error_when_spreadsheet_not_found(self):
        client = MagicMock()
        client.open.side_effect = gspread.SpreadsheetNotFound

        with patch('sheets_db.Credentials'), \
             patch('sheets_db.gspread.authorize', return_value=client):
            with pytest.raises(DatabaseError, match='service account'):
                SheetsDatabase(credentials_info=FAKE_CREDS)

    def test_should_open_by_key_when_spreadsheet_id_given(self):
        ws = MagicMock()
        ws.row_values.return_value = SEARCHES_HEADERS
        spreadsheet = MagicMock()
        spreadsheet.worksheet.return_value = ws
        client = MagicMock()
        client.open_by_key.return_value = spreadsheet

        with patch('sheets_db.Credentials'), \
             patch('sheets_db.gspread.authorize', return_value=client):
            SheetsDatabase(credentials_info=FAKE_CREDS, spreadsheet_id='abc123')

        client.open_by_key.assert_called_once_with('abc123')
        client.open.assert_not_called()


class TestSearches:
    def _sample_rows(self):
        return [
            {
                'timestamp': '2026-07-27 10:00:00', 'origen': 'EZE', 'destino': 'MIA',
                'fecha_salida': '2026-09-01', 'fecha_regreso': '2026-09-10',
                'adultos': 1, 'precio': 900.0, 'moneda': 'USD',
                'aerolinea': 'LATAM Airlines', 'simulado': 'FALSE'
            },
            {
                'timestamp': '2026-07-28 10:00:00', 'origen': 'EZE', 'destino': 'MIA',
                'fecha_salida': '2026-09-01', 'fecha_regreso': '2026-09-10',
                'adultos': 1, 'precio': 850.5, 'moneda': 'USD',
                'aerolinea': 'American Airlines', 'simulado': 'FALSE'
            },
            {
                'timestamp': '2026-07-28 11:00:00', 'origen': 'AEP', 'destino': 'SCL',
                'fecha_salida': '2026-08-15', 'fecha_regreso': '',
                'adultos': 2, 'precio': 300.0, 'moneda': 'USD',
                'aerolinea': 'Sky Airline', 'simulado': 'TRUE'
            },
        ]

    def test_should_map_spanish_headers_to_english_keys(self):
        db, searches_ws, _ = make_db()
        searches_ws.get_all_records.return_value = self._sample_rows()

        results = db.get_recent_searches(simulated=False)

        assert results[0]['origin'] == 'EZE'
        assert results[0]['price'] == 850.5
        assert results[0]['airline'] == 'American Airlines'
        assert 'search_timestamp' in results[0]

    def test_should_filter_by_simulated_flag(self):
        db, searches_ws, _ = make_db()
        searches_ws.get_all_records.return_value = self._sample_rows()

        real = db.get_recent_searches(simulated=False)
        simulated = db.get_recent_searches(simulated=True)

        assert len(real) == 2
        assert len(simulated) == 1
        assert simulated[0]['origin'] == 'AEP'

    def test_should_sort_recent_first_and_apply_limit(self):
        db, searches_ws, _ = make_db()
        searches_ws.get_all_records.return_value = self._sample_rows()

        results = db.get_recent_searches(limit=1, simulated=False)

        assert len(results) == 1
        assert results[0]['search_timestamp'] == '2026-07-28 10:00:00'

    def test_should_return_unique_routes_for_mode(self):
        db, searches_ws, _ = make_db()
        searches_ws.get_all_records.return_value = self._sample_rows()

        assert db.get_unique_routes(simulated=False) == [('EZE', 'MIA')]
        assert db.get_unique_routes(simulated=True) == [('AEP', 'SCL')]

    def test_should_append_offers_in_single_batch(self):
        db, searches_ws, _ = make_db()
        offers = [
            {'price': 850.5, 'currency': 'USD', 'airline': 'LATAM Airlines'},
            {'price': 920.0, 'currency': 'USD', 'airline': 'American Airlines'},
        ]

        saved = db.insert_flight_offers(
            origin='EZE', destination='MIA',
            departure_date='2026-09-01', return_date='2026-09-10',
            adults=1, offers=offers, is_simulated=False
        )

        assert saved == 2
        searches_ws.append_rows.assert_called_once()
        rows = searches_ws.append_rows.call_args[0][0]
        assert len(rows) == 2
        assert rows[0][1] == 'EZE'
        assert rows[0][6] == 850.5
        assert rows[0][9] == 'FALSE'

    def test_should_not_call_api_when_no_offers(self):
        db, searches_ws, _ = make_db()

        saved = db.insert_flight_offers(
            origin='EZE', destination='MIA',
            departure_date='2026-09-01', return_date=None,
            adults=1, offers=[]
        )

        assert saved == 0
        searches_ws.append_rows.assert_not_called()


class TestAlerts:
    def _sample_alerts(self):
        return [
            {
                'id': 'abc12345', 'origen': 'EZE', 'destino': 'MIA',
                'fecha_salida': '2026-09-01', 'fecha_regreso': '2026-09-10',
                'adultos': 1, 'precio_objetivo': 800.0, 'ultimo_precio': 850.5,
                'activa': 'TRUE', 'ultima_revision': '', 'disparada_en': '',
                'creada_en': '2026-07-28 10:00:00'
            },
            {
                'id': 'def67890', 'origen': 'AEP', 'destino': 'SCL',
                'fecha_salida': '2026-08-15', 'fecha_regreso': '',
                'adultos': 2, 'precio_objetivo': 250.0, 'ultimo_precio': '',
                'activa': 'FALSE', 'ultima_revision': '', 'disparada_en': '',
                'creada_en': '2026-07-20 10:00:00'
            },
        ]

    def test_should_return_only_active_alerts_with_parsed_types(self):
        db, _, alerts_ws = make_db()
        alerts_ws.get_all_records.return_value = self._sample_alerts()

        alerts = db.get_active_alerts()

        assert len(alerts) == 1
        alert = alerts[0]
        assert alert['id'] == 'abc12345'
        assert alert['departure_date'] == date(2026, 9, 1)
        assert alert['return_date'] == date(2026, 9, 10)
        assert alert['target_price'] == 800.0
        assert alert['last_price'] == 850.5

    def test_should_skip_alerts_with_invalid_data(self):
        db, _, alerts_ws = make_db()
        broken = self._sample_alerts()[0].copy()
        broken['fecha_salida'] = 'not-a-date'
        alerts_ws.get_all_records.return_value = [broken]

        assert db.get_active_alerts() == []

    def test_should_create_alert_and_return_id(self):
        db, _, alerts_ws = make_db()

        alert_id = db.create_price_alert(
            origin='EZE', destination='MIA',
            departure_date='2026-09-01', return_date='2026-09-10',
            adults=1, target_price=800.0, last_price=850.5
        )

        assert len(alert_id) == 8
        alerts_ws.append_row.assert_called_once()
        row = alerts_ws.append_row.call_args[0][0]
        assert row[0] == alert_id
        assert row[8] == 'TRUE'

    def test_should_update_last_price_and_revision_timestamp(self):
        from gspread.utils import rowcol_to_a1
        db, _, alerts_ws = make_db()
        alerts_ws.find.return_value = MagicMock(row=5)

        db.update_alert_price('abc12345', 720.0)

        calls = {c.args[1]: c.args[0][0][0] for c in alerts_ws.update.call_args_list}
        price_cell = rowcol_to_a1(5, ALERTS_HEADERS.index('ultimo_precio') + 1)
        revision_cell = rowcol_to_a1(5, ALERTS_HEADERS.index('ultima_revision') + 1)
        assert calls[price_cell] == 720.0
        assert revision_cell in calls

    def test_should_deactivate_and_stamp_when_triggered(self):
        from gspread.utils import rowcol_to_a1
        db, _, alerts_ws = make_db()
        alerts_ws.find.return_value = MagicMock(row=3)

        db.mark_alert_triggered('abc12345')

        calls = {c.args[1]: c.args[0][0][0] for c in alerts_ws.update.call_args_list}
        active_cell = rowcol_to_a1(3, ALERTS_HEADERS.index('activa') + 1)
        triggered_cell = rowcol_to_a1(3, ALERTS_HEADERS.index('disparada_en') + 1)
        assert calls[active_cell] == 'FALSE'
        assert triggered_cell in calls

    def test_should_raise_when_alert_not_found(self):
        db, _, alerts_ws = make_db()
        alerts_ws.find.return_value = None

        with pytest.raises(DatabaseError, match='no encontrada'):
            db.deactivate_alert('missing1')
