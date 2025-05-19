import os
import logging
import requests
from typing import Optional
from urllib.parse import urlparse
import pandas as pd

# Configuração básica de logging (caso não esteja configurado globalmente)
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


def download_arquivo(url: str, destino: str) -> None:
    """
    Faz o download de um arquivo pela URL e salva em destino.
    """
    dest_dir = os.path.dirname(destino)
    if dest_dir:
        os.makedirs(dest_dir, exist_ok=True)
    try:
        logger.info(f"Iniciando download: {url}")
        resp = requests.get(url, stream=True, timeout=60)
        resp.raise_for_status()
        total_bytes = 0
        with open(destino, "wb") as f:
            for chunk in resp.iter_content(8192):
                if chunk:
                    f.write(chunk)
                    total_bytes += len(chunk)
        logger.info(f"✅ Download concluído: {destino} ({total_bytes:,} bytes)")
    except Exception as e:
        logger.error(f"❌ Falha no download {url}: {e}")
        raise


def download_pnad_microdados(
    ano: int,
    trimestre: int,
    destino_pasta: str = "/opt/airflow/dados",
    nome_arquivo: Optional[str] = None
) -> None:
    """
    Baixa o microdados PNAD para o ano e trimestre especificados.
    """
    logger.info(f"Preparando download de microdados PNAD: ano={ano}, trimestre={trimestre}")
    url = (
        f"https://ftp.ibge.gov.br/Trabalho_e_Rendimento/"
        f"Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/"
        f"Trimestral/Microdados/{ano}/PNADC_{trimestre:02d}{ano}.zip"
    )
    parsed = urlparse(url)
    arquivo = nome_arquivo or os.path.basename(parsed.path).strip()
    destino = os.path.join(destino_pasta, arquivo)
    logger.info(f"📥 Preparando download dos microdados para: {destino}")
    download_arquivo(url, destino)


def download_dicionario_pnad_2022(
    destino_pasta: str = "/opt/airflow/dados"
) -> None:
    """
    Baixa o dicionário PNAD Microdados 2022 (visita 1) em Excel (.xls)
    e converte para o formato .xlsx.
    """
    xls_url = (
        "https://ftp.ibge.gov.br/Trabalho_e_Rendimento/"
        "Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/"
        "Anual/Microdados/Visita/Visita_1/Documentacao/"
        "dicionario_PNADC_microdados_2022_visita1_20231129.xls"
    )
    parsed = urlparse(xls_url)
    arquivo_xls = os.path.basename(parsed.path).strip()
    path_xls = os.path.join(destino_pasta, arquivo_xls)

    logger.info(f"📥 Preparando download do dicionário PNAD 2022 para: {path_xls}")
    download_arquivo(xls_url, path_xls)

    # Conversão para XLSX
    path_xlsx = path_xls.replace(".xls", ".xlsx")
    logger.info(f"🔄 Convertendo para XLSX: {path_xls} → {path_xlsx}")
    try:
        # Lê todas as abas do .xls com engine xlrd
        xls = pd.read_excel(path_xls, sheet_name=None, engine="xlrd")
        # Escreve cada aba no arquivo .xlsx
        with pd.ExcelWriter(path_xlsx, engine="openpyxl") as writer:
            for sheet_name, df in xls.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        logger.info(f"✅ Conversão concluída: {path_xlsx}")
    except Exception as e:
        logger.error(f"❌ Erro durante a conversão para XLSX: {e}")
        raise
