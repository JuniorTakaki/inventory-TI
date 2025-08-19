import platform
import psutil
import socket
import uuid
import re
import json
import requests
import datetime
import subprocess
import os
import getpass
try:
    import wmi
except ImportError:
    wmi = None


API_URL = "http://127.0.0.1:5000/api/inventory"

def get_device_model():
    """Obtém o modelo do aparelho (ex: Dell Latitude, Lenovo ThinkPad)."""
    uname = platform.uname()
    if uname.system == "Windows" and wmi:
        try:
            c = wmi.WMI()
            cs = c.Win32_ComputerSystem()[0]
            manufacturer = cs.Manufacturer.strip()
            model = cs.Model.strip()
            return f"{manufacturer} {model}"
        except Exception:
            return "Desconhecido"
    elif uname.system == "Linux":
        try:
            with open("/sys/class/dmi/id/sys_vendor", "r") as f:
                manufacturer = f.read().strip()
            with open("/sys/class/dmi/id/product_name", "r") as f:
                model = f.read().strip()
            return f"{manufacturer} {model}"
        except Exception:
            return "Desconhecido"
    else:
        return "Desconhecido"

def get_serial_number():
    """Obtém o número de série do dispositivo."""
    try:
        if platform.system() == "Windows" and wmi:
            c = wmi.WMI()
            bios = c.Win32_BIOS()[0]
            return bios.SerialNumber.strip()
        elif platform.system() == "Linux":
            try:
                with open("/sys/class/dmi/id/product_serial", "r") as f:
                    return f.read().strip()
            except Exception:
                return "Desconhecido"
        else:
            return "Desconhecido"
    except Exception:
        return "Desconhecido"

def get_ram_slots():
    """Obtém informações sobre os slots de RAM."""
    try:
        if platform.system() == "Windows" and wmi:
            c = wmi.WMI()
            slots = c.Win32_PhysicalMemory()
            return f"{len(slots)} slots ocupados"
        elif platform.system() == "Linux":
            try:
                output = subprocess.check_output("dmidecode -t memory | grep -i 'Locator'", shell=True).decode()
                slots = [line for line in output.splitlines() if line.strip()]
                return f"{len(slots)} slots ocupados"
            except Exception:
                return "Desconhecido"
        else:
            return "Não disponível"
    except Exception:
        return "Desconhecido"

def get_installed_software():
    try:
        if platform.system() == "Windows":
            try:
                output = subprocess.check_output(
                    'powershell -Command "Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | Select-Object DisplayName | Format-Table -HideTableHeaders"',
                    shell=True
                ).decode(errors='ignore')
                lines = [line.strip() for line in output.splitlines() if line.strip()]
                return "; ".join(lines[:20]) + (" ..." if len(lines) > 20 else "") if lines else "Nenhum"
            except Exception:
                return "Não disponível"
        elif platform.system() == "Linux":
            try:
                output = subprocess.check_output("dpkg-query -W -f='${binary:Package}\n'", shell=True).decode()
                lines = [line.strip() for line in output.splitlines() if line.strip()]
                return "; ".join(lines[:20]) + (" ..." if len(lines) > 20 else "") if lines else "Nenhum"
            except Exception:
                return "Não disponível"
        else:
            return "Não disponível"
    except Exception:
        return "Desconhecido"

def get_storage_health():
    """Retorna informações básicas sobre saúde do armazenamento (apenas exemplo simplificado)."""
    try:
        if platform.system() == "Windows" and wmi:
            c = wmi.WMI()
            disks = c.Win32_DiskDrive()
            health = []
            for d in disks:
                status = getattr(d, 'Status', 'Desconhecido')
                health.append(f"{d.Model.strip()}: {status}")
            return "; ".join(health) if health else "Desconhecido"
        elif platform.system() == "Linux":
            # Exemplo: tenta smartctl se disponível
            try:
                output = subprocess.check_output(['which', 'smartctl']).decode().strip()
                if output:
                    result = subprocess.check_output(['sudo', 'smartctl', '-H', '/dev/sda']).decode()
                    for line in result.splitlines():
                        if "SMART overall-health self-assessment test result" in line:
                            return line.split(":")[-1].strip()
                    return "Sem informação SMART"
                else:
                    return "smartctl não instalado"
            except Exception:
                return "Desconhecido"
        else:
            return "Desconhecido"
    except Exception:
        return "Desconhecido"

def get_gpu_info():
    """Retorna informações sobre GPU instalada."""
    try:
        if platform.system() == "Windows" and wmi:
            c = wmi.WMI()
            gpus = c.Win32_VideoController()
            return "; ".join([g.Name for g in gpus]) if gpus else "Nenhuma GPU detectada"
        elif platform.system() == "Linux":
            try:
                output = subprocess.check_output("lspci | grep VGA", shell=True).decode()
                return output.strip() if output else "Nenhuma GPU detectada"
            except Exception:
                return "Desconhecido"
        else:
            return "Desconhecido"
    except Exception:
        return "Desconhecido"

