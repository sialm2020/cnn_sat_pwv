from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urljoin
import pandas as pd
import numpy as np
import re

# ==========================================================
# CONFIGURAÇÕES
# ==========================================================

BASE = Path.home() / "cnn_sat_pwv"

ARQ_GATILHOS = BASE / "data_raw" / "Analise_Picos_Chuva_1para1_n8_2025.xlsx"

OUT_DIR = BASE / "data_processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_CSV = OUT_DIR / "mapa_gatilho_goes_2025.csv"

BASE_URL = "https://ftp.cptec.inpe.br/goes/goes16/retangular/ch13/2025/"

# Pelo print, no servidor aparecem 01, 02, 03 e 04.
# Se depois surgirem outros meses, basta adicionar aqui.
MESES = ["01", "02", "03", "04"]

TOL_MIN = 10


# ==========================================================
# FUNÇÕES
# ==========================================================

def excel_time_to_datetime(x):
    """
    Converte data/hora da planilha para datetime.
    Aceita Timestamp, número serial do Excel ou string.
    """
    if pd.isna(x):
        return pd.NaT

    if isinstance(x, pd.Timestamp):
        return x

    if isinstance(x, (int, float, np.integer, np.floating)):
        return pd.to_datetime(x, unit="D", origin="1899-12-30")

    return pd.to_datetime(x, errors="coerce")


def read_html_links(url):
    """
    Lê uma página de diretório via HTTPS e retorna os links href.
    Usa apenas biblioteca padrão do Python.
    """
    with urlopen(url, timeout=120) as response:
        html = response.read().decode("utf-8", errors="ignore")

    links = re.findall(r'href=[\'"]?([^\'" >]+)', html)
    return links


def parse_time_from_goes_name(filename):
    """
    Extrai horário YYYYMMDDHHMM do nome do arquivo GOES.
    Exemplo:
    S10635346_202501010000.nc
    """
    name = Path(filename).name

    m = re.search(r"(20\d{10})", name)
    if m:
        return pd.to_datetime(m.group(1), format="%Y%m%d%H%M")

    return pd.NaT


def list_goes_files_https(base_url, meses):
    """
    Lista arquivos .nc ou .nc.gz nos meses disponíveis.
    Funciona para estrutura:
    .../2025/01/
    .../2025/02/
    .../2025/03/
    .../2025/04/
    """
    files = []

    for mes in meses:
        mes_url = urljoin(base_url, f"{mes}/")
        print(f"Listando {mes_url}")

        try:
            links = read_html_links(mes_url)
        except Exception as e:
            print(f"Não consegui acessar {mes_url}: {e}")
            continue

        for link in links:
            if link in ["../", "./"]:
                continue

            # Se houver subpastas, entra nelas
            if link.endswith("/"):
                sub_url = urljoin(mes_url, link)
                print(f"  Subpasta: {sub_url}")

                try:
                    sub_links = read_html_links(sub_url)
                except Exception as e:
                    print(f"  Não consegui acessar {sub_url}: {e}")
                    continue

                for sub_link in sub_links:
                    if sub_link.endswith(".nc") or sub_link.endswith(".nc.gz"):
                        files.append(urljoin(sub_url, sub_link))

            # Se os arquivos estiverem diretamente no mês
            elif link.endswith(".nc") or link.endswith(".nc.gz"):
                files.append(urljoin(mes_url, link))

    return sorted(set(files))


# ==========================================================
# 1. LER GATILHOS 2025
# ==========================================================

df = pd.read_excel(ARQ_GATILHOS, sheet_name="Dados_1para1")

df["trigger_time_utc"] = df["Tempo_Pico_PWV"].apply(excel_time_to_datetime)

df = df.dropna(subset=["trigger_time_utc"]).copy()
df = df.sort_values("trigger_time_utc").reset_index(drop=True)

df["event_id"] = [
    f"ATTO_2025_{i:04d}" for i in range(1, len(df) + 1)
]

print("Gatilhos lidos:", len(df))
print("Período dos gatilhos:")
print(df["trigger_time_utc"].min(), "até", df["trigger_time_utc"].max())


# ==========================================================
# 2. LISTAR ARQUIVOS GOES VIA HTTPS
# ==========================================================

print("\nListando arquivos GOES via HTTPS...")
goes_files = list_goes_files_https(BASE_URL, MESES)

print("\nArquivos encontrados:", len(goes_files))

goes = pd.DataFrame({"goes_file": goes_files})
goes["goes_time_utc"] = goes["goes_file"].apply(parse_time_from_goes_name)

goes = goes.dropna(subset=["goes_time_utc"]).copy()
goes = goes.sort_values("goes_time_utc").reset_index(drop=True)

print("Arquivos com horário reconhecido:", len(goes))

if len(goes) > 0:
    print("Período GOES disponível:")
    print(goes["goes_time_utc"].min(), "até", goes["goes_time_utc"].max())
    print(goes.head())


# ==========================================================
# 3. ASSOCIAR GATILHO À IMAGEM MAIS PRÓXIMA
# ==========================================================

if len(goes) == 0:
    raise RuntimeError("Nenhum arquivo GOES com horário reconhecido foi encontrado.")

matched = pd.merge_asof(
    df.sort_values("trigger_time_utc"),
    goes.sort_values("goes_time_utc"),
    left_on="trigger_time_utc",
    right_on="goes_time_utc",
    direction="nearest"
)

matched["delta_goes_min"] = (
    matched["goes_time_utc"] - matched["trigger_time_utc"]
).dt.total_seconds() / 60.0

matched["match_status"] = np.where(
    matched["delta_goes_min"].abs() <= TOL_MIN,
    "ok",
    "fora_tolerancia"
)

matched.loc[matched["goes_file"].isna(), "match_status"] = "sem_imagem"


# ==========================================================
# 4. SALVAR MAPA FINAL
# ==========================================================

cols_out = [
    "event_id",
    "trigger_time_utc",
    "goes_file",
    "goes_time_utc",
    "delta_goes_min",
    "match_status"
]

matched[cols_out].to_csv(OUT_CSV, index=False)

print("\nResumo do match:")
print(matched["match_status"].value_counts(dropna=False))

print("\nArquivo salvo em:")
print(OUT_CSV)

print("\nPrimeiras linhas:")
print(matched[cols_out].head(10))