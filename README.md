# 📘 Projeto PNAD Contínua: Educação (4º Trim. 2022)

> **Objetivo:** Realizar o download, transformação e análise descritiva dos microdados da PNAD Contínua – Educação (4º trimestre de 2022), utilizando Python, SQL, Apache Airflow e Flask para visualização.

---

## 🚀 Guia Rápido para Executar o Projeto

Siga estes passos detalhados para executar o projeto localmente.

---

### 1. ✅ Pré-requisitos

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- Git

Clone o repositório:
```bash
git clone https://github.com/lucastinoco/pnad-educacao.git
cd pnad-educacao
```

---

### 2. ⚙️ Configure o Ambiente (`.env`)

Crie um arquivo `.env` na raiz com este conteúdo (e lembre-se de adicioná-lo ao `.gitignore` para evitar versionamento acidental):

```env
POSTGRES_USER=pnad_user
POSTGRES_PASSWORD=pnad_pass
POSTGRES_DB=pnad_db
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://pnad_user:pnad_pass@postgres:5432/pnad_db
```

> **Atenção:** Não adicione espaços em branco ao redor do `=`.

---

### 3. 🧱 Construindo e Inicializando Containers

Para executar o projeto completamente do zero, rode:

```bash
docker-compose down -v --remove-orphans  # Encerra todos os containers e remove volumes e dependências órfãs
docker-compose up --build
```

A primeira execução pode levar alguns minutos devido ao download dos arquivos IBGE.

---

## 🌐 Acesso às Interfaces

### 🔧 Apache Airflow

- URL: [http://localhost:8080](http://localhost:8080)
- Login padrão:
  - Usuário: `airflow`
  - Senha: `airflow`  
> _Você pode alterar essas credenciais para maior segurança criando um novo usuário com o comando `airflow users create` no container._

### 📊 Dashboard Flask

- URL: [http://localhost:5000](http://localhost:5000)
- Explore dados com filtros:
  - UF, Sexo, Cor/Raça, Região
  - Frequência Escolar, Curso frequentado, Rede de Ensino, Renda

---

## ⚙️ Como Funciona o Pipeline ETL

O pipeline (`pnad_educacao_etl`) é orquestrado pelo Apache Airflow, seguindo estas etapas:

1. **Download dos microdados PNAD** (.zip do 4º trim. 2022)
2. **Download e conversão do dicionário** (.xls → .xlsx)
3. **Carga do dicionário** no PostgreSQL (`pnad_dict`)
4. **Leitura dos dados brutos** do `.txt` para tabela staging (`pnad_staging_raw`)
5. **Criação da tabela final tratada** (`pnad_educacao`)

---

## 🗃️ Estrutura do Banco de Dados

| Tabela              | Descrição                                         |
|---------------------|--------------------------------------------------|
| `pnad_dict`         | Dicionário extraído do `.xls` IBGE               |
| `pnad_staging_raw`  | Dados brutos do `.txt`                           |
| `pnad_educacao`     | Dados finais tratados                            |

---

## 🧪 Executando e Monitorando o Pipeline

- **Ative manualmente** a DAG `pnad_educacao_etl` no Airflow.
- **Monitore logs** usando:

```bash
docker logs -f airflow-scheduler
docker logs -f flask-app
```

---

## 🛠️ Troubleshooting e Dicas

- **Reiniciar totalmente o ambiente:**
```bash
docker-compose down -v --remove-orphans
docker system prune -a
```

- **Acessar o banco PostgreSQL diretamente:**
```bash
docker exec -it postgres psql -U pnad_user -d pnad_db
```

- **Erros comuns:**
  - Se Airflow não abrir, confirme credenciais padrão (`airflow`/`airflow`).
  - Se portas estiverem ocupadas, encerre outras instâncias Docker.

---

## 📦 Pacotes Utilizados

- **pandas, numpy**: Manipulação de dados
- **SQLAlchemy, psycopg2-binary**: Conexão com PostgreSQL
- **requests**: Download automático de arquivos
- **openpyxl, xlrd**: Conversão e manipulação Excel
- **Flask**: Servidor Web API
- **Apache Airflow**: Orquestrador de tarefas
- **dotenv**: Gerenciamento de variáveis de ambiente

Veja mais detalhes no [`requirements.txt`](requirements.txt).

---

## 📄 Licença

Projeto educacional usando dados públicos do [IBGE – PNAD Contínua](https://www.ibge.gov.br/).

---

📌 **Dúvidas ou sugestões?** [Abra uma issue no GitHub](https://github.com/seu-usuario/pnad-educacao/issues).

---
