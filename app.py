import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from database import Database
from amadeus_client import AmadeusClient
import time

# Configuración de la página
st.set_page_config(
    page_title="Flight Scan - Monitor de Tarifas",
    page_icon="✈️",
    layout="wide"
)

# Inicializar conexiones
@st.cache_resource
def init_database():
    return Database(
        host=st.secrets["DB_HOST"],
        port=st.secrets["DB_PORT"],
        database=st.secrets["DB_NAME"],
        user=st.secrets["DB_USER"],
        password=st.secrets["DB_PASSWORD"]
    )

@st.cache_resource
def init_amadeus():
    return AmadeusClient(
        api_key=st.secrets["AMADEUS_API_KEY"],
        api_secret=st.secrets["AMADEUS_API_SECRET"]
    )

db = init_database()
amadeus = init_amadeus()

# Título principal
st.title("✈️ Flight Scan - Monitor de Tarifas Aéreas")
st.markdown("---")

# Sidebar para configuración
with st.sidebar:
    st.header("⚙️ Configuración de Búsqueda")
    
    # Parámetros de búsqueda
    origen = st.text_input("Origen (código IATA)", "EZE", max_chars=3).upper()
    destino = st.text_input("Destino (código IATA)", "MIA", max_chars=3).upper()
    fecha_ida = st.date_input("Fecha de ida", datetime.now() + timedelta(days=30))
    fecha_vuelta = st.date_input("Fecha de vuelta", datetime.now() + timedelta(days=37))
    adultos = st.number_input("Adultos", min_value=1, max_value=9, value=1)
    
    st.markdown("---")
    st.header("📊 Configuración de Ingesta")
    
    # Configuración de monitoreo
    frecuencia = st.selectbox(
        "Frecuencia de consulta",
        ["Manual", "Cada 5 minutos", "Cada 30 minutos", "Cada 2 horas", "Cada 24 horas"]
    )
    
    frecuencia_map = {
        "Cada 5 minutos": 5,
        "Cada 30 minutos": 30,
        "Cada 2 horas": 120,
        "Cada 24 horas": 1440
    }
    
    if frecuencia != "Manual":
        duracion_dias = st.number_input(
            "Duración del monitoreo (días)",
            min_value=1,
            max_value=30,
            value=7
        )
    
    st.markdown("---")
    
    # Botón de búsqueda inmediata
    if st.button("🔍 Buscar Vuelos Ahora", type="primary"):
        with st.spinner("Consultando Amadeus..."):
            try:
                ofertas = amadeus.search_flights(
                    origin=origen,
                    destination=destino,
                    departure_date=fecha_ida.strftime("%Y-%m-%d"),
                    return_date=fecha_vuelta.strftime("%Y-%m-%d"),
                    adults=adultos
                )
                
                if ofertas:
                    # Guardar en base de datos
                    for oferta in ofertas:
                        db.insert_flight_offer(
                            origin=origen,
                            destination=destino,
                            departure_date=fecha_ida.strftime("%Y-%m-%d"),
                            return_date=fecha_vuelta.strftime("%Y-%m-%d"),
                            price=oferta['price'],
                            currency=oferta['currency'],
                            airline=oferta.get('airline', 'Unknown'),
                            flight_data=oferta
                        )
                    st.success(f"✅ Se encontraron {len(ofertas)} ofertas")
                else:
                    st.warning("No se encontraron ofertas")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    # Botón para iniciar monitoreo
    if frecuencia != "Manual":
        if st.button("▶️ Iniciar Monitoreo Automático"):
            st.session_state['monitoring'] = True
            st.session_state['monitoring_config'] = {
                'origen': origen,
                'destino': destino,
                'fecha_ida': fecha_ida,
                'fecha_vuelta': fecha_vuelta,
                'adultos': adultos,
                'frecuencia': frecuencia_map[frecuencia],
                'duracion': duracion_dias
            }
        
        if st.session_state.get('monitoring', False):
            if st.button("⏸️ Detener Monitoreo"):
                st.session_state['monitoring'] = False

# Tabs principales
tab1, tab2, tab3 = st.tabs(["📈 Análisis de Tarifas", "📋 Historial de Búsquedas", "ℹ️ Información"])

