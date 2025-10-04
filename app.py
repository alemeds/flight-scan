import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database import Database
from amadeus_client import AmadeusClient
import time
import os

# Configuración de la página
st.set_page_config(
    page_title="Flight Scan - Monitor de Vuelos",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar conexiones
@st.cache_resource
def init_database():
    """Inicializa la conexión a la base de datos"""
    try:
        db = Database(
            host=st.secrets["DB_HOST"],
            port=int(st.secrets.get("DB_PORT", 5432)),
            database=st.secrets["DB_NAME"],
            user=st.secrets["DB_USER"],
            password=st.secrets["DB_PASSWORD"]
        )
        return db
    except Exception as e:
        st.error(f"Error conectando a la base de datos: {str(e)}")
        return None

@st.cache_resource
def init_amadeus():
    """Inicializa el cliente de Amadeus"""
    try:
        amadeus = AmadeusClient(
            api_key=st.secrets["AMADEUS_API_KEY"],
            api_secret=st.secrets["AMADEUS_API_SECRET"]
        )
        return amadeus
    except Exception as e:
        st.error(f"Error inicializando cliente Amadeus: {str(e)}")
        return None

# Inicializar
db = init_database()
amadeus = init_amadeus()

# Título principal
st.title("✈️ Flight Scan - Monitor de Precios de Vuelos")
st.markdown("**Sistema de monitoreo y análisis de tarifas usando Amadeus API**")

# Sidebar - Configuración de búsqueda
st.sidebar.header("🔍 Búsqueda de Vuelos")

with st.sidebar.form("search_form"):
    origin = st.text_input(
        "Origen (Código IATA)", 
        value="EZE",
        help="Ejemplo: EZE para Buenos Aires"
    ).upper()
    
    destination = st.text_input(
        "Destino (Código IATA)", 
        value="MIA",
        help="Ejemplo: MIA para Miami"
    ).upper()
    
    col1, col2 = st.columns(2)
    with col1:
        departure_date = st.date_input(
            "Fecha de salida",
            value=datetime.now() + timedelta(days=30),
            min_value=datetime.now().date()
        )
    
    with col2:
        return_date = st.date_input(
            "Fecha de regreso",
            value=datetime.now() + timedelta(days=37),
            min_value=datetime.now().date()
        )
    
    adults = st.number_input("Adultos", min_value=1, max_value=9, value=1)
    
    submit_search = st.form_submit_button("🔍 Buscar Vuelos Ahora", use_container_width=True)

# Procesar búsqueda
if submit_search:
    if not db or not amadeus:
        st.error("Error: No se pudo inicializar las conexiones necesarias.")
    elif origin and destination:
        with st.spinner("🔎 Buscando vuelos disponibles..."):
            try:
                # Buscar vuelos
                offers = amadeus.search_flights(
                    origin=origin,
                    destination=destination,
                    departure_date=departure_date.strftime('%Y-%m-%d'),
                    return_date=return_date.strftime('%Y-%m-%d'),
                    adults=adults
                )
                
                if offers:
                    st.success(f"✅ Se encontraron {len(offers)} ofertas de vuelos")
                    
                    # Guardar ofertas en la base de datos
                    saved_count = 0
                    for offer in offers:
                        try:
                            db.insert_flight_offer(
                                origin=origin,
                                destination=destination,
                                departure_date=departure_date.strftime('%Y-%m-%d'),
                                return_date=return_date.strftime('%Y-%m-%d'),
                                adults=adults,
                                price=offer['price'],
                                currency=offer['currency'],
                                airline=offer.get('airline', 'N/A'),
                                flight_data=offer
                            )
                            saved_count += 1
                        except Exception as e:
                            st.warning(f"Error guardando oferta: {str(e)}")
                    
                    st.info(f"💾 Se guardaron {saved_count} ofertas en la base de datos")
                    
                    # Mostrar resultados
                    df_offers = pd.DataFrame(offers)
                    st.dataframe(
                        df_offers[['airline', 'price', 'currency', 'duration', 'stops']],
                        use_container_width=True
                    )
                else:
                    st.warning("⚠️ No se encontraron vuelos para los criterios especificados")
                    
            except Exception as e:
                st.error(f"❌ Error buscando vuelos: {str(e)}")
    else:
        st.warning("⚠️ Por favor ingresa origen y destino")

# Sección de monitoreo automático
st.sidebar.markdown("---")
st.sidebar.header("⏰ Monitoreo Automático")

with st.sidebar.form("monitor_form"):
    st.markdown("**Configuración de Monitoreo**")
    
    frequency = st.selectbox(
        "Frecuencia de consulta",
        options=[
            ("5 minutos", 5),
            ("30 minutos", 30),
            ("2 horas", 120),
            ("24 horas", 1440)
        ],
        format_func=lambda x: x[0]
    )
    
    duration_days = st.number_input(
        "Duración del monitoreo (días)",
        min_value=1,
        max_value=30,
        value=7
    )
    
    submit_monitor = st.form_submit_button("▶️ Iniciar Monitoreo", use_container_width=True)

if submit_monitor:
    st.sidebar.info(
        "ℹ️ El monitoreo automático en Streamlit Cloud requiere configuración adicional. "
        "Para monitoreo continuo, considera usar GitHub Actions según el README."
    )

# Tabs principales
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📈 Análisis de Tarifas", "📋 Historial"])

# TAB 1: Dashboard
with tab1:
    st.header("📊 Resumen General")
    
    if db:
        try:
            # Obtener datos recientes
            recent_data = db.get_recent_searches(limit=100)
            
            if recent_data:
                df = pd.DataFrame(recent_data)
                
                # Métricas principales
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Búsquedas", len(df))
                
                with col2:
                    if 'price' in df.columns:
                        avg_price = df['price'].mean()
                        st.metric("Precio Promedio", f"${avg_price:.2f}")
                
                with col3:
                    if 'price' in df.columns:
                        min_price = df['price'].min()
                        st.metric("Precio Mínimo", f"${min_price:.2f}")
                
                with col4:
                    if 'price' in df.columns:
                        max_price = df['price'].max()
                        st.metric("Precio Máximo", f"${max_price:.2f}")
                
                # Gráfico de evolución de precios
                st.subheader("Evolución de Precios")
                
                if 'search_timestamp' in df.columns and 'price' in df.columns:
                    df['search_timestamp'] = pd.to_datetime(df['search_timestamp'])
                    
                    fig = px.line(
                        df.sort_values('search_timestamp'),
                        x='search_timestamp',
                        y='price',
                        color='airline' if 'airline' in df.columns else None,
                        title='Evolución Temporal de Precios',
                        labels={'search_timestamp': 'Fecha', 'price': 'Precio (USD)'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                # Distribución por aerolínea
                if 'airline' in df.columns:
                    st.subheader("Distribución por Aerolínea")
                    
                    fig2 = px.box(
                        df,
                        x='airline',
                        y='price',
                        title='Distribución de Precios por Aerolínea',
                        labels={'airline': 'Aerolínea', 'price': 'Precio (USD)'}
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                
            else:
                st.info("📭 No hay datos disponibles. Realiza una búsqueda para comenzar.")
                
        except Exception as e:
            st.error(f"Error cargando dashboard: {str(e)}")
    else:
        st.error("No se pudo conectar a la base de datos")

# TAB 2: Análisis de Tarifas
with tab2:
    st.header("📈 Análisis Detallado de Tarifas")
    
    if db:
        try:
            # Filtros
            col1, col2 = st.columns(2)
            
            with col1:
                routes = db.get_unique_routes()
                if routes:
                    selected_route = st.selectbox(
                        "Seleccionar Ruta",
                        options=routes,
                        format_func=lambda x: f"{x[0]} → {x[1]}"
                    )
                else:
                    selected_route = None
                    st.info("No hay rutas disponibles")
            
            with col2:
                days_back = st.slider(
                    "Días hacia atrás",
                    min_value=1,
                    max_value=90,
                    value=30
                )
            
            if selected_route:
                # Obtener datos de la ruta seleccionada
                route_data = db.get_searches_by_route(
                    origin=selected_route[0],
                    destination=selected_route[1],
                    days=days_back
                )
                
                if route_data:
                    df_route = pd.DataFrame(route_data)
                    df_route['search_timestamp'] = pd.to_datetime(df_route['search_timestamp'])
                    
                    # Estadísticas
                    st.subheader("📊 Estadísticas de la Ruta")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Búsquedas", len(df_route))
                    with col2:
                        st.metric("Precio Min", f"${df_route['price'].min():.2f}")
                    with col3:
                        st.metric("Precio Promedio", f"${df_route['price'].mean():.2f}")
                    with col4:
                        st.metric("Precio Max", f"${df_route['price'].max():.2f}")
                    
                    # Gráfico temporal
                    fig = px.scatter(
                        df_route,
                        x='search_timestamp',
                        y='price',
                        color='airline' if 'airline' in df_route.columns else None,
                        size='price',
                        title=f'Precios {selected_route[0]} → {selected_route[1]}',
                        labels={'search_timestamp': 'Fecha', 'price': 'Precio (USD)'}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Tabla de datos
                    st.subheader("📋 Datos Detallados")
                    st.dataframe(
                        df_route[['search_timestamp', 'departure_date', 'return_date', 'airline', 'price', 'currency']],
                        use_container_width=True
                    )
                    
                    # Botón de exportación
                    csv = df_route.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Descargar CSV",
                        data=csv,
                        file_name=f"flight_data_{selected_route[0]}_{selected_route[1]}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No hay datos para esta ruta en el período seleccionado")
                    
        except Exception as e:
            st.error(f"Error en análisis: {str(e)}")

# TAB 3: Historial
with tab3:
    st.header("📋 Historial Completo de Búsquedas")
    
    if db:
        try:
            # Obtener todo el historial
            all_data = db.get_recent_searches(limit=500)
            
            if all_data:
                df_all = pd.DataFrame(all_data)
                
                # Filtros
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if 'origin' in df_all.columns:
                        origins = ['Todos'] + sorted(df_all['origin'].unique().tolist())
                        filter_origin = st.selectbox("Filtrar por Origen", origins)
                
                with col2:
                    if 'destination' in df_all.columns:
                        destinations = ['Todos'] + sorted(df_all['destination'].unique().tolist())
                        filter_destination = st.selectbox("Filtrar por Destino", destinations)
                
                with col3:
                    if 'airline' in df_all.columns:
                        airlines = ['Todos'] + sorted(df_all['airline'].dropna().unique().tolist())
                        filter_airline = st.selectbox("Filtrar por Aerolínea", airlines)
                
                # Aplicar filtros
                df_filtered = df_all.copy()
                
                if filter_origin != 'Todos':
                    df_filtered = df_filtered[df_filtered['origin'] == filter_origin]
                
                if filter_destination != 'Todos':
                    df_filtered = df_filtered[df_filtered['destination'] == filter_destination]
                
                if filter_airline != 'Todos':
                    df_filtered = df_filtered[df_filtered['airline'] == filter_airline]
                
                # Mostrar resultados
                st.write(f"**Mostrando {len(df_filtered)} registros**")
                
                st.dataframe(
                    df_filtered[[
                        'search_timestamp', 'origin', 'destination', 
                        'departure_date', 'return_date', 'airline', 
                        'price', 'currency', 'adults'
                    ]],
                    use_container_width=True,
                    height=400
                )
                
                # Exportar
                csv_all = df_filtered.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Exportar Historial Completo",
                    data=csv_all,
                    file_name=f"flight_history_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
                
            else:
                st.info("📭 No hay historial disponible")
                
        except Exception as e:
            st.error(f"Error cargando historial: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>🚀 Flight Scan - Desarrollado para Programación Avanzada en Ciencia de Datos</p>
        <p>Universidad de la Ciudad de Buenos Aires | Powered by Amadeus API & PostgreSQL</p>
    </div>
    """,
    unsafe_allow_html=True
)
