import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from sheets_db import SheetsDatabase, DEFAULT_SPREADSHEET_NAME
from skyscrapper_client import SkyScrapperClient
from config import get_secret, get_gcp_credentials
import time
import os
import random

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
    """Inicializa la conexión a la planilla de Google Sheets"""
    try:
        db = SheetsDatabase(
            credentials_info=get_gcp_credentials(),
            spreadsheet_name=get_secret("SHEET_NAME", DEFAULT_SPREADSHEET_NAME),
            spreadsheet_id=get_secret("SHEET_ID")
        )
        return db
    except Exception as e:
        st.error(f"Error conectando a la base de datos: {str(e)}")
        return None

@st.cache_resource
def init_flight_client():
    """Inicializa el cliente de la API de vuelos (Sky Scrapper via RapidAPI)"""
    try:
        api_key = get_secret("RAPIDAPI_KEY")
        if not api_key:
            st.warning("RAPIDAPI_KEY no configurada - Solo modo simulación disponible")
            return None
        return SkyScrapperClient(api_key=api_key)
    except Exception as e:
        st.warning(f"API de vuelos no disponible: {str(e)}")
        return None

# Función de simulación de vuelos mejorada
def simulate_flight_search(origin, destination, departure_date, return_date, adults):
    """Simula búsqueda de vuelos cuando no hay API disponible"""
    try:
        # Calcular precio base según distancia estimada
        base_price = random.randint(300, 1500)
        
        # Factor de anticipación
        if isinstance(departure_date, str):
            dep_date = datetime.strptime(departure_date, '%Y-%m-%d')
        else:
            dep_date = departure_date
            
        days_ahead = (dep_date - datetime.now()).days
        
        if days_ahead < 7:
            base_price *= 1.8
        elif days_ahead < 30:
            base_price *= 1.3
        elif days_ahead > 90:
            base_price *= 0.7
        
        # Generar múltiples ofertas
        airlines = [
            'American Airlines', 'Delta Air Lines', 'United Airlines',
            'LATAM Airlines', 'Aerolíneas Argentinas', 'Avianca',
            'Copa Airlines', 'Iberia', 'Air France', 'KLM'
        ]
        
        airline_codes = ['AA', 'DL', 'UA', 'LA', 'AR', 'AV', 'CM', 'IB', 'AF', 'KL']
        
        offers = []
        
        for i in range(random.randint(5, 12)):
            price = base_price * random.uniform(0.85, 1.35)
            airline_idx = random.randint(0, len(airlines) - 1)
            airline = airlines[airline_idx]
            airline_code = airline_codes[airline_idx]
            stops = random.choice([0, 0, 1, 1, 2])
            
            hours = random.randint(4, 18)
            minutes = random.randint(0, 59)
            duration = f"{hours}h {minutes}m"
            
            # Generar horarios realistas
            dep_hour = random.randint(0, 23)
            dep_minute = random.randint(0, 59)
            
            if isinstance(dep_date, str):
                dep_datetime = datetime.strptime(dep_date, '%Y-%m-%d')
            else:
                dep_datetime = dep_date
                
            departure_time = dep_datetime.replace(hour=dep_hour, minute=dep_minute).isoformat()
            arrival_time = (dep_datetime + timedelta(hours=hours, minutes=minutes)).isoformat()
            
            offers.append({
                'id': f'SIM{i+1}_{origin}{destination}',
                'price': round(price, 2),
                'currency': 'USD',
                'airline': airline,
                'airline_code': airline_code,
                'stops': stops,
                'duration': duration,
                'departure_time': departure_time,
                'arrival_time': arrival_time,
                'number_of_bookable_seats': random.randint(1, 9)
            })
        
        return sorted(offers, key=lambda x: x['price'])
    except Exception as e:
        st.error(f"Error en simulación: {str(e)}")
        return []

# Inicializar
db = init_database()
flight_client = init_flight_client()

# Inicializar estado de sesión
if 'simulation_mode' not in st.session_state:
    st.session_state.simulation_mode = (flight_client is None)

# Título principal
st.title("✈️ Flight Scan - Monitor de Precios de Vuelos")
st.markdown("**Sistema de monitoreo y análisis de tarifas usando Sky Scrapper API**")

# Sidebar - Configuración de búsqueda
st.sidebar.header("🔍 Búsqueda de Vuelos")

# Modo de operación
col_mode1, col_mode2 = st.sidebar.columns(2)
with col_mode1:
    if st.button("🌐 Modo Real" if st.session_state.simulation_mode else "✅ Modo Real",
                 disabled=(flight_client is None)):
        st.session_state.simulation_mode = False
        st.rerun()

with col_mode2:
    if st.button("✅ Modo Demo" if st.session_state.simulation_mode else "🎮 Modo Demo"):
        st.session_state.simulation_mode = True
        st.rerun()

