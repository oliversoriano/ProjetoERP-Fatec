# INSTALAR BIBLIOTECA PARA TKINTER
# python interface_tkinter.py

import tkinter as tk
from tkinter import messagebox
from projetoerp import (
    cadastrar_peca,
    registrar_movimentacao,
    ver_historico,
    limpar_movimentacoes,
    criar_banco_dados
)

def iniciar_interface():
    criar_banco_dados()  # Garante que o banco esteja criado

    def acao_cadastrar():
        cadastrar_peca()

    def acao_movimentar():
        registrar_movimentacao()

    def acao_historico():
        ver_historico()

    def acao_limpar():
        limpar_movimentacoes()

    def acao_sair():
        if messagebox.askokcancel("Sair", "Deseja realmente sair?"):
            root.destroy()

    root = tk.Tk()
    root.title("Sistema de Movimentação de Peças")
    root.geometry("400x350")
    root.configure(bg="#f0f0f0")

    tk.Label(root, text="Sistema de Movimentação de Peças", font=('Arial', 14, 'bold'), bg="#f0f0f0").pack(pady=15)

    botoes = [
        ("Cadastrar Nova Peça", acao_cadastrar),
        ("Registrar Movimentação", acao_movimentar),
        ("Ver Histórico", acao_historico),
        ("Limpar Movimentações", acao_limpar),
        ("Sair", acao_sair)
    ]

    for texto, comando in botoes:
        tk.Button(root, text=texto, command=comando, width=30, height=2, bg="#007acc", fg="white", font=("Arial", 10)).pack(pady=5)

    root.mainloop()

if __name__ == "__main__":
    iniciar_interface()