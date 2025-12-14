import pdfplumber
from pathlib import Path
import pandas as pd
import re

# ===========================
# CONFIGURAÇÃO DE CAMINHOS
# ===========================

BASE_DIR = Path(__file__).resolve().parent
PDF_DIR = BASE_DIR / "data" / "pdf_raw" / "2025"   # ajuste o ano se precisar
OUTPUT_DIR = BASE_DIR / "data" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
CSV_PATH = OUTPUT_DIR / "frequencia_estaca_2025.csv"


def sort_week_cols(cols):
    """Ordena colunas '9 nov', '16 nov', '7 dez' em ordem cronológica."""
    month_map = {
        "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
        "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12
    }
    def key(label):
        parts = label.split()
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


def extrair_nome_ala(page):
    """
    Lê a primeira linha do PDF e extrai o nome da ala/ramo.
    Ex: 'Frequência à classe e ao quórum Rio Vermelho Branch (2281716)'
         -> 'Rio Vermelho'
    """
    text = page.extract_text()
    if not text:
        return None
    linha0 = text.splitlines()[0]
    if "quórum" in linha0:
        parte = linha0.split("quórum", 1)[1].strip()
    else:
        parte = linha0

    # remove coisas entre parênteses, tipo (2281716)
    parte = re.sub(r"\(.*?\)", "", parte).strip()

    # remove sufixos tipo Branch, Ward, Ramo, Ala, se existirem
    for suf in ["Branch", "Ward", "Ramo", "Ala"]:
        if parte.endswith(suf):
            parte = parte[: -len(suf)].strip()
    return parte or None


def get_date_columns_for_page(page):
    """
    Acha as colunas de datas na página, retornando um dict:
    {'9 nov': x_center, '16 nov': x_center, ...}
    """
    words = page.extract_words()
    nome_words = [w for w in words if w["text"] == "Nome"]
    if not nome_words:
        return {}

    header_top = nome_words[0]["top"]
    header_words = [w for w in words if abs(w["top"] - header_top) < 1.0]
    header_words_sorted = sorted(header_words, key=lambda w: w["x0"])

    cols = {}
    i = 0
    while i < len(header_words_sorted):
        w = header_words_sorted[i]
        # datas vêm como "9 nov", "16 nov", etc. em duas palavras
        if w["text"].isdigit():
            if i + 1 < len(header_words_sorted):
                w2 = header_words_sorted[i + 1]
                label = f"{w['text']} {w2['text']}"  # '9 nov', '7 dez'
                x_center = (w["x0"] + w2["x1"]) / 2
                cols[label] = x_center
                i += 2
                continue
        i += 1
    return cols


def agrupar_linhas_por_y(circulos, tolerancia=3):
    """
    Recebe uma lista de círculos [{'cx':..., 'cy':..., 'data':...}, ...]
    e agrupa por linha (pessoas) com base no Y (cy).
    Retorna lista de grupos; cada grupo é uma lista de círculos.
    """
    if not circulos:
        return []

    circulos_sorted = sorted(circulos, key=lambda c: c["cy"])
    grupos = []
    grupo_atual = [circulos_sorted[0]]
    y_ref = circulos_sorted[0]["cy"]

    for c in circulos_sorted[1:]:
        if abs(c["cy"] - y_ref) <= tolerancia:
            grupo_atual.append(c)
        else:
            grupos.append(grupo_atual)
            grupo_atual = [c]
            y_ref = c["cy"]

    grupos.append(grupo_atual)
    return grupos


def contar_presencas_pdf(pdf_path):
    """
    Conta quantas PESSOAS estavam presentes em cada data do PDF.
    Regra:
      - Cada linha (pessoa) pode ter várias bolinhas em uma mesma data.
      - Mesmo que tenha 2, 3, 4 bolinhas naquela coluna, conta como 1 presença.
    Retorna algo tipo: {'9 nov': 20, '16 nov': 10, ...}
    """
    print(f"\nLendo PDF: {pdf_path.name}")
    totais = {}

    with pdfplumber.open(pdf_path) as pdf:
        for page_idx, page in enumerate(pdf.pages, start=1):
            cols = get_date_columns_for_page(page)
            if not cols:
                continue

            words = page.extract_words()
            nome_words = [w for w in words if w["text"] == "Nome"]
            if not nome_words:
                continue

            header_top = nome_words[0]["top"]
            header_words = [w for w in words if abs(w["top"] - header_top) < 1.0]
            header_bottom = max(w["bottom"] for w in header_words)

            # 1) Coletar todos os círculos válidos abaixo do cabeçalho
            circulos = []
            for c in page.curves:
                # queremos apenas círculos preenchidos (bolinha cheia)
                if not c.get("fill"):
                    continue
                if c.get("non_stroking_color") is None:
                    continue

                cx = (c["x0"] + c["x1"]) / 2
                cy = (c["top"] + c["bottom"]) / 2

                # ignora coisas na linha do cabeçalho
                if cy <= header_bottom + 2:
                    continue

                # escolhe a coluna de data mais próxima
                label_mais_proxima = min(cols.keys(), key=lambda lab: abs(cols[lab] - cx))
                # se estiver muito longe de qualquer coluna, ignora
                if abs(cols[label_mais_proxima] - cx) > 15:
                    continue

                circulos.append({"cx": cx, "cy": cy, "data": label_mais_proxima})

            if not circulos:
                continue

            # 2) Agrupar círculos por linha (pessoa)
            grupos_linhas = agrupar_linhas_por_y(circulos, tolerancia=3)

            # 3) Para cada linha, verificar em quais datas há pelo menos uma bolinha
            for grupo in grupos_linhas:
                presencas_linha = set()
                for c in grupo:
                    presencas_linha.add(c["data"])

                # Para cada data marcada nessa linha, conta +1 pessoa presente
                for data in presencas_linha:
                    totais[data] = totais.get(data, 0) + 1

    print(f"  Pessoas presentes por data: {totais}")
    return totais


def main():
    if not PDF_DIR.exists():
        print(f"Pasta de PDFs não encontrada: {PDF_DIR}")
        return

    pdf_files = sorted(PDF_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"Nenhum PDF encontrado em {PDF_DIR}")
        return

    registros = []

    for pdf_path in pdf_files:
        try:
            with pdfplumber.open(pdf_path) as pdf:
                primeira_pagina = pdf.pages[0]
                nome_ala = extrair_nome_ala(primeira_pagina)

            if not nome_ala:
                nome_ala = pdf_path.stem

            print(f"\n=== Processando ala: {nome_ala} ===")
            contagens = contar_presencas_pdf(pdf_path)

            if not contagens:
                print("  ⚠ Nenhuma presença encontrada neste PDF, pulando.")
                continue

            registro = {"Alas": nome_ala}
            registro.update(contagens)
            registros.append(registro)
        except Exception as e:
            print(f"❌ Erro ao processar {pdf_path.name}: {e}")

    if not registros:
        print("Nenhuma presença foi encontrada em nenhum PDF.")
        return

    df = pd.DataFrame(registros)
    df = df.set_index("Alas")

    # garante valores numéricos
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # ordena colunas (semanas) em ordem cronológica
    weeks = sort_week_cols(df.columns.tolist())
    df = df[weeks]

    print("\nDataFrame final (pessoas presentes por ala/data):")
    print(df)

    df.to_csv(CSV_PATH, encoding="utf-8-sig")
    print(f"\n✅ Arquivo salvo em: {CSV_PATH}")


if __name__ == "__main__":
    main()
