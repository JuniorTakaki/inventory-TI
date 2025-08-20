import sqlite3
import sys

DB_FILE = 'inventory.db'

try:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Verifica se a tabela 'assets' tem pelo menos uma linha
    cursor.execute("SELECT COUNT(*) FROM assets")
    count = cursor.fetchone()[0]

    conn.close()

    if count > 0:
        print(f"SUCESSO: {count} registro(s) encontrado(s) no banco de dados.")
        sys.exit(0)  # Saída com sucesso
    else:
        print("ERRO: Nenhum registro foi encontrado no banco de dados.")
        sys.exit(1)  # Saída com erro

except Exception as e:
    print(f"ERRO ao verificar o banco de dados: {e}")
    sys.exit(1)  # Saída com erro