if st.session_state.simulation_mode:
    st.sidebar.info("🎮 **Modo Simulación Activo** - Datos de prueba realistas")
else:
    st.sidebar.success("🌐 **Modo Real** - API Sky Scrapper")

if flight_client is None:
    st.sidebar.warning("⚠️ API no configurada - Solo modo simulación disponible")

st.sidebar.markdown("---")

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
    
    # Precio objetivo
    target_price = st.number_input(
        "💰 Precio Objetivo (USD)", 
        min_value=0.0, 
        value=0.0,
        step=50.0,
        help="Recibirás una alerta si se encuentra un precio igual o menor"
    )
    
    submit_search = st.form_submit_button("🔍 Buscar Vuelos Ahora", use_container_width=True)

# Procesar búsqueda
if submit_search:
    if origin and destination:
        with st.spinner("🔎 Buscando vuelos disponibles..."):
            try:
                offers = []
                
                # Usar simulación o API real según el modo
                if st.session_state.simulation_mode:
                    st.info("🎮 Usando datos simulados para demostración")
                    offers = simulate_flight_search(
                        origin, destination, 
                        departure_date.strftime('%Y-%m-%d'),
                        return_date.strftime('%Y-%m-%d'),
                        adults
                    )
                else:
                    if not flight_client:
                        st.warning("⚠️ API no disponible. Activando modo simulación...")
                        st.session_state.simulation_mode = True
                        offers = simulate_flight_search(
                            origin, destination,
                            departure_date.strftime('%Y-%m-%d'),
                            return_date.strftime('%Y-%m-%d'),
                            adults
                        )
                    else:
                        try:
                            offers = flight_client.search_flights(
                                origin=origin,
                                destination=destination,
                                departure_date=departure_date.strftime('%Y-%m-%d'),
                                return_date=return_date.strftime('%Y-%m-%d'),
                                adults=adults
                            )
                        except Exception as api_error:
                            st.error(f"Error con API de vuelos: {str(api_error)}")
                            st.info("Cambiando a modo simulación...")
                            st.session_state.simulation_mode = True
                            offers = simulate_flight_search(
                                origin, destination,
                                departure_date.strftime('%Y-%m-%d'),
                                return_date.strftime('%Y-%m-%d'),
                                adults
                            )
                
                if offers:
                    st.success(f"✅ Se encontraron {len(offers)} ofertas de vuelos")
                    
                    # Verificar precio objetivo
                    lowest_price = min(offer['price'] for offer in offers)
                    if target_price > 0 and lowest_price <= target_price:
                        st.balloons()
                        st.success(f"🎯 ¡Precio objetivo alcanzado! Precio más bajo: ${lowest_price:.2f}")
                    
                    # Guardar ofertas en la planilla (una sola llamada por lote)
                    if db:
                        try:
                            saved_count = db.insert_flight_offers(
                                origin=origin,
                                destination=destination,
                                departure_date=departure_date.strftime('%Y-%m-%d'),
                                return_date=return_date.strftime('%Y-%m-%d'),
                                adults=adults,
                                offers=offers,
                                is_simulated=st.session_state.simulation_mode
                            )
                            st.info(f"💾 Se guardaron {saved_count} ofertas en la base de datos")
                        except Exception as e:
                            st.warning(f"Error guardando ofertas: {str(e)}")
                    
                    # Crear alerta de precio persistente si hay precio objetivo
                    if target_price > 0 and db:
                        # Evitar duplicados entre alertas activas
                        exists = any(
                            a['origin'] == origin and
                            a['destination'] == destination and
                            a['departure_date'] == departure_date
                            for a in db.get_active_alerts()
                        )

                        if not exists:
                            db.create_price_alert(
                                origin=origin,
                                destination=destination,
                                departure_date=departure_date.strftime('%Y-%m-%d'),
                                return_date=return_date.strftime('%Y-%m-%d'),
                                adults=adults,
                                target_price=target_price,
                                last_price=lowest_price
                            )
                            st.success("📌 Alerta de precio guardada para monitoreo automático")
                        else:
                            st.info("ℹ️ Ya existe una alerta activa para esta búsqueda")
                    
                    # Mostrar resultados en tabla mejorada
                    df_offers = pd.DataFrame(offers)
                    
                    # Preparar columnas para mostrar
                    display_columns = ['airline', 'price', 'currency', 'duration', 'stops']
                    
                    # Agregar columna de cumplimiento de objetivo
                    if target_price > 0:
                        df_offers['Cumple Objetivo'] = df_offers['price'] <= target_price
                        display_columns.append('Cumple Objetivo')
                    
                    st.dataframe(
                        df_offers[display_columns],
                        use_container_width=True,
                        column_config={
                            'price': st.column_config.NumberColumn('Precio', format="$%.2f"),
                            'stops': st.column_config.NumberColumn('Escalas'),
                            'Cumple Objetivo': st.column_config.CheckboxColumn('🎯 Objetivo')
                        }
                    )
                    
                    # Mostrar detalles adicionales en expander
                    with st.expander("📋 Ver detalles completos"):
                        st.dataframe(df_offers, use_container_width=True)
                    
                else:
                    st.warning("⚠️ No se encontraron vuelos para los criterios especificados")
                    
            except Exception as e:
                st.error(f"❌ Error buscando vuelos: {str(e)}")
    else:
        st.warning("⚠️ Por favor ingresa origen y destino")

