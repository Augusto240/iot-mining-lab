import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Galeria - Indicadores de Negocio",
    page_icon="\U0001f3ed",
    layout="wide"
)

st.title("Indicadores de Negocio - Qualidade do Ar")
st.subheader("Galeria Subterranea de Mineracao")

CRATE_HOST = "localhost"
CRATE_PORT = 4200

@st.cache_resource
def get_connection():
    return create_engine(f"crate://{CRATE_HOST}:{CRATE_PORT}/")

def load_data(hours=24):
    engine = get_connection()
    cutoff_ms = int((datetime.utcnow() - timedelta(hours=hours)).timestamp() * 1000)
    query = text("""
        SELECT time_index as ts, ch4, co, co2, temperatura, umidade, ventilador, status
        FROM doc.etairqualitysensor
        WHERE time_index > :cutoff
        ORDER BY time_index DESC
    """)
    try:
        df = pd.read_sql(query, engine, params=[cutoff_ms])
        if not df.empty and df['ts'].dtype in ['int64', 'float64']:
            df['ts'] = pd.to_datetime(df['ts'], unit='ms')
        return df
    except Exception as e:
        st.warning(f"Erro ao conectar ao CrateDB: {e}")
        return pd.DataFrame()

def calculate_indicators(df):
    if df.empty:
        return None

    total = len(df)
    alert = len(df[df['status'] == 'alerta'])
    atencao = len(df[df['status'] == 'atencao'])
    normal = len(df[df['status'] == 'normal'])

    alert_pct = (alert / total * 100) if total > 0 else 0
    atencao_pct = (atencao / total * 100) if total > 0 else 0
    compliance_pct = 100 - alert_pct

    fan_on = len(df[df['ventilador'] == True]) if 'ventilador' in df.columns else 0
    fan_hours = fan_on * 2 / 3600
    energy_cost = fan_hours * 15.0

    return {
        'total': total,
        'alert_pct': alert_pct,
        'atencao_pct': atencao_pct,
        'compliance_pct': compliance_pct,
        'fan_hours': fan_hours,
        'energy_cost': energy_cost,
        'incidents': alert,
        'normal_pct': (normal / total * 100) if total > 0 else 0
    }

hours = st.selectbox("Periodo de analise:", [1, 6, 12, 24, 48], index=2)
df = load_data(hours)
ind = calculate_indicators(df)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Registros", f"{ind['total']}" if ind else "0")
with col2:
    st.metric("Conformidade NR-33", f"{ind['compliance_pct']:.1f}%" if ind else "N/A")
with col3:
    st.metric("Incidentes", f"{ind['incidents']}" if ind else "0")
with col4:
    st.metric("Custo Energia Ventilacao", f"R$ {ind['energy_cost']:.2f}" if ind else "R$ 0,00")

st.markdown("---")

if ind:
    tab1, tab2, tab3 = st.tabs(["Indicadores", "Historico", "Arquitetura"])

    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Conformidade NR-33")
            comp = ind['compliance_pct']
            if comp >= 95:
                st.success(f"Conforme - {comp:.1f}% dentro dos limites")
            elif comp >= 80:
                st.warning(f"Atencao - {comp:.1f}% dentro dos limites")
            else:
                st.error(f"Nao conforme - {comp:.1f}% dentro dos limites")
            st.progress(comp / 100)

        with c2:
            st.subheader("Impacto Economico")
            st.metric("Custo Energia", f"R$ {ind['energy_cost']:.2f}")
            st.metric("Horas Ventilador", f"{ind['fan_hours']:.2f}h")
            st.caption("Custo estimado: R$ 15,00/hora")

        st.markdown("---")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Alertas", ind['incidents'])
            st.caption("CH4 > 1% ou CO > 25ppm")
        with c2:
            st.metric("Atencao", f"{ind['atencao_pct']:.1f}%")
            st.caption("CH4 0.5-1% ou CO 15-25ppm")
        with c3:
            st.metric("Normal", f"{ind['normal_pct']:.1f}%")
            st.caption("Dentro dos limites seguros")

    with tab2:
        st.subheader("Historico de Qualidade do Ar")
        if not df.empty:
            chart_df = df.sort_values('ts').set_index('ts')
            st.line_chart(chart_df[['ch4', 'co']])
            st.subheader("Temperatura e Umidade")
            st.line_chart(chart_df[['temperatura', 'umidade']])
            st.subheader("Dados Recentes")
            st.dataframe(df.head(20))
        else:
            st.info("Sem dados disponiveis.")

    with tab3:
        st.subheader("Arquitetura do Sistema")
        st.code("""
Publisher (simulacao)
    |  MQTT (Mosquitto)
    v
Node-RED (regras de negocio + dashboard)
    |  HTTP PATCH (NGSI v2)
    v
Mock Orion (context broker)
    |  HTTP POST (notificacoes)
    v
QuantumLeap (série temporal)
    |
    v
CrateDB (armazenamento)
    |
    v
Streamlit (indicadores de negocio)
        """)
        st.write("**Regra de negocio:** CH4 > 1%% ou CO > 25ppm → Ativar ventilador + alerta")
        st.write("**Pergunta que a visualizacao responde:** Qual o impacto operacional e economico da qualidade do ar?")

else:
    st.info("Aguardando dados do sensor...")

st.sidebar.header("Sobre")
st.sidebar.info("""
**Gemeo Digital - Mineracao**

Monitoramento de qualidade do ar em galeria subterranea.

**Pergunta:** Qual o impacto operacional e economico?

**Componentes:**
- Publisher (simulacao)
- MQTT (Mosquitto)
- Node-RED (regras)
- Mock Orion (gemeo digital)
- QuantumLeap (serie temporal)
- CrateDB (armazenamento)
- Streamlit (indicadores)
""")
