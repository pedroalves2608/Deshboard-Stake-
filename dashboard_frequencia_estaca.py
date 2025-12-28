import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

# ===========================
# CONFIGURAÇÃO BÁSICA
# ===========================

st.set_page_config(
    page_title="Dashboard - Frequência Estaca Florianópolis",
    page_icon="⛪",
    layout="wide"
)

st.title("📊 Dashboard de Frequência - Estaca Florianópolis")

st.markdown(
    "Este painel permite explorar a frequência das alas ao longo das semanas, "
    "identificar padrões, outliers e a participação de cada ala no total da estaca."
)

# ===========================
# CARREGAR DADOS DO CSV
# ===========================

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "data" / "output" / "frequencia_estaca_2025.csv"

if not CSV_PATH.exists():
    st.error(
        f"Arquivo de dados não encontrado: {CSV_PATH}\n\n"
        "Rode antes o script `processar_pdfs.py` para gerar o CSV."
    )
    st.stop()

df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

if "Alas" not in df.columns:
    st.error("O CSV não possui a coluna 'Alas'.")
    st.stop()

df = df.set_index("Alas")

for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

# ===========================
# ORDENAR SEMANAS
# ===========================

def sort_week_cols(cols):
    month_map = {
        "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
        "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12
    }

    def key(label):
        parts = str(label).split()
        if len(parts) != 2:
            return (99, 99)
        dia, mes = parts
        return (month_map.get(mes.lower(), 99), int(dia))

    return sorted(cols, key=key)

weeks = sort_week_cols(df.columns.tolist())
df = df[weeks]

if "TOTAL" not in df.index:
    df.loc["TOTAL"] = df.sum(axis=0)

df_ala = df.drop("TOTAL")

# ===========================
# SIDEBAR
# ===========================

st.sidebar.header("⚙️ Filtros")

alas_sel = st.sidebar.multiselect(
    "Selecione as alas",
    options=df_ala.index.tolist(),
    default=df_ala.index.tolist()
)

start_week, end_week = st.sidebar.select_slider(
    "Intervalo de semanas",
    options=weeks,
    value=(weeks[0], weeks[-1])
)

weeks_sel = weeks[weeks.index(start_week): weeks.index(end_week) + 1]

df_ala_filt = df_ala.loc[alas_sel, weeks_sel]
df_total_filt = df.loc["TOTAL", weeks_sel]

# ===========================
# TIPO DE DOMINGO
# ===========================

week_type = {}
is_quorum = True  # 28 dez

for week in reversed(weeks):
    week_type[week] = "Quórum & Classe" if is_quorum else "Escola Dominical"
    is_quorum = not is_quorum

st.markdown("### 📅 Tipo de Domingo")
cols = st.columns(len(weeks_sel))
for i, w in enumerate(weeks_sel):
    if week_type[w] == "Quórum & Classe":
        cols[i].success(f"{w}\nQuórum & Classe")
    else:
        cols[i].info(f"{w}\nEscola Dominical")

# ===========================
# MÉTRICAS
# ===========================

st.markdown("---")
st.subheader("📌 Métricas gerais")

c1, c2, c3 = st.columns(3)

c1.metric("Média geral", f"{df_ala_filt.values.mean():.1f}")
c2.metric("Maior total", int(df_total_filt.max()), df_total_filt.idxmax())
c3.metric("Menor total", int(df_total_filt.min()), df_total_filt.idxmin())

# ===========================
# LINHAS (PLOTLY)
# ===========================

st.markdown("---")
st.subheader("📈 Frequência por Ala")

df_long = df_ala_filt.reset_index().melt(
    id_vars="Alas",
    var_name="Semana",
    value_name="Frequência"
)

fig_line = px.line(
    df_long,
    x="Semana",
    y="Frequência",
    color="Alas",
    markers=True,
    title="Frequência por Ala ao Longo das Semanas",
)

fig_line.update_layout(hovermode="x unified")
st.plotly_chart(fig_line, use_container_width=True)

# ===========================
# BARRAS EMPILHADAS
# ===========================

st.markdown("---")
st.subheader("📚 Frequência Total Empilhada")

fig_bar = go.Figure()

for ala in df_ala_filt.index:
    fig_bar.add_bar(
        name=ala,
        x=weeks_sel,
        y=df_ala_filt.loc[ala]
    )

fig_bar.update_layout(
    barmode="stack",
    title="Frequência Total Empilhada por Semana",
    hovermode="x unified"
)

st.plotly_chart(fig_bar, use_container_width=True)

# ===========================
# MAPA DE CALOR
# ===========================

st.markdown("---")
st.subheader("🔥 Mapa de Calor da Frequência")

fig_heat = px.imshow(
    df_ala_filt.values,
    labels=dict(x="Semana", y="Ala", color="Frequência"),
    x=weeks_sel,
    y=df_ala_filt.index,
    aspect="auto",
    title="Mapa de Calor da Frequência por Ala"
)

st.plotly_chart(fig_heat, use_container_width=True)

# ===========================
# BOXPLOT
# ===========================

st.markdown("---")
st.subheader("📦 Distribuição de Frequência")

fig_box = px.box(
    df_long,
    x="Alas",
    y="Frequência",
    title="Distribuição de Frequência por Ala"
)

st.plotly_chart(fig_box, use_container_width=True)

# ===========================
# PARTICIPAÇÃO PERCENTUAL
# ===========================

st.markdown("---")
st.subheader("📌 Participação Percentual no Total")

df_pct = df_ala_filt.div(df_total_filt, axis=1) * 100
df_pct_long = df_pct.reset_index().melt(
    id_vars="Alas",
    var_name="Semana",
    value_name="% do total"
)

fig_pct = px.line(
    df_pct_long,
    x="Semana",
    y="% do total",
    color="Alas",
    markers=True,
    title="Participação Percentual no Total da Estaca"
)

fig_pct.update_layout(hovermode="x unified")
st.plotly_chart(fig_pct, use_container_width=True)

st.markdown("---")
st.markdown(
    "💡 Use os filtros para comparar alas, identificar padrões e entender o impacto "
    "do tipo de domingo (Quórum x Escola Dominical) na frequência."
)
