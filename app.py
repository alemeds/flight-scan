import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from database import Database
from amadeus_client import AmadeusClient
import time
import numpy as np

# Configuración de la página
st.set_page_config(
    page_title="Flight Trading Monitor",
    page_icon="📈",
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

# Inicializar session state
if 'monitoring_active' not in st.session_state:
    st.session_state['monitoring_active'] = False
if 'selected_flight' not in st.session_state:
    st.session_state['selected_flight'] = None
if 'last_update' not in st.session_state:
    st.session_state['last_update'] = None
if 'price_history' not in st.session_state:
    st.session_state['price_history'] = []

# Título principal
st.title("📈 Flight Trading Monitor")
st.markdown("### Análisis de Tarifas Aéreas en Tiempo Real")
st.markdown("---")

# Sidebar - Configuración
with st.sidebar:
    st.header("🎯 Configuración de Tracking")
    
    # Selector de ruta
    col1, col2 = st.columns(2)
    with col1:
        origen = st.text_input("Origen (IATA)", "EZE", max_chars=3).upper()
    with col2:
        destino = st.text_input("Destino (IATA)", "MIA", max_chars=3).upper()
    
    # Rango de fechas para escanear
    st.subheader("📅 Fechas a Analizar")
    fecha_inicio = st.date_input(
        "Desde",
        datetime.now() + timedelta(days=15),
        min_value=datetime.now() + timedelta(days=1)
    )
    fecha_fin = st.date_input(
        "Hasta",
        datetime.now() + timedelta(days=60),
        min_value=datetime.now() + timedelta(days=1)
    )
    
    # Tipo de vuelo
    tipo_vuelo = st.radio("Tipo de vuelo", ["Ida y vuelta", "Solo ida"])
    
    if tipo_vuelo == "Ida y vuelta":
        dias_estadia = st.slider("Días de estadía", 1, 30, 7)
    
    adultos = st.number_input("Pasajeros", min_value=1, max_value=9, value=1)
    
    st.markdown("---")
    
    # Configuración de monitoreo
    st.header("⏱️ Frecuencia de Tracking")
    frecuencia = st.selectbox(
        "Actualizar cada:",
        ["Manual", "30 segundos", "1 minuto", "5 minutos", "15 minutos", "30 minutos", "1 hora", "2 horas"]
    )
    
    frecuencia_segundos = {
        "30 segundos": 30,
        "1 minuto": 60,
        "5 minutos": 300,
        "15 minutos": 900,
        "30 minutos": 1800,
        "1 hora": 3600,
        "2 horas": 7200
    }
    
    if frecuencia != "Manual":
        duracion_tracking = st.number_input(
            "Duración del tracking (horas)",
            min_value=1,
            max_value=72,
            value=24
        )
    
    st.markdown("---")
    
    # Botones de control
    if st.button("🔍 Escanear Fechas Disponibles", type="primary", use_container_width=True):
        with st.spinner(f"Escaneando {origen} → {destino}..."):
            # Escanear múltiples fechas
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            fechas_a_escanear = []
            current_date = fecha_inicio
            while current_date <= fecha_fin:
                fechas_a_escanear.append(current_date)
                current_date += timedelta(days=1)
            
            total_fechas = len(fechas_a_escanear)
            vuelos_encontrados = []
            
            for idx, fecha_salida in enumerate(fechas_a_escanear):
                progress_bar.progress((idx + 1) / total_fechas)
                status_text.text(f"Escaneando {fecha_salida.strftime('%Y-%m-%d')}...")
                
                if tipo_vuelo == "Ida y vuelta":
                    fecha_vuelta = fecha_salida + timedelta(days=dias_estadia)
                    return_date = fecha_vuelta.strftime("%Y-%m-%d")
                else:
                    return_date = None
                
                try:
                    ofertas = amadeus.search_flights(
                        origin=origen,
                        destination=destino,
                        departure_date=fecha_salida.strftime("%Y-%m-%d"),
                        return_date=return_date,
                        adults=adultos,
                        max_results=5
                    )
                    
                    for oferta in ofertas:
                        # Guardar en BD
                        flight_id = db.insert_flight_offer(
                            origin=origen,
                            destination=destino,
                            departure_date=fecha_salida.strftime("%Y-%m-%d"),
                            return_date=return_date,
                            price=oferta['price'],
                            currency=oferta['currency'],
                            airline=oferta.get('airline', 'Unknown'),
                            flight_data=oferta,
                            adults=adultos
                        )
                        
                        vuelos_encontrados.append({
                            'id': flight_id,
                            'fecha_salida': fecha_salida,
                            'precio': oferta['price'],
                            'aerolinea': oferta.get('airline', 'Unknown')
                        })
                    
                    time.sleep(0.5)  # Para no saturar la API
                    
                except Exception as e:
                    st.error(f"Error en {fecha_salida}: {str(e)}")
            
            progress_bar.empty()
            status_text.empty()
            
            st.success(f"✅ Escaneo completo: {len(vuelos_encontrados)} vuelos encontrados")
            st.session_state['vuelos_disponibles'] = vuelos_encontrados
    
    # Control de monitoreo
    if frecuencia != "Manual":
        st.markdown("---")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("▶️ Iniciar", use_container_width=True):
                st.session_state['monitoring_active'] = True
                st.rerun()
        
        with col2:
            if st.button("⏸️ Pausar", use_container_width=True):
                st.session_state['monitoring_active'] = False
                st.rerun()
        
        if st.session_state.get('monitoring_active', False):
            st.success("🟢 Tracking ACTIVO")
            if frecuencia in frecuencia_segundos:
                st.info(f"⏱️ Próxima actualización: {frecuencia}")

# Tabs principales
tab1, tab2, tab3, tab4 = st.tabs(["📊 Trading Monitor", "🎯 Selector de Vuelos", "📈 Análisis Histórico", "💡 Recomendaciones"])

with tab1:
    st.header("Monitor de Tarifas en Tiempo Real")
    
    # Verificar si hay un vuelo seleccionado
    if st.session_state.get('selected_flight'):
        flight_info = st.session_state['selected_flight']
        
        # Información del vuelo
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Ruta", f"{flight_info['origin']} → {flight_info['destination']}")
        with col2:
            st.metric("Fecha", flight_info['departure_date'])
        with col3:
            st.metric("Pasajeros", flight_info['adults'])
        with col4:
            if st.button("🔄 Cambiar Vuelo"):
                st.session_state['selected_flight'] = None
                st.rerun()
        
        st.markdown("---")
        
        # Obtener histórico de precios para este vuelo específico
        df_tracking = db.get_flight_tracking(
            origin=flight_info['origin'],
            destination=flight_info['destination'],
            departure_date=flight_info['departure_date'],
            return_date=flight_info.get('return_date')
        )
        
        if not df_tracking.empty:
            # Calcular métricas
            precio_actual = df_tracking.iloc[-1]['price']
            precio_inicial = df_tracking.iloc[0]['price']
            precio_min = df_tracking['price'].min()
            precio_max = df_tracking['price'].max()
            precio_promedio = df_tracking['price'].mean()
            variacion = ((precio_actual - precio_inicial) / precio_inicial) * 100
            
            # Métricas principales
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric(
                    "Precio Actual",
                    f"${precio_actual:.2f}",
                    f"{variacion:+.2f}%",
                    delta_color="inverse"
                )
            with col2:
                st.metric("Precio Inicial", f"${precio_inicial:.2f}")
            with col3:
                st.metric("Mínimo", f"${precio_min:.2f}")
            with col4:
                st.metric("Máximo", f"${precio_max:.2f}")
            with col5:
                st.metric("Promedio", f"${precio_promedio:.2f}")
            
            # Gráfico tipo trading con velas
            st.subheader("📊 Gráfico de Evolución de Precios")
            
            # Preparar datos para candlestick
            df_tracking['date'] = pd.to_datetime(df_tracking['search_timestamp'])
            df_tracking = df_tracking.sort_values('date')
            
            # Crear intervalos de tiempo
            if len(df_tracking) > 1:
                # Gráfico de línea con área
                fig = go.Figure()
                
                # Área de precio
                fig.add_trace(go.Scatter(
                    x=df_tracking['date'],
                    y=df_tracking['price'],
                    fill='tozeroy',
                    name='Precio',
                    line=dict(color='#00D9FF', width=3),
                    fillcolor='rgba(0, 217, 255, 0.1)'
                ))
                
                # Línea de promedio móvil
                if len(df_tracking) >= 5:
                    df_tracking['ma'] = df_tracking['price'].rolling(window=5).mean()
                    fig.add_trace(go.Scatter(
                        x=df_tracking['date'],
                        y=df_tracking['ma'],
                        name='Media Móvil (5)',
                        line=dict(color='#FF6B6B', width=2, dash='dash')
                    ))
                
                # Líneas de soporte/resistencia
                fig.add_hline(y=precio_min, line_dash="dot", line_color="green", 
                             annotation_text="Mínimo", annotation_position="right")
                fig.add_hline(y=precio_max, line_dash="dot", line_color="red",
                             annotation_text="Máximo", annotation_position="right")
                fig.add_hline(y=precio_promedio, line_dash="dash", line_color="gray",
                             annotation_text="Promedio", annotation_position="right")
                
                fig.update_layout(
                    title="Evolución del Precio en Tiempo Real",
                    xaxis_title="Fecha/Hora",
                    yaxis_title="Precio (USD)",
                    hovermode='x unified',
                    height=500,
                    template='plotly_dark'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Indicadores técnicos
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("📉 Volatilidad")
                    volatilidad = df_tracking['price'].std()
                    coef_variacion = (volatilidad / precio_promedio) * 100
                    
                    st.metric("Desviación Estándar", f"${volatilidad:.2f}")
                    st.metric("Coeficiente de Variación", f"{coef_variacion:.2f}%")
                    
                    if coef_variacion < 5:
                        st.success("✅ Precio estable")
                    elif coef_variacion < 10:
                        st.warning("⚠️ Volatilidad moderada")
                    else:
                        st.error("🔴 Alta volatilidad")
                
                with col2:
                    st.subheader("🎯 Señales de Trading")
                    
                    # Calcular tendencia
                    if len(df_tracking) >= 3:
                        precios_recientes = df_tracking.tail(3)['price'].values
                        if precios_recientes[-1] < precios_recientes[0]:
                            st.success("📉 TENDENCIA BAJISTA - Buen momento para comprar")
                        elif precios_recientes[-1] > precios_recientes[0]:
                            st.warning("📈 TENDENCIA ALCISTA - Considera esperar")
                        else:
                            st.info("➡️ PRECIO LATERAL - Monitorear")
                    
                    # Señal basada en posición actual
                    if precio_actual <= precio_min * 1.05:
                        st.success("🟢 COMPRAR - Precio cerca del mínimo")
                    elif precio_actual >= precio_max * 0.95:
                        st.error("🔴 ESPERAR - Precio cerca del máximo")
                    else:
                        st.info("🟡 MONITOREAR - Precio en rango medio")
                
                # Histograma de distribución de precios
                st.subheader("📊 Distribución de Precios")
                fig_hist = px.histogram(
                    df_tracking,
                    x='price',
                    nbins=20,
                    title="Frecuencia de Precios",
                    labels={'price': 'Precio (USD)', 'count': 'Frecuencia'}
                )
                fig_hist.add_vline(x=precio_actual, line_dash="dash", line_color="red",
                                  annotation_text="Precio Actual")
                st.plotly_chart(fig_hist, use_container_width=True)
                
                # Tabla de datos detallados
                with st.expander("📋 Ver Datos Detallados"):
                    st.dataframe(
                        df_tracking[['search_timestamp', 'price', 'airline']].sort_values(
                            'search_timestamp', ascending=False
                        ),
                        use_container_width=True
                    )
            else:
                st.info("Se necesitan al menos 2 datos para generar gráficos. Continúa el tracking...")
        
        else:
            st.warning("No hay datos históricos aún. Iniciando tracking...")
        
        # Auto-refresh si está activo
        if st.session_state.get('monitoring_active', False) and frecuencia != "Manual":
            time.sleep(frecuencia_segundos.get(frecuencia, 60))
            
            # Realizar nueva consulta
            with st.spinner("Actualizando precios..."):
                try:
                    ofertas = amadeus.search_flights(
                        origin=flight_info['origin'],
                        destination=flight_info['destination'],
                        departure_date=flight_info['departure_date'],
                        return_date=flight_info.get('return_date'),
                        adults=flight_info['adults'],
                        max_results=5
                    )
                    
                    for oferta in ofertas:
                        db.insert_flight_offer(
                            origin=flight_info['origin'],
                            destination=flight_info['destination'],
                            departure_date=flight_info['departure_date'],
                            return_date=flight_info.get('return_date'),
                            price=oferta['price'],
                            currency=oferta['currency'],
                            airline=oferta.get('airline', 'Unknown'),
                            flight_data=oferta,
                            adults=flight_info['adults']
                        )
                    
                    st.session_state['last_update'] = datetime.now()
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Error actualizando: {str(e)}")
    
    else:
        st.info("👈 Selecciona un vuelo en la pestaña '🎯 Selector de Vuelos' para comenzar el tracking")

with tab2:
    st.header("Selector de Vuelos para Tracking")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_origin = st.text_input("Filtrar origen", value=origen, key="f_origin")
    with col2:
        filter_dest = st.text_input("Filtrar destino", value=destino, key="f_dest")
    with col3:
        order_by = st.selectbox("Ordenar por", ["Precio menor", "Precio mayor", "Fecha más cercana"])
    
    # Obtener vuelos disponibles
    df_available = db.get_available_flights(
        origin=filter_origin,
        destination=filter_dest,
        from_date=datetime.now().strftime("%Y-%m-%d")
    )
    
    if not df_available.empty:
        # Ordenar según preferencia
        if order_by == "Precio menor":
            df_available = df_available.sort_values('min_price')
        elif order_by == "Precio mayor":
            df_available = df_available.sort_values('min_price', ascending=False)
        else:
            df_available = df_available.sort_values('departure_date')
        
        st.success(f"📊 {len(df_available)} vuelos disponibles")
        
        # Mostrar tabla interactiva
        for idx, row in df_available.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
            
            with col1:
                st.write(f"**{row['origin']} → {row['destination']}**")
            with col2:
                st.write(f"📅 {row['departure_date']}")
            with col3:
                st.write(f"👥 {int(row['adults'])}")
            with col4:
                st.metric("Desde", f"${row['min_price']:.2f}")
            with col5:
                if st.button("📊 Trackear", key=f"track_{idx}"):
                    st.session_state['selected_flight'] = {
                        'origin': row['origin'],
                        'destination': row['destination'],
                        'departure_date': row['departure_date'],
                        'return_date': row.get('return_date'),
                        'adults': int(row['adults'])
                    }
                    st.success("✅ Vuelo seleccionado")
                    st.rerun()
            
            st.markdown("---")
    
    else:
        st.info("No hay vuelos disponibles. Usa el escáner en el sidebar para buscar vuelos.")

with tab3:
    st.header("Análisis Histórico Comparativo")
    
    # Selector de ruta para análisis
    col1, col2 = st.columns(2)
    with col1:
        hist_origin = st.text_input("Origen", origen, key="hist_origin")
    with col2:
        hist_dest = st.text_input("Destino", destino, key="hist_dest")
    
    dias_historico = st.slider("Ver últimos (días)", 7, 90, 30)
    
    df_hist = db.get_price_history(
        origin=hist_origin,
        destination=hist_dest,
        date_from=(datetime.now() - timedelta(days=dias_historico)).strftime("%Y-%m-%d")
    )
    
    if not df_hist.empty:
        # Gráfico comparativo por fecha de salida
        st.subheader("Comparación de Precios por Fecha de Salida")
        
        fig_comp = px.box(
            df_hist,
            x='departure_date',
            y='price',
            color='airline',
            title=f"Distribución de Precios - {hist_origin} → {hist_dest}"
        )
        st.plotly_chart(fig_comp, use_container_width=True)
        
        # Mejor día para volar
        st.subheader("🎯 Mejores Fechas para Volar")
        best_dates = df_hist.groupby('departure_date').agg({
            'price': ['min', 'mean', 'count']
        }).reset_index()
        best_dates.columns = ['Fecha', 'Precio Mínimo', 'Precio Promedio', 'Muestras']
        best_dates = best_dates.sort_values('Precio Mínimo').head(10)
        
        st.dataframe(best_dates, use_container_width=True)
    
    else:
        st.info("No hay datos históricos para esta ruta")

with tab4:
    st.header("💡 Recomendaciones Inteligentes")
    
    st.markdown("""
    ### Estrategias de Compra
    
    #### 🟢 Momento IDEAL para Comprar:
    - Precio actual ≤ 5% del mínimo histórico
    - Tendencia bajista en las últimas 3 mediciones
    - Volatilidad baja (< 5%)
    
    #### 🟡 Momento ACEPTABLE:
    - Precio entre mínimo y promedio histórico
    - Tendencia lateral
    - Volatilidad moderada (5-10%)
    
    #### 🔴 ESPERAR:
    - Precio actual ≥ 95% del máximo histórico
    - Tendencia alcista fuerte
    - Alta volatilidad (> 10%)
    
    ### Tips Profesionales:
    1. **Horarios**: Los precios suelen bajar los martes y miércoles
    2. **Anticipación**: Reserva 6-8 semanas antes para vuelos internacionales
    3. **Flexibilidad**: Volar entre semana es hasta 30% más barato
    4. **Alertas**: Configura tracking de 5 minutos para cambios bruscos
    5. **Paciencia**: No compres por impulso, deja que el sistema trabaje
    """)
    
    # Calculadora de ahorro potencial
    st.subheader("💰 Calculadora de Ahorro")
    
    col1, col2 = st.columns(2)
    with col1:
        precio_visto = st.number_input("Precio que viste ($)", min_value=0.0, value=500.0)
    with col2:
        dias_espera = st.number_input("Días a esperar", min_value=1, max_value=60, value=7)
    
    # Simulación simple
    ahorro_estimado = precio_visto * 0.15  # 15% de ahorro promedio
    st.success(f"🎯 Ahorro potencial esperando {dias_espera} días: **${ahorro_estimado:.2f}** (15% promedio)")
    st.info("💡 Usa el tracking automático para encontrar el momento óptimo")

# Footer con estado del sistema
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.session_state.get('last_update'):
        st.info(f"🕐 Última actualización: {st.session_state['last_update'].strftime('%H:%M:%S')}")

with col2:
    if st.session_state.get('selected_flight'):
        flight = st.session_state['selected_flight']
        st.success(f"✈️ Tracking: {flight['origin']}→{flight['destination']}")

with col3:
    status = "🟢 ACTIVO" if st.session_state.get('monitoring_active') else "⚪ INACTIVO"
    st.write(f"Estado: {status}")
