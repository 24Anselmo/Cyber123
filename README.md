# Sistema de Deteção de Cyberbullying

**Instituto Superior Politécnico da Lunda-Sul — Saurimo, Angola**

Sistema multiplataforma para deteção de cyberbullying em texto, com interface **web** (Flask) e **desktop** (Tkinter). Utiliza um dicionário enriquecido de palavras ofensivas e gírias locais angolanas (Lunda-Sul), com classificação por níveis de gravidade e classificador BERT opcional.

---

## Funcionalidades

- **Análise de texto em tempo real** — classifica como Crítico / Ofensivo / Suspeito / Neutro
- **Classificação por níveis** — crítico, alto, médio, baixo, neutro
- **Dicionário local** — 170+ palavras ofensivas + 80+ gírias regionais (dialetos da Lunda-Sul)
- **Classificador BERT** — `distilbert-base-multilingual-cased` para deteção complementar via similaridade de cosseno (fallback para rule-based se modelo não carregar)
- **Alertas inteligentes** — threshold >= 50% de confiança com WebSockets em tempo real
- **Notificações browser** — notificações nativas ao receber novo alerta
- **Painel web** — sidebar com páginas: Análise, Alertas, Análises, Fontes, Dicionário, Usuários, Relatório
- **Aplicação desktop** — interface Tkinter com as mesmas funcionalidades
- **BD partilhado** — web e desktop escrevem na mesma base SQLite
- **Auto-save** — toda análise é guardada automaticamente
- **Exportação** — relatórios em CSV, TXT e PDF
- **Monitorização Facebook** — monitorização de páginas via Graph API
- **Autenticação RBAC** — login protegido com senhas hasheadas (bcrypt); papéis: admin / moderador
- **Testes automatizados** — 15 testes pytest (deteção, API, autenticação)
- **GitHub** — repositório em `https://github.com/24Anselmo/Cyber123`

---

## Arquitetura

```
cyberbullying_detector/
├── app/                          # Aplicação Web (Flask)
│   ├── __init__.py               # Factory, BD, CORS, SocketIO
│   ├── models.py                 # Modelos SQLAlchemy
│   ├── routes.py                 # Endpoints REST + login + PDF
│   ├── detector.py               # Motor de deteção rule-based
│   ├── bert_classifier.py        # Classificador BERT (distanilbert)
│   ├── facebook_api.py           # Monitorização Facebook Graph API
│   ├── socket_events.py          # Eventos WebSocket
│   ├── static/
│   │   ├── css/style.css         # Estilos web
│   │   ├── js/main.js            # Lógica frontend
│   │   └── logo.png              # Logótipo web
│   └── templates/
│       ├── index.html            # Dashboard web
│       └── login.html            # Página de login
├── offline/                      # Aplicação Desktop (Tkinter)
│   ├── desktop_app.py            # UI desktop + lançamento browser
│   ├── logo.png                  # Logótipo desktop
│   ├── CyberbullyingDetector.spec# Configuração PyInstaller
│   └── dist/
│       └── CyberbullyingDetector.exe   # Executável compilado
├── data/
│   ├── cyberbullying.db          # Base de dados SQLite partilhada
│   ├── local_dictionary.json     # Dicionário local (80+ girias)
│   └── debug.log                 # Log de diagnóstico
├── tests/
│   ├── conftest.py               # Fixture BD temporário
│   ├── test_detector.py          # Testes do motor de deteção
│   ├── test_api.py               # Testes dos endpoints REST
│   └── test_auth.py              # Testes de autenticação
├── requirements.txt              # Dependências Python
└── run.py                        # Ponto de entrada web
```

---

## Tecnologias

| Componente       | Tecnologia                          |
|------------------|-------------------------------------|
| Web server       | Flask 3.0 + Flask-SocketIO          |
| ORM              | SQLAlchemy + SQLite                 |
| Frontend         | HTML, CSS, JavaScript (vanilla)     |
| Desktop          | Tkinter (Python)                    |
| Deteção          | Rule-based (dicionário+pesos) + BERT|
| Autenticação     | bcrypt (senhas hasheadas)           |
| WebSockets       | Flask-SocketIO + eventlet           |
| BERT             | transformers + torch (distilbert)   |
| PDF              | fpdf2                               |
| CORS             | Flask-CORS                          |
| Testes           | pytest                              |
| Empacotamento    | PyInstaller (EXE --onefile)         |
| Repositório      | GitHub                              |