def get_windows_update_status():
    """Retorna status do Windows Update (apenas Windows)."""
    try:
        if platform.system() == "Windows" and wmi:
            c = wmi.WMI(namespace='root\\cimv2')
            wu = c.Win32_QuickFixEngineering()
            updates = [u.Description for u in wu if hasattr(u, 'Description')]
            return f"{len(updates)} atualizações instaladas" if updates else "Nenhuma atualização encontrada"
        else:
            return "Não aplicável"
    except Exception:
        return "Desconhecido"

def get_inventory_data():
    """Coleta dados de hardware e software da máquina local usando os melhores métodos."""
    data = {}
    uname = platform.uname()
    data['hostname'] = uname.node
    data['id_patrimonio'] = ""  # Preencha manualmente ou via input/config
    data['serial_number'] = get_serial_number()
    data['device_model'] = get_device_model()
    data['fabricante'] = ""  # Preencha manualmente ou via input/config
    data['data_compra'] = ""
    data['fornecedor'] = ""
    data['custo'] = ""
    data['garantia_venc'] = ""
    data['local_fisico'] = ""
    data['centro_custo'] = ""
    data['usuario_designado'] = ""
    data['departamento'] = ""
    data['status'] = ""
    data['ultima_manutencao'] = ""

    # Coleta correta do SO e CPU (mantendo o comportamento antigo)
    if uname.system == "Windows" and wmi:
        try:
            c = wmi.WMI()
            os_info = c.Win32_OperatingSystem()[0]
            data['os'] = os_info.Caption.strip()
            data['architecture'] = os_info.OSArchitecture.strip() if hasattr(os_info, 'OSArchitecture') else uname.machine
            cpu_info = c.Win32_Processor()[0]
            data['cpu_model'] = cpu_info.Name.strip()
        except Exception as e:
            data['os'] = f"Windows {uname.release}"
            data['architecture'] = uname.machine
            data['cpu_model'] = platform.processor()
    else:
        data['os'] = f"{uname.system} {uname.release}"
        data['architecture'] = uname.machine
        data['cpu_model'] = platform.processor()

    data['cpu_cores_physical'] = psutil.cpu_count(logical=False)
    data['cpu_cores_logical'] = psutil.cpu_count(logical=True)
    memoria = psutil.virtual_memory()
    data['ram_total_gb'] = round(memoria.total / (1024**3), 2)
    data['ram_slots'] = get_ram_slots()
    disks = []
    for particao in psutil.disk_partitions():
        if 'loop' in particao.opts or particao.fstype == '':
            continue
        try:
            uso = psutil.disk_usage(particao.mountpoint)
            disks.append({
                'device': particao.device,
                'mountpoint': particao.mountpoint,
                'total_gb': round(uso.total / (1024**3), 2),
                'used_gb': round(uso.used / (1024**3), 2),
                'percent_used': uso.percent
            })
        except PermissionError:
            continue
    data['disks'] = disks
    mac_address = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
    data['mac_address'] = mac_address
    try:
        data['ip_address'] = socket.gethostbyname(socket.gethostname())
    except socket.gaierror:
        data['ip_address'] = '127.0.0.1'
    data['last_updated'] = datetime.datetime.now().isoformat()
    data['storage_health'] = get_storage_health()
    data['gpu_info'] = get_gpu_info()
    data['windows_update_status'] = get_windows_update_status()
    data['installed_software'] = get_installed_software()

    # Garante que todos os campos essenciais existam
    expected_fields = [
        'hostname', 'id_patrimonio', 'serial_number', 'device_model', 'fabricante', 'data_compra', 'fornecedor', 'custo', 'garantia_venc',
        'local_fisico', 'centro_custo', 'usuario_designado', 'departamento', 'status', 'ultima_manutencao',
        'os', 'architecture', 'cpu_model', 'cpu_cores_physical', 'cpu_cores_logical', 'ram_total_gb', 'ram_slots',
        'mac_address', 'ip_address', 'last_updated', 'disks', 'storage_health', 'gpu_info', 'windows_update_status', 'installed_software'
    ]
    for field in expected_fields:
        if field not in data or data[field] is None:
            data[field] = "Desconhecido"
        if field != 'disks' and isinstance(data[field], (list, dict)):
            data[field] = json.dumps(data[field])
    if isinstance(data['disks'], str):
        try:
            data['disks'] = json.loads(data['disks'])
        except json.JSONDecodeError:
            data['disks'] = []

    return data

def send_data_to_api(data):
    """Envia os dados coletados em formato JSON para a API."""
    try:
        headers = {'Content-Type': 'application/json'}
        response = requests.post(API_URL, data=json.dumps(data), headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("SUCESSO: Dados de inventário enviados com sucesso.")
            print(f"Resposta do servidor: {response.json()}")
        else:
            print(f"ERRO: Falha ao enviar dados. Status: {response.status_code}")
            print(f"Resposta: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"ERRO DE CONEXÃO: Não foi possível conectar à API em {API_URL}.")
        print(f"Detalhes: {e}")

if __name__ == "__main__":
    print("Coletando dados de inventário (v5 - Final Otimizada)...")
    inventory_data = get_inventory_data()
    
    print("\nEnviando dados para o servidor de inventário...")
    send_data_to_api(inventory_data)