with tab1:
    st.header("Evolución de Precios")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filtro_origen = st.text_input("Filtrar por origen", value=origen, key="filter_origin")
    with col2:
        filtro_destino = st.text_input("Filtrar por destino", value=destino, key="filter_dest")
    with col3:
        dias_atras = st.selectbox("Período", [7, 14, 30, 60, 90], index=0)
    
    # Obtener datos históricos
    fecha_desde = (datetime.now() - timedelta(days=dias_atras)).strftime("%Y-%m-%d")
    df_historico = db.get_price_history(
        origin=filtro_origen,
        destination=filtro_destino,
        date_from=fecha_desde
    )
    
    if not df_historico.empty:
        # Gráfico de evolución de precios
        fig_lineas = px.line(
            df_historico,
            x='search_timestamp',
            y='price',
            color='airline',
            title=f'Evolución de Tarifas {filtro_origen} → {filtro_destino}',
            labels={
                'search_timestamp': 'Fecha de Consulta',
                'price': 'Precio (USD)',
                'airline': 'Aerolínea'
            }
        )
        fig_lineas.update_layout(height=500)
        st.plotly_chart(fig_lineas, use_container_width=True)
        
        # Estadísticas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Precio Mínimo", f"${df_historico['price'].min():.2f}")
        with col2:
            st.metric("Precio Promedio", f"${df_historico['price'].mean():.2f}")
        with col3:
            st.metric("Precio Máximo", f"${df_historico['price'].max():.2f}")
        with col4:
            st.metric("Total Consultas", len(df_historico))
        
        # Distribución de precios por aerolínea
        st.subheader("Distribución de Precios por Aerolínea")
        fig_box = px.box(
            df_historico,
            x='airline',
            y='price',
            color='airline',
            title='Comparación de Precios por Aerolínea'
        )
        st.plotly_chart(fig_box, use_container_width=True)
        
        # Tabla de datos
        st.subheader("Datos Detallados")
        st.dataframe(
            df_historico[['search_timestamp', 'origin', 'destination', 
                         'departure_date', 'price', 'currency', 'airline']],
            use_container_width=True
        )
        
    else:
        st.info("No hay datos históricos para mostrar. Realiza algunas búsquedas primero.")

with tab2:
    st.header("Historial de Búsquedas")
    
    # Obtener todas las búsquedas recientes
    df_all = db.get_all_searches(limit=100)
    
    if not df_all.empty:
        st.dataframe(df_all, use_container_width=True)
        
        # Botón para exportar
        csv = df_all.to_csv(index=False)
        st.download_button(
            label="📥 Descargar CSV",
            data=csv,
            file_name=f"flight_searches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No hay búsquedas registradas aún.")

with tab3:
    st.header("Información del Proyecto")
    
    st.markdown("""
    ### 📌 Acerca de Flight Scan
    
    Flight Scan es una herramienta de monitoreo de tarifas aéreas que permite:
    
    - 🔍 **Búsqueda de vuelos**: Consulta ofertas en tiempo real usando la API de Amadeus
    - 📊 **Monitoreo automático**: Programa búsquedas periódicas (cada 5 min, 30 min, 2h o diarias)
    - 💾 **Almacenamiento**: Guarda el historial en PostgreSQL para análisis posterior
    - 📈 **Visualización**: Gráficos interactivos de evolución de precios
    - 📉 **Análisis**: Estadísticas y comparaciones por aerolínea
    
    ### 🛠️ Tecnologías Utilizadas
    
    - **Frontend**: Streamlit
    - **Base de Datos**: PostgreSQL (Render)
    - **API**: Amadeus Flight Offers
    - **Visualización**: Plotly
    
    ### 👨‍💻 Desarrollado para
    
    Trabajo Práctico - Segundo Módulo  
    Programación Avanzada en Ciencia de Datos  
    Universidad de la Ciudad de Buenos Aires
    
    ### 📚 Repositorio
    
    [github.com/alemeds/flight-scan](https://github.com/alemeds/flight-scan)
    """)

# Monitoreo automático (ejecuta en background si está activo)
if st.session_state.get('monitoring', False):
    config = st.session_state['monitoring_config']
    
    st.sidebar.success("🟢 Monitoreo ACTIVO")
    st.sidebar.info(f"Frecuencia: {frecuencia}")
    
    # Aquí irían las consultas automáticas
    # Nota: Streamlit no mantiene procesos en background nativamente
    # Para monitoreo real, se recomienda usar una tarea programada externa
    st.sidebar.warning("⚠️ Para monitoreo 24/7, usa un scheduler externo (cron, GitHub Actions, etc.)")
