import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sqlite3
import json
import os

DB_FILE = 'inventory.db'
detalhes_windows = {}  # Dicionário para controlar popups abertos por hostname

def atualizar_inventario():
    try:
        # Executa o coletor para atualizar os dados
        subprocess.run(['python', 'collector.py'], cwd=os.path.dirname(__file__), check=True)
        messagebox.showinfo("Atualização", "Inventário atualizado com sucesso!")
        carregar_inventario()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao atualizar inventário:\n{e}")

def carregar_inventario(filtro_hostname=""):
    tree.delete(*tree.get_children())
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if filtro_hostname:
            cursor.execute("SELECT * FROM assets WHERE hostname LIKE ? ORDER BY hostname", (f"%{filtro_hostname}%",))
        else:
            cursor.execute("SELECT * FROM assets ORDER BY hostname")
        assets = cursor.fetchall()
        for asset in assets:
            disks = ""
            try:
                disks_data = json.loads(asset['disks'])
                if disks_data:
                    disks = "; ".join([f"{d['mountpoint']} {d['total_gb']}GB" for d in disks_data])
            except Exception:
                disks = ""
            tree.insert('', 'end', values=(
                asset['hostname'],
                asset['device_model'] if 'device_model' in asset.keys() else 'Desconhecido',
                asset['os'],
                asset['ip_address'],
                asset['mac_address'],
                asset['cpu_model'],
                asset['ram_total_gb'],
                disks,
                asset['last_updated']
            ))
        conn.close()
        tag_rows()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao carregar inventário:\n{e}")

def pesquisar_maquina(event=None):
    filtro = search_var.get().strip()
    carregar_inventario(filtro)

def mostrar_detalhes():
    selected = tree.focus()
    if not selected:
        return
    values = tree.item(selected, 'values')
    hostname = values[0]
    global detalhes_windows
    # Se já existe uma janela para este hostname, traga para frente e atualize
    if hostname in detalhes_windows and detalhes_windows[hostname].winfo_exists():
        win = detalhes_windows[hostname]
        win.lift()
        win.focus_force()
        atualizar_detalhes_win(win, hostname)
        return
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM assets WHERE hostname=?", (hostname,))
        asset = cursor.fetchone()
        conn.close()
        if asset:
            detalhes_win = tk.Toplevel(root)
            detalhes_win.title(f"Propriedades de {asset['hostname']}")
            detalhes_win.geometry("700x600")
            detalhes_win.minsize(600, 500)
            detalhes_win.configure(bg="#f8fafc")
            detalhes_windows[hostname] = detalhes_win  # Salva referência

            # Ao fechar, remove do dicionário
            def on_close():
                if hostname in detalhes_windows:
                    detalhes_windows.pop(hostname)
                detalhes_win.destroy()
            detalhes_win.protocol("WM_DELETE_WINDOW", on_close)

            atualizar_detalhes_win(detalhes_win, hostname)
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao mostrar detalhes:\n{e}")

