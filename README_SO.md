# ============================================
# SISTEMA DE DETEÇÃO DE CYBERBULLYING
# MVP - PP1 Engenharia de Software + SO
# Instituto Superior Politécnico da Lunda-Sul
# ============================================

# Estrutura do Projeto:
# cyberbullying_detector/
# ├── app/
# │   ├── __init__.py           # Inicializacao Flask + SocketIO
# │   ├── models.py             # Modelos SQLAlchemy
# │   ├── routes.py             # Endpoints REST + login + PDF
# │   ├── detector.py           # Motor de deteccao rule-based
# │   ├── bert_classifier.py    # Classificador BERT (distilbert)
# │   ├── facebook_api.py       # Monitorizacao Facebook Graph API
# │   ├── socket_events.py      # Eventos WebSocket
# │   ├── static/
# │   │   ├── css/style.css
# │   │   ├── js/main.js
# │   │   └── logo.png
# │   └── templates/
# │       ├── index.html
# │       └── login.html
# ├── offline/
# │   ├── desktop_app.py        # UI Tkinter
# │   ├── logo.png
# │   ├── CyberbullyingDetector.spec
# │   └── dist/
# │       └── CyberbullyingDetector.exe
# ├── data/
# │   ├── cyberbullying.db      # Banco SQLite (gerado)
# │   └── local_dictionary.json # 80+ girias regionais
# ├── tests/
# │   ├── conftest.py
# │   ├── test_detector.py
# │   ├── test_api.py
# │   └── test_auth.py
# ├── requirements.txt
# └── run.py                    # Ponto de entrada web

# ============================================
# COMANDOS DE TERMINAL (Ubuntu/Linux)
# ============================================

# 1. Navegacao e organizacao de arquivos:
cd ~/cyberbullying_detector          # Entrar no diretorio do projeto
ls -la                                # Listar arquivos com detalhes
pwd                                   # Mostrar diretorio atual
tree -L 2                             # Mostrar arvore de diretorios

# 2. Permissoes e execucao:
chmod +x run.py                       # Dar permissao de execucao
python3 run.py                        # Executar aplicacao web
python3 offline/desktop_app.py        # Executar aplicacao desktop
python3 -m pytest tests/ -v           # Executar testes

# 3. Instalar dependencias:
pip3 install -r requirements.txt     # Instalar dependencias
python3 -m pip install --upgrade pip  # Atualizar pip

# 4. Git e controle de versao:
git init                              # Inicializar repositorio
git add .                             # Adicionar arquivos
git commit -m "Mensagem"              # Criar commit
git status                            # Verificar estado
git log --oneline                     # Ver historico
git remote add origin <url>           # Adicionar remote
git push -u origin main               # Publicar

# 5. Ativar ambiente virtual (opcional):
python3 -m venv venv
source venv/bin/activate

# ============================================
# INSTALACAO NO UBUNTU/DEBIAN
# ============================================

# sudo apt update
# sudo apt install python3 python3-pip git
# cd ~/cyberbullying_detector
# pip3 install -r requirements.txt
# python3 run.py
# Acessar: http://localhost:5000
# Login: Alberto Baptista / 240520

# ============================================
# COMANDOS WINDOWS (PowerShell)
# ============================================

# Executar aplicacao web:
python run.py
# Acessar: http://localhost:5000

# Executar aplicacao desktop:
cd offline
python desktop_app.py

# Executar testes:
python -m pytest tests/ -v

# Instalar dependencias:
pip install -r requirements.txt

# Construir EXE (--onefile):
$env:TCL_LIBRARY = "C:\caminho\para\python\tcl\tcl8.6"
$env:TK_LIBRARY = "C:\caminho\para\python\tcl\tk8.6"
cd offline
py -m PyInstaller --onefile --noconsole --name CyberbullyingDetector `
  --add-data "..\app;app" `
  --add-data "..\data\local_dictionary.json;data" `
  --add-data "logo.png;." `
  --collect-all flask_sqlalchemy `
  desktop_app.py

# Git no Windows:
git add .
git commit -m "Mensagem"
git push -u origin main

# Listar arquivos:
dir /s /b
