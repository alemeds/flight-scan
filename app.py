# app.py

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from database import Database
from amadeus_client import AmadeusClient

# ==============================
# Configuración inicial
# ==============================
st.set_page_config(
    page_title="✈️ Flight Scan",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("✈️ Flight Scan - Buscador y Analizador de Vuelos")

# ==============================
# Conexión a la base de datos
# ==============================
db_params = {
    "host": st.secrets["db_host"],
    "port": st.secrets["db_port"],
    "database": st.secrets["db_name"],
    "user": st.secrets["db_user"],
    "password": st.secrets["db_password"],
}
db = Database(**db_params)
db.create_tables()

# ==============================
# Cliente Amadeus
# ==============================
amadeus = AmadeusClient(
    api_key=st.secrets["amadeus_api_key"],
    api_secret=st.secrets["amadeus_api_secret"]
)

# ==============================
# Sidebar - búsqueda
# ==============================
st.sidebar.header("🔍 Parámetros de búsqueda")

origin = st.sidebar.text_input("Origen (IATA)", "EZE")
destination = st.sidebar.text_input("Destino (IATA)", "MIA")

departure_date = st.sidebar.date_input("Fecha de ida", datetime.today())
return_date = st.sidebar.date_input("Fecha de vuelta (opcional)", None)
adults = st.sidebar.number_input("Adultos", min_value=1, max_value=9, value=1)
max_results = st.sidebar.slider("Resultados máx.", 5, 50, 10)

if st.sidebar.button("Buscar vuelos"):
    st.sidebar.success("Buscando vuelos...")

    offers = amadeus.search_flights(
        origin=origin,
        destination=destination,
        departure_date=departure_date.strftime("%Y-%m-%d"),
        return_date=return_date.strftime("%Y-%m-%d") if return_date else None,
        adults=adults,
        max_results=max_results
    )

    if offers:
        st.success(f"✅ Se encontraron {len(offers)} ofertas")

        for offer in offers:
            try:
                db.insert_flight_offer(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date,
                    return_date=return_date if return_date else None,
                    adults=adults,
                    price=offer.get("price", 0),
                    currency=offer.get("currency", "USD"),
                    airline=offer.get("airline", "Unknown"),
                    flight_data=offer
                )
            except Exception as e:
                st.warning(f"⚠️ No se pudo guardar oferta {offer.get('id')}: {e}")
    else:
        st.error("❌ No se encontraron ofertas")

# ==============================
# Tabs de navegación
# ==============================
tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Estadísticas", "📈 Evolución de precios", "🛫 Seguimiento de rutas", "🕒 Últimas búsquedas"]
)

# ==============================
# Tab 1: Estadísticas
# ==============================
with tab1:
    st.subheader("📊 Estadísticas de vuelos")

    df_stats = db.get_price_statistics(origin, destination)
    if not df_stats.empty:
        min_price = float(df_stats["min_price"].iloc[0])
        max_price = float(df_stats["max_price"].iloc[0])
        avg_price = float(df_stats["avg_price"].iloc[0])

        col1, col2, col3 = st.columns(3)
        col1.metric("Precio mínimo", f"{min_price:.2f} {df_stats['currency'].iloc[0]}")
        col2.metric("Precio promedio", f"{avg_price:.2f} {df_stats['currency'].iloc[0]}")
        col3.metric("Precio máximo", f"{max_price:.2f} {df_stats['currency'].iloc[0]}")
    else:
        st.info("ℹ️ No hay estadísticas disponibles todavía")

# ==============================
# Tab 2: Evolución histórica
# ==============================
with tab2:
    st.subheader("📈 Evolución histórica de precios")

    history = db.get_price_history(origin, destination, days=30)
    if not history.empty:
        fig = px.line(
            history,
            x="search_timestamp",
            y="price",
            color="airline",
            markers=True,
            title=f"Evolución de precios: {origin} → {destination}"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ℹ️ No hay historial disponible todavía")

# ==============================
# Tab 3: Seguimiento de rutas
# ==============================
with tab3:
    st.subheader("🛫 Seguimiento de rutas")

    flights = db.get_flights_by_route(
        origin=origin,
        destination=destination,
        from_date=datetime.now().replace(hour=0, minute=0, second=0),
        limit=50
    )

    if not flights.empty:
        st.dataframe(flights)

        fig = px.histogram(
            flights,
            x="airline",
            y="price",
            color="airline",
            title="Distribución de precios por aerolínea",
            histfunc="avg"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ℹ️ No hay vuelos registrados para esta ruta")

# ==============================
# Tab 4: Últimas búsquedas
# ==============================
with tab4:
    st.subheader("🕒 Últimas búsquedas")

    recent = db.get_recent_searches(limit=20)
    if not recent.empty:
        st.dataframe(recent)
    else:
        st.info("ℹ️ No hay búsquedas recientes")

# ==============================
# Cierre de conexión
# ==============================
db.close()
