import os
import sys

# Tenta usar a mesma BD que o EXE (offline/dist/data/) se existir,
# senão usa project_root/data/ (modo script).
_exe_db = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                       'offline', 'dist', 'data', 'cyberbullying.db')
if os.path.exists(_exe_db):
    os.environ['CYBERBULLYING_DB_PATH'] = _exe_db

from app import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("  SISTEMA DE DETEÇÃO DE CYBERBULLYING - MVP")
    print("  Saurimo, Angola - 2026")
    print("=" * 60)
    print("\nIniciando servidor...")
    print("Acesse: http://localhost:5000")
    print("API: http://localhost:5000/api/estatisticas")
    print("\nPara testar a detecção:")
    print("  curl -X POST http://localhost:5000/api/detectar -H 'Content-Type: application/json' -d '{\"texto\":\"Seu texto aqui\"}'")
    print("\n" + "=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
