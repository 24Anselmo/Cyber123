# 🛡️ Sistema de Deteção de Cyberbullying

**Instituto Superior Politécnico da Lunda-Sul — Saurimo, Angola**

Sistema multiplataforma para deteção de cyberbullying em texto, com interface **web** (Flask) e **desktop** (Tkinter). Utiliza um dicionário enriquecido de palavras ofensivas e gírias locais angolanas (Lunda-Sul), com classificação por níveis de gravidade.

---

## Funcionalidades

- **Análise de texto em tempo real** — classifica como Crítico / Ofensivo / Suspeito / Neutro
- **Classificação por níveis** — crítico 🔴, alto 🟠, médio 🟡, baixo 🟤, neutro ⚪
- **Dicionário local** — 170+ palavras ofensivas + 40+ gírias regionais (dialetos da Lunda-Sul)
- **Alertas inteligentes** — threshold ≥ 50% de confiança
- **Painel web** — sidebar com páginas: Análise, Alertas, Análises, Fontes, Dicionário, Usuários, Relatório
- **Aplicação desktop** — interface Tkinter com as mesmas funcionalidades
- **BD partilhado** — web e desktop escrevem na mesma base SQLite
- **Auto-save** — toda análise é guardada automaticamente
- **Exportação** — relatórios em CSV e TXT
- **Report ao Facebook** — cópia do alerta para área de transferência
- **Autenticação** — login protegido (web e desktop)
- **Logótipo personalizado** — exibido em ambos os programas

---

## Arquitetura

```
cyberbullying_detector/
├── app/                          # Aplicação Web (Flask)
│   ├── __init__.py               # Factory, BD, CORS
│   ├── models.py                 # Modelos SQLAlchemy
│   ├── routes.py                 # Endpoints REST + login
│   ├── detector.py               # Motor de deteção
│   ├── static/
│   │   ├── css/style.css         # Estilos web
│   │   ├── js/main.js            # Lógica frontend
│   │   └── logo.png              # Logótipo web
│   └── templates/
│       ├── index.html            # Dashboard web
│       └── login.html            # Página de login
├── offline/                      # Aplicação Desktop (Tkinter)
│   ├── desktop_app.py             # UI desktop + servidor web embutido
│   ├── logo.png                  # Logótipo desktop
│   ├── iniciar.bat               # Atalho Windows
│   ├── CyberbullyingDetector.spec # Configuração PyInstaller
│   └── dist/
│       └── CyberbullyingDetector.exe   # Executável compilado
├── data/
│   ├── cyberbullying.db          # Base de dados SQLite partilhada
│   ├── local_dictionary.json     # Dicionário local (fallback)
│   └── debug.log                 # Log de diagnóstico
├── DOCUMENTACAO.md               # Documentação completa
├── requirements.txt              # Dependências Python
└── run.py                        # Ponto de entrada web
```

---

## Tecnologias

| Componente    | Tecnologia                    |
|---------------|-------------------------------|
| Web server    | Flask 3.0                     |
| ORM           | SQLAlchemy + SQLite           |
| Frontend      | HTML, CSS, JavaScript (vanilla) |
| Desktop       | Tkinter (Python)              |
| Deteção       | Rule-based (dicionário+pesos) |
| CORS          | Flask-CORS                    |
| Empacotamento | PyInstaller (EXE)             |

---

## Instalação

### 1. Requisitos

- Python 3.10+
- pip

### 2. Clonar ou extrair o projeto

```bash
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

#### Modo desktop (Tkinter + web server embutido)

```bash
cd offline
python desktop_app.py
# Login: Alberto Baptista / 240520
# Web server: http://localhost:5000
```

#### Executável compilado

```bash
offline/dist/CyberbullyingDetector.exe
```

Ou clicar duas vezes no ficheiro.

---

## API REST

Todas as rotas requerem autenticação por sessão (login via `/login`). Retornam 401 se não autenticado.

| Método | Rota                              | Descrição                          |
|--------|-----------------------------------|------------------------------------|
| GET    | `/`                               | Página principal (dashboard)       |
| GET    | `/login`                          | Página de login                    |
| POST   | `/login`                          | Autenticar (Alberto Baptista / 240520) |
| GET    | `/logout`                         | Terminar sessão                    |
| GET    | `/api/estatisticas`               | Estatísticas gerais                |
| GET    | `/api/alertas`                    | Alertas pendentes (confiança ≥ 50) |
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
| GET    | `/api/relatorio`                  | Relatório com estatísticas         |
| POST   | `/api/inicializar`                | Carregar dados iniciais            |
| POST   | `/api/importar-comentarios`       | Importar comentários de teste      |

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

### Pontuação

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
| ≥ 90%     | Crítico       |
| ≥ 70%     | Ofensivo      |
| ≥ 50%     | Suspeito      |
| < 50%     | Neutro        |

Alertas são gerados para confiança **≥ 50%** (Suspeito+).

---

## Base de Dados

Ficheiro: `data/cyberbullying.db`

### Tabelas

| Tabela         | Colunas                                              |
|----------------|------------------------------------------------------|
| `usuarios`     | id, nome, email, senha, papel, avatar                |
| `fontes`       | id, url, nome, tipo, ativo                           |
| `comentarios`  | id, fonte_id (FK), texto, autor, data                |
| `analises`     | id, comentario_id (FK), classificacao, confianca, girias, resolvido, data |
| `girias_db`    | id, termo, significado, tipo, nivel                  |

---

## Desktop (Tkinter)

### Abas

1. **🔍 Análise** — inserir texto, ver resultado com detalhes
2. **🚨 Alertas** — lista de alertas pendentes, resolver, reportar Facebook
3. **📚 Dicionário** — gerir gírias locais
4. **📰 Fontes** — gerir fontes Facebook
5. **📊 Relatório** — estatísticas, exportar CSV/TXT
6. **👥 Usuários** — equipa do projeto

### Atalhos

- `Ctrl+Enter` — analisar texto rapidamente

---

## Logótipo

O logótipo (`logo.png`) é exibido em:

- Web: navbar + favicon + página de login
- Desktop: ecrã de login + header + ícone da janela

---

## Empacotamento (EXE)

Para reconstruir o executável:

```bash
cd offline
py -m PyInstaller --onefile --windowed --name CyberbullyingDetector ^
  --add-data "..\app;app" ^
  --add-data "logo.png;." ^
  --add-data "..\data\local_dictionary.json;data" ^
  desktop_app.py
```

---

## Credenciais

| Utilizador        | Senha  | Papel     |
|-------------------|--------|-----------|
| Alberto Baptista  | 240520 | admin     |
| Augusta Mulungia  | 1234   | moderador |
| Rafael Mussumari  | 1234   | moderador |

---

## Desenvolvido por

**PP1 — Engenharia de Software I + Sistemas Operacionais**

- Alberto Baptista
- Augusta Mulungia
- Rafael Mussumari

**IPLS — Instituto Superior Politécnico da Lunda-Sul**
**Saurimo, Angola — 2026**