def atualizar_detalhes_win(detalhes_win, hostname):
    for widget in detalhes_win.winfo_children():
        widget.destroy()
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM assets WHERE hostname=?", (hostname,))
        asset = cursor.fetchone()
        conn.close()
        if not asset:
            return

        notebook = ttk.Notebook(detalhes_win)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Identificação
        tab_id = ttk.Frame(notebook)
        notebook.add(tab_id, text="Identificação")
        add_field(tab_id, "ID Patrimônio:", asset['id_patrimonio'], 0)
        add_field(tab_id, "Serial:", asset['serial_number'], 1)
        add_field(tab_id, "Modelo:", asset['device_model'], 2)
        add_field(tab_id, "Fabricante:", asset['fabricante'], 3)

        # Compra
        tab_compra = ttk.Frame(notebook)
        notebook.add(tab_compra, text="Compra")
        add_field(tab_compra, "Data da Compra:", asset['data_compra'], 0)
        add_field(tab_compra, "Fornecedor:", asset['fornecedor'], 1)
        add_field(tab_compra, "Custo:", asset['custo'], 2)
        add_field(tab_compra, "Garantia até:", asset['garantia_venc'], 3)

        # Localização e Usuário
        tab_local = ttk.Frame(notebook)
        notebook.add(tab_local, text="Localização/Usuário")
        add_field(tab_local, "Local Físico:", asset['local_fisico'], 0)
        add_field(tab_local, "Centro de Custo:", asset['centro_custo'], 1)
        add_field(tab_local, "Usuário Designado:", asset['usuario_designado'], 2)
        add_field(tab_local, "Departamento:", asset['departamento'], 3)

        # Status/Ciclo de Vida
        tab_status = ttk.Frame(notebook)
        notebook.add(tab_status, text="Status/Ciclo de Vida")
        add_field(tab_status, "Status:", asset['status'], 0)
        add_field(tab_status, "Última Manutenção:", asset['ultima_manutencao'], 1)

        # Especificações Técnicas
        tab_tec = ttk.Frame(notebook)
        notebook.add(tab_tec, text="Especificações Técnicas")
        add_field(tab_tec, "SO:", asset['os'], 0)
        add_field(tab_tec, "Arquitetura:", asset['architecture'], 1)
        add_field(tab_tec, "CPU:", asset['cpu_model'], 2)
        add_field(tab_tec, "Cores Físicos:", asset['cpu_cores_physical'], 3)
        add_field(tab_tec, "Threads:", asset['cpu_cores_logical'], 4)
        add_field(tab_tec, "RAM Total:", asset['ram_total_gb'], 5)
        add_field(tab_tec, "Slots RAM:", asset['ram_slots'], 6)
        add_field(tab_tec, "MAC:", asset['mac_address'], 7)
        add_field(tab_tec, "IP:", asset['ip_address'], 8)
        add_field(tab_tec, "Última Atualização:", asset['last_updated'], 9)
        add_field(tab_tec, "Saúde do Armazenamento:", asset['storage_health'], 10)
        add_field(tab_tec, "GPU:", asset['gpu_info'], 11)
        add_field(tab_tec, "Windows Update:", asset['windows_update_status'], 12)
        # Discos
        try:
            disks_data = json.loads(asset['disks'])
            if disks_data:
                for idx, disk in enumerate(disks_data):
                    add_field(
                        tab_tec,
                        f"Disco {disk['mountpoint']}:",
                        f"{disk['total_gb']:.2f} GB (Usado: {disk['used_gb']:.2f} GB - {disk['percent_used']}%)",
                        13 + idx
                    )
        except Exception:
            pass

        # Softwares
        tab_soft = ttk.Frame(notebook)
        notebook.add(tab_soft, text="Softwares")
        softwares = asset['installed_software']
        if softwares and softwares != "Desconhecido":
            sw_list = [s.strip() for s in softwares.split(';') if s.strip()]
            lbl = ttk.Label(tab_soft, text="Softwares Instalados:", font=("Segoe UI", 10, "bold"), anchor='w')
            lbl.grid(row=0, column=0, sticky='w', padx=(18, 8), pady=(6, 2))
            for idx, sw in enumerate(sw_list):
                lbl_sw = ttk.Label(tab_soft, text=sw, font=("Segoe UI", 10), anchor='w', wraplength=400, justify='left')
                lbl_sw.grid(row=idx+1, column=0, sticky='w', padx=(36, 8), pady=2)
        else:
            lbl = ttk.Label(tab_soft, text="Nenhum software encontrado.", font=("Segoe UI", 10), anchor='w')
            lbl.grid(row=0, column=0, sticky='w', padx=(18, 8), pady=6)

        btn_fechar = ttk.Button(detalhes_win, text="Fechar", command=detalhes_win.destroy)
        btn_fechar.pack(pady=(0, 10))
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao atualizar detalhes:\n{e}")

def add_field(parent, titulo, valor, row):
    lbl_titulo = ttk.Label(parent, text=titulo, font=("Segoe UI", 10, "bold"), anchor='w')
    lbl_titulo.grid(row=row, column=0, sticky='w', padx=(18, 8), pady=6)
    lbl_valor = ttk.Label(parent, text=str(valor), font=("Segoe UI", 10), anchor='w', wraplength=400, justify='left')
    lbl_valor.grid(row=row, column=1, sticky='w', padx=(0, 8), pady=6)

