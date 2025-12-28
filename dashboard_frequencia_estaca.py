import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

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
    st.error("O CSV não possui a coluna 'Alas'. Verifique o script de processamento.")
    st.stop()

df = df.set_index("Alas")

for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

# ===========================
# FUNÇÃO AUXILIAR PARA ORDENAR SEMANAS
# ===========================

def sort_week_cols(cols):
    month_map = {
        "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
        "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12
    }

    def key(label):
        parts = str(label).split()
        if len(parts) != 2:
            return (99, 99, label)
        dia_txt, mes_txt = parts
        try:
            dia = int(dia_txt)
        except ValueError:
            dia = 99
        mes = month_map.get(mes_txt.lower(), 99)
        return (mes, dia, label)

    return sorted(cols, key=key)

weeks = sort_week_cols(df.columns.tolist())
df = df[weeks]

if "TOTAL" not in df.index:
    df.loc["TOTAL"] = df.sum(axis=0)

df_ala = df.drop("TOTAL")

st.markdown("#### Prévia dos dados carregados do CSV")
st.dataframe(df)

# ===========================
# SIDEBAR - CONTROLES
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

start_idx = weeks.index(start_week)
end_idx = weeks.index(end_week) + 1
weeks_sel = weeks[start_idx:end_idx]

df_ala_filt = df_ala.loc[alas_sel, weeks_sel]
df_total_filt = df.loc["TOTAL", weeks_sel]

st.sidebar.markdown("---")
st.sidebar.markdown("ℹ️ Dica: use os filtros para investigar quedas, picos e a participação de cada ala.")

# ===========================
# TIPO DE DOMINGO (QUÓRUM x ESCOLA DOMINICAL)
# ===========================

LAST_QUORUM_WEEK = "28 dez"

week_type = {}
is_quorum = True

for week in reversed(weeks):
    week_type[week] = "Quórum & Classe" if is_quorum else "Escola Dominical"
    is_quorum = not is_quorum

st.markdown("### 📅 Tipo de Domingo")

cols = st.columns(len(weeks_sel))
for i, week in enumerate(weeks_sel):
    tipo = week_type.get(week, "")
    if tipo == "Quórum & Classe":
        cols[i].success(f"{week}\nQuórum & Classe")
    else:
        cols[i].info(f"{week}\nEscola Dominical")

# ===========================
# MÉTRICAS GERAIS
# ===========================

st.markdown("---")
st.subheader("📌 Métricas gerais")

col1, col2, col3 = st.columns(3)

media_geral = df_ala_filt.values.mean()
col1.metric("Média de frequência (alas filtradas)", f"{media_geral:.1f}")

max_total = df_total_filt.max()
max_week = df_total_filt.idxmax()
col2.metric("Maior frequência total da estaca", f"{int(max_total)}", max_week)

min_total = df_total_filt.min()
min_week = df_total_filt.idxmin()
col3.metric("Menor frequência total da estaca", f"{int(min_total)}", min_week)

st.markdown("---")

# ===========================
# LINHA - FREQUÊNCIA POR ALA
# ===========================

st.subheader("📈 Frequência por Ala (Linhas)")

fig1, ax1 = plt.subplots(figsize=(8, 4))
for ala in df_ala_filt.index:
    ax1.plot(weeks_sel, df_ala_filt.loc[ala], marker="o", label=ala)

ax1.set_xlabel("Semana")
ax1.set_ylabel("Frequência")
ax1.set_title(
    "Frequência por Ala ao Longo das Semanas\n"
    "Verde = Quórum & Classe | Azul = Escola Dominical"
)
ax1.tick_params(axis="x", rotation=45)
ax1.legend()
fig1.tight_layout()
st.pyplot(fig1)

# ===========================
# BARRAS EMPILHADAS - TOTAL
# ===========================

st.subheader("📚 Frequência Total Empilhada por Semana")

fig2, ax2 = plt.subplots(figsize=(8, 4))
bottom = np.zeros(len(weeks_sel))
for ala in df_ala.index:
    ax2.bar(weeks_sel, df_ala.loc[ala, weeks_sel], bottom=bottom, label=ala)
    bottom += df_ala.loc[ala, weeks_sel].values

ax2.set_xlabel("Semana")
ax2.set_ylabel("Frequência")
ax2.set_title("Frequência Total Empilhada por Semana (Todas as Alas)")
ax2.tick_params(axis="x", rotation=45)
ax2.legend()
fig2.tight_layout()
st.pyplot(fig2)

# ===========================
# MAPA DE CALOR
# ===========================

st.subheader("🔥 Mapa de Calor da Frequência por Ala")

fig3, ax3 = plt.subplots(figsize=(8, 4))
im = ax3.imshow(df_ala.loc[:, weeks_sel].values, aspect="auto")
ax3.set_yticks(range(len(df_ala.index)))
ax3.set_yticklabels(df_ala.index)
ax3.set_xticks(range(len(weeks_sel)))
ax3.set_xticklabels(weeks_sel, rotation=45)
ax3.set_title("Mapa de Calor da Frequência")
cbar = fig3.colorbar(im, ax=ax3)
cbar.set_label("Frequência")
fig3.tight_layout()
st.pyplot(fig3)

# ===========================
# BOXPLOT + ESTATÍSTICAS
# ===========================

st.subheader("📦 Distribuição de Frequência por Ala")

fig4, ax4 = plt.subplots(figsize=(8, 4))
data_box = df_ala_filt.T.values
ax4.boxplot(data_box, labels=df_ala_filt.index)
ax4.set_ylabel("Frequência")
ax4.set_title("Distribuição de Frequência (Boxplot) - Alas Filtradas")
ax4.tick_params(axis="x", rotation=45)
fig4.tight_layout()
st.pyplot(fig4)

st.markdown("**Estatísticas por ala (alas filtradas):**")
stats = df_ala_filt.T.describe().T[["mean", "std", "min", "max"]]
stats = stats.rename(columns={
    "mean": "Média",
    "std": "Desvio Padrão",
    "min": "Mínimo",
    "max": "Máximo"
})
st.dataframe(stats.style.format("{:.1f}"))

# ===========================
# PARTICIPAÇÃO PERCENTUAL
# ===========================

st.subheader("📌 Participação Percentual no Total da Estaca")

df_pct = df_ala.loc[:, weeks_sel].div(df.loc["TOTAL", weeks_sel], axis=1) * 100

fig5, ax5 = plt.subplots(figsize=(8, 4))
for ala in df_pct.index:
    ax5.plot(weeks_sel, df_pct.loc[ala], marker="o", label=ala)

ax5.set_xlabel("Semana")
ax5.set_ylabel("% do total da estaca")
ax5.set_title("Participação Percentual de Cada Ala no Total Semanal")
ax5.tick_params(axis="x", rotation=45)
ax5.legend()
fig5.tight_layout()
st.pyplot(fig5)

st.markdown("---")
st.markdown(
    "💡 **Como usar este dashboard:** "
    "Use os filtros na barra lateral para investigar alas específicas, períodos de queda ou aumento, "
    "e compare a participação relativa de cada ala no total da estaca."
)
