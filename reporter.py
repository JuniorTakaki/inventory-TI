import sqlite3
import json

def view_inventory():
    """Conecta ao banco de dados e exibe o inventário de forma organizada."""
    try:
        conn = sqlite3.connect('inventory.db')
        conn.row_factory = sqlite3.Row 
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM assets ORDER BY hostname")
        
        assets = cursor.fetchall()

        if not assets:
            print("Nenhum ativo encontrado no inventário.")
            return

        print("=" * 110)
        print("||" + "INVENTÁRIO DE ATIVOS DE TI".center(106) + "||")
        print("=" * 110)
        
        for asset in assets:
            print(f"Hostname: {asset['hostname']}")
            # Exibe modelo do aparelho de forma segura
            print(f"  - Modelo: {asset['device_model'] if 'device_model' in asset.keys() else 'Desconhecido'}")
            print(f"  - SO: {asset['os']} ({asset['architecture']})")
            print(f"  - IP: {asset['ip_address']:<15} | MAC: {asset['mac_address']}")
            
            # --- LINHA MODIFICADA ---
            # Adicionado o 'cpu_model' que já estava sendo salvo no banco de dados.
            print(f"  - CPU: {asset['cpu_model']} ({asset['cpu_cores_physical']} Cores Físicos / {asset['cpu_cores_logical']} Threads)")
            
            print(f"  - RAM Total: {asset['ram_total_gb']} GB")
            print(f"  - Última Atualização: {asset['last_updated']}")
            
            disks_data = json.loads(asset['disks'])
            if disks_data:
                print("  - Discos:")
                for disk in disks_data:
                    print(f"    - {disk['mountpoint']} {disk['total_gb']:.2f} GB (Usado: {disk['used_gb']:.2f} GB - {disk['percent_used']}%)")
            
            print("-" * 110)
            
        conn.close()

    except sqlite3.Error as e:
        print(f"Erro ao acessar o banco de dados: {e}")
    except FileNotFoundError:
        print("Erro: O arquivo de banco de dados 'inventory.db' não foi encontrado.")

if __name__ == "__main__":
    view_inventory()