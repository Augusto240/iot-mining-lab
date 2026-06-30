import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(
    page_title="Galeria - Indicadores de Negocio",
    page_icon="\U0001f3ed",
    layout="wide"
)

st.title("Indicadores de Negocio - Qualidade do Ar")
st.subheader("Galeria Subterranea de Mineracao")

CRATE_URL = "http://localhost:4200/_sql"

def query_crate(stmt, params=None):
    body = {"stmt": stmt}
    if params:
        body["args"] = params
    r = requests.post(CRATE_URL, json=body, timeout=10)
    data = r.json()
    return pd.DataFrame(data["rows"], columns=data["cols"])

def load_data(hours=24):
    cutoff_ms = int((datetime.utcnow() - timedelta(hours=hours)).timestamp() * 1000)
    try:
        df = query_crate(
            "SELECT time_index as ts, ch4, co, co2, temperatura, umidade, ventilador, status "
            "FROM doc.etairqualitysensor WHERE time_index > $1 ORDER BY time_index DESC",
            [cutoff_ms]
        )
        if not df.empty:
            df["ts"] = pd.to_datetime(df["ts"], unit="ms")
        return df
    except Exception as e:
        st.warning(f"Erro ao conectar ao CrateDB: {e}")
        return pd.DataFrame()

def calculate_indicators(df):
    if df.empty:
        return None
    total = len(df)
    alert = len(df[df["status"] == "alerta"])
    atencao = len(df[df["status"] == "atencao"])
    normal = len(df[df["status"] == "normal"])
    fan_on = len(df[df["ventilador"] == True])
    fan_hours = fan_on * 2 / 3600
    return {
        "total": total,
        "alert_pct": alert / total * 100,
        "atencao_pct": atencao / total * 100,
        "compliance_pct": 100 - (alert / total * 100),
        "fan_hours": fan_hours,
        "energy_cost": fan_hours * 15.0,
        "incidents": alert,
        "normal_pct": normal / total * 100,
    }

hours = st.selectbox("Periodo de analise:", [1, 6, 12, 24, 48], index=2)
df = load_data(hours)
ind = calculate_indicators(df)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Registros", f"{ind['total']:,}" if ind else "0")
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
            comp = ind["compliance_pct"]
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
            st.metric("Alertas", ind["incidents"])
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
            chart_df = df.sort_values("ts").set_index("ts")
            st.line_chart(chart_df[["ch4", "co"]])
            st.subheader("Temperatura e Umidade")
            st.line_chart(chart_df[["temperatura", "umidade"]])
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
QuantumLeap (serie temporal)
    |
    v
CrateDB (armazenamento)
    |
    v
Streamlit (indicadores de negocio)
        """)
        st.write("**Regra de negocio:** CH4 > 1% ou CO > 25ppm -> Ativar ventilador + alerta")
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