---

## Instalação

### 1. Requisitos

- Python 3.10+
- pip
- Git (opcional)

### 2. Clonar ou extrair o projeto

```bash
git clone https://github.com/24Anselmo/Cyber123.git
cd cyberbullying_detector
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

### 4. Executar

#### Modo web (servidor Flask)

```bash
python run.py
# Acessar: http://localhost:5000
# Login: Alberto Baptista / 240520
```

#### Modo desktop (Tkinter)

```bash
cd offline
python desktop_app.py
# Login: Alberto Baptista / 240520
# O browser abre em http://localhost:5000 (executar run.py separadamente)
```

#### Executável compilado

Clique duas vezes em `offline/dist/CyberbullyingDetector.exe`.

---

## API REST

Todas as rotas requerem autenticação por sessão (login via `/login`). Retornam 401 se não autenticado.

| Método | Rota                              | Descrição                          |
|--------|-----------------------------------|------------------------------------|
| GET    | `/`                               | Página principal (dashboard)       |
| GET    | `/login`                          | Página de login                    |
| POST   | `/login`                          | Autenticar                         |
| GET    | `/logout`                         | Terminar sessão                    |
| GET    | `/api/estatisticas`               | Estatísticas gerais                |
| GET    | `/api/alertas`                    | Alertas pendentes (confiança >= 50)|
| GET    | `/api/analises`                   | Últimas 100 análises               |
| POST   | `/api/analises/<id>/resolver`     | Marcar análise como resolvida      |
| GET    | `/api/comentarios`                | Últimos comentários                |
| POST   | `/api/comentarios`                | Adicionar comentário + analisar    |
| POST   | `/api/detectar`                   | Analisar texto                     |
| GET    | `/api/fontes`                     | Listar fontes Facebook             |
| POST   | `/api/fontes`                     | Adicionar fonte                    |
| DELETE | `/api/fontes/<id>`                | Remover fonte                      |
| GET    | `/api/dicionario`                 | Listar gírias                      |
| POST   | `/api/dicionario`                 | Adicionar gíria                    |
| DELETE | `/api/dicionario/<id>`            | Remover gíria                      |
| GET    | `/api/usuarios`                   | Listar usuários                    |
| GET    | `/api/relatorio`                  | Relatório JSON com estatísticas    |
| GET    | `/api/relatorio/pdf`              | Relatório PDF para download        |
| POST   | `/api/inicializar`                | Carregar dados iniciais            |
| POST   | `/api/importar-comentarios`       | Importar comentários de teste      |

### WebSockets

| Evento              | Direção       | Descrição                      |
|---------------------|---------------|--------------------------------|
| `novo_alerta`       | server -> client | Novo alerta detetado        |
| `alerta_resolvido`  | server -> client | Alerta resolvido            |

### Exemplo de análise

```bash
curl -X POST http://localhost:5000/api/detectar \
  -H "Content-Type: application/json" \
  -d '{"texto": "Vou te matar seu idiota"}'
