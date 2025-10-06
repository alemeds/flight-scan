# 📈 Flight Trading Monitor - Guía de Uso

## 🎯 Concepto

Flight Trading Monitor transforma el análisis de tarifas aéreas en una experiencia similar al trading de acciones, permitiéndote:

- **Trackear vuelos específicos** en tiempo real
- **Analizar tendencias** como si fueran gráficos de bolsa
- **Recibir señales de compra** basadas en análisis técnico
- **Monitorear múltiples fechas** simultáneamente
- **Tomar decisiones informadas** sobre cuándo comprar

---

## 🚀 Cómo Funciona

### 1️⃣ Fase de Escaneo

**Objetivo**: Encontrar todas las fechas disponibles para tu ruta

1. **Configura tu búsqueda** en el sidebar:
   - Origen y destino (códigos IATA)
   - Rango de fechas a analizar (ej: del 15 de nov al 15 de dic)
   - Tipo de vuelo (ida y vuelta o solo ida)
   - Número de pasajeros

2. **Haz clic en "🔍 Escanear Fechas Disponibles"**
   - El sistema consultará la API de Amadeus día por día
   - Guardará todos los precios encontrados en la base de datos
   - Te mostrará cuántos vuelos encontró

**Resultado**: Tendrás una base de datos con precios de múltiples fechas de salida

---

### 2️⃣ Fase de Selección

**Objetivo**: Elegir el vuelo específico que quieres trackear

1. Ve a la pestaña **"🎯 Selector de Vuelos"**

2. Verás una lista de todos los vuelos disponibles con:
   - Ruta completa
   - Fecha de salida
   - Número de pasajeros
   - Precio mínimo encontrado
   - Botón "📊 Trackear"

3. **Filtra y ordena**:
   - Por precio (menor a mayor o viceversa)
   - Por fecha más cercana
   - Por origen/destino específico

4. **Selecciona un vuelo** haciendo clic en "📊 Trackear"

**Resultado**: El vuelo queda seleccionado para monitoreo en tiempo real

---

### 3️⃣ Fase de Tracking

**Objetivo**: Monitorear el precio del vuelo seleccionado automáticamente

1. Con el vuelo seleccionado, configura la **frecuencia de actualización**:
   - 30 segundos (para seguimiento intensivo)
   - 1 minuto
   - 5 minutos (recomendado)
   - 15 minutos
   - 30 minutos
   - 1 hora
   - 2 horas

2. Define la **duración del tracking**:
   - Cuántas horas quieres que el sistema siga monitoreando
   - Puede ser desde 1 hora hasta 72 horas (3 días)

3. **Haz clic en "▶️ Iniciar"**

**Resultado**: El sistema comenzará a consultar automáticamente el precio del vuelo

---

## 📊 Interpretación del Trading Monitor

### Métricas Principales

```
┌─────────────────────────────────────────────────────────┐
│ Precio Actual │ Precio Inicial │ Mínimo │ Máximo │ Promedio │
│   $850.00     │    $900.00     │ $820   │  $950  │  $880    │
│   -5.56% ↓    │                │        │        │          │
└─────────────────────────────────────────────────────────┘
```

- **Precio Actual**: Último precio consultado
- **Delta (%)**: Variación desde el inicio del tracking
  - ↓ Verde: Precio bajando (bueno para comprar)
  - ↑ Rojo: Precio subiendo (considera esperar)
- **Precio Inicial**: Primer precio cuando iniciaste el tracking
- **Mínimo/Máximo**: Rango de precios observados
- **Promedio**: Punto medio de referencia

---

### Gráfico de Evolución

El gráfico muestra:

1. **Línea azul (área)**: Evolución del precio en el tiempo
2. **Línea roja punteada**: Media móvil (promedio de últimos 5 puntos)
3. **Línea verde horizontal**: Precio mínimo histórico (soporte)
4. **Línea roja horizontal**: Precio máximo histórico (resistencia)
5. **Línea gris horizontal**: Precio promedio

#### ¿Cómo interpretarlo?

```
ZONA ROJA (cerca del máximo)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  $950 (Máximo)
                    ↑
              NO COMPRES AÚN
                    
ZONA AMARILLA (promedio)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  $880 (Promedio)
              MONITOREA
                    
ZONA VERDE (cerca del mínimo)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━  $820 (Mínimo)
                    ↓
              ¡COMPRA AHORA!
```

---

### Indicadores Técnicos

#### 📉 Volatilidad

- **Desviación Estándar**: Cuánto varían los precios
  - Baja (< $30): Precio estable
  - Media ($30-$60): Variaciones normales
  - Alta (> $60): Mucha fluctuación

