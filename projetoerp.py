# INSTALAR BIBLIOTECA PARA BIPAR QRCODE
# pip install opencv-python qrcode pillow

# VISUALIZAR SE A BIBLIOTECA ESTÁ INSTALADA
# python -c "import cv2; import qrcode; from PIL import Image; import sqlite3; print('Todas as bibliotecas estão instaladas!')"

import sqlite3
from datetime import datetime
import qrcode
from PIL import Image
import cv2
import os

# Configurações
PASTA_QR_CODES = "qrcodes_pecas"
if not os.path.exists(PASTA_QR_CODES):
    os.makedirs(PASTA_QR_CODES)

# Definir setores atualizados
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

# Criar banco de dados
def criar_banco_dados():
    conn = sqlite3.connect('movimentacao_pecas.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pecas (
        codigo TEXT PRIMARY KEY,
        descricao TEXT,
        quantidade INTEGER,
        data_cadastro TEXT,
        caminho_qrcode TEXT
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_peca TEXT,
        origem TEXT,
        destino TEXT,
        data_hora TEXT,
        FOREIGN KEY (codigo_peca) REFERENCES pecas (codigo)
    )
    ''')
    conn.commit()
    conn.close()

# Mostrar setores disponíveis
def mostrar_setores():
    print("\nSetores disponíveis:")
    for key, value in SETORES.items():
        print(f"{key}. {value}")

# Gerar QR Code
def gerar_qrcode(codigo, descricao):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(codigo)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    caminho_arquivo = os.path.join(PASTA_QR_CODES, f"peca_{codigo}.png")
    img.save(caminho_arquivo)
    return caminho_arquivo

# Cadastrar nova peça
def cadastrar_peca():
    print("\n--- Cadastro de Nova Peça ---")
    codigo = input("Digite o código numérico da peça: ").strip()
    
    conn = sqlite3.connect('movimentacao_pecas.db')
    cursor = conn.cursor()
    cursor.execute('SELECT codigo FROM pecas WHERE codigo = ?', (codigo,))
    if cursor.fetchone():
        print("Erro: Já existe uma peça com este código!")
        conn.close()
        return
    
    descricao = input("Digite a descrição da peça: ").strip()
    
    try:
        quantidade = int(input("Digite a quantidade de peças: ").strip())
        if quantidade <= 0:
            raise ValueError
    except ValueError:
        print("Erro: Quantidade deve ser um número inteiro positivo!")
        conn.close()
        return
    
    caminho_qrcode = gerar_qrcode(codigo, descricao)
    
    cursor.execute('''
    INSERT INTO pecas (codigo, descricao, quantidade, data_cadastro, caminho_qrcode)
    VALUES (?, ?, ?, ?, ?)
    ''', (codigo, descricao, quantidade, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), caminho_qrcode))
    
    conn.commit()
    conn.close()
    print(f"\nPeça cadastrada com sucesso!")
    print(f"Código: {codigo} | Descrição: {descricao} | Quantidade: {quantidade}")
    print(f"QR Code gerado em: {caminho_qrcode}")

# Ler QR Code
def ler_qrcode():
    cap = cv2.VideoCapture(0)
    detector = cv2.QRCodeDetector()
    
    print("\nAponte a câmera para o QR Code da peça...")
    print("Pressione 'q' para cancelar")
    
    while True:
        _, img = cap.read()
        data, bbox, _ = detector.detectAndDecode(img)
        
        if data:
            print(f"\nCódigo lido: {data}")
            cap.release()
            cv2.destroyAllWindows()
            return data
        
        cv2.imshow("Leitor QR Code", img)
        
        if cv2.waitKey(1) == ord("q"):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    return None

# Registrar movimentação
def registrar_movimentacao():
    print("\n--- Registro de Movimentação ---")
    codigo = ler_qrcode()
    if not codigo:
        return
    
    conn = sqlite3.connect('movimentacao_pecas.db')
    cursor = conn.cursor()
    cursor.execute('SELECT descricao, quantidade FROM pecas WHERE codigo = ?', (codigo,))
    resultado = cursor.fetchone()
    
    if not resultado:
        print("Erro: Peça não encontrada no sistema!")
        conn.close()
        return
    
    descricao, quantidade = resultado
    print(f"\nPeça encontrada: {codigo} - {descricao} (Quantidade: {quantidade})")
    
    mostrar_setores()
    
    origem = input("\nDigite o número do setor de origem: ").strip()
    destino = input("Digite o número do setor de destino: ").strip()
    
    if origem not in SETORES or destino not in SETORES:
        print("Erro: Setor inválido!")
        conn.close()
        return
    
    cursor.execute('''
    INSERT INTO movimentacoes (codigo_peca, origem, destino, data_hora)
    VALUES (?, ?, ?, ?)
    ''', (codigo, SETORES[origem], SETORES[destino], datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    conn.commit()
    conn.close()
    print(f"\nMovimentação registrada: {SETORES[origem]} → {SETORES[destino]}")

# Limpar movimentações
def limpar_movimentacoes():
    print("\n--- Limpar Registros de Movimentação ---")
    print("1. Buscar pelo código da peça")
    print("2. Ler QR Code da peça")
    opcao = input("Escolha uma opção: ").strip()
    
    if opcao == '1':
        codigo = input("Digite o código da peça: ").strip()
    elif opcao == '2':
        codigo = ler_qrcode()
        if not codigo:
            return
    else:
        print("Opção inválida!")
        return
    
    conn = sqlite3.connect('movimentacao_pecas.db')
    cursor = conn.cursor()
    cursor.execute('SELECT descricao FROM pecas WHERE codigo = ?', (codigo,))
    if not cursor.fetchone():
        print("Erro: Peça não encontrada no sistema!")
        conn.close()
        return
    
    cursor.execute('''
    SELECT id, origem, destino, data_hora 
    FROM movimentacoes 
    WHERE codigo_peca = ?
    ORDER BY data_hora DESC
    ''', (codigo,))
    
    movimentacoes = cursor.fetchall()
    
    if not movimentacoes:
        print("Esta peça não possui movimentações registradas!")
        conn.close()
        return
    
    print("\nMovimentações registradas para esta peça:")
    for mov in movimentacoes:
        print(f"ID: {mov[0]} | {mov[3]} | {mov[1]} → {mov[2]}")
    
    confirmacao = input("\nDeseja realmente apagar TODAS as movimentações desta peça? (S/N): ").strip().upper()
    if confirmacao == 'S':
        cursor.execute('DELETE FROM movimentacoes WHERE codigo_peca = ?', (codigo,))
        conn.commit()
        print(f"Todas as movimentações da peça {codigo} foram removidas!")
    else:
        print("Operação cancelada.")
    
    conn.close()

# Ver histórico
def ver_historico():
    conn = sqlite3.connect('movimentacao_pecas.db')
    cursor = conn.cursor()
    
    print("\n--- Histórico de Movimentações ---")
    print("1. Ver histórico completo")
    print("2. Buscar por código da peça")
    print("3. Ler QR Code da peça")
    opcao = input("Escolha uma opção: ").strip()
    
    if opcao == '1':
        cursor.execute('''
        SELECT m.codigo_peca, p.descricao, p.quantidade, m.origem, m.destino, m.data_hora
        FROM movimentacoes m
        JOIN pecas p ON m.codigo_peca = p.codigo
        ORDER BY m.data_hora DESC
        LIMIT 50
        ''')
    elif opcao == '2':
        codigo = input("Digite o código da peça: ").strip()
        cursor.execute('''
        SELECT m.codigo_peca, p.descricao, p.quantidade, m.origem, m.destino, m.data_hora
        FROM movimentacoes m
        JOIN pecas p ON m.codigo_peca = p.codigo
        WHERE m.codigo_peca = ?
        ORDER BY m.data_hora DESC
        ''', (codigo,))
    elif opcao == '3':
        codigo = ler_qrcode()
        if not codigo:
            conn.close()
            return
        cursor.execute('''
        SELECT m.codigo_peca, p.descricao, p.quantidade, m.origem, m.destino, m.data_hora
        FROM movimentacoes m
        JOIN pecas p ON m.codigo_peca = p.codigo
        WHERE m.codigo_peca = ?
        ORDER BY m.data_hora DESC
        ''', (codigo,))
    else:
        print("Opção inválida!")
        conn.close()
        return
    
    movimentacoes = cursor.fetchall()
    conn.close()
    
    if not movimentacoes:
        print("\nNenhuma movimentação encontrada!")
        return
    
    print("\nData/Hora | Peça | Descrição | Quantidade | Origem → Destino")
    print("-" * 80)
    for mov in movimentacoes:
        print(f"{mov[5]} | {mov[0]} | {mov[1]} | {mov[2]} | {mov[3]} → {mov[4]}")

# Menu principal
def menu_principal():
    print("\n=== Sistema de Movimentação de Peças ===")
    print("1. Registrar movimentação")
    print("2. Cadastrar nova peça")
    print("3. Ver histórico")
    print("4. Limpar movimentações de peça")
    print("5. Sair")
    return input("Escolha uma opção: ").strip()

# Função principal
def main():
    criar_banco_dados()
    
    while True:
        opcao = menu_principal()
        
        if opcao == '1':
            registrar_movimentacao()
        elif opcao == '2':
            cadastrar_peca()
        elif opcao == '3':
            ver_historico()
        elif opcao == '4':
            limpar_movimentacoes()
        elif opcao == '5':
            print("Saindo do sistema...")
            break
        else:
            print("Opção inválida!")
        
        input("\nPressione Enter para continuar...")

if __name__ == "__main__":
    main()