```

Resposta:

```json
{
  "classificacao": "Crítico",
  "confianca": 95.0,
  "girias": [],
  "palavras": [
    {"termo": "vou te matar", "nivel": "critico"},
    {"termo": "idiota", "nivel": "medio"}
  ],
  "critico": true,
  "nivel_geral": "critico"
}
```

---

## Motor de Deteção

### Pontuação (Rule-based)

| Elemento              | Pontos     |
|-----------------------|------------|
| Base                  | 5.0        |
| Palavra crítica       | +45        |
| Palavra alta          | +25        |
| Palavra média         | +15        |
| Palavra baixa         | +8         |
| Bónus crítico         | +35*       |
| MAIÚSCULAS (>50%)     | +10        |
| Pontos !?             | +2 cada    |

*Bónus crítico aplica-se se pelo menos uma palavra/gíria de nível crítico for detetada.

### Thresholds de classificação

| Confiança | Classificação |
|-----------|---------------|
| >= 90%    | Crítico       |
| >= 70%    | Ofensivo      |
| >= 50%    | Suspeito      |
| < 50%     | Neutro        |

Alertas são gerados para confiança **>= 50%** (Suspeito+).

### Classificador BERT

O `bert_classifier.py` carrega o modelo `distilbert-base-multilingual-cased` lazy (apenas quando usado). Classifica por similaridade de cosseno entre o embedding do texto e embeddings de referência. Se o modelo não carregar (ex.: sem torch/transformers), faz fallback para Neutro com 0% de confiança.

---

## Base de Dados

Ficheiro: `data/cyberbullying.db`

### Tabelas

| Tabela         | Colunas                                              |
|----------------|------------------------------------------------------|
| `usuarios`     | id, nome, email, senha (bcrypt), papel, avatar       |
| `fontes`       | id, url, nome, tipo, ativo                           |
| `comentarios`  | id, fonte_id (FK), texto, autor, data                |
| `analises`     | id, comentario_id (FK), classificacao, confianca, girias, resolvido, data |
| `girias_db`    | id, termo, significado, tipo, nivel                  |

As senhas em texto plano existentes são migradas automaticamente para bcrypt na inicialização.

---

## Testes

```bash
python -m pytest tests/ -v
```

15 testes automatizados:
- `test_detector.py` — 6 testes: neutro, crítico, ofensivo, suspeito, girias, maiúsculas
- `test_api.py` — 6 testes: login, deteção, alertas, fontes, dicionário, inicializar
- `test_auth.py` — 3 testes: login válido, login inválido, logout

---

## Desktop (Tkinter)

### Abas

1. **Análise** — inserir texto, ver resultado com detalhes
2. **Alertas** — lista de alertas pendentes, resolver, reportar Facebook
3. **Dicionário** — gerir gírias locais
4. **Fontes** — gerir fontes Facebook
5. **Relatório** — estatísticas, exportar CSV/TXT
6. **Usuários** — equipa do projeto

### Atalhos

- `Ctrl+Enter` — analisar texto rapidamente

---

## Empacotamento (EXE)

Para reconstruir o executável `--onefile`:

```powershell
$env:TCL_LIBRARY = "C:\caminho\para\python\tcl\tcl8.6"
$env:TK_LIBRARY = "C:\caminho\para\python\tcl\tk8.6"
cd offline
py -m PyInstaller --onefile --noconsole --name CyberbullyingDetector ^
  --add-data "..\app;app" ^
  --add-data "..\data\local_dictionary.json;data" ^
  --add-data "logo.png;." ^
  --hidden-import flask_cors ^
  --hidden-import flask_socketio ^
  --hidden-import flask_sqlalchemy ^
  --hidden-import bcrypt ^
  --hidden-import fpdf2 ^
  --hidden-import eventlet ^
  --hidden-import numpy ^
  --hidden-import requests ^
  --collect-all flask_sqlalchemy ^
  desktop_app.py
```

> **Nota:** As variáveis `TCL_LIBRARY` e `TK_LIBRARY` são necessárias para evitar o erro `Tcl data directory not found` no EXE compilado (Python 3.14 + PyInstaller).

Alternativa mais rápida (`--onedir`, ~35 s em vez de ~1-2 min):

```powershell
py -m PyInstaller --onedir --noconsole --name CyberbullyingDetector ^
  --add-data "..\app;app" ^
  --add-data "..\data\local_dictionary.json;data" ^
  --add-data "logo.png;." ^
  --collect-all flask_sqlalchemy ^
  desktop_app.py
```

---

## Credenciais

| Utilizador        | Senha  | Papel     |
|-------------------|--------|-----------|
| Alberto Baptista  | 240520 | admin     |
| Augusta Mulungia  | 1234   | moderador |
| Rafael Mussumari  | 1234   | moderador |

> As senhas são armazenadas com hash bcrypt. Na primeira execução, senhas em texto plano são migradas automaticamente.

---

## GitHub

Repositório: [https://github.com/24Anselmo/Cyber123](https://github.com/24Anselmo/Cyber123)

```bash
git remote add origin https://github.com/24Anselmo/Cyber123.git
git push -u origin main
```

---

## Desenvolvido por

**PP1 — Engenharia de Software I + Sistemas Operacionais**

- Alberto Baptista
- Augusta Mulungia
- Rafael Mussumari

**IPLS — Instituto Superior Politécnico da Lunda-Sul**
**Saurimo, Angola — 2026**