- **Coeficiente de Variación**:
  - < 5%: ✅ Precio muy estable
  - 5-10%: ⚠️ Volatilidad moderada
  - > 10%: 🔴 Alta volatilidad (riesgoso)

#### 🎯 Señales de Trading

**Tendencia**:
- 📉 **BAJISTA**: Los últimos 3 precios están descendiendo → **COMPRA**
- 📈 **ALCISTA**: Los últimos 3 precios están subiendo → **ESPERA**
- ➡️ **LATERAL**: Precio estable → **MONITOREA**

**Posición Actual**:
- 🟢 **COMPRAR**: Precio ≤ Mínimo + 5%
- 🟡 **MONITOREAR**: Precio entre mínimo y máximo
- 🔴 **ESPERAR**: Precio ≥ Máximo - 5%

---

## 💡 Estrategias Recomendadas

### Estrategia 1: "Day Trader" (Corto Plazo)

**Configuración**:
- Frecuencia: 30 segundos - 1 minuto
- Duración: 2-4 horas
- Objetivo: Capturar caídas repentinas

**Cuándo usar**: 
- Cuando necesitas comprar HOY
- Para rutas muy volátiles
- Durante promociones flash

**Acción**:
- Monitorea constantemente
- Compra cuando veas 🟢 COMPRAR + Tendencia BAJISTA
- No esperes más de 10 minutos si encuentras buen precio

---

### Estrategia 2: "Swing Trader" (Mediano Plazo)

**Configuración**:
- Frecuencia: 5-15 minutos
- Duración: 24-48 horas
- Objetivo: Encontrar el mejor precio en 1-2 días

**Cuándo usar**:
- Vuelo en 2-4 semanas
- Puedes esperar unos días
- Quieres optimizar precio

**Acción**:
- Deja el tracking corriendo
- Revisa 3-4 veces al día
- Compra cuando precio esté en ZONA VERDE
- Si volatilidad es alta, espera a que se estabilice

---

### Estrategia 3: "Position Trader" (Largo Plazo)

**Configuración**:
- Frecuencia: 1-2 horas
- Duración: 48-72 horas
- Objetivo: Análisis profundo de tendencias

**Cuándo usar**:
- Vuelo en 4+ semanas
- Flexibilidad total de fechas
- Buscas el mejor precio posible

**Acción**:
- Trackea múltiples fechas simultáneamente
- Analiza patrones semanales
- Compra en el día históricamente más barato
- No tengas prisa, deja que la data trabaje

---

## 🎓 Casos de Uso Reales

### Caso 1: Viaje de Negocios Urgente

**Situación**: Necesitas volar a Miami en 1 semana

```
1. Escanea fechas: Del día 7 al día 14
2. Selecciona: Día 10 (más barato en el escaneo)
3. Tracking: 5 minutos por 12 horas
4. Monitorea: Revisa cada 2 horas
5. Compra: Cuando veas precio < $750 o tendencia bajista fuerte
```

---

### Caso 2: Vacaciones Familiares Planificadas

**Situación**: Viaje a Europa en 2 meses, 4 personas

```
1. Escanea fechas: Rango de 30 días
2. Compara: Identifica la semana más barata
3. Selecciona: 3-4 fechas de esa semana
4. Tracking múltiple: 1 hora por 7 días cada una
5. Analiza: Compara evolución entre fechas
6. Compra: La que tenga mejor combinación precio/tendencia
```

---

### Caso 3: Viajero Flexible

**Situación**: Quieres viajar "algún día" al Caribe

```
1. Escanea: Todo el próximo trimestre
2. Identifica: Top 10 fechas más baratas
3. Tracking: 2 horas por 3 días en cada una
4. Dashboard: Compara en "Análisis Histórico"
5. Espera: Hasta ver oportunidad excepcional
6. Compra: Cuando encuentres 20%+ por debajo del promedio
```

---

## 📈 Interpretando el Análisis Histórico

En la pestaña **"📈 Análisis Histórico"**:

### Box Plot (Cajas y Bigotes)

```
        │
   Max  ●━━━━━┓
        │     ┃  <- Outliers (precios anormales)
   Q3   ├─────┨
        │█████┃  <- 50% de los precios están aquí
  Median├─────┨
        │█████┃
   Q1   ├─────┨
        │     ┃
   Min  ●━━━━━┛
        │
```

**Qué buscar**:
- Cajas pequeñas = Precios estables
- Cajas grandes = Mucha variación
- Medianas bajas = Fechas con buenos precios
- Outliers arriba = Evitar esos días

