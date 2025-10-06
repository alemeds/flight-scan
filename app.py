import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database import Database
from amadeus_client import AmadeusClient
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

# Función de simulación de vuelos
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
        airlines = ['Avianca', 'LATAM', 'Aerolineas Argentinas', 'American Airlines', 'Delta', 'United']
        offers = []
        
        for i in range(random.randint(3, 8)):
            price = base_price * random.uniform(0.85, 1.35)
            airline = random.choice(airlines)
            stops = random.choice([0, 1, 2])
            duration = f"{random.randint(4, 16)}h {random.randint(0, 59)}m"
            
            offers.append({
                'price': round(price, 2),
                'currency': 'USD',
                'airline': airline,
                'stops': stops,
                'duration': duration
            })
        
        return sorted(offers, key=lambda x: x['price'])
    except Exception as e:
        st.error(f"Error en simulación: {str(e)}")
        return []

# Inicializar
db = init_database()
amadeus = init_amadeus()

# Inicializar estado de sesión para modo simulación
if 'simulation_mode' not in st.session_state:
    st.session_state.simulation_mode = False

if 'active_searches' not in st.session_state:
    st.session_state.active_searches = []

# Título principal
st.title("✈️ Flight Scan - Monitor de Precios de Vuelos")
st.markdown("**Sistema de monitoreo y análisis de tarifas usando Amadeus API**")

# Sidebar - Configuración de búsqueda
st.sidebar.header("🔍 Búsqueda de Vuelos")

# Modo de operación
col_mode1, col_mode2 = st.sidebar.columns(2)
with col_mode1:
    if st.button("🌐 Modo Real" if st.session_state.simulation_mode else "✅ Modo Real"):
        st.session_state.simulation_mode = False
        st.rerun()

with col_mode2:
    if st.button("✅ Modo Demo" if st.session_state.simulation_mode else "🎮 Modo Demo"):
        st.session_state.simulation_mode = True
        st.rerun()

if st.session_state.simulation_mode:
    st.sidebar.info("🎮 **Modo Simulación Activo** - Datos de prueba")
else:
    st.sidebar.success("🌐 **Modo Real** - API de Amadeus")

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
                    if not amadeus:
                        st.warning("⚠️ API no disponible. Activando modo simulación...")
                        st.session_state.simulation_mode = True
                        offers = simulate_flight_search(
                            origin, destination,
                            departure_date.strftime('%Y-%m-%d'),
                            return_date.strftime('%Y-%m-%d'),
                            adults
                        )
                    else:
                        offers = amadeus.search_flights(
                            origin=origin,
                            destination=destination,
                            departure_date=departure_date.strftime('%Y-%m-%d'),
                            return_date=return_date.strftime('%Y-%m-%d'),
                            adults=adults
                        )
                
                if offers:
                    st.success(f"✅ Se encontraron {len(offers)} ofertas de vuelos")
                    
                    # Verificar precio objetivo
                    lowest_price = min(offer['price'] for offer in offers)
                    if target_price > 0 and lowest_price <= target_price:
                        st.balloons()
                        st.success(f"🎯 ¡Precio objetivo alcanzado! Precio más bajo: ${lowest_price:.2f}")
                    
                    # Guardar ofertas en la base de datos
                    if db:
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
                    
                    # Agregar a búsquedas activas si hay precio objetivo
                    if target_price > 0:
                        search_item = {
                            'origin': origin,
                            'destination': destination,
                            'departure_date': departure_date.strftime('%Y-%m-%d'),
                            'return_date': return_date.strftime('%Y-%m-%d'),
                            'adults': adults,
                            'target_price': target_price,
                            'current_price': lowest_price,
                            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        st.session_state.active_searches.append(search_item)
                        st.success(f"📌 Búsqueda agregada a monitoreo activo")
                    
                    # Mostrar resultados
                    df_offers = pd.DataFrame(offers)
                    
                    # Destacar ofertas que cumplen el objetivo
                    if target_price > 0:
                        df_offers['Cumple Objetivo'] = df_offers['price'] <= target_price
                    
                    st.dataframe(
                        df_offers,
                        use_container_width=True,
                        column_config={
                            'price': st.column_config.NumberColumn('Precio', format="$%.2f"),
                            'Cumple Objetivo': st.column_config.CheckboxColumn('🎯 Objetivo')
                        } if target_price > 0 else None
                    )
                else:
                    st.warning("⚠️ No se encontraron vuelos para los criterios especificados")
                    
            except Exception as e:
                st.error(f"❌ Error buscando vuelos: {str(e)}")
    else:
        st.warning("⚠️ Por favor ingresa origen y destino")

# Gestión de búsquedas activas
if st.session_state.active_searches:
    st.sidebar.markdown("---")
    st.sidebar.header("📋 Búsquedas Activas")
    
    for idx, search in enumerate(st.session_state.active_searches):
        with st.sidebar.expander(f"{search['origin']} → {search['destination']}"):
            st.write(f"**Objetivo:** ${search['target_price']:.2f}")
            st.write(f"**Actual:** ${search['current_price']:.2f}")
            
            if search['current_price'] <= search['target_price']:
                st.success("✅ Objetivo alcanzado")
            else:
                diff = search['current_price'] - search['target_price']
                st.info(f"📊 Faltan ${diff:.2f}")
            
            if st.button(f"🗑️ Eliminar", key=f"del_{idx}"):
                st.session_state.active_searches.pop(idx)
                st.rerun()

# Tabs principales
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📈 Análisis de Tarifas", "📋 Historial"])

# TAB 1: Dashboard
with tab1:
    st.header("📊 Resumen General")
    
    if db:
        try:
            # Obtener datos recientes - con manejo de errores
            try:
                recent_data = db.get_recent_searches(limit=100)
            except AttributeError:
                st.error("⚠️ El método 'get_recent_searches' no está disponible en database.py")
                recent_data = None
            
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
            # Filtros
            col1, col2 = st.columns(2)
            
            with col1:
                try:
                    routes = db.get_unique_routes()
                except AttributeError:
                    st.error("⚠️ El método 'get_unique_routes' no está disponible en database.py")
                    routes = None
                    
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
                # Obtener datos de la ruta seleccionada
                try:
                    route_data = db.get_searches_by_route(
                        origin=selected_route[0],
                        destination=selected_route[1],
                        days=days_back
                    )
                except AttributeError:
                    st.error("⚠️ El método 'get_searches_by_route' no está disponible en database.py")
                    route_data = None
                
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
            try:
                all_data = db.get_recent_searches(limit=500)
            except AttributeError:
                st.error("⚠️ El método 'get_recent_searches' no está disponible en database.py")
                all_data = None
            
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
        <p>Universidad de la Ciudad de Buenos Aires | Powered by Amadeus API & PostgreSQL</p>
    </div>
    """,
    unsafe_allow_html=True
)
