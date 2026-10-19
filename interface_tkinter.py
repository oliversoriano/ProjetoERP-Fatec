"""
Interface gráfica (Tkinter) do Sistema de Movimentação de Peças.
Execute com: python interface_tkinter.py
"""

import tkinter as tk
from tkinter import messagebox, ttk

import projetoerp as erp

COR_PRIMARIA = "#007acc"
NOMES_SETORES = list(erp.SETORES.values())


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        erp.criar_banco_dados()

        self.title("Sistema de Movimentação de Peças")
        self.geometry("900x560")
        self.minsize(820, 480)

        estilo = ttk.Style(self)
        estilo.theme_use("clam")
        estilo.configure("TNotebook.Tab", padding=(16, 8), font=("Arial", 10))
        estilo.configure("Primario.TButton", background=COR_PRIMARIA, foreground="white", font=("Arial", 10, "bold"))
        estilo.map("Primario.TButton", background=[("active", "#005f9e")])
        estilo.configure("Treeview.Heading", font=("Arial", 9, "bold"))

        tk.Label(self, text="Sistema de Movimentação de Peças", font=("Arial", 15, "bold"),
                 bg=COR_PRIMARIA, fg="white", pady=12).pack(fill="x")

        abas = ttk.Notebook(self)
        abas.pack(fill="both", expand=True, padx=12, pady=12)

        self.aba_movimentar = ttk.Frame(abas, padding=16)
        self.aba_cadastrar = ttk.Frame(abas, padding=16)
        self.aba_historico = ttk.Frame(abas, padding=16)
        abas.add(self.aba_movimentar, text="Registrar Movimentação")
        abas.add(self.aba_cadastrar, text="Cadastrar Peça")
        abas.add(self.aba_historico, text="Histórico")

        self.montar_movimentar()
        self.montar_cadastrar()
        self.montar_historico()
        abas.bind("<<NotebookTabChanged>>", lambda e: self.atualizar_historico())

    # ---------- utilidades ----------

    @staticmethod
    def campo(pai, rotulo, linha, largura=30):
        ttk.Label(pai, text=rotulo).grid(row=linha, column=0, sticky="w", pady=6, padx=(0, 10))
        entrada = ttk.Entry(pai, width=largura)
        entrada.grid(row=linha, column=1, sticky="w", pady=6)
        return entrada

    def ler_qrcode_para(self, entrada):
        codigo = erp.ler_qrcode()
        if codigo:
            entrada.delete(0, tk.END)
            entrada.insert(0, codigo)
        else:
            messagebox.showwarning("QR Code", "Nenhum QR Code lido (câmera indisponível ou leitura cancelada).")

    # ---------- aba: registrar movimentação ----------

    def montar_movimentar(self):
        f = self.aba_movimentar

        ttk.Label(f, text="Código da peça").grid(row=0, column=0, sticky="w", pady=6, padx=(0, 10))
        self.mov_codigo = ttk.Entry(f, width=20)
        self.mov_codigo.grid(row=0, column=1, sticky="w")
        ttk.Button(f, text="📷 Ler QR Code", command=lambda: self.ler_qrcode_para(self.mov_codigo)).grid(row=0, column=2, padx=8)
        self.mov_codigo.bind("<FocusOut>", lambda e: self.mostrar_peca())
        self.mov_codigo.bind("<Return>", lambda e: self.mostrar_peca())

        self.mov_info = ttk.Label(f, text="", foreground="#555")
        self.mov_info.grid(row=1, column=1, columnspan=2, sticky="w", pady=(0, 10))

        ttk.Label(f, text="Setor de origem").grid(row=2, column=0, sticky="w", pady=6)
        self.mov_origem = ttk.Combobox(f, values=NOMES_SETORES, state="readonly", width=32)
        self.mov_origem.grid(row=2, column=1, columnspan=2, sticky="w")

        ttk.Label(f, text="Setor de destino").grid(row=3, column=0, sticky="w", pady=6)
        self.mov_destino = ttk.Combobox(f, values=NOMES_SETORES, state="readonly", width=32)
        self.mov_destino.grid(row=3, column=1, columnspan=2, sticky="w")

        ttk.Button(f, text="Registrar movimentação", style="Primario.TButton",
                   command=self.registrar).grid(row=4, column=1, sticky="w", pady=18)

    def mostrar_peca(self):
        peca = erp.buscar_peca(self.mov_codigo.get().strip())
        if peca:
            self.mov_info.config(text=f"✔ {peca[1]} — quantidade: {peca[2]}", foreground="#1a7f37")
        elif self.mov_codigo.get().strip():
            self.mov_info.config(text="Peça não encontrada", foreground="#c0392b")
        else:
            self.mov_info.config(text="")

    def registrar(self):
        codigo = self.mov_codigo.get().strip()
        origem, destino = self.mov_origem.get(), self.mov_destino.get()
        try:
            erp.registrar_movimentacao(codigo, origem, destino)
        except ValueError as erro:
            messagebox.showerror("Movimentação", str(erro))
            return
        messagebox.showinfo("Movimentação", f"Peça {codigo} movimentada:\n{origem} → {destino}")
        self.mov_origem.set(destino)  # a próxima origem costuma ser o destino atual
        self.mov_destino.set("")

    # ---------- aba: cadastrar peça ----------

    def montar_cadastrar(self):
        f = self.aba_cadastrar
        self.cad_codigo = self.campo(f, "Código numérico", 0, 20)
        self.cad_descricao = self.campo(f, "Descrição", 1, 36)
        self.cad_quantidade = self.campo(f, "Quantidade", 2, 10)

        ttk.Button(f, text="Cadastrar e gerar QR Code", style="Primario.TButton",
                   command=self.cadastrar).grid(row=3, column=1, sticky="w", pady=18)

        self.cad_qr = ttk.Label(f)
        self.cad_qr.grid(row=0, column=2, rowspan=5, padx=24, sticky="n")

    def cadastrar(self):
        try:
            caminho = erp.cadastrar_peca(self.cad_codigo.get(), self.cad_descricao.get(), self.cad_quantidade.get())
        except ValueError as erro:
            messagebox.showerror("Cadastro", str(erro))
            return

        # Mostra o QR Code gerado na própria tela
        self.imagem_qr = tk.PhotoImage(file=caminho).subsample(2, 2)
        self.cad_qr.config(image=self.imagem_qr, text=f"peca_{self.cad_codigo.get().strip()}.png", compound="top")
        messagebox.showinfo("Cadastro", f"Peça cadastrada!\nQR Code salvo em:\n{caminho}")
        for entrada in (self.cad_codigo, self.cad_descricao, self.cad_quantidade):
            entrada.delete(0, tk.END)

    # ---------- aba: histórico ----------

    def montar_historico(self):
        f = self.aba_historico
        filtros = ttk.Frame(f)
        filtros.pack(fill="x", pady=(0, 10))

        ttk.Label(filtros, text="Código da peça:").pack(side="left")
        self.hist_codigo = ttk.Entry(filtros, width=16)
        self.hist_codigo.pack(side="left", padx=6)
        self.hist_codigo.bind("<Return>", lambda e: self.atualizar_historico())
        ttk.Button(filtros, text="Filtrar", command=self.atualizar_historico).pack(side="left")
        ttk.Button(filtros, text="📷", width=3, command=lambda: (self.ler_qrcode_para(self.hist_codigo), self.atualizar_historico())).pack(side="left", padx=4)
        ttk.Button(filtros, text="Limpar filtro", command=lambda: (self.hist_codigo.delete(0, tk.END), self.atualizar_historico())).pack(side="left")
        ttk.Button(filtros, text="Apagar histórico da peça", command=self.apagar).pack(side="right")

        colunas = ("data", "codigo", "descricao", "qtd", "origem", "destino")
        titulos = ("Data/Hora", "Peça", "Descrição", "Qtd", "Origem", "Destino")
        larguras = (150, 50, 150, 40, 220, 220)
        self.tabela = ttk.Treeview(f, columns=colunas, show="headings")
        for col, titulo, largura in zip(colunas, titulos, larguras):
            self.tabela.heading(col, text=titulo)
            self.tabela.column(col, width=largura, anchor="center" if col in ("codigo", "qtd") else "w")
        self.tabela.pack(fill="both", expand=True)

    def atualizar_historico(self):
        self.tabela.delete(*self.tabela.get_children())
        for linha in erp.listar_movimentacoes(self.hist_codigo.get().strip() or None):
            self.tabela.insert("", tk.END, values=linha)

    def apagar(self):
        codigo = self.hist_codigo.get().strip()
        if not codigo:
            messagebox.showwarning("Apagar", "Informe o código da peça no filtro.")
            return
        if messagebox.askyesno("Apagar", f"Apagar TODAS as movimentações da peça {codigo}?"):
            removidas = erp.apagar_movimentacoes(codigo)
            messagebox.showinfo("Apagar", f"{removidas} movimentação(ões) removida(s).")
            self.atualizar_historico()


if __name__ == "__main__":
    App().mainloop()
