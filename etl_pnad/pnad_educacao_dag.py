import os
import logging
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

from etl_pnad.download    import download_pnad_microdados, download_dicionario_pnad_2022
from etl_pnad.transform   import run_transform_pipeline
from etl_pnad.dict_loader import load_pnad_dictionary
from etl_pnad.loader      import main as load_to_postgres

# ─── logging ──────────────────────────────────────────────
logger = logging.getLogger(__name__)
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(h)
logger.setLevel(logging.INFO)

# ─── callbacks ────────────────────────────────────────────
def task_success_callback(ctx): logger.info(f"✅ Task succeeded: {ctx['task_instance'].task_id}")
def task_failure_callback(ctx): logger.error(f"❌ Task failed: {ctx['task_instance'].task_id}")

# ─── DAG default args ─────────────────────────────────────
default_args = {
    "owner": "lucas",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2025, 5, 15),
    "on_success_callback": task_success_callback,
    "on_failure_callback": task_failure_callback,
}

BASE_DIR = "/opt/airflow/dados"

# ─── DAG definition ───────────────────────────────────────
with DAG(
    dag_id="pnad_educacao_etl",
    default_args=default_args,
    description="Pipeline completo PNAD Educação (sem arquivo de schema)",
    schedule_interval="0 4 10 3,6,9,12 *",
    catchup=False,
    tags=["pnad", "educacao", "etl"],
) as dag:

    # 1) Downloads ---------------------------------------------------
    dl_micro = PythonOperator(
        task_id="download_microdados",
        python_callable=download_pnad_microdados,
        op_kwargs=dict(ano=2022, trimestre=4, destino_pasta=BASE_DIR),
    )

    dl_dict = PythonOperator(
        task_id="download_dicionario",
        python_callable=download_dicionario_pnad_2022,
        op_kwargs=dict(destino_pasta=BASE_DIR),
    )

    # 2) Dicionário → Postgres --------------------------------------
    load_dict = PythonOperator(
        task_id="load_dictionary",
        python_callable=load_pnad_dictionary,
        op_kwargs=dict(
            xls_path=f"{BASE_DIR}/dicionario_PNADC_microdados_2022_visita1_20231129.xlsx",
            dict_table="pnad_dict",
        ),
    )

    # 3) Staging do TXT ---------------------------------------------
    staging = PythonOperator(
        task_id="run_staging",
        python_callable=run_transform_pipeline,
        op_kwargs=dict(
            zip_path=f"{BASE_DIR}/PNADC_042022.zip",
            raw_dir=f"{BASE_DIR}/raw/PNADC_042022",
            db_table="pnad_staging_raw",
            chunksize=50_000,
        ),
    )

    # 4) Loader dinâmico --------------------------------------------
    load_final = PythonOperator(
        task_id="load_to_postgres",
        python_callable=load_to_postgres,
        op_kwargs=dict(
            dict_table="pnad_dict",
            staging_table="pnad_staging_raw",
            target_table="pnad_educacao",
        ),
    )

    # ─── Dependências ──────────────────────────────────────────────
    dl_dict  >> load_dict
    [dl_micro, load_dict] >> staging     # staging só depois dos dois downloads
    [staging, load_dict]  >> load_final  # loader requer staging + dicionário
