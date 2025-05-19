import os
import logging
import traceback
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from sqlalchemy import create_engine, text
import numpy as np

# ─── Logging ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ─── Configuração DB (.env) ─────────────────────────────────────────
load_dotenv()
USER = os.getenv("POSTGRES_USER", "airflow")
PWD  = os.getenv("POSTGRES_PASSWORD", "airflow")
HOST = os.getenv("POSTGRES_HOST", "postgres")
PORT = os.getenv("POSTGRES_PORT", "5432")
DB   = os.getenv("POSTGRES_DB", "pnad_db")
ENGINE = create_engine(f"postgresql://{USER}:{PWD}@{HOST}:{PORT}/{DB}", pool_pre_ping=True)

# ─── Mapeamentos estáticos ───────────────────────────────────────────
UF_MAP = {
    11:"RO",12:"AC",13:"AM",14:"RR",15:"PA",16:"AP",17:"TO",
    21:"MA",22:"PI",23:"CE",24:"RN",25:"PB",26:"PE",27:"AL",28:"SE",29:"BA",
    31:"MG",32:"ES",33:"RJ",35:"SP",41:"PR",42:"SC",43:"RS",
    50:"MS",51:"MT",52:"GO",53:"DF"
}
REDE_MAP = {1:"Pública", 2:"Privada", 9:"Ignorado"}

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/health")
def health():
    return {"status":"ok","ts":datetime.utcnow().isoformat()+"Z"}

@app.route("/api/analise-descritiva")
def analise_descritiva():
    try:
        # 1) Frequência escolar por UF: todos V3002 > 0 = "Sim", senão "Não"
        freq_sql = text("""
            SELECT
              (CAST("UF" AS BIGINT)/10000000)::INT AS uf_code,
              CASE
                WHEN CAST("V3002" AS INT) > 0 THEN 'Sim'
                ELSE 'Não'
              END AS frequenta,
              COUNT(*) AS total,
              COUNT(*)::FLOAT
                / SUM(COUNT(*)) OVER (
                    PARTITION BY (CAST("UF" AS BIGINT)/10000000)::INT
                  )
                AS percentual
            FROM pnad_educacao
            GROUP BY 1,2
            ORDER BY 1,2
        """)
        freq_rows = ENGINE.execute(freq_sql).all()

        # 2) Rede de Ensino (apenas quem efetivamente frequenta: V3002 > 0)
        rede_sql = text("""
            SELECT
              CAST("V3002A" AS INT) AS rede_code,
              COUNT(*) AS total,
              COUNT(*)::FLOAT / SUM(COUNT(*)) OVER () AS percentual
            FROM pnad_educacao
            WHERE CAST("V3002" AS INT) > 0
              AND CAST("V3002A" AS INT) IN (1,2,9)
            GROUP BY rede_code
            ORDER BY rede_code
        """)
        rede_rows = ENGINE.execute(rede_sql).all()

    except Exception as e:
        logger.error("Erro nas queries: %s", e)
        logger.debug(traceback.format_exc())
        return jsonify(error="Falha ao consultar o banco."), 500

    # ─── Monta JSON para o front ───────────────────────────────────────
    freq_df = [
        {
          "uf": UF_MAP.get(r.uf_code, str(r.uf_code)),
          "frequenta": r.frequenta,
          "percentual": float(r.percentual)
        }
        for r in freq_rows
    ]
    rede_df = [
        {
          "rede": REDE_MAP.get(r.rede_code, "Outro"),
          "percentual": float(r.percentual),
          "total": r.total
        }
        for r in rede_rows
    ]

    # ─── Estatísticas resumidas ────────────────────────────────────────
    sim = [r for r in freq_df if r["frequenta"] == "Sim"]
    if sim:
        vals = [r["percentual"]*100 for r in sim]
        ufs = [r["uf"] for r in sim]
        stats_freq = {
            "uf_maior_freq": ufs[np.argmax(vals)],
            "maior_freq_percent": round(max(vals),2),
            "uf_menor_freq": ufs[np.argmin(vals)],
            "menor_freq_percent": round(min(vals),2),
            "media_percent": round(np.mean(vals),2),
            "desvio_padrao": round(np.std(vals),2),
        }
    else:
        stats_freq = {}

    total_resp = sum(r["total"] for r in rede_df)
    rede_stats = {
        r["rede"]: {"percentual": round(r["percentual"]*100,2), "total": r["total"]}
        for r in rede_df
    }

    return jsonify(
        frequencia_escolar_uf=freq_df,
        rede_ensino=rede_df,
        graficos_stats={
            "frequencia_escolar": stats_freq,
            "rede_ensino": {"total_respondentes": total_resp, "resumo": rede_stats}
        }
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=os.getenv("FLASK_DEBUG")=="1")
