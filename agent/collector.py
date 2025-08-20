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
    # Se a importação falhar (não está no Windows ou não está instalado), wmi será None
    wmi = None

# IMPORTANTE: Altere para o IP do seu servidor se não estiver rodando na mesma máquina
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
                output = subprocess.check_output(
                    "dmidecode -t memory | grep -i 'Locator'", shell=True, stderr=subprocess.DEVNULL).decode()
                slots = [line for line in output.splitlines() if line.strip()]
                return f"{len(slots)} slots ocupados"
            except Exception:
                return "Desconhecido"
        else:
            return "Não disponível"
    except Exception:
        return "Desconhecido"


def get_installed_software():
    """Obtém uma lista de softwares instalados."""
    try:
        if platform.system() == "Windows":
            try:
                output = subprocess.check_output(
                    'powershell -Command "Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* | Select-Object DisplayName | Format-Table -HideTableHeaders"',
                    shell=True, stderr=subprocess.DEVNULL
                ).decode(errors='ignore')
                lines = [line.strip()
                         for line in output.splitlines() if line.strip()]
                return "; ".join(lines) if lines else "Nenhum"
            except Exception:
                return "Não disponível"
        elif platform.system() == "Linux":
            try:
                output = subprocess.check_output(
                    "dpkg-query -W -f='${binary:Package}\\n'", shell=True, stderr=subprocess.DEVNULL).decode()
                lines = [line.strip()
                         for line in output.splitlines() if line.strip()]
                return "; ".join(lines) if lines else "Nenhum"
            except Exception:
                return "Não disponível"
        else:
            return "Não disponível"
    except Exception:
        return "Desconhecido"


def get_storage_health():
    """Retorna informações básicas sobre saúde do armazenamento."""
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
            try:
                output = subprocess.check_output(
                    ['which', 'smartctl'], stderr=subprocess.DEVNULL).decode().strip()
                if output:
                    result = subprocess.check_output(
                        ['sudo', 'smartctl', '-H', '/dev/sda'], stderr=subprocess.DEVNULL).decode()
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
                output = subprocess.check_output(
                    "lspci | grep VGA", shell=True, stderr=subprocess.DEVNULL).decode()
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
            return f"{len(wu)} atualizações instaladas"
        else:
            return "Não aplicável"
    except Exception:
        return "Desconhecido"

def get_monitor_info():
    """Retorna uma lista de dicionários com informações sobre cada monitor conectado."""
    monitors = []
    try:
        if platform.system() == "Windows" and wmi:
            c = wmi.WMI(namespace='root\\wmi')
            monitor_info = c.WmiMonitorID()
            for monitor in monitor_info:
                manufacturer = "".join(
                    chr(i) for i in monitor.ManufacturerName if i != 0).strip()
                serial_number = "".join(
                    chr(i) for i in monitor.SerialNumberID if i != 0).strip()
                model_name = "".join(
                    chr(i) for i in monitor.UserFriendlyName if i != 0).strip()
                monitors.append({
                    "manufacturer": manufacturer or "Desconhecido",
                    "model": model_name or "Desconhecido",
                    "serial_number": serial_number or "Desconhecido"
                })
            return monitors if monitors else "Nenhum monitor detectado"

        elif platform.system() == "Linux":
            try:
                output = subprocess.check_output(
                    "xrandr", shell=True, stderr=subprocess.DEVNULL).decode()
                connected_monitors = [
                    line for line in output.splitlines() if " connected " in line]
                for line in connected_monitors:
                    parts = line.split()
                    device_name = parts[0]
                    resolution = "N/A"
                    for part in parts:
                        if 'x' in part and '+' in part:
                            resolution = part.split('+')[0]
                            break
                    monitors.append({
                        "device_name": device_name,
                        "resolution": resolution
                    })
                return monitors if monitors else "Nenhum monitor detectado"
            except Exception:
                return "xrandr não disponível"
        else:
            return "Não disponível neste SO"
            
    # ALTERAÇÃO PRINCIPAL AQUI: Capturamos o erro 'e' e o exibimos.
    except Exception as e:
        return f"Erro ao obter informações do monitor: {e}"

def get_inventory_data():
    """Coleta todos os dados de hardware e software da máquina local."""
    data = {}
    uname = platform.uname()

    # --- Dados manuais / a serem preenchidos ---
    data['id_patrimonio'] = ""
    data['fabricante'] = ""
    data['data_compra'] = ""
    data['fornecedor'] = ""
    data['custo'] = ""
    data['garantia_venc'] = ""
    data['local_fisico'] = ""
    data['centro_custo'] = ""
    data['usuario_designado'] = getpass.getuser()  # Pega o usuário logado
    data['departamento'] = ""
    data['status'] = "Em uso"
    data['ultima_manutencao'] = ""

    # --- Coleta automática ---
    data['hostname'] = uname.node
    data['serial_number'] = get_serial_number()
    data['device_model'] = get_device_model()

    if uname.system == "Windows" and wmi:
        try:
            c = wmi.WMI()
            os_info = c.Win32_OperatingSystem()[0]
            data['os'] = os_info.Caption.strip()
            data['architecture'] = os_info.OSArchitecture.strip()
            cpu_info = c.Win32_Processor()[0]
            data['cpu_model'] = cpu_info.Name.strip()
        except Exception:
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
                'device': particao.device, 'mountpoint': particao.mountpoint,
                'total_gb': round(uso.total / (1024**3), 2),
                'used_gb': round(uso.used / (1024**3), 2), 'percent_used': uso.percent
            })
        except PermissionError:
            continue
    data['disks'] = disks

    data['mac_address'] = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
    try:
        data['ip_address'] = socket.gethostbyname(socket.gethostname())
    except socket.gaierror:
        data['ip_address'] = '127.0.0.1'

    data['last_updated'] = datetime.datetime.now().isoformat()
    data['storage_health'] = get_storage_health()
    data['gpu_info'] = get_gpu_info()
    data['windows_update_status'] = get_windows_update_status()
    data['installed_software'] = get_installed_software()
    data['monitors'] = get_monitor_info()  # <-- CHAMADA DA NOVA FUNÇÃO

    return data


def send_data_to_api(data):
    """Envia os dados coletados em formato JSON para a API."""
    try:
        # Converte qualquer dado não serializável (como datetime) para string
        payload = json.dumps(data, default=str)
        headers = {'Content-Type': 'application/json'}
        response = requests.post(
            API_URL, data=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            print("SUCESSO: Dados de inventário enviados com sucesso.")
            print(f"Resposta do servidor: {response.json()}")
        else:
            print(
                f"ERRO: Falha ao enviar dados. Status: {response.status_code}")
            print(f"Resposta: {response.text}")

    except requests.exceptions.RequestException as e:
        print(
            f"ERRO DE CONEXÃO: Não foi possível conectar à API em {API_URL}.")
        print(f"Detalhes: {e}")


if __name__ == "__main__":
    print("Coletando dados de inventário...")
    inventory_data = get_inventory_data()

    print("\nDados Coletados:")
    # Imprime os dados de forma legível para verificação
    print(json.dumps(inventory_data, indent=4, default=str))

    print("\nEnviando dados para o servidor de inventário...")
    send_data_to_api(inventory_data)
