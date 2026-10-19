"""
Sistema de Movimentação de Peças (mini ERP de chão de fábrica)

Cada peça recebe um QR Code. Ao passar de um setor para outro, a peça é
"bipada" pela câmera e a movimentação fica registrada no banco SQLite.

Este módulo tem duas partes:
  1. Funções de regra de negócio (usadas pelo terminal e pela interface gráfica)
  2. Menu de terminal (executado com: python projetoerp.py)
"""

import os
import sqlite3
from datetime import datetime

import cv2
import qrcode

# Caminhos sempre relativos à pasta do projeto, independente de onde o script é executado
PASTA_PROJETO = os.path.dirname(os.path.abspath(__file__))
CAMINHO_BANCO = os.path.join(PASTA_PROJETO, "movimentacao_pecas.db")
PASTA_QR_CODES = os.path.join(PASTA_PROJETO, "qrcodes_pecas")

SETORES = {
    '1': 'Ferbal',
    '2': 'Serra',
    '3': 'Fundição',
    '4': 'Usinagem (Torno conv.)',
    '5': 'Usinagem (Torno CNC)',
    '6': 'Usinagem (Fresa conv.)',
    '7': 'Usinagem (Centro de Usinagem)',
    '8': 'Montagem Leve',
    '9': 'Montagem Pesada',
    '10': 'Pintura',
    '11': 'Expedição'
}


# =====================================================================
# 1. REGRAS DE NEGÓCIO
# =====================================================================

def conectar():
    return sqlite3.connect(CAMINHO_BANCO)


def criar_banco_dados():
    os.makedirs(PASTA_QR_CODES, exist_ok=True)
    with conectar() as conn:
        conn.execute('''
        CREATE TABLE IF NOT EXISTS pecas (
            codigo TEXT PRIMARY KEY,
            descricao TEXT,
            quantidade INTEGER,
            data_cadastro TEXT,
            caminho_qrcode TEXT
        )''')
        conn.execute('''
        CREATE TABLE IF NOT EXISTS movimentacoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo_peca TEXT,
            origem TEXT,
            destino TEXT,
            data_hora TEXT,
            FOREIGN KEY (codigo_peca) REFERENCES pecas (codigo)
        )''')


def agora():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def gerar_qrcode(codigo):
    """Gera a imagem do QR Code com o código da peça e devolve o caminho do arquivo."""
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(codigo)
    qr.make(fit=True)

    caminho = os.path.join(PASTA_QR_CODES, f"peca_{codigo}.png")
    qr.make_image(fill_color="black", back_color="white").save(caminho)
    return caminho


def buscar_peca(codigo):
    """Devolve (codigo, descricao, quantidade, caminho_qrcode) ou None."""
    with conectar() as conn:
        return conn.execute(
            'SELECT codigo, descricao, quantidade, caminho_qrcode FROM pecas WHERE codigo = ?', (codigo,)
        ).fetchone()


def cadastrar_peca(codigo, descricao, quantidade):
    """Cadastra a peça e gera o QR Code. Lança ValueError com a mensagem do problema."""
    codigo = str(codigo).strip()
    descricao = str(descricao).strip()

    if not codigo.isdigit():
        raise ValueError("O código da peça deve conter apenas números.")
    if not descricao:
        raise ValueError("Informe a descrição da peça.")
    try:
        quantidade = int(quantidade)
    except (TypeError, ValueError):
        raise ValueError("A quantidade deve ser um número inteiro.")
    if quantidade <= 0:
        raise ValueError("A quantidade deve ser maior que zero.")
    if buscar_peca(codigo):
        raise ValueError("Já existe uma peça com este código.")

    caminho_qrcode = gerar_qrcode(codigo)
    with conectar() as conn:
        conn.execute(
            'INSERT INTO pecas (codigo, descricao, quantidade, data_cadastro, caminho_qrcode) VALUES (?, ?, ?, ?, ?)',
            (codigo, descricao, quantidade, agora(), caminho_qrcode)
        )
    return caminho_qrcode


def registrar_movimentacao(codigo, origem, destino):
    """Registra a passagem da peça de um setor para outro. Lança ValueError se algo estiver errado."""
    if not buscar_peca(codigo):
        raise ValueError("Peça não encontrada no sistema.")
    if origem not in SETORES.values() or destino not in SETORES.values():
        raise ValueError("Setor inválido.")
    if origem == destino:
        raise ValueError("O setor de origem e o de destino devem ser diferentes.")

    with conectar() as conn:
        conn.execute(
            'INSERT INTO movimentacoes (codigo_peca, origem, destino, data_hora) VALUES (?, ?, ?, ?)',
            (codigo, origem, destino, agora())
        )


def listar_movimentacoes(codigo=None, limite=50):
    """Lista (data_hora, codigo, descricao, quantidade, origem, destino), mais recentes primeiro."""
    sql = '''
        SELECT m.data_hora, m.codigo_peca, p.descricao, p.quantidade, m.origem, m.destino
        FROM movimentacoes m
        JOIN pecas p ON m.codigo_peca = p.codigo
    '''
    parametros = []
    if codigo:
        sql += ' WHERE m.codigo_peca = ?'
        parametros.append(codigo)
    sql += ' ORDER BY m.data_hora DESC, m.id DESC LIMIT ?'
    parametros.append(limite)

    with conectar() as conn:
        return conn.execute(sql, parametros).fetchall()


