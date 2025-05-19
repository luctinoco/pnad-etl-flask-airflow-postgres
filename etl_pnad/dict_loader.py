import os
import logging
import pandas as pd
from sqlalchemy import create_engine

# Configuração básica de logging\logger = logging.getLogger(__name__)
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def load_pnad_dictionary(
    xls_path: str,
    dict_table: str = "pnad_dict"
) -> None:
    """
    Carrega o dicionário PNAD de um arquivo Excel (.xls ou .xlsx) para uma tabela SQL,
    incluindo col_index, width e var_code.

    Parâmetros:
    - xls_path: Caminho para o arquivo Excel do dicionário.
    - dict_table: Nome da tabela de destino no banco.
    """
    logger.info(f"Iniciando carga do dicionário PNAD a partir de: {xls_path}")

    if not os.path.exists(xls_path):
        logger.error(f"Dicionário não encontrado: {xls_path}")
        raise FileNotFoundError(f"Dicionário não encontrado: {xls_path}")

    conn_str = os.getenv("AIRFLOW__CORE__SQL_ALCHEMY_CONN")
    if not conn_str:
        logger.error("Variável AIRFLOW__CORE__SQL_ALCHEMY_CONN não definida")
        raise EnvironmentError("Conexão SQLAlchemy não configurada. Defina AIRFLOW__CORE__SQL_ALCHEMY_CONN")
    engine = create_engine(conn_str)

    # Detecta engine de leitura
    ext = os.path.splitext(xls_path)[1].lower()
    engine_name = "xlrd" if ext == ".xls" else "openpyxl"

    try:
        # Lê col_index (0), width (1), var_code (2)
        df = pd.read_excel(
            xls_path,
            skiprows=1,
            header=0,
            usecols=[0, 1, 2],  # 0=col_index, 1=width, 2=var_code
            names=["col_index", "width", "var_code"],
            engine=engine_name
        )
        logger.info(f"Lido {len(df):,} linhas com col_index, width e var_code")

        # Limpa e converte tipos
        df["col_index"] = pd.to_numeric(df["col_index"], errors="coerce")
        df["width"] = pd.to_numeric(df["width"], errors="coerce")
        df = df.dropna(subset=["col_index", "width"]).copy()
        df["col_index"] = df["col_index"].astype(int)
        df["width"] = df["width"].astype(int)
        df["var_code"] = df["var_code"].astype(str).str.strip()

        # Salva no banco
        df.to_sql(dict_table, engine, if_exists="replace", index=False)
        logger.info(f"✅ Dicionário carregado em '{dict_table}' com {len(df):,} registros")

    except Exception:
        logger.exception("Falha durante o processamento do dicionário PNAD")
        raise
