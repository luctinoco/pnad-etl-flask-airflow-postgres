import os
import logging
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

# ─── Logging ─────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)
if not logger.handlers:
    h = logging.StreamHandler()
    h.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(h)
logger.setLevel(logging.INFO)

# ─── Variáveis de ambiente ───────────────────────────────────────────
load_dotenv()
USER = os.getenv("POSTGRES_USER")
PWD  = os.getenv("POSTGRES_PASSWORD")
HOST = os.getenv("POSTGRES_HOST")
PORT = os.getenv("POSTGRES_PORT")
DB   = os.getenv("POSTGRES_DB")


def create_table_from_dict(conn, dict_table: str, target_table: str) -> None:
    """
    Cria a tabela final usando var_code em ordem de col_index.
    Todas as colunas são criadas como TEXT.
    """
    logger.info(f"▶️ Gerando tabela '{target_table}' a partir de '{dict_table}'")
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("SELECT var_code FROM {} ORDER BY col_index").format(
                sql.Identifier(dict_table)
            )
        )
        var_codes = [r[0] for r in cur.fetchall()]
        if not var_codes:
            raise ValueError(f"Nenhuma entrada em {dict_table!r}")

        cur.execute(sql.SQL("DROP TABLE IF EXISTS {};").format(sql.Identifier(target_table)))

        ddl = sql.SQL("CREATE TABLE {} ({})").format(
            sql.Identifier(target_table),
            sql.SQL(", ").join(
                sql.SQL("{} TEXT").format(sql.Identifier(vc)) for vc in var_codes
            )
        )
        cur.execute(ddl)
    conn.commit()
    logger.info(f"✅ Tabela '{target_table}' pronta")


def populate_final_table(conn, dict_table: str, staging_table: str, target_table: str) -> None:
    logger.info(f"▶️ Populando '{target_table}' a partir de '{staging_table}'")
    with conn.cursor() as cur:
        logger.info(f"🧹 Limpando tabela '{target_table}' antes da carga")
        cur.execute(
            sql.SQL("TRUNCATE TABLE {};").format(sql.Identifier(target_table))
        )

        # Busca lista de var_codes e col_index ordenada
        cur.execute(
            sql.SQL("SELECT var_code, col_index FROM {} ORDER BY col_index").format(
                sql.Identifier(dict_table)
            )
        )
        var_and_idx = cur.fetchall()
        if not var_and_idx:
            raise ValueError(f"Nenhuma variável para inserir em {dict_table!r}")

        # Número de colunas reais no staging
        cur.execute(
            sql.SQL("SELECT * FROM {} LIMIT 0").format(sql.Identifier(staging_table))
        )
        num_staging_cols = len(cur.description or [])

        # Filtra para só usar variáveis com col_index <= num_staging_cols
        filtered = [
            (code, idx) for code, idx in var_and_idx
            if idx is not None and 1 <= idx <= num_staging_cols
        ]
        if len(filtered) != len(var_and_idx):
            logger.warning(f"Algumas variáveis do dicionário foram ignoradas por terem col_index fora do staging.")

        var_codes = [code for code, idx in filtered]
        select_parts = [
            sql.SQL("{} AS {}").format(
                sql.Identifier(f"col{idx}"),
                sql.Identifier(code)
            )
            for code, idx in filtered
        ]

        insert_sql = sql.SQL(
            "INSERT INTO {target} ({cols}) SELECT {sels} FROM {stg};"
        ).format(
            target=sql.Identifier(target_table),
            cols=sql.SQL(", ").join(sql.Identifier(c) for c in var_codes),
            sels=sql.SQL(", ").join(select_parts),
            stg=sql.Identifier(staging_table)
        )
        logger.info(f"SQL de inserção gerado:\n{insert_sql.as_string(conn)}")
        cur.execute(insert_sql)
    conn.commit()
    logger.info(f"✅ Dados inseridos em '{target_table}'")

def main(
    dict_table: str = "pnad_dict",
    staging_table: str = "pnad_staging_raw",
    target_table: str = "pnad_educacao"
) -> None:
    logger.info("=== Iniciando carga dinâmica PNAD Educação ===")
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=DB,
            user=USER,
            password=PWD,
            host=HOST,
            port=PORT
        )
        logger.info("🔌 Conectado ao PostgreSQL")

        create_table_from_dict(conn, dict_table, target_table)
        populate_final_table(conn, dict_table, staging_table, target_table)

    except Exception:
        logger.exception("❌ Erro durante a carga dinâmica")
        raise

    finally:
        if conn:
            conn.close()
            logger.info("🔌 Conexão encerrada")


if __name__ == "__main__":
    main()
