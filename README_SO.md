# ============================================
# SISTEMA DE DETEÇÃO DE CYBERBULLYING
# MVP - PP1 Engenharia de Software + SO
# Instituto Superior Politécnico da Lunda-Sul
# ============================================

# Estrutura do Projeto:
# cyberbullying_detector/
# ├── app/
# │   ├── __init__.py       # Inicialização da aplicação Flask
# │   ├── models.py         # Modelos de banco de dados
# │   ├── routes.py         # Endpoints da API REST
# │   ├── detector.py       # Lógica de detecção de cyberbullying
# │   ├── static/
# │   │   ├── css/
# │   │   │   └── style.css
# │   │   └── js/
# │   │       └── main.js
# │   └── templates/
# │       └── index.html
# ├── data/
# │   ├── cyberbullying.db  # Banco SQLite (gerado)
# │   └── local_dictionary.json
# ├── models/               #预留 para modelos de IA
# ├── utils/                #预留 para utilitários
# ├── requirements.txt
# └── run.py                # Ponto de entrada
#
# data/                     # Dados运行时
# reports/                  # Relatórios gerados

# ============================================
# COMANDOS DE TERMINAL (Ubuntu/Linux)
# ============================================

# 1. Navegação e organização de arquivos:
# cd ~/cyberbullying_detector          # Entrar no diretório do projeto
# ls -la                                # Listar arquivos com detalhes
# pwd                                   # Mostrar diretório atual
# mkdir data reports                    # Criar diretórios
# tree -L 2                             # Mostrar árvore de diretórios

# 2. Permissões e execução:
# chmod +x run.py                       # Dar permissão de execução
# python3 run.py                        # Executar aplicação
# pip3 install -r requirements.txt     # Instalar dependências

# 3. Git e controle de versão:
# git init                              # Inicializar repositório
# git add .                             # Adicionar arquivos
# git commit -m "MVP Cyberbullying"     # Criar commit
# git status                            # Verificar estado

# 4. Docker (opcional):
# docker build -t cyberbullying-mvp .   # Construir imagem
# docker run -p 5000:5000 cyberbullying-mvp

# ============================================
# INSTALAÇÃO NO UBUNTU/DEBIAN
# ============================================

# sudo apt update
# sudo apt install python3 python3-pip git
# cd ~/cyberbullying_detector
# pip3 install -r requirements.txt
# python3 run.py

# ============================================
# COMANDOS WINDOWS (PowerShell)
# ============================================

# python run.py                        # Executar aplicação
# pip install -r requirements.txt     # Instalar dependências
# dir                                  # Listar arquivos
# cd cyberbullying_detector            # Navegar
