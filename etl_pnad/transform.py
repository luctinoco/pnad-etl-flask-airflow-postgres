import os
import logging
from zipfile import ZipFile
from typing import List, Tuple, Optional
import pandas as pd
from sqlalchemy import create_engine

# Configuração básica de logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def descompactar(zip_path: str, destino: str) -> None:
    """
    Extrai o conteúdo de um arquivo ZIP para o diretório destino.
    """
    logger.info(f"Iniciando descompactação: {zip_path} → {destino}")
    if not os.path.exists(zip_path):
        logger.error(f"ZIP não encontrado: {zip_path}")
        raise FileNotFoundError(f"ZIP não encontrado: {zip_path}")
    os.makedirs(destino, exist_ok=True)
    try:
        with ZipFile(zip_path) as zf:
            zf.extractall(destino)
        logger.info(f"✅ Descompactado em: {destino}")
    except Exception as e:
        logger.exception(f"Falha ao descompactar {zip_path}: {e}")
        raise


def staging_txt_to_db(
    txt_path: str,
    colspecs: List[Tuple[int, Optional[int]]],
    db_table: str,
    chunksize: int = 50_000
) -> None:
    """
    Lê arquivo TXT em chunks e insere em tabela de staging no banco.
    """
    logger.info(f"Iniciando staging de TXT para DB: {txt_path} → {db_table}")
    if not os.path.exists(txt_path):
        logger.error(f"TXT não encontrado: {txt_path}")
        raise FileNotFoundError(f"TXT não encontrado: {txt_path}")

    conn_str = os.getenv("AIRFLOW__CORE__SQL_ALCHEMY_CONN")
    if not conn_str:
        logger.error("Variável de ambiente 'AIRFLOW__CORE__SQL_ALCHEMY_CONN' não definida")
        raise EnvironmentError("Conexão SQLAlchemy não configurada")

    engine = create_engine(conn_str)
    n_cols = len(colspecs)
    logger.info(f"Total de colunas na especificação: {n_cols}")
    cols = [f"col{i}" for i in range(1, n_cols+1)]

    reader = pd.read_fwf(
        txt_path,
        colspecs=colspecs,
        names=cols,
        header=None,
        encoding="latin1",
        chunksize=chunksize
    )
    for i, chunk in enumerate(reader, start=1):
        mode = 'replace' if i == 1 else 'append'
        try:
            chunk.to_sql(db_table, engine, if_exists=mode, index=False)
            logger.info(f"✔️ Chunk {i} inserido em '{db_table}': {len(chunk):,} linhas")
        except Exception as e:
            logger.exception(f"Falha ao inserir chunk {i} em '{db_table}': {e}")
            raise


def run_transform_pipeline(
    zip_path: str,
    raw_dir: str,
    db_table: str = "pnad_staging_raw",
    chunksize: int = 50_000
) -> None:
    logger.info("=== Iniciando staging bruto PNAD Educação ===")
    descompactar(zip_path, raw_dir)

    conn_str = os.getenv("AIRFLOW__CORE__SQL_ALCHEMY_CONN")
    if not conn_str:
        logger.error("Variável AIRFLOW__CORE__SQL_ALCHEMY_CONN não definida")
        raise EnvironmentError("Conexão SQLAlchemy não configurada")
    engine = create_engine(conn_str)

    # --- NOVO: carrega col_index e width
    df_dict = pd.read_sql("SELECT col_index, width FROM pnad_dict ORDER BY col_index", engine)
    positions = df_dict["col_index"].tolist()
    widths = df_dict["width"].tolist()

    colspecs = []
    for start, w in zip(positions, widths):
        start0 = start - 1
        end0 = start0 + w
        colspecs.append((start0, end0))
    logger.info(f"📑 Colspecs gerados: {len(colspecs)} colunas")

    txt_file = os.path.join(raw_dir, os.path.basename(zip_path).replace(".zip", ".txt"))
    cols = [f"col{i+1}" for i in range(len(colspecs))]

    reader = pd.read_fwf(
        txt_file,
        colspecs=colspecs,
        names=cols,
        header=None,
        encoding="latin1",
        chunksize=chunksize
    )
    for i, chunk in enumerate(reader, start=1):
        mode = 'replace' if i == 1 else 'append'
        chunk.to_sql(db_table, engine, if_exists=mode, index=False)
        logger.info(f"✔️ Chunk {i} inserido em '{db_table}': {len(chunk):,} linhas")
    logger.info("=== Staging bruto PNAD Educação concluído com sucesso ===")
