# Sistema de Detecao de Cyberbullying — Documentacao Tecnica

**Instituto Superior Politecnico da Lunda-Sul — Saurimo, Angola**
PP1 — Engenharia de Software I + Sistemas Operacionais | 2026

---

## Indice

1. [Visao Geral](#1-visao-geral)
2. [Arquitetura do Sistema](#2-arquitetura-do-sistema)
3. [Instalacao e Configuracao](#3-instalacao-e-configuracao)
4. [Guia de Utilizacao](#4-guia-de-utilizacao)
5. [API REST](#5-api-rest)
6. [Motor de Detecao](#6-motor-de-detecao)
7. [Classificador BERT](#7-classificador-bert)
8. [WebSockets e Notificacoes](#8-websockets-e-notificacoes)
9. [Base de Dados](#9-base-de-dados)
10. [Gestao de Utilizadores e Permissoes](#10-gestao-de-utilizadores-e-permissoes)
11. [Testes Automatizados](#11-testes-automatizados)
12. [Empacotamento (EXE)](#12-empacotamento-exe)
13. [Manutencao e Resolucao de Problemas](#13-manutencao-e-resolucao-de-problemas)
14. [Credenciais](#14-credenciais)
15. [Equipa de Desenvolvimento](#15-equipa-de-desenvolvimento)

---

## 1. Visao Geral

Sistema multiplataforma para detecao de cyberbullying em texto, desenvolvido para o Instituto Superior Politecnico da Lunda-Sul (Saurimo, Angola). Combina uma interface **web** (Flask), uma aplicacao **desktop** (Tkinter) e um executavel autonomo (**EXE --onefile**) que partilham a mesma base de dados SQLite e o mesmo motor de detecao enriquecido com dicionario de girias regionais angolanas.

### 1.1 Funcionalidades Principais

| Funcionalidade | Descricao |
|---|---|
| Analise de texto em tempo real | Classifica como Critico / Ofensivo / Suspeito / Neutro |
| Dicionario alargado | 170+ palavras ofensivas + 80+ girias regionais angolanas (Lunda-Sul) |
| Classificacao por niveis | critico, alto, medio, baixo, neutro |
| Classificador BERT | distilbert-base-multilingual-cased como complemento ao motor rule-based |
| Alertas inteligentes | Threshold >= 50% de confianca (Suspeito+) |
| Notificacoes em tempo real | WebSockets (Flask-SocketIO) com notificacoes nativas no browser |
| Interface web e desktop | Mesma BD partilhada, mesma experiencia |
| Autenticacao RBAC | Login protegido com senhas hasheadas (bcrypt); papeis: admin / moderador |
| Auto-save | Toda analise e guardada automaticamente na BD |
| Exportacao de relatorios | CSV, TXT e PDF |
| Monitorizacao Facebook | Integracao com Graph API para monitorizar paginas |
| Testes automatizados | 15 testes pytest (detecao, API, autenticacao) |
| Executavel autonomo | EXE --onefile (PyInstaller) sem dependencias externas |
| Repositorio GitHub | https://github.com/24Anselmo/Cyber123 |

### 1.2 Tecnologias

| Componente | Tecnologia |
|---|---|
| Servidor web | Flask 3.0 + Flask-SocketIO |
| ORM | SQLAlchemy + SQLite (WAL mode) |
| Frontend | HTML5, CSS3, JavaScript (vanilla) |
| Interface desktop | Tkinter (Python) |
| Motor de detecao | Rule-based (dicionario + pesos) + BERT |
| Autenticacao | bcrypt (senhas hasheadas) |
| WebSockets | Flask-SocketIO + eventlet / threading |
| BERT | transformers + torch (distilbert-base-multilingual-cased) |
| PDF | fpdf2 |
| CORS | Flask-CORS |
| Testes | pytest |
| Empacotamento | PyInstaller (EXE --onefile / --onedir) |
| Repositorio | Git + GitHub |

---

## 2. Arquitetura do Sistema

### 2.1 Estrutura de Diretorios

```
cyberbullying_detector/
+-- app/                                # Aplicacao Web (Flask)
|   +-- __init__.py                     # Factory, BD, CORS, SocketIO, migracao
|   +-- models.py                       # Modelos SQLAlchemy
|   +-- routes.py                       # Endpoints REST + login + PDF
|   +-- detector.py                     # Motor de detecao (singleton rule-based)
|   +-- bert_classifier.py              # Classificador BERT (distilbert)
|   +-- facebook_api.py                 # Monitorizacao Facebook Graph API
|   +-- socket_events.py                # Eventos WebSocket
|   +-- static/
|   |   +-- css/style.css               # Estilos responsivos
|   |   +-- js/main.js                  # Logica frontend completa
|   |   +-- logo.png                    # Logotipo
|   +-- templates/
|       +-- index.html                  # Dashboard principal
|       +-- login.html                  # Pagina de autenticacao
+-- offline/                            # Aplicacao Desktop
|   +-- desktop_app.py                  # UI Tkinter
|   +-- logo.png                        # Logotipo desktop
|   +-- CyberbullyingDetector.spec      # Configuracao PyInstaller
|   +-- dist/
|       +-- CyberbullyingDetector.exe   # Executavel compilado
+-- data/                               # Dados persistentes
|   +-- cyberbullying.db                # Base de dados SQLite
|   +-- local_dictionary.json           # Dicionario local (80+ girias)
|   +-- debug.log                       # Log de diagnostico
+-- tests/                              # Testes automatizados
|   +-- conftest.py                     # Fixture BD temporario
|   +-- test_detector.py                # Testes do motor de detecao (6)
|   +-- test_api.py                     # Testes dos endpoints REST (6)
|   +-- test_auth.py                    # Testes de autenticacao (3)
+-- DOCUMENTACAO.html                   # Documentacao (HTML)
+-- DOCUMENTACAO.md                     # Documentacao (Markdown)
+-- README.md                           # Manual rapido
+-- README_SO.md                        # Comandos SO
+-- requirements.txt                    # Dependencias Python
+-- run.py                              # Ponto de entrada web
```

### 2.2 Fluxo de Funcionamento

```
                    +---------------------+
                    | Base de Dados SQLite  |
                    | data/cyberbullying.db |
                    +----------+----------+
                               |
              +----------------+----------------+
              |                |                |
              v                v                v
       +----------+     +------------+     +----------+
       |  Desktop  |<--->|  Servidor  |<--->|    Web    |
       | (Tkinter) |     | Web Flask  |     | (Browser) |
       |   .exe    |     | :5000      |     | localhost  |
       +----------+     +------------+     +----------+
```

- Desktop e Web partilham o mesmo ficheiro `cyberbullying.db`
- O EXE desktop abre o browser para o utilizador aceder a interface web
- Motor de detecao (`app/detector.py`) e o mesmo para ambas as interfaces
- Classificador BERT (`app/bert_classifier.py`) e opcional (lazy loading)
- Toda a analise e auto-salva na BD antes de ser exibida
- Notificacoes em tempo real via WebSockets (Flask-SocketIO)

### 2.3 Autenticacao e Sessao

- **Web**: sessao Flask armazenada em cookie assinado (`secret_key`)
- **Desktop**: login verificado localmente via SQLite com bcrypt; `user_id`, `nome` e `papel` passados ao construtor da app
- **Senhas**: armazenadas com hash bcrypt; migracao automatica de texto plano existente
- **Logout (web)**: `session.clear()` + redirect para `/login`
- **Logout (desktop)**: `root.destroy()` + `main()` (re-inicia ciclo de login)

---

## 3. Instalacao e Configuracao

### 3.1 Requisitos

- Windows 10/11 ou Linux (Ubuntu 22.04+)
- Python 3.10 ou superior
- pip (gestor de pacotes Python)
- Git (opcional, para clonar repositorio)

### 3.2 Obter o Projeto

```bash
git clone https://github.com/24Anselmo/Cyber123.git
cd cyberbullying_detector
```

### 3.3 Instalacao de Dependencias

```bash
pip install -r requirements.txt
```

Conteudo do `requirements.txt`:

```
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-CORS==4.0.0
Flask-SocketIO==5.6.1
bcrypt==5.0.0
scikit-learn==1.3.2
numpy==1.26.2
pandas==2.1.3
requests==2.31.0
python-dotenv==1.0.0
gunicorn==21.2.0
transformers>=4.30.0
torch>=2.0.0
eventlet>=0.41.0
fpdf2>=2.7.0
```

### 3.4 Execucao

**Modo Web (Servidor Flask):**
```bash
python run.py
# Acessar: http://localhost:5000
```

**Modo Desktop (Tkinter):**
```bash
cd offline
python desktop_app.py
```

**Executavel Compilado (Recomendado):**
Clique duas vezes em `offline/dist/CyberbullyingDetector.exe`.

### 3.5 Configuracao

| Variavel de Ambiente | Descricao | Padrao |
|---|---|---|
| `CYBERBULLYING_DB_PATH` | Caminho completo para a BD SQLite | `data/cyberbullying.db` |

Se a variavel nao for definida, o caminho e calculado automaticamente:
- **Script**: diretorio raiz do projeto + `/data/cyberbullying.db`
- **EXE**: procura recursivamente desde o diretorio do executavel ate a raiz

---

## 4. Guia de Utilizacao

### 4.1 Interface Web

Acesso: http://localhost:5000

**Barra lateral (sidebar):**

| Botao | Visivel para | Descricao |
|---|---|---|
| Analise | Todos | Inserir texto e classificar |
| Alertas | Todos | Alertas pendentes (>= 50% confianca) |
| Analises | Todos | Historico de analises |
| Fontes | Todos | Gerir fontes Facebook |
| Dicionario | Todos | Gerir girias locais |
| Usuarios | Admin | Gerir utilizadores |
| Relatorio | Admin | Estatisticas e exportacao (CSV, TXT, PDF) |
| Inicializar | Admin | Carregar dados iniciais |
| Importar Testes | Admin | Importar 10 comentarios de teste |
| Atualizar | Todos | Atualizar todos os dados |
| Minha Senha | Todos | Alterar propria senha |
| Sair | Todos | Terminar sessao |

**Pagina de Analise:**
1. Digite o texto na caixa de texto
2. Clique "Analisar" ou pressione `Ctrl+Enter`
3. Veja a classificacao, confianca, palavras e girias detetadas

**Pagina de Alertas:**
- Lista comentarios com confianca >= 50% ainda nao resolvidos
- Botao para resolver (marcar como revisto)
- Botao para copiar alerta para area de transferencia (report ao Facebook)
- Notificacoes nativas do browser ao receber novo alerta via WebSocket

**Relatorio PDF:**
- Na pagina Relatorio, clique "Baixar PDF" para descarregar um relatorio completo em PDF
- O PDF e gerado com fpdf2 e inclui todas as estatisticas do sistema

### 4.2 Interface Desktop

**Abas disponiveis (admin):**

| Aba | Descricao |
|---|---|
| Analise | Analisar texto com resultado detalhado |
| Alertas | Alertas pendentes com auto-refresh (5s) |
| Dicionario | Gerir girias e niveis |
| Fontes | Gerir fontes Facebook |
| Relatorio | Estatisticas e exportacao CSV/TXT |
| Usuarios | Gerir equipa (admin apenas) |

**Abas disponiveis (moderador):** Todas exceto Relatorio e Usuarios.

**Atalhos de teclado:**
- `Ctrl+Enter` — analisar texto rapidamente

### 4.3 Gestao de Utilizadores (Admin)

**Criar utilizador:**
1. Aba Usuarios -> botao "Novo Usuario"
2. Preencher Nome, Email, Senha, Papel (admin/moderador)
3. Clicar "Salvar"

**Alterar senha de outro utilizador:**
1. Aba Usuarios -> selecionar utilizador na lista
2. Clicar "Alterar Senha"
3. Escolher novo utilizador e nova senha

**Alterar propria senha:**
- Web: sidebar -> "Minha Senha"
- Desktop: barra de status -> "Alterar Senha"

**Remover utilizador:**
1. Aba Usuarios -> selecionar utilizador
2. Clicar "Remover"

---

## 5. API REST

Todas as rotas (exceto `/login` e `/logout`) requerem autenticacao por sessao. Rotas **Admin** requerem `papel='admin'`.

### 5.1 Autenticacao

| Metodo | Rota | Acesso | Descricao |
|---|---|---|---|
| GET | `/login` | Publico | Pagina de login |
| POST | `/login` | Publico | Autenticar (`username`, `password`) |
| GET | `/logout` | Publico | Terminar sessao |

### 5.2 Dashboard e Estatisticas

| Metodo | Rota | Acesso | Descricao |
|---|---|---|---|
| GET | `/` | Autenticado | Pagina principal (dashboard) |
| GET | `/api/estatisticas` | Autenticado | Estatisticas gerais do sistema |
| GET | `/api/alertas` | Autenticado | Alertas pendentes (confianca >= 50%, nao resolvidos) |
| GET | `/api/analises` | Autenticado | Ultimas 100 analises com detalhes |
| POST | `/api/analises/<id>/resolver` | Autenticado | Marcar analise como resolvida |

### 5.3 Comentarios

| Metodo | Rota | Acesso | Descricao |
|---|---|---|---|
| GET | `/api/comentarios` | Autenticado | Ultimos 100 comentarios |
| POST | `/api/comentarios` | Autenticado | Adicionar comentario + analise automatica |

### 5.4 Detecao

| Metodo | Rota | Acesso | Descricao |
|---|---|---|---|
| POST | `/api/detectar` | Autenticado | Analisar texto (`{"texto": "..."}`). Guarda na BD. |

### 5.5 Fontes

| Metodo | Rota | Acesso | Descricao |
|---|---|---|---|
| GET | `/api/fontes` | Autenticado | Listar fontes Facebook |
| POST | `/api/fontes` | Autenticado | Adicionar fonte |
| DELETE | `/api/fontes/<id>` | Admin | Remover fonte |

### 5.6 Dicionario

| Metodo | Rota | Acesso | Descricao |
|---|---|---|---|
| GET | `/api/dicionario` | Autenticado | Listar girias |
| POST | `/api/dicionario` | Autenticado | Adicionar giria |
| DELETE | `/api/dicionario/<id>` | Admin | Remover giria |

### 5.7 Utilizadores

| Metodo | Rota | Acesso | Descricao |
|---|---|---|---|
| GET | `/api/usuarios` | Autenticado | Listar utilizadores |
| POST | `/api/usuarios` | Admin | Criar utilizador |
| DELETE | `/api/usuarios/<id>` | Admin | Remover utilizador |
| POST | `/api/alterar-senha` | Admin | Alterar senha de outro |
| POST | `/api/minha-senha` | Autenticado | Alterar propria senha |

### 5.8 Utilitarios

| Metodo | Rota | Acesso | Descricao |
|---|---|---|---|
| GET | `/api/relatorio` | Admin | Relatorio completo |
| GET | `/api/relatorio/pdf` | Admin | Download do relatorio em PDF |
| POST | `/api/inicializar` | Admin | Carregar dados iniciais |
| POST | `/api/importar-comentarios` | Admin | Importar 10 comentarios de teste |

### 5.9 Exemplo de Analise

```bash
curl -X POST http://localhost:5000/api/detectar \
  -H "Content-Type: application/json" \
  -d '{"texto": "Vou te matar seu idiota"}'
```

Resposta:

```json
{
  "classificacao": "Critico",
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

## 6. Motor de Detecao

### 6.1 Arquitetura

O motor (`app/detector.py`) e um singleton baseado em regras (rule-based), partilhado entre web e desktop. Utiliza:

1. **Lista hardcoded**: 170+ palavras e expressoes ofensivas em portugues
2. **Dicionario local (`data/local_dictionary.json`)**: 80+ girias regionais angolanas carregadas dinamicamente
3. **Girias da BD (`girias_db`)**: girias adicionadas pelo utilizador
4. **Classificador BERT (`app/bert_classifier.py`)**: complemento opcional

### 6.2 Sistema de Pontuacao

| Fator | Pontos |
|---|---|
| Base (confianca inicial) | 5.0 |
| Por palavra/giria critica | +45 |
| Por palavra/giria alta | +25 |
| Por palavra/giria media | +15 |
| Por palavra/giria baixa | +8 |
| Bonus critico (se pelo menos 1 termo critico detetado) | +35 |
| MAIUSCULAS (>50% do texto em maiusculas) | +10 |
| Sinais de exclamacao/interrogacao | +2 cada (max. +10) |
| **Maximo** | **100** |

### 6.3 Thresholds de Classificacao

| Confianca | Classificacao | Alerta |
|---|---|---|
| >= 90% | Critico | Sim |
| >= 70% | Ofensivo | Sim |
| >= 50% | Suspeito | Sim |
| < 50% | Neutro | Nao |

### 6.4 Nivel de Gravidade

O `nivel_geral` e determinado pelo nivel mais alto entre todas as palavras e girias detetadas:

```
critico > alto > medio > baixo > neutro
```

### 6.5 Dicionario Local (JSON)

Ficheiro: `data/local_dictionary.json`

Contem 80+ girias regionais de Angola, organizadas por nivel de gravidade:

```json
{
  "girias": [
    {"termo": "kamba", "significado": "amigo", "nivel": "neutro"},
    {"termo": "mbora", "significado": "vamos embora", "nivel": "neutro"},
    {"termo": "safado", "significado": "descarado", "nivel": "alto"},
    {"termo": "muteta", "significado": "pessoa fraca", "nivel": "medio"}
  ]
}
```

As girias sao carregadas na BD na inicializacao (`/api/inicializar`), evitando INSERTs hardcoded.

---

## 7. Classificador BERT

### 7.1 Arquitetura

O `bert_classifier.py` implementa um classificador baseado no modelo `distilbert-base-multilingual-cased` da Hugging Face. Este modelo foi escolhido por:
- Suportar multiplos idiomas (incluindo portugues e misturas com linguas angolanas)
- Ser mais leve que o BERT completo (menos parametros, inferencia mais rapida)
- Nao necessitar de fine-tuning no cenario atual

### 7.2 Funcionamento

1. O modelo e carregado _lazy_ (apenas na primeira chamada a `classificar()`)
2. O texto e convertido em embeddings usando a saida `pooler_output` do modelo
3. A classificacao e feita por similaridade de cosseno entre o embedding do texto e embeddings de referencia pre-definidos (ofensivo, neutro)
4. Se o modelo nao carregar (ex.: sem torch/transformers instalados), faz fallback para Neutro com 0% de confianca

### 7.3 Integracao

O classificador BERT e chamado apos o motor rule-based. Se a confianca do BERT for superior a do motor rule-based, a classificacao final usa o resultado do BERT. Caso contrario, prevalece o resultado rule-based.

---

## 8. WebSockets e Notificacoes

### 8.1 Arquitetura

O sistema utiliza **Flask-SocketIO** para comunicacao em tempo real entre o servidor e os clientes web. O servidor emite eventos WebSocket sempre que um novo alerta e detetado ou resolvido.

### 8.2 Eventos

| Evento | Direcao | Descricao |
|---|---|---|
| `novo_alerta` | servidor -> cliente | Emitido quando uma analise nova atinge confianca >= 50% |
| `alerta_resolvido` | servidor -> cliente | Emitido quando um alerta e marcado como resolvido |

### 8.3 Notificacoes no Browser

O cliente JavaScript (`main.js`) escuta eventos SocketIO e exibe notificacoes nativas usando a API `Notification` do browser:

```javascript
socket.on('novo_alerta', function(alerta) {
    if (Notification.permission === 'granted') {
        new Notification('Alerta de Cyberbullying', {
            body: alerta.texto,
            icon: '/static/logo.png'
        });
    }
});
```

### 8.4 Async Mode

O SocketIO e configurado com `async_mode='threading'` para compatibilidade com o EXE congelado (eventlet falha em ambientes PyInstaller). Em execucao normal com `python run.py`, usa eventlet para melhor desempenho.

---

## 9. Base de Dados

### 9.1 Esquema

**Ficheiro:** `data/cyberbullying.db`
**Modo:** WAL (Write-Ahead Logging) para concorrencia
**Timeout:** 10 segundos (multiplas conexoes)

#### Tabela `usuarios`

| Coluna | Tipo | Descricao |
|---|---|---|
| `id` | INTEGER PK | Identificador unico |
| `nome` | TEXT | Nome do utilizador |
| `email` | TEXT | Email |
| `senha` | TEXT | Hash bcrypt da palavra-passe |
| `papel` | TEXT | 'admin' ou 'moderador' |
| `avatar` | TEXT | (reservado) |

#### Tabela `fontes`

| Coluna | Tipo | Descricao |
|---|---|---|
| `id` | INTEGER PK | Identificador unico |
| `url` | TEXT | URL da fonte (ex: grupo Facebook) |
| `nome` | TEXT | Nome da fonte |
| `tipo` | TEXT | Tipo de fonte ('API', 'manual') |
| `ativo` | INTEGER | 1=ativo, 0=inativo |

#### Tabela `comentarios`

| Coluna | Tipo | Descricao |
|---|---|---|
| `id` | INTEGER PK | Identificador unico |
| `fonte_id` | INTEGER FK | Referencia a fonte |
| `texto` | TEXT | Conteudo do comentario |
| `autor` | TEXT | Autor do comentario |
| `data` | TEXT | Data/hora ISO 8601 |

#### Tabela `analises`

| Coluna | Tipo | Descricao |
|---|---|---|
| `id` | INTEGER PK | Identificador unico |
| `comentario_id` | INTEGER FK | Referencia ao comentario |
| `classificacao` | TEXT | Critico/Ofensivo/Suspeito/Neutro |
| `confianca` | REAL | Percentagem de confianca (0-100) |
| `girias` | TEXT | Girias detetadas (separadas por virgula) |
| `resolvido` | INTEGER | 0=pendente, 1=resolvido |
| `data` | TEXT | Data/hora ISO 8601 |

#### Tabela `girias_db`

| Coluna | Tipo | Descricao |
|---|---|---|
| `id` | INTEGER PK | Identificador unico |
| `termo` | TEXT | Termo/giria |
| `significado` | TEXT | Significado |
| `tipo` | TEXT | 'ofensivo' ou 'neutro' |
| `nivel` | TEXT | Nivel de gravidade (critico/alto/medio/baixo/neutro) |

### 9.2 Dados Iniciais (Seed)

**Utilizadores:**

| Nome | Email | Senha (hash bcrypt) | Papel |
|---|---|---|---|
| Alberto Baptista | alberto@saurimo.ao | bcrypt de 240520 | admin |
| Augusta Mulungia | augusta@saurimo.ao | bcrypt de 1234 | moderador |
| Rafael Mussumari | rafael@saurimo.ao | bcrypt de 1234 | moderador |

**Fontes Facebook:** Juventude Saurimo, Lunda-Sul Geral
**Girias regionais:** 80+ termos lidos de `data/local_dictionary.json`

### 9.3 Migracao Automatica

Na primeira execucao, o sistema:
1. Cria as tabelas se nao existirem
2. Adiciona colunas em falta (migracao segura com tratamento de erros)
3. Migra senhas em texto plano para bcrypt automaticamente
4. Atualiza o utilizador admin para "Alberto Baptista" / "240520"
5. Remove duplicados do utilizador admin antigo

---

## 10. Gestao de Utilizadores e Permissoes

### 10.1 Papeis (Roles)

| Papel | Acesso |
|---|---|
| `admin` | Todas as funcionalidades, incluindo gestao de utilizadores, relatorios, inicializacao, exportacao PDF |
| `moderador` | Analise, alertas, analises, fontes, dicionario, alterar propria senha |

### 10.2 Controlo de Acesso

**Web (JavaScript):** Elementos com atributo `data-admin` sao ocultados para moderadores.

**Web (Python decorators):**
```python
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('papel') != 'admin':
            return jsonify({'erro': 'Acesso negado'}), 403
        return f(*args, **kwargs)
    return decorated
```

**Desktop:** Abas de Relatorio e Usuarios sao adicionadas apenas se `self.papel == 'admin'`.

### 10.3 Seguranca

- **Senhas com bcrypt**: hasheadas com custo 12; migracao automatica de texto plano existente
- **Offline-first**: o sistema funciona 100% offline (localhost)
- **Servidor web**: bind a `0.0.0.0:5000` — acessivel apenas na rede local
- **Chave secreta**: definida no codigo (`SECRET_KEY`) — adequado para ambiente academico controlado

---

## 11. Testes Automatizados

### 11.1 Estrutura

Os testes estao em `tests/` e utilizam pytest com uma fixture de BD temporaria (`conftest.py`):

```bash
python -m pytest tests/ -v
```

### 11.2 Testes do Motor de Detecao (`test_detector.py`)

| Teste | Descricao |
|---|---|
| `test_texto_neutro` | Texto normal -> Neutro com < 50% confianca |
| `test_texto_critico` | Ameaca direta -> Critico com > 90% confianca |
| `test_texto_ofensivo` | Palavrao grave -> Ofensivo com > 70% confianca |
| `test_texto_suspeito` | Palavra media -> Suspeito com > 50% confianca |
| `test_girias_detetadas` | Girias regionais sao detetadas corretamente |
| `test_maiusculas` | Texto em MAIUSCULAS ganha bonus de +10 |

### 11.3 Testes da API (`test_api.py`)

| Teste | Descricao |
|---|---|
| `test_login` | Login valido retorna 200 e redireciona |
| `test_detectar` | API de detecao retorna classificacao correta |
| `test_alertas` | Endpoint de alertas retorna lista |
| `test_fontes` | CRUD de fontes funciona |
| `test_dicionario` | CRUD de girias funciona |
| `test_inicializar` | Seed data carrega sem erros |

### 11.4 Testes de Autenticacao (`test_auth.py`)

| Teste | Descricao |
|---|---|
| `test_login_valido` | Credenciais corretas -> sessao criada |
| `test_login_invalido` | Senha errada -> 401 |
| `test_logout` | Logout limpa sessao e redireciona |

---

## 12. Empacotamento (EXE)

### 12.1 Construir o Executavel (--onefile)

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

**Tempo de compilacao:** ~1-2 minutos (--onefile), ~35 segundos (--onedir)

### 12.2 Hidden Imports

Os seguintes modulos sao explicitamente incluidos para evitar erros em tempo de execucao no EXE compilado:
- `flask_cors`, `flask_socketio`, `flask_sqlalchemy`
- `bcrypt`, `fpdf2`, `eventlet`, `numpy`, `requests`
- `sqlalchemy`, `jinja2`, `markupsafe`, `itsdangerous`
- `werkzeug`, `click`, `flask`
- `tkinter`, `tkinter.ttk`, `tkinter.messagebox`, `tkinter.filedialog`

### 12.3 Variaveis TCL_LIBRARY / TK_LIBRARY

Estas variaveis de ambiente sao **obrigatorias** no Python 3.14 + PyInstaller para evitar o erro:

```
FileNotFoundError: Tcl data directory "..._internal\_tcl_data" not found.
```

Apontam para os diretorios Tcl/Tk dentro da instalacao Python.

### 12.4 Executavel Compilado

**Localizacao:** `offline/dist/CyberbullyingDetector.exe` (35 MB)
**Modo:** --noconsole (sem janela de terminal)

Na primeira execucao, cria a BD partilhada no diretorio do projeto (procura recursivamente por `data/cyberbullying.db`).

---

## 13. Manutencao e Resolucao de Problemas

### 13.1 Log de Diagnostico

O sistema escreve para `data/debug.log`:
- Estado da BD antes/depois da migracao
- Tentativas de login (utilizador, senha, resultado)
- Erros de conexao a BD
- Diagnostico automatico ao iniciar

### 13.2 Problemas Comuns

| Problema | Causa Provavel | Solucao |
|---|---|---|
| "Usuario ou senha invalidos" | BD corrompida ou migracao incompleta | Apagar `data/cyberbullying.db` e reiniciar |
| "Database is locked" | Concorrencia entre web e desktop | Aguardar ou reiniciar. WAL mode + timeout 10s |
| Servidor web nao inicia | Porta 5000 ocupada | Fechar outras instancias do Flask |
| EXE nao abre | TCL_LIBRARY nao definido na compilacao | Recompilar com as variaveis de ambiente Tcl/Tk |
| Login falha apos logout (desktop) | Thread do servidor web ainda ativa | Fechar completamente o EXE e reabrir |
| Invalid async_mode specified | eventlet incompativel com EXE congelado | Usar `async_mode='threading'` no SocketIO() |
| Modulo nao encontrado no EXE | Hidden import em falta | Adicionar `--hidden-import` ao PyInstaller |

### 13.3 Reset Completo

```bash
# Apagar base de dados
rm data/cyberbullying.db

# Apagar log
rm data/debug.log

# Reiniciar
python run.py
```

Na primeira execucao, o sistema recria a BD e insere os dados iniciais automaticamente.

### 13.4 Verificacao de Integridade

No desktop, o diagnostico automatico corre ao iniciar e regista no log:
- Caminho da BD
- Se o ficheiro existe
- Numero de analises, comentarios e alertas
- Ultimas 5 analises

---

## 14. Credenciais

| Sistema | Utilizador | Senha | Papel |
|---|---|---|---|
| Admin | Alberto Baptista | 240520 | admin |
| Moderador | Augusta Mulungia | 1234 | moderador |
| Moderador | Rafael Mussumari | 1234 | moderador |

As senhas sao armazenadas com hash bcrypt. Na primeira execucao, senhas em texto plano sao migradas automaticamente.

**Repositorio GitHub:** https://github.com/24Anselmo/Cyber123

---

## 15. Equipa de Desenvolvimento

**Disciplina:** PP1 — Engenharia de Software I + Sistemas Operacionais

| Membro | Papel no Projeto |
|---|---|
| Alberto Baptista | Desenvolvedor principal |
| Augusta Mulungia | Documentacao e testes |
| Rafael Mussumari | Interface e validacao |

**Instituicao:** Instituto Superior Politecnico da Lunda-Sul (IPLS)
**Localizacao:** Saurimo, Angola
**Ano Letivo:** 2026

---

*Documentacao gerada em Junho de 2026. Para mais informacoes, contactar a equipa de desenvolvimento ou consultar o repositorio GitHub.*
