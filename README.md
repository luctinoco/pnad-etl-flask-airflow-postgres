# 📘 Projeto PNAD Contínua – Educação (4º Trim. 2022)

**Objetivo:** Desenvolver um pipeline completo para download, transformação e análise descritiva dos microdados da PNAD Contínua – Educação (4º trimestre de 2022), com orquestração via Apache Airflow e visualização interativa via Flask.

---

## 🚀 Guia Rápido de Execução

### 1. Pré-requisitos

- Docker  
- Docker Compose  
- Git  

```bash
git clone https://github.com/lucastinoco/pnad-educacao.git
cd pnad-educacao
```

### 2. Configuração de Ambiente

1. Crie um arquivo `.env` na raiz do projeto e inclua:

   ```env
   POSTGRES_USER=pnad_user
   POSTGRES_PASSWORD=pnad_pass
   POSTGRES_DB=pnad_db
   POSTGRES_HOST=postgres
   POSTGRES_PORT=5432

   AIRFLOW__CORE__SQL_ALCHEMY_CONN=postgresql+psycopg2://pnad_user:pnad_pass@postgres:5432/pnad_db
   ```

2. Adicione `.env` ao `.gitignore` para evitar versionamento de credenciais.

### 3. Construção e Inicialização

Para construir e subir todos os serviços do zero:

```bash
docker-compose down -v --remove-orphans
docker-compose up --build
```

> A primeira execução faz download dos microdados e pode levar alguns minutos.

---

## 🌐 Acesso às Interfaces

- **Apache Airflow**  
  - URL: http://localhost:8080  
  - Login: `airflow` / `airflow`  
  > Você pode criar usuários adicionais dentro do container.

- **Dashboard Flask**  
  - URL: http://localhost:5000  
  - Filtros disponíveis: UF, Sexo, Cor/Raça, Região  

---

## 👨‍💻 Componentes do Projeto

- **`app.py`**  
  Servidor Flask que expõe:
  - Rota `/` para renderizar o template `index.html`.  
  - API `/api/analise-descritiva` que executa queries no PostgreSQL e retorna JSON para os gráficos.  
  - Mapeamentos estáticos (UF, Rede de Ensino) e cálculo de estatísticas via NumPy. citeturn1file0

- **`templates/index.html`**  
  - Layout responsivo com HTML/CSS para exibir abas de navegação.  
  - Espaços para gráficos via `<canvas>` e painel de estatísticas.  
  - Estilos customizados para cores, fontes e responsividade. citeturn1file1

- **`static/app.js`**  
  - Lógica JavaScript para:
    - Buscar dados da API (`/api/analise-descritiva`).  
    - Renderizar gráfico de barras empilhadas (Frequência Escolar) e gráfico de pizza (Rede de Ensino) usando Chart.js.  
    - Gerenciar abas e exibir estatísticas no painel. citeturn1file2

---

## ⚙️ Pipeline ETL

1. **Download**  
   - Microdados PNAD (ZIP)  
   - Dicionário IBGE (XLS → XLSX)

2. **Carga Dicionário**  
   - Tabela: `pnad_dict`

3. **Staging de Dados Brutos**  
   - Leitura do `.txt`  
   - Tabela: `pnad_staging_raw`

4. **Geração da Tabela Final**  
   - Tabela: `pnad_educacao`  
   - Mapeamento dinâmico de colunas via `col_index` e `width`

5. **Orquestração**  
   - Definida no DAG `pnad_educacao_etl` do Airflow

---

## 🗃️ Estrutura do Banco de Dados

| Tabela               | Descrição                                          |
|----------------------|----------------------------------------------------|
| `pnad_dict`          | Dicionário extraído do Excel (col_index, width, var_code) |
| `pnad_staging_raw`   | Dados fix-width lidos do arquivo `.txt`            |
| `pnad_educacao`      | Dados tratados e estruturados para análise         |

---

## 📂 Estrutura de Pastas

```text
.
├── app/                       # Aplicação Flask: backend e frontend
│   ├── app.py                 # Servidor Flask
│   ├── static/                # Assets estáticos (JS, CSS)
│   │   └── app.js
│   └── templates/             # Modelos HTML
│       └── index.html
├── etl_pnad/                  # Módulos Python do pipeline ETL
│   ├── download.py            # Download de microdados e dicionário
│   ├── dict_loader.py         # Geração de dicionário no PostgreSQL (pnad_dict)
│   ├── loader.py              # Carregamento de staging e criação de pnad_educacao
│   ├── transform.py           # Transformações de dados e schema
│   └── pnad_educacao_dag.py   # DAG do Airflow para orquestração
├── imagens/                   # Exemplos de gráficos e imagens de apoio
├── docker-compose.yml         # Definição de serviços Docker
├── Dockerfile.airflow         # Imagem customizada para Apache Airflow
├── Dockerfile.flask           # Imagem customizada para Flask
├── requirements.txt           # Lista de dependências Python
├── LICENSE                    # Licença do projeto
└── README.md                  # Documentação e guia de execução
```

---

## 🛠️ Execução e Monitoramento

- **Ativar DAG**  
  Dentro do Airflow, ative a DAG `pnad_educacao_etl`.

- **Logs em Tempo Real**  
  ```bash
  docker logs -f airflow-scheduler
  docker logs -f flask-app
  ```

- **Acesso ao PostgreSQL**  
  ```bash
  docker exec -it pnad-educacao_postgres_1 psql -U pnad_user -d pnad_db
  ```

- **Reinicialização Completa**  
  ```bash
  docker-compose down -v --remove-orphans
  docker system prune -a
  ```

---

## 📦 Principais Dependências

| Pacote                | Função                                       |
|-----------------------|----------------------------------------------|
| pandas, numpy         | Manipulação e análise de dados               |
| SQLAlchemy, psycopg2  | Conexão e operações com PostgreSQL           |
| requests              | Download automático de arquivos              |
| openpyxl, xlrd        | Leitura e conversão de arquivos Excel        |
| Flask                 | Servidor Web e API                           |
| Apache Airflow        | Orquestração de tarefas                      |
| python-dotenv         | Carregamento de variáveis de ambiente        |

Consulte o arquivo `requirements.txt` para versões completas.

---

## 📄 Licença

Dados públicos do IBGE – PNAD Contínua.  

---


---

## 📈 Exemplos de Gráficos

A seguir, dois exemplos gerados pela aplicação para ilustrar a visualização de dados:

| Gráfico de Pizza - Rede de Ensino | Resumo Estatístico - Frequência Escolar por UF |
|:---------------------------------:|:----------------------------------------------:|
| ![Gráfico de Pizza](imagens/pie_chart.png) | ![Resumo Estatístico](imagens/status.png) |

> As imagens estão disponíveis em `imagens/` ou no repositório:
> - `imagens/pie_chart.png`
> - `imagens/status.png`


🔗 **Contribuições e Issues**  
Abra uma issue em https://github.com/lucastinoco/pnad-educacao/issues  