---

### Mejores Fechas

La tabla muestra:
- **Precio Mínimo**: El mejor precio encontrado ese día
- **Precio Promedio**: Precio típico
- **Muestras**: Cuántas veces se consultó

**Tip**: Fechas con muchas muestras son más confiables

---

## 🎯 Calculadora de Ahorro

En la pestaña **"💡 Recomendaciones"**:

**Ejemplo**:
```
Precio visto: $1000
Días a esperar: 7
Ahorro estimado: $150 (15%)
```

Basado en estadísticas históricas:
- Esperar 1 semana: ~15% de ahorro promedio
- Esperar 2 semanas: ~20-25% de ahorro
- Comprar con 1 día: +30% más caro

---

## ⚠️ Advertencias Importantes

### No Garantías

❌ **El sistema NO garantiza que**:
- Los precios siempre bajen
- Encontrarás el precio absoluto mínimo
- Los vuelos estarán disponibles cuando decidas comprar

✅ **El sistema SÍ te ayuda a**:
- Tomar decisiones informadas
- Identificar tendencias
- Comprar con más confianza
- Evitar compras impulsivas caras

---

### Limitaciones Técnicas

1. **API de Amadeus (Test)**:
   - 10,000 requests/mes
   - 10 requests/segundo
   - Datos pueden variar vs. precio real

2. **Streamlit Cloud**:
   - Puede entrar en "sleep" tras inactividad
   - Tracking se detiene si cierras el navegador
   - Usar GitHub Actions para tracking 24/7

3. **Disponibilidad**:
   - Los asientos pueden agotarse
   - Precios pueden cambiar drásticamente
   - Promociones pueden ser limitadas

---

## 🔥 Tips de Experto

### Timing Óptimo

**Mejor momento para comprar** (estadísticamente):
- **Día**: Martes o Miércoles
- **Hora**: Entre 15:00 y 18:00 (hora local)
- **Anticipación**: 
  - Doméstico: 3-4 semanas
  - Internacional: 6-8 semanas
  - Intercontinental: 10-12 semanas

### Configuración Ideal por Ruta

**Rutas Cortas (< 3 horas)**:
- Tracking: 15-30 minutos
- Duración: 24 horas
- Volatilidad: Media

**Rutas Medias (3-8 horas)**:
- Tracking: 30 minutos - 1 hora
- Duración: 48 horas
- Volatilidad: Baja

**Rutas Largas (8+ horas)**:
- Tracking: 1-2 horas
- Duración: 72 horas
- Volatilidad: Alta

---

## 📱 Uso con GitHub Actions

Para tracking 24/7 sin mantener el navegador abierto:

1. Configura GitHub Actions (ver README)
2. El script consultará automáticamente cada X horas
3. Los datos se guardan en PostgreSQL
4. Abre el dashboard cuando quieras ver resultados
5. Todos los datos históricos estarán disponibles

---

## ❓ FAQ

**P: ¿Cuánto tiempo debo trackear un vuelo?**  
R: Mínimo 12 horas para ver tendencias. Ideal: 24-48 horas.

**P: ¿Puedo trackear varios vuelos a la vez?**  
R: Sí, pero en la interfaz seleccionas uno a la vez. Todos quedan guardados.

**P: ¿Los precios incluyen impuestos?**  
R: Sí, Amadeus devuelve precio total.

**P: ¿Qué hago si el precio sube mucho?**  
R: Considera otras fechas o aerolíneas. Revisa el "Análisis Histórico".

**P: ¿Cuándo es MUY urgente comprar?**  
R: Cuando veas: Precio mínimo + Tendencia bajista + Alta volatilidad

---

## 🏆 Resumen de Acciones Rápidas

### Para Usuarios Nuevos

1. ⚙️ Configura origen, destino y fechas
2. 🔍 Escanea fechas disponibles
3. 🎯 Selecciona un vuelo
4. ▶️ Inicia tracking (5-15 min)
5. 📊 Espera al menos 2-3 horas
6. 💰 Compra cuando veas señal VERDE

### Para Usuarios Avanzados

1. 📈 Escanea múltiples semanas
2. 📊 Compara en "Análisis Histórico"
3. 🎯 Selecciona top 3 fechas
4. 🔄 Tracking paralelo con GitHub Actions
5. 📉 Analiza volatilidad y tendencias
6. 🎯 Ejecuta cuando convergencia sea óptima

---

**¡Feliz Trading de Vuelos!** ✈️📈

_Recuerda: La paciencia y el análisis son tus mejores aliados para encontrar las mejores tarifas._