root = tk.Tk()
root.title("Inventário de TI")
root.state('zoomed')  # Tela cheia (Windows)
root.resizable(True, True)

# --- ESTILIZAÇÃO ---
style = ttk.Style()
style.theme_use('clam')
style.configure("Treeview",
    background="#f5f5f5",
    foreground="#222",
    rowheight=28,
    fieldbackground="#f5f5f5",
    font=('Segoe UI', 10)
)
style.configure("Treeview.Heading",
    background="#0078d7",
    foreground="white",
    font=('Segoe UI', 10, 'bold')
)
style.map("Treeview.Heading",
    background=[('active', '#005a9e')]
)
style.configure("TButton",
    font=('Segoe UI', 10, 'bold'),
    padding=6
)
style.configure("TLabel",
    font=('Segoe UI', 10)
)
style.configure("TFrame",
    background="#e9ecef"
)

root.configure(bg="#e9ecef")

frame = ttk.Frame(root, padding=10, style="TFrame")
frame.pack(fill='both', expand=True)

# Barra de pesquisa
search_frame = ttk.Frame(frame, style="TFrame")
search_frame.pack(fill='x', pady=(0, 10))
search_var = tk.StringVar()
search_entry = ttk.Entry(search_frame, textvariable=search_var, width=40, font=('Segoe UI', 10))
search_entry.pack(side='left', padx=(0, 5))
search_entry.bind('<Return>', pesquisar_maquina)
btn_pesquisar = ttk.Button(search_frame, text="Pesquisar", command=pesquisar_maquina)
btn_pesquisar.pack(side='left')

btn_frame = ttk.Frame(frame, style="TFrame")
btn_frame.pack(fill='x', pady=(0, 10))

btn_atualizar = ttk.Button(btn_frame, text="Atualizar Inventário", command=atualizar_inventario)
btn_atualizar.pack(side='left', padx=(0, 5))

btn_sair = ttk.Button(btn_frame, text="Sair", command=root.destroy)
btn_sair.pack(side='right')

columns = (
    "Hostname", "Modelo", "SO", "IP", "MAC", "CPU", "RAM (GB)", "Discos", "Última Atualização"
)
tree = ttk.Treeview(frame, columns=columns, show='headings', height=13, style="Treeview")
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=120, anchor='center')
tree.column("Hostname", width=130)
tree.column("Modelo", width=160)
tree.column("SO", width=120)
tree.column("Discos", width=180)
tree.column("Última Atualização", width=160)
tree.pack(fill='both', expand=True)
tree.bind("<<TreeviewSelect>>", lambda e: mostrar_detalhes())

# Alternância de cor nas linhas
def tag_rows():
    for i, item in enumerate(tree.get_children()):
        tree.item(item, tags=('evenrow' if i % 2 == 0 else 'oddrow'))
tree.tag_configure('evenrow', background='#f5f5f5')
tree.tag_configure('oddrow', background='#e1eafc')

carregar_inventario()

root.mainloop()

carregar_inventario()

root.mainloop()
root.mainloop()
btn_sair = ttk.Button(btn_frame, text="Sair", command=root.destroy)
btn_sair.pack(side='right')

columns = (
    "Hostname", "Modelo", "SO", "IP", "MAC", "CPU", "RAM (GB)", "Discos", "Última Atualização"
)
tree = ttk.Treeview(frame, columns=columns, show='headings', height=13, style="Treeview")
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=120, anchor='center')
tree.column("Hostname", width=130)
tree.column("Modelo", width=160)
tree.column("SO", width=120)
tree.column("Discos", width=180)
tree.column("Última Atualização", width=160)
tree.pack(fill='both', expand=True)
tree.bind("<<TreeviewSelect>>", lambda e: mostrar_detalhes())

# Alternância de cor nas linhas
def tag_rows():
    for i, item in enumerate(tree.get_children()):
        tree.item(item, tags=('evenrow' if i % 2 == 0 else 'oddrow'))
tree.tag_configure('evenrow', background='#f5f5f5')
tree.tag_configure('oddrow', background='#e1eafc')

carregar_inventario()

root.mainloop()

carregar_inventario()

root.mainloop()
root.mainloop()
