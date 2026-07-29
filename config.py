"""
Helper de configuración: lee st.secrets en Streamlit Cloud y cae a
variables de entorno / archivo local en desarrollo o scripts sin Streamlit.
"""

import os
import json
from typing import Dict, Optional


def get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    """Busca un secret en st.secrets primero, después en variables de entorno"""
    try:
        import streamlit as st
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        # Sin contexto Streamlit o sin archivo de secrets: usar entorno
        pass
    return os.getenv(name, default)


def get_gcp_credentials() -> Dict:
    """
    Obtiene las credenciales de la service account de Google.

    Producción (Streamlit Cloud): sección [gcp_service_account] de st.secrets.
    Local / monitor por cron: archivo JSON referenciado por GCP_SERVICE_ACCOUNT_FILE.
    """
    try:
        import streamlit as st
        if 'gcp_service_account' in st.secrets:
            return dict(st.secrets['gcp_service_account'])
    except Exception:
        pass

    path = os.getenv('GCP_SERVICE_ACCOUNT_FILE')
    if not path:
        raise ValueError(
            "Credenciales de Google no configuradas: definir [gcp_service_account] "
            "en secrets o la variable de entorno GCP_SERVICE_ACCOUNT_FILE"
        )

    with open(path, 'r') as f:
        return json.load(f)
