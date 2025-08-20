import tkinter as tk
from tkinter import ttk, messagebox, Text, Scrollbar
import subprocess
import sqlite3
import json
import os
import datetime

DB_FILE = 'inventory.db'
detalhes_windows = {}


def create_db_tables():
    """Garante que as tabelas 'assets' e 'maintenance_logs' existam."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    # Adicionando a coluna 'monitors' se ela não existir, para compatibilidade
    try:
        cursor.execute("ALTER TABLE assets ADD COLUMN monitors TEXT")
    except sqlite3.OperationalError:
        pass  # Coluna já existe

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS assets (
            hostname TEXT PRIMARY KEY, id_patrimonio TEXT, serial_number TEXT, device_model TEXT, fabricante TEXT,
            data_compra TEXT, fornecedor TEXT, custo TEXT, garantia_venc TEXT, local_fisico TEXT, centro_custo TEXT, 
            usuario_designado TEXT, departamento TEXT, status TEXT, ultima_manutencao TEXT, maintenance_history_note TEXT,
            os TEXT, architecture TEXT, cpu_model TEXT, cpu_cores_physical INTEGER, cpu_cores_logical INTEGER, 
            ram_total_gb REAL, ram_slots TEXT, mac_address TEXT, ip_address TEXT, last_updated TEXT, disks TEXT,
            storage_health TEXT, gpu_info TEXT, windows_update_status TEXT, installed_software TEXT,
            monitors TEXT -- ADICIONE ESTA LINHA
        )
    ''')
    # ... o resto da função continua igual ...
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS maintenance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, asset_hostname TEXT, maintenance_date TEXT,
            description TEXT, technician TEXT, FOREIGN KEY (asset_hostname) REFERENCES assets (hostname)
        )
    ''')
    conn.commit()
    conn.close()


def atualizar_inventario():
    try:
        script_path = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), 'collector.py')
        if not os.path.exists(script_path):
            messagebox.showerror(
                "Erro", f"Arquivo 'collector.py' não encontrado no diretório do script.")
            return
        subprocess.run(['python', script_path], check=True,
                       cwd=os.path.dirname(script_path))
        messagebox.showinfo(
            "Atualização", "Inventário atualizado com sucesso!")
        carregar_inventario()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao atualizar inventário:\n{e}")


def carregar_inventario(filtro_hostname=""):
    for item in tree.get_children():
        tree.delete(item)
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        query = "SELECT hostname, device_model, status, os, ip_address, usuario_designado, last_updated FROM assets"
        params = ()
        if filtro_hostname:
            query += " WHERE hostname LIKE ?"
            params = (f"%{filtro_hostname}%",)
        query += " ORDER BY hostname"
        cursor.execute(query, params)
        for asset in cursor.fetchall():
            tree.insert('', 'end', values=(
                asset['hostname'], asset['device_model'], asset['status'], asset['os'],
                asset['ip_address'], asset['usuario_designado'], asset['last_updated']
            ))
        conn.close()
        tag_rows()
    except Exception as e:
        messagebox.showerror("Erro", f"Erro ao carregar inventário:\n{e}")


def pesquisar_maquina(event=None):
    carregar_inventario(search_var.get().strip())


def mostrar_detalhes(event=None):
    selected = tree.focus()
    if not selected:
        return
    hostname = tree.item(selected, 'values')[0]

    if hostname in detalhes_windows and detalhes_windows[hostname].winfo_exists():
        win = detalhes_windows[hostname]
        win.lift()
        win.focus_force()
        return

    detalhes_win = tk.Toplevel(root)
    detalhes_win.title(f"Propriedades de {hostname}")
    detalhes_win.geometry("900x700")
    detalhes_windows[hostname] = detalhes_win
    detalhes_win.protocol("WM_DELETE_WINDOW",
                          lambda: on_close(hostname, detalhes_win))
    atualizar_detalhes_win(detalhes_win, hostname)


def on_close(hostname, window):
    detalhes_windows.pop(hostname, None)
    window.destroy()


def format_datetime(iso_string):
    if not iso_string:
        return "N/A"
    try:
        dt = datetime.datetime.fromisoformat(iso_string)
        return dt.strftime('%d/%m/%Y às %H:%M:%S')
    except (ValueError, TypeError):
        return iso_string


def atualizar_detalhes_win(detalhes_win, hostname):
    for widget in detalhes_win.winfo_children():
        widget.destroy()

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM assets WHERE hostname=?", (hostname,))
    asset = cursor.fetchone()
    if not asset:
        conn.close()
        messagebox.showerror("Erro", "Ativo não encontrado.")
        detalhes_win.destroy()
        return

    notebook = ttk.Notebook(detalhes_win)
    notebook.pack(fill='both', expand=True, padx=10, pady=10)
    asset_dict = dict(asset)

    # --- ABA 1: STATUS E MANUTENÇÃO (INTERATIVO) ---
    tab_status = ttk.Frame(notebook, padding="10")
    notebook.add(tab_status, text="Status e Manutenção")
    form_frame = ttk.Frame(tab_status)
    form_frame.pack(fill='x', padx=10, pady=10)
    ttk.Label(form_frame, text="Status do Ativo:", font=(
        'Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky='w', pady=5)
    status_options = ['Em funcionamento', 'Em manutenção',
                      'Em estoque', 'Danificado', 'Descartado']
    status_var = tk.StringVar(value=asset['status'])
    status_combo = ttk.Combobox(
        form_frame, textvariable=status_var, values=status_options, state='readonly', width=30)
    status_combo.grid(row=0, column=1, sticky='w', pady=5)
    ttk.Separator(tab_status, orient='horizontal').pack(
        fill='x', padx=10, pady=15)
    new_log_frame = ttk.LabelFrame(
        tab_status, text=" Adicionar Novo Relatório de Manutenção ", padding="10")
    new_log_frame.pack(fill='x', padx=10, pady=5)
    ttk.Label(new_log_frame, text="Descrição do Serviço:").grid(
        row=0, column=0, columnspan=2, sticky='w', pady=(0, 5))
    desc_text = Text(new_log_frame, height=5, width=60, font=(
        'Segoe UI', 10), relief='solid', borderwidth=1)
    desc_text.grid(row=1, column=0, columnspan=2, sticky='ew', pady=(0, 10))
    ttk.Label(new_log_frame, text="Técnico:").grid(
        row=2, column=0, sticky='w', pady=5)
    tech_var = tk.StringVar()
    tech_entry = ttk.Entry(new_log_frame, textvariable=tech_var, width=32)
    tech_entry.grid(row=2, column=1, sticky='w', pady=5)
    btn_salvar = ttk.Button(new_log_frame, text="Salvar Alterações e Adicionar Relatório", command=lambda: salvar_status_e_manutencao(
        hostname, status_var.get(), desc_text.get("1.0", "end-1c").strip(), tech_var.get().strip(), detalhes_win))
    btn_salvar.grid(row=3, column=0, columnspan=2, pady=10)
    history_frame = ttk.LabelFrame(
        tab_status, text=" Histórico de Manutenções ", padding="10")
    history_frame.pack(fill='both', expand=True, padx=10, pady=10)
    log_cols = ("Data", "Técnico", "Descrição")
    log_tree = ttk.Treeview(
        history_frame, columns=log_cols, show='headings', height=5)
    log_tree.pack(fill='both', expand=True, side='left')
    log_scroll = ttk.Scrollbar(
        history_frame, orient="vertical", command=log_tree.yview)
    log_scroll.pack(side='right', fill='y')
    log_tree.configure(yscrollcommand=log_scroll.set)
    for col in log_cols:
        log_tree.heading(col, text=col)
    log_tree.column("Data", width=120, anchor='center')
    log_tree.column("Técnico", width=150)
    log_tree.column("Descrição", width=400)
    cursor.execute(
        "SELECT * FROM maintenance_logs WHERE asset_hostname=? ORDER BY maintenance_date DESC", (hostname,))
    for log in cursor.fetchall():
        log_tree.insert('', 'end', values=(
            log['maintenance_date'], log['technician'], log['description']))

    # ==============================================================================
    # --- ABA 2: IDENTIFICAÇÃO (NOVO LAYOUT) ---
    # ==============================================================================
    tab_id = ttk.Frame(notebook, padding="10")
    notebook.add(tab_id, text="Identificação")
    tab_id.columnconfigure((0, 1), weight=1)  # Duas colunas

    # Coluna da Esquerda
    id_col1 = ttk.Frame(tab_id)
    id_col1.grid(row=0, column=0, sticky="new", padx=(0, 10))
    add_field(id_col1, "ID Patrimônio:", asset_dict.get('id_patrimonio'), 0)
    add_field(id_col1, "Número de Série:", asset_dict.get('serial_number'), 1)

    # Coluna da Direita
    id_col2 = ttk.Frame(tab_id)
    id_col2.grid(row=0, column=1, sticky="new", padx=(10, 0))
    add_field(id_col2, "Fabricante:", asset_dict.get('fabricante'), 0)
    add_field(id_col2, "Modelo:", asset_dict.get('device_model'), 1)

    # ==============================================================================
    # --- ABA 3: ESPECIFICAÇÕES TÉCNICAS (LAYOUT ORGANIZADO) ---
    # ==============================================================================
    tab_tec = ttk.Frame(notebook, padding="10")
    notebook.add(tab_tec, text="Especificações Técnicas")
    tab_tec.columnconfigure((0, 1), weight=1, uniform="group1")
    frame_sistema = ttk.LabelFrame(tab_tec, text=" Sistema ", padding=10)
    frame_sistema.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=5)
    add_field(frame_sistema, "SO:", asset_dict.get('os'), 0)
    add_field(frame_sistema, "Arquitetura:", asset_dict.get('architecture'), 1)
    frame_cpu = ttk.LabelFrame(tab_tec, text=" Processador (CPU) ", padding=10)
    frame_cpu.grid(row=1, column=0, sticky="ew", padx=(0, 5), pady=5)
    add_field(frame_cpu, "Modelo:", asset_dict.get('cpu_model'), 0)
    add_field(frame_cpu, "Cores Físicos:",
              asset_dict.get('cpu_cores_physical'), 1)
    add_field(frame_cpu, "Threads:", asset_dict.get('cpu_cores_logical'), 2)
    frame_memoria = ttk.LabelFrame(tab_tec, text=" Memória (RAM) ", padding=10)
    frame_memoria.grid(row=2, column=0, sticky="ew", padx=(0, 5), pady=5)
    add_field(frame_memoria, "Total:",
              f"{asset_dict.get('ram_total_gb', 0):.2f} GB", 0)
    add_field(frame_memoria, "Slots:", asset_dict.get('ram_slots'), 1)
    frame_gpu = ttk.LabelFrame(
        tab_tec, text=" Gráficos e Sistema ", padding=10)
    frame_gpu.grid(row=3, column=0, sticky="ew", padx=(0, 5), pady=5)
    add_field(frame_gpu, "GPU:", asset_dict.get('gpu_info'), 0)
    add_field(frame_gpu, "Windows Update:",
              asset_dict.get('windows_update_status'), 1)
    frame_rede = ttk.LabelFrame(tab_tec, text=" Rede ", padding=10)
    frame_rede.grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=5)
    add_field(frame_rede, "Endereço IP:", asset_dict.get('ip_address'), 0)
    add_field(frame_rede, "Endereço MAC:", asset_dict.get('mac_address'), 1) 
    frame_monitores = ttk.LabelFrame(tab_tec, text=" Monitores Conectados ", padding=10)
    # 2. Posiciona o novo quadro na grid (linha 2, coluna 1)
    frame_monitores.grid(row=2, column=1, rowspan=2,
                         sticky="nsew", padx=(5, 0), pady=5)

    try:
        # 3. Lê a string JSON do banco de dados e a transforma em uma lista Python
        monitors_data = json.loads(asset_dict.get('monitors', '[]') or '[]')

        # 4. Verifica se a lista não está vazia
        if monitors_data and isinstance(monitors_data, list):
            # 5. Loop para adicionar cada monitor encontrado ao quadro
            for idx, monitor in enumerate(monitors_data):
                info = f"{monitor.get('manufacturer', '')} {monitor.get('model', '')}".strip(
                )
                serial = monitor.get('serial_number')
                if serial and serial != 'Desconhecido':
                    info += f" (S/N: {serial})"
                # Usa a função add_field para mostrar o monitor na tela
                add_field(frame_monitores, f"Monitor {idx+1}:", info, idx)
        else:
            add_field(frame_monitores, "Info:", "Nenhum monitor detectado.", 0)

    except (json.JSONDecodeError, TypeError):
        # 6. Se houver erro na leitura do JSON, mostra uma mensagem amigável
        add_field(frame_monitores, "Erro:", "Dados de monitores inválidos.", 0)
    frame_armazenamento = ttk.LabelFrame(
        tab_tec, text=" Armazenamento ", padding=10)
    frame_armazenamento.grid(row=1, column=1, rowspan=3,
                             sticky="nsew", padx=(5, 0), pady=5)
    add_field(frame_armazenamento, "Saúde Geral:",
              asset_dict.get('storage_health'), 0)
    try:
        disks_data = json.loads(asset_dict.get('disks', '[]'))
        for idx, disk in enumerate(disks_data):
            add_field(frame_armazenamento, f"Disco {disk.get('mountpoint', '')}:",
                      f"{disk.get('total_gb', 0):.2f} GB (Usado: {disk.get('used_gb', 0):.2f} GB - {disk.get('percent_used', 0)}%)", idx + 1)
    except (json.JSONDecodeError, TypeError):
        pass
    last_updated_frame = ttk.Frame(tab_tec)
    last_updated_frame.grid(row=4, column=0, columnspan=2,
                            sticky="ew", pady=(10, 0))
    ttk.Label(last_updated_frame, text="Última Coleta de Dados:",
              font=("Segoe UI", 9, "italic")).pack(side='left')
    ttk.Label(last_updated_frame, text=format_datetime(asset_dict.get(
        'last_updated')), font=("Segoe UI", 9, "italic")).pack(side='left', padx=5)

    # ==============================================================================
    # --- ABA 4: COMPRA (NOVO LAYOUT) ---
    # ==============================================================================
    tab_compra = ttk.Frame(notebook, padding="10")
    notebook.add(tab_compra, text="Compra")
    tab_compra.columnconfigure((0, 1), weight=1)

    # Coluna da Esquerda
    compra_col1 = ttk.Frame(tab_compra)
    compra_col1.grid(row=0, column=0, sticky="new", padx=(0, 10))
    add_field(compra_col1, "Data da Compra:", asset_dict.get('data_compra'), 0)
    add_field(compra_col1, "Fornecedor:", asset_dict.get('fornecedor'), 1)

    # Coluna da Direita
    compra_col2 = ttk.Frame(tab_compra)
    compra_col2.grid(row=0, column=1, sticky="new", padx=(10, 0))
    add_field(compra_col2, "Custo (R$):", asset_dict.get('custo'), 0)
    add_field(compra_col2, "Venc. Garantia:",
              asset_dict.get('garantia_venc'), 1)

    # ==============================================================================
    # --- ABA 5: LOCALIZAÇÃO E USUÁRIO (NOVO LAYOUT) ---
    # ==============================================================================
    tab_local = ttk.Frame(notebook, padding="10")
    notebook.add(tab_local, text="Localização e Usuário")
    tab_local.columnconfigure((0, 1), weight=1)

    # Coluna da Esquerda
    local_col1 = ttk.Frame(tab_local)
    local_col1.grid(row=0, column=0, sticky="new", padx=(0, 10))
    add_field(local_col1, "Usuário Designado:",
              asset_dict.get('usuario_designado'), 0)
    add_field(local_col1, "Departamento:", asset_dict.get('departamento'), 1)

    # Coluna da Direita
    local_col2 = ttk.Frame(tab_local)
    local_col2.grid(row=0, column=1, sticky="new", padx=(10, 0))
    add_field(local_col2, "Local Físico:", asset_dict.get('local_fisico'), 0)
    add_field(local_col2, "Centro de Custo:",
              asset_dict.get('centro_custo'), 1)

    # ==============================================================================
    # --- ABA 6: SOFTWARES (LAYOUT MANTIDO) ---
    # ==============================================================================
    tab_soft = ttk.Frame(notebook, padding="10")
    notebook.add(tab_soft, text="Softwares")
    sw_text = Text(tab_soft, wrap="word", font=(
        "Segoe UI", 10), relief='solid', borderwidth=1)
    sw_scroll = ttk.Scrollbar(
        tab_soft, orient="vertical", command=sw_text.yview)
    sw_text.configure(yscrollcommand=sw_scroll.set)
    sw_text.pack(side="left", fill="both", expand=True)
    sw_scroll.pack(side="right", fill="y")
    softwares = asset_dict.get('installed_software', '')
    sw_list = sorted([s.strip() for s in softwares.split(';') if s.strip(
    )]) if softwares and softwares != "Desconhecido" else ["Nenhum software encontrado."]
    sw_text.insert("1.0", "\n".join(sw_list))
    sw_text.config(state="disabled")

    conn.close()


def salvar_status_e_manutencao(hostname, new_status, new_desc, new_tech, window_ref):
    if not new_status:
        messagebox.showwarning(
            "Aviso", "O campo 'Status' não pode estar vazio.", parent=window_ref)
        return
    if new_desc and not new_tech:
        messagebox.showwarning(
            "Aviso", "O nome do técnico é obrigatório ao adicionar um relatório.", parent=window_ref)
        return
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE assets SET status=? WHERE hostname=?", (new_status, hostname))
        if new_desc and new_tech:
            today = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
            cursor.execute("INSERT INTO maintenance_logs (asset_hostname, maintenance_date, description, technician) VALUES (?, ?, ?, ?)",
                           (hostname, today, new_desc, new_tech))
            cursor.execute(
                "UPDATE assets SET ultima_manutencao=? WHERE hostname=?", (today.split(' ')[0], hostname))
        conn.commit()
        conn.close()
        messagebox.showinfo(
            "Sucesso", "Dados salvos com sucesso!", parent=window_ref)
        atualizar_detalhes_win(window_ref, hostname)
        pesquisar_maquina()
    except Exception as e:
        messagebox.showerror("Erro de Banco de Dados",
                             f"Não foi possível salvar os dados:\n{e}", parent=window_ref)


def add_field(parent, titulo, valor, row):
    parent.columnconfigure(1, weight=1)
    ttk.Label(parent, text=titulo, font=("Segoe UI", 10, "bold")).grid(
        row=row, column=0, sticky='nw', padx=5, pady=3)
    ttk.Label(parent, text=str(valor if valor is not None else ""), wraplength=350,
              justify='left').grid(row=row, column=1, sticky='w', padx=5, pady=3)


# --- CONFIGURAÇÃO DA JANELA PRINCIPAL ---
root = tk.Tk()
root.title("Inventário de TI")
root.geometry("1200x700")
style = ttk.Style()
style.theme_use('clam')
style.configure("Treeview.Heading", font=('Segoe UI', 10, 'bold'))
frame = ttk.Frame(root, padding="10")
frame.pack(fill='both', expand=True)
top_frame = ttk.Frame(frame)
top_frame.pack(fill='x', pady=(0, 10))
search_var = tk.StringVar()
search_entry = ttk.Entry(top_frame, textvariable=search_var, width=40)
search_entry.pack(side='left', padx=(0, 5))
search_entry.bind('<Return>', pesquisar_maquina)
ttk.Button(top_frame, text="Pesquisar",
           command=pesquisar_maquina).pack(side='left')
ttk.Button(top_frame, text="Coletar/Atualizar Dados",
           command=atualizar_inventario).pack(side='left', padx=5)
ttk.Button(top_frame, text="Sair", command=root.destroy).pack(side='right')
columns = ("Hostname", "Modelo", "Status", "SO",
           "IP", "Usuário", "Última Atualização")
tree = ttk.Treeview(frame, columns=columns, show='headings')
tree_scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
tree.configure(yscrollcommand=tree_scroll.set)
tree.pack(side='left', fill='both', expand=True)
tree_scroll.pack(side='right', fill='y')
for col in columns:
    tree.heading(col, text=col)
    tree.column(col, width=150, anchor='w')
tree.bind("<Double-1>", mostrar_detalhes)


def tag_rows():
    for i, item in enumerate(tree.get_children()):
        tree.item(item, tags=('evenrow' if i % 2 == 0 else 'oddrow'))


tree.tag_configure('evenrow', background='#f0f0f0')
tree.tag_configure('oddrow', background='#ffffff')
create_db_tables()
carregar_inventario()
root.mainloop()
