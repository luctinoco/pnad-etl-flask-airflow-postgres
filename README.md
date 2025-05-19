
# 📘 Projeto PNAD Contínua: Educação (4º Trim. 2022)

> **Objetivo:** Este projeto realiza o download, transformação e análise descritiva dos microdados da PNAD Contínua – Educação para o 4º trimestre de 2022, utilizando um pipeline completo em Python + SQL com orquestração via Apache Airflow e visualização com Flask.

---

## 🚀 Como Executar o Projeto

### 1. ✅ Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- Clonar este repositório:
```bash
git clone https://github.com/seu-usuario/pnad-educacao.git
cd pnad-educacao
```

---

### 2. ⚙️ Variáveis de Ambiente

Crie um arquivo `.env` na raiz com:

```env
POSTGRES_USER=pnad_user
POSTGRES_PASSWORD=pnad_pass
POSTGRES_DB=pnad_db
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://pnad_user:pnad_pass@postgres:5432/pnad_db
```

---

### 3. 🧱 Build e Start dos Containers

Execute tudo do zero com:

```bash
docker-compose down -v --remove-orphans
docker-compose up --build
```

---

## 🧩 Explicação Técnica

### 📦 Pacotes Utilizados

- **pandas**: leitura e transformação dos dados `.txt` e `.xls`.
- **openpyxl, xlrd**: leitura e conversão de arquivos do dicionário PNAD.
- **SQLAlchemy, psycopg2-binary**: comunicação com PostgreSQL.
- **requests**: download automatizado dos microdados via FTP.
- **Flask**: API para servir os dados tratados.
- **Apache Airflow**: orquestração de todas as etapas do ETL.
- **dotenv**: carregamento seguro das variáveis de ambiente.

---

## ⚙️ Pipeline de ETL (orquestrado com Airflow)

A DAG `pnad_educacao_etl` define o fluxo:

### 🧭 Etapas:

1. **download_microdados**  
   - Baixa automaticamente o `.zip` do 4º trimestre de 2022 da PNAD no site do IBGE.

2. **download_dicionario**  
   - Baixa o arquivo `.xls` do dicionário e converte para `.xlsx`.

3. **load_dictionary**  
   - Carrega o dicionário para uma tabela auxiliar (`pnad_dict`) no PostgreSQL.

4. **run_staging**  
   - Descompacta o `.zip`, lê o `.txt` com base nos índices do dicionário e carrega em `pnad_staging_raw`.

5. **load_to_postgres**  
   - Cria a tabela final `pnad_educacao` com nomes reais das variáveis e popula com os dados do staging.

---

## 🌐 Acesso à Interface Web

### 🔧 Airflow

- Acesse: [http://localhost:8080](http://localhost:8080)
- Login padrão:
  - Usuário: `airflow`
  - Senha: `airflow`

### 📊 Dashboard Flask

- Acesse: [http://localhost:5000](http://localhost:5000)
- Fornece visualizações interativas com filtros por UF sobre:
  - Frequência escolar
  - Curso mais elevado frequentado
  - Tipo de rede de ensino
  - Rendimento médio
  - Perfil por sexo, cor/raça, região

---

## 🗃️ Banco de Dados

O projeto usa o PostgreSQL em container com três tabelas principais:

| Tabela              | Descrição                                         |
|---------------------|--------------------------------------------------|
| `pnad_dict`         | Dicionário extraído do `.xls` do IBGE            |
| `pnad_staging_raw`  | Dados brutos carregados do `.txt` por colspec    |
| `pnad_educacao`     | Tabela final com colunas nomeadas e tratadas     |

---

## 🧪 Teste o Pipeline

1. Acesse o Airflow e **execute manualmente** a DAG `pnad_educacao_etl`.
2. Acompanhe os logs por container:

```bash
docker logs -f airflow-scheduler
docker logs -f flask-app
```

---

## 🛠️ Troubleshooting

- Se precisar limpar tudo:
```bash
docker-compose down -v --remove-orphans
docker system prune -a
```

- Para acessar o banco diretamente:
```bash
docker exec -it postgres psql -U pnad_user -d pnad_db
```

---

## 📄 Licença

Projeto demonstrativo com dados públicos da [PNAD Contínua - IBGE](https://www.ibge.gov.br/).