# Gestión de alertas de precio activas (persistidas en BD)
if db:
    active_alerts = db.get_active_alerts()

    if active_alerts:
        st.sidebar.markdown("---")
        st.sidebar.header("📋 Alertas de Precio Activas")

        for alert in active_alerts:
            with st.sidebar.expander(f"{alert['origin']} → {alert['destination']}"):
                st.write(f"**Salida:** {alert['departure_date']}")
                st.write(f"**Objetivo:** ${alert['target_price']:.2f}")

                if alert['last_price'] is not None:
                    st.write(f"**Último precio:** ${alert['last_price']:.2f}")

                    if alert['last_price'] <= alert['target_price']:
                        st.success("✅ Objetivo alcanzado")
                    else:
                        diff = alert['last_price'] - alert['target_price']
                        st.info(f"📊 Faltan ${diff:.2f}")

                        # Barra de progreso
                        progress = min(1.0, float(alert['target_price']) / float(alert['last_price']))
                        st.progress(progress)

                if st.button("🗑️ Eliminar", key=f"del_alert_{alert['id']}"):
                    db.deactivate_alert(alert['id'])
                    st.rerun()

# Tabs principales
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📈 Análisis de Tarifas", "📋 Historial"])

# TAB 1: Dashboard
with tab1:
    st.header("📊 Resumen General")
    
    if db:
        try:
            recent_data = db.get_recent_searches(
                limit=100,
                simulated=st.session_state.simulation_mode
            )
            
            if recent_data and len(recent_data) > 0:
                df = pd.DataFrame(recent_data)
                
                # Métricas principales
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Búsquedas", len(df))
                
                with col2:
                    if 'price' in df.columns and len(df) > 0:
                        avg_price = df['price'].mean()
                        st.metric("Precio Promedio", f"${avg_price:.2f}")
                
                with col3:
                    if 'price' in df.columns and len(df) > 0:
                        min_price = df['price'].min()
                        st.metric("Precio Mínimo", f"${min_price:.2f}")
                
                with col4:
                    if 'price' in df.columns and len(df) > 0:
                        max_price = df['price'].max()
                        st.metric("Precio Máximo", f"${max_price:.2f}")
                
                # Gráfico de evolución de precios
                st.subheader("Evolución de Precios")
                
                if 'search_timestamp' in df.columns and 'price' in df.columns and len(df) > 0:
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
                if 'airline' in df.columns and len(df) > 0:
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
                st.info("🔭 No hay datos disponibles. Realiza una búsqueda para comenzar.")
                
        except Exception as e:
            st.error(f"Error cargando dashboard: {str(e)}")
    else:
        st.error("No se pudo conectar a la base de datos")

# TAB 2: Análisis de Tarifas
with tab2:
    st.header("📈 Análisis Detallado de Tarifas")
    
    if db:
        try:
            col1, col2 = st.columns(2)
            
            with col1:
                routes = db.get_unique_routes(simulated=st.session_state.simulation_mode)
                if routes and len(routes) > 0:
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
                route_data = db.get_searches_by_route(
                    origin=selected_route[0],
                    destination=selected_route[1],
                    days=days_back,
                    simulated=st.session_state.simulation_mode
                )
                
                if route_data and len(route_data) > 0:
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
                        title=f'Precios {selected_route[0]} → {selected_route[1]}',
                        labels={'search_timestamp': 'Fecha', 'price': 'Precio (USD)'}
                    )
                    fig.update_traces(marker=dict(size=10))
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
            all_data = db.get_recent_searches(
                limit=500,
                simulated=st.session_state.simulation_mode
            )
            
            if all_data and len(all_data) > 0:
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
                st.info("🔭 No hay historial disponible")
                
        except Exception as e:
            st.error(f"Error cargando historial: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center'>
        <p>🚀 Flight Scan - Desarrollado para Programación Avanzada en Ciencia de Datos</p>
        <p>Universidad de la Ciudad de Buenos Aires | Powered by Sky Scrapper API & Google Sheets</p>
    </div>
    """,
    unsafe_allow_html=True
)
