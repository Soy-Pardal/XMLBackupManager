import os
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import xml.etree.ElementTree as ET
from datetime import datetime
import zipfile


class XMLBackupManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Gerenciador de XML - Filtros e Exportação")
        self.xml_folder = "xml_backups"  # Pasta para armazenar backups
        os.makedirs(self.xml_folder, exist_ok=True)

        self.setup_ui()

    def setup_ui(self):
        # Adicionando uma barra de status
        status_bar = tk.Label(self.root, text="Desenvolvido por Gabriel Dal Prá", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Adicionando um menu
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Ajuda", menu=help_menu)
        help_menu.add_command(label="Sobre", command=self.show_about)

        # Layout principal
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Gerenciador de pastas (lado esquerdo)
        folder_frame = tk.Frame(main_frame, width=200)
        folder_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        tk.Label(folder_frame, text="Pastas por Data").pack(pady=5)

        self.folder_tree = ttk.Treeview(folder_frame)
        self.folder_tree.pack(fill=tk.BOTH, expand=True)
        self.folder_tree.bind("<<TreeviewSelect>>", self.on_folder_select)

        folder_button_frame = tk.Frame(folder_frame)
        folder_button_frame.pack(fill=tk.X)

        update_button = ttk.Button(folder_button_frame, text="Atualizar", command=self.update_folder_tree)
        update_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Frame direito para filtros e botões
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Filtros
        filter_frame = tk.Frame(right_frame)
        filter_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

        tk.Label(filter_frame, text="Data (AAAA-MM-DD):").grid(row=0, column=0, padx=5)
        self.date_entry = tk.Entry(filter_frame, width=12)
        self.date_entry.grid(row=0, column=1, padx=5)

        tk.Label(filter_frame, text="Mês/Ano (AAAA-MM):").grid(row=0, column=2, padx=5)
        self.month_entry = tk.Entry(filter_frame, width=12)
        self.month_entry.grid(row=0, column=3, padx=5)

        tk.Label(filter_frame, text="Ano (AAAA):").grid(row=0, column=4, padx=5)
        self.year_entry = tk.Entry(filter_frame, width=12)
        self.year_entry.grid(row=0, column=5, padx=5)

        tk.Label(filter_frame, text="CNPJ:").grid(row=0, column=6, padx=5)
        self.cnpj_entry = tk.Entry(filter_frame, width=20)
        self.cnpj_entry.grid(row=0, column=7, padx=5)

        search_button = tk.Button(filter_frame, text="Pesquisar", command=self.apply_filters)
        search_button.grid(row=0, column=8, padx=5)


        result_frame = tk.Frame(right_frame)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.file_list = tk.Listbox(result_frame, selectmode=tk.MULTIPLE, height=20)
        self.file_list.pack(fill=tk.BOTH, expand=True)

        self.total_label = tk.Label(result_frame, text="Total de Resultados: 0")
        self.total_label.pack(pady=5)


        action_frame = tk.Frame(right_frame)
        action_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=5)

        select_all_button = tk.Button(action_frame, text="Selecionar Tudo", command=self.select_all_files)
        select_all_button.pack(side=tk.LEFT, padx=5)

        export_button = tk.Button(action_frame, text="Exportar Selecionados", command=self.export_selected_files)
        export_button.pack(side=tk.LEFT, padx=5)

        self.update_folder_tree()

    def show_about(self):
        """
        Exibe informações sobre o programa.
        """
        messagebox.showinfo("Sobre", "Gerenciador de XML\nVersão 1.0\nDesenvolvido por Gabriel Dal Prá")

    def update_folder_tree(self):
        """
        Atualiza o gerenciador de pastas com base nas subpastas da pasta principal.
        """
        self.folder_tree.delete(*self.folder_tree.get_children())  # Limpa a árvore
        for folder in os.listdir(self.xml_folder):
            folder_path = os.path.join(self.xml_folder, folder)
            if os.path.isdir(folder_path):
                self.folder_tree.insert("", "end", text=folder, values=(folder_path,))

        self.file_list.delete(0, tk.END)  # Limpa a lista de arquivos

    def on_folder_select(self, event):
        """
        Exibe os arquivos contidos na pasta selecionada no gerenciador.
        """
        selected_item = self.folder_tree.selection()
        if not selected_item:
            return

        folder_path = self.folder_tree.item(selected_item[0], "values")[0]
        self.display_files_in_folder(folder_path)

    def display_files_in_folder(self, folder_path):
        """
        Exibe os arquivos na lista de arquivos com base na pasta selecionada.
        """
        self.file_list.delete(0, tk.END)
        if os.path.exists(folder_path):
            for file_name in os.listdir(folder_path):
                file_path = os.path.join(folder_path, file_name)
                self.file_list.insert(tk.END, file_path)

        # Atualizar total de resultados
        self.total_label.config(text=f"Total de Resultados: {len(self.file_list.get(0, tk.END))}")

    def apply_filters(self):
        """
        Aplica os filtros e exibe os arquivos correspondentes.
        """
        date_filter = self.date_entry.get().strip()
        month_filter = self.month_entry.get().strip()
        year_filter = self.year_entry.get().strip()
        cnpj_filter = self.cnpj_entry.get().strip()

        matched_files = []

        # Iterar por todas as pastas e arquivos
        for root_dir, _, files in os.walk(self.xml_folder):
            for file_name in files:
                if not file_name.endswith(".xml"):
                    continue

                file_path = os.path.join(root_dir, file_name)
                try:
                    tree = ET.parse(file_path)
                    root = tree.getroot()

                    # Extrai informações do XML
                    namespace = self.get_namespace(root)
                    ET.register_namespace('', namespace)

                    dh_emi = root.find(".//{%s}dhEmi" % namespace)
                    cnpj_emit = root.find(".//{%s}emit/{%s}CNPJ" % (namespace, namespace))
                    cnpj_dest = root.find(".//{%s}dest/{%s}CNPJ" % (namespace, namespace))

                    # Filtros
                    if dh_emi is not None:
                        emission_date = dh_emi.text.split("T")[0]  # Apenas a data
                        emission_month = "-".join(emission_date.split("-")[:2])
                        emission_year = emission_date.split("-")[0]

                        if date_filter and emission_date != date_filter:
                            continue
                        if month_filter and emission_month != month_filter:
                            continue
                        if year_filter and emission_year != year_filter:
                            continue

                    if cnpj_filter:
                        if (cnpj_emit is not None and cnpj_filter not in cnpj_emit.text) and (
                                cnpj_dest is not None and cnpj_filter not in cnpj_dest.text):
                            continue

                    matched_files.append(file_path)
                except Exception as e:
                    print(f"Erro ao processar o arquivo {file_name}: {e}")
                    continue

        # Atualizar lista de arquivos
        self.file_list.delete(0, tk.END)
        for file_path in matched_files:
            self.file_list.insert(tk.END, file_path)

        # Atualizar total de resultados
        self.total_label.config(text=f"Total de Resultados: {len(matched_files)}")

    def export_selected_files(self):
        """
        Exporta os arquivos selecionados em um arquivo ZIP.
        """
        selected_indices = self.file_list.curselection()
        if not selected_indices:
            messagebox.showerror("Erro", "Nenhum arquivo selecionado.")
            return

        selected_files = [self.file_list.get(i) for i in selected_indices]
        save_path = filedialog.asksaveasfilename(defaultextension=".zip", filetypes=[("ZIP Files", "*.zip")])

        if not save_path:
            return

        try:
            with zipfile.ZipFile(save_path, 'w') as zipf:
                for file_path in selected_files:
                    zipf.write(file_path, os.path.basename(file_path))
            messagebox.showinfo("Sucesso", f"Arquivos exportados para: {save_path}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao criar o arquivo ZIP: {e}")

    def select_all_files(self):
        """
        Seleciona todos os arquivos listados.
        """
        self.file_list.select_set(0, tk.END)

    def get_namespace(self, element):
        """
        Extrai o namespace do elemento XML.
        """
        if element.tag.startswith("{"):
            return element.tag.split("}")[0][1:]
        return ""


if __name__ == "__main__":
    root = tk.Tk()
    root.iconbitmap("icone.ico")  # Substitua "icone.ico" pelo nome do arquivo do seu ícone
    root.minsize(1090, 600)
    root.maxsize(1090, 600)
    app = XMLBackupManager(root)
    root.geometry("1090x600")
    root.mainloop()