def apagar_movimentacoes(codigo):
    """Apaga todas as movimentações de uma peça e devolve quantas foram removidas."""
    with conectar() as conn:
        return conn.execute('DELETE FROM movimentacoes WHERE codigo_peca = ?', (codigo,)).rowcount


def ler_qrcode():
    """Abre a câmera até ler um QR Code. Devolve o texto lido ou None (cancelado/sem câmera)."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Erro: nenhuma câmera encontrada.")
        return None

    detector = cv2.QRCodeDetector()
    print("\nAponte a câmera para o QR Code da peça... (pressione 'q' para cancelar)")
    lido = None

    while True:
        ok, img = cap.read()
        if not ok:
            break

        dados, _, _ = detector.detectAndDecode(img)
        if dados:
            lido = dados
            break

        cv2.imshow("Leitor QR Code - pressione 'q' para cancelar", img)
        if cv2.waitKey(1) == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    return lido


# =====================================================================
# 2. MENU DE TERMINAL
# =====================================================================

def escolher_setor(pergunta):
    print("\nSetores disponíveis:")
    for numero, nome in SETORES.items():
        print(f"{numero}. {nome}")
    return SETORES.get(input(pergunta).strip())


def obter_codigo():
    print("1. Digitar o código da peça")
    print("2. Ler QR Code da peça")
    opcao = input("Escolha uma opção: ").strip()
    if opcao == '1':
        return input("Digite o código da peça: ").strip()
    if opcao == '2':
        return ler_qrcode()
    print("Opção inválida!")
    return None


def menu_cadastrar():
    print("\n--- Cadastro de Nova Peça ---")
    codigo = input("Código numérico da peça: ")
    descricao = input("Descrição da peça: ")
    quantidade = input("Quantidade: ")
    try:
        caminho = cadastrar_peca(codigo, descricao, quantidade)
        print(f"\nPeça cadastrada com sucesso! QR Code gerado em: {caminho}")
    except ValueError as erro:
        print(f"Erro: {erro}")


def menu_movimentar():
    print("\n--- Registro de Movimentação ---")
    codigo = ler_qrcode()
    if not codigo:
        return

    peca = buscar_peca(codigo)
    if not peca:
        print("Erro: Peça não encontrada no sistema!")
        return
    print(f"\nPeça encontrada: {peca[0]} - {peca[1]} (Quantidade: {peca[2]})")

    origem = escolher_setor("\nNúmero do setor de origem: ")
    destino = escolher_setor("Número do setor de destino: ")
    try:
        registrar_movimentacao(codigo, origem, destino)
        print(f"\nMovimentação registrada: {origem} → {destino}")
    except ValueError as erro:
        print(f"Erro: {erro}")


def menu_historico():
    print("\n--- Histórico de Movimentações ---")
    print("0. Ver histórico completo")
    opcao = input("Digite 0 ou Enter para escolher uma peça: ").strip()
    codigo = None if opcao == '0' else obter_codigo()
    if opcao != '0' and not codigo:
        return

    movimentacoes = listar_movimentacoes(codigo)
    if not movimentacoes:
        print("\nNenhuma movimentação encontrada!")
        return

    print("\nData/Hora | Peça | Descrição | Quantidade | Origem → Destino")
    print("-" * 80)
    for data_hora, cod, descricao, qtd, origem, destino in movimentacoes:
        print(f"{data_hora} | {cod} | {descricao} | {qtd} | {origem} → {destino}")


def menu_limpar():
    print("\n--- Limpar Registros de Movimentação ---")
    codigo = obter_codigo()
    if not codigo:
        return
    if not buscar_peca(codigo):
        print("Erro: Peça não encontrada no sistema!")
        return

    movimentacoes = listar_movimentacoes(codigo, limite=1000)
    if not movimentacoes:
        print("Esta peça não possui movimentações registradas!")
        return

    for data_hora, _, _, _, origem, destino in movimentacoes:
        print(f"{data_hora} | {origem} → {destino}")

    if input("\nApagar TODAS as movimentações desta peça? (S/N): ").strip().upper() == 'S':
        print(f"{apagar_movimentacoes(codigo)} movimentação(ões) removida(s).")
    else:
        print("Operação cancelada.")


def main():
    criar_banco_dados()
    acoes = {'1': menu_movimentar, '2': menu_cadastrar, '3': menu_historico, '4': menu_limpar}

    while True:
        print("\n=== Sistema de Movimentação de Peças ===")
        print("1. Registrar movimentação")
        print("2. Cadastrar nova peça")
        print("3. Ver histórico")
        print("4. Limpar movimentações de peça")
        print("5. Sair")
        opcao = input("Escolha uma opção: ").strip()

        if opcao == '5':
            print("Saindo do sistema...")
            break
        if opcao in acoes:
            acoes[opcao]()
        else:
            print("Opção inválida!")

        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    main()
