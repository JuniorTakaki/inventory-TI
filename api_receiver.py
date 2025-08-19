import sqlite3
import json
from flask import Flask, request, jsonify

app = Flask(__name__)
DB_FILE = 'inventory.db'

def init_db():
    """Cria a tabela no banco de dados se ela não existir."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            hostname TEXT PRIMARY KEY,
            id_patrimonio TEXT,
            serial_number TEXT,
            device_model TEXT,
            fabricante TEXT,
            data_compra TEXT,
            fornecedor TEXT,
            custo REAL,
            garantia_venc TEXT,
            local_fisico TEXT,
            centro_custo TEXT,
            usuario_designado TEXT,
            departamento TEXT,
            status TEXT,
            ultima_manutencao TEXT,
            os TEXT,
            architecture TEXT,
            cpu_model TEXT,
            cpu_cores_physical INTEGER,
            cpu_cores_logical INTEGER,
            ram_total_gb REAL,
            ram_slots TEXT,
            mac_address TEXT,
            ip_address TEXT,
            last_updated TEXT,
            disks TEXT,
            storage_health TEXT,
            gpu_info TEXT,
            windows_update_status TEXT,
            installed_software TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/api/inventory', methods=['POST'])
def receive_inventory():
    """Endpoint para receber e salvar dados de inventário."""
    data = request.json

    if not data or 'hostname' not in data:
        return jsonify({"status": "error", "message": "Dados inválidos ou hostname ausente"}), 400

    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        disks_json = json.dumps(data.get('disks', []))

        # INSERT OR REPLACE é a mágica aqui: atualiza o registro se o hostname já existir.
        cursor.execute('''
            INSERT OR REPLACE INTO assets (
                hostname, id_patrimonio, serial_number, device_model, fabricante, data_compra, fornecedor, custo, garantia_venc,
                local_fisico, centro_custo, usuario_designado, departamento, status, ultima_manutencao,
                os, architecture, cpu_model, cpu_cores_physical, cpu_cores_logical, ram_total_gb, ram_slots,
                mac_address, ip_address, last_updated, disks, storage_health, gpu_info, windows_update_status, installed_software
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('hostname'), data.get('id_patrimonio'), data.get('serial_number'), data.get('device_model'), data.get('fabricante'),
            data.get('data_compra'), data.get('fornecedor'), data.get('custo'), data.get('garantia_venc'),
            data.get('local_fisico'), data.get('centro_custo'), data.get('usuario_designado'), data.get('departamento'), data.get('status'), data.get('ultima_manutencao'),
            data.get('os'), data.get('architecture'), data.get('cpu_model'), data.get('cpu_cores_physical'), data.get('cpu_cores_logical'),
            data.get('ram_total_gb'), data.get('ram_slots'), data.get('mac_address'), data.get('ip_address'), data.get('last_updated'),
            disks_json, data.get('storage_health'), data.get('gpu_info'), data.get('windows_update_status'), data.get('installed_software')
        ))
        
        conn.commit()
        conn.close()
        
        print(f"Dados recebidos e salvos do host: {data.get('hostname')}")
        return jsonify({"status": "success", "message": f"Dados do host {data.get('hostname')} salvos."}), 200
        
    except Exception as e:
        import traceback
        print(f"\n!!! ERRO INTERNO DETALHADO !!!")
        print(f"Tipo de Erro: {type(e).__name__}")
        print(f"Mensagem: {e}")
        print("--- Traceback Completo ---")
        traceback.print_exc() # Imprime o rastreamento completo do erro
        print("--- Dados Brutos Recebidos ---")
        # Imprime os dados exatos que causaram o problema
        print(request.data.decode('utf-8'))
        print("!!! FIM DO RELATÓRIO DE ERRO !!!\n")

        return jsonify({"status": "error", "message": "Erro interno do servidor"}), 500

@app.route('/api/support_status', methods=['GET'])
def support_status():
    """Consulta se o serial informado tem suporte (mock)."""
    serial = request.args.get('serial')
    # Exemplo: lógica real seria consultar um sistema externo
    if not serial:
        return jsonify({"status": "error", "message": "Serial não informado"}), 400
    # Simulação: se serial termina com número par, tem suporte
    if serial[-1].isdigit() and int(serial[-1]) % 2 == 0:
        return jsonify({"serial": serial, "suporte": True, "mensagem": "Este ativo ainda possui suporte."})
    else:
        return jsonify({"serial": serial, "suporte": False, "mensagem": "Este ativo não possui mais suporte."})

if __name__ == '__main__':
    init_db()
    # '0.0.0.0' faz o servidor ser acessível por outras máquinas na mesma rede
    app.run(host='0.0.0.0', port=5000, debug=True)