#!/usr/bin/env python3
"""
Base de dados local de despesas domesticas para Home Assistant.
Usa sqlite3 (incluido no Python, sem dependencias externas).

Uso:
    python3 despesas_db.py init
    python3 despesas_db.py add_fornecedor "<categoria>" "<nome>" ["<nif>"]
    python3 despesas_db.py add_despesa "<categoria>" "<fornecedor>" <valor> "<forma_pagamento>"
    python3 despesas_db.py listar_fornecedores "<categoria>"
    python3 despesas_db.py listar_categorias
    python3 despesas_db.py totais
    python3 despesas_db.py pesquisar "<termo>"
    python3 despesas_db.py historico [limite]

Todas as saidas sao em JSON, para serem lidas facilmente por sensores
command_line da Home Assistant.
"""
import sqlite3
import sys
import json
import os
import re
from datetime import datetime, timedelta

DB_PATH = os.environ.get("DESPESAS_DB_PATH", os.path.join(os.path.dirname(__file__), "despesas.db"))

CATEGORIAS_PADRAO = [
    "Supermercados", "Farmácias", "Combustível", "Serviços", "Médicos",
    "Vestuário", "Restaurantes", "Despesas Correntes", "Jogos de Azar",
    "Animais", "Manutenções", "Futilidades",
]

FORMAS_PAGAMENTO_PADRAO = ["Numerário", "Multibanco", "MB WAY", "Débito Direto"]


def conectar():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db():
    con = conectar()
    con.executescript("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS fornecedores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria_id INTEGER NOT NULL REFERENCES categorias(id),
            nome TEXT NOT NULL,
            nif TEXT,
            UNIQUE(categoria_id, nome)
        );
        CREATE TABLE IF NOT EXISTS despesas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            categoria_id INTEGER NOT NULL REFERENCES categorias(id),
            fornecedor_id INTEGER NOT NULL REFERENCES fornecedores(id),
            valor REAL NOT NULL,
            forma_pagamento TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS formas_pagamento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE NOT NULL
        );
    """)
    # Migracao segura: acrescenta a coluna numero_documento se a base de
    # dados ja existia de antes (sem partir nada do que ja la esta).
    try:
        con.execute("ALTER TABLE despesas ADD COLUMN numero_documento TEXT")
    except sqlite3.OperationalError:
        pass  # a coluna ja existe, nao ha nada a fazer
    for nome in CATEGORIAS_PADRAO:
        con.execute("INSERT OR IGNORE INTO categorias (nome) VALUES (?)", (nome,))
    for nome in FORMAS_PAGAMENTO_PADRAO:
        con.execute("INSERT OR IGNORE INTO formas_pagamento (nome) VALUES (?)", (nome,))
    con.commit()
    con.close()
    print(json.dumps({"ok": True, "mensagem": "Base de dados inicializada"}))
    print(json.dumps({"ok": True, "mensagem": "Base de dados inicializada"}))


def get_categoria_id(con, nome_categoria):
    row = con.execute("SELECT id FROM categorias WHERE nome = ?", (nome_categoria,)).fetchone()
    if not row:
        con.execute("INSERT INTO categorias (nome) VALUES (?)", (nome_categoria,))
        con.commit()
        row = con.execute("SELECT id FROM categorias WHERE nome = ?", (nome_categoria,)).fetchone()
    return row["id"]


def add_fornecedor(categoria, nome, nif=None):
    con = conectar()
    cat_id = get_categoria_id(con, categoria)
    con.execute(
        "INSERT OR IGNORE INTO fornecedores (categoria_id, nome, nif) VALUES (?, ?, ?)",
        (cat_id, nome, nif),
    )
    con.commit()
    con.close()
    print(json.dumps({"ok": True, "categoria": categoria, "nome": nome, "nif": nif}))


def verificar_duplicado_por_documento(con, numero_documento):
    """Um MESMO número de documento/ATCUD nunca pode aparecer duas vezes —
    isto é uma certeza absoluta, ao contrário do palpite por fornecedor+valor+dia,
    por isso este tipo de duplicado nunca é 'forçável'."""
    row = con.execute(
        "SELECT id, timestamp FROM despesas WHERE numero_documento = ? LIMIT 1",
        (numero_documento,),
    ).fetchone()
    return dict(row) if row else None


def verificar_duplicado(con, cat_id, fornecedor_id, valor, data_str):
    """Procura uma despesa ja existente no MESMO dia, MESMO fornecedor e
    MESMO valor — sinal provavel de duplo-toque ou re-leitura do mesmo QR.
    So se usa quando NAO ha numero de documento disponivel (registo manual)."""
    row = con.execute("""
        SELECT id, timestamp FROM despesas
        WHERE categoria_id = ? AND fornecedor_id = ? AND valor = ?
          AND timestamp LIKE ?
        LIMIT 1
    """, (cat_id, fornecedor_id, float(valor), f"{data_str}%")).fetchone()
    return dict(row) if row else None


def add_despesa(categoria, fornecedor, valor, forma_pagamento, data=None, forcar="0", numero_documento=""):
    con = conectar()
    cat_id = get_categoria_id(con, categoria)
    con.execute(
        "INSERT OR IGNORE INTO fornecedores (categoria_id, nome) VALUES (?, ?)",
        (cat_id, fornecedor),
    )
    forn_row = con.execute(
        "SELECT id FROM fornecedores WHERE categoria_id = ? AND nome = ?",
        (cat_id, fornecedor),
    ).fetchone()
    if data:
        # data esperada como YYYY-MM-DD; junta a hora atual so para ordenacao
        agora = f"{data}T{datetime.now().strftime('%H:%M:%S')}"
        dia_str = data
    else:
        agora = datetime.now().isoformat(timespec="seconds")
        dia_str = agora[0:10]

    numero_documento = (numero_documento or "").strip()

    if numero_documento:
        # Ha numero de documento (veio de um QR) — e este que manda, e
        # NUNCA e forcavel: o mesmo documento nao pode ser inserido 2 vezes.
        duplicado = verificar_duplicado_por_documento(con, numero_documento)
        if duplicado:
            con.close()
            print(json.dumps({
                "ok": False, "duplicado": True, "duplicado_tipo": "documento",
                "existente_id": duplicado["id"], "existente_timestamp": duplicado["timestamp"],
            }, ensure_ascii=False))
            return
    elif str(forcar) not in ("1", "true", "True"):
        # Sem numero de documento (registo manual) — usa o palpite antigo,
        # que pode ser forcado se for mesmo uma segunda compra igual.
        duplicado = verificar_duplicado(con, cat_id, forn_row["id"], valor, dia_str)
        if duplicado:
            con.close()
            print(json.dumps({
                "ok": False, "duplicado": True, "duplicado_tipo": "heuristica",
                "existente_id": duplicado["id"], "existente_timestamp": duplicado["timestamp"],
            }, ensure_ascii=False))
            return

    con.execute(
        "INSERT INTO despesas (timestamp, categoria_id, fornecedor_id, valor, forma_pagamento, numero_documento) VALUES (?, ?, ?, ?, ?, ?)",
        (agora, cat_id, forn_row["id"], float(valor), forma_pagamento, numero_documento or None),
    )
    con.commit()
    con.close()
    print(json.dumps({"ok": True, "timestamp": agora, "categoria": categoria,
                       "fornecedor": fornecedor, "valor": float(valor),
                       "forma_pagamento": forma_pagamento, "numero_documento": numero_documento}))


def listar_categorias():
    con = conectar()
    rows = con.execute("SELECT nome FROM categorias ORDER BY nome").fetchall()
    con.close()
    print(json.dumps({"categorias": [r["nome"] for r in rows]}, ensure_ascii=False))


def listar_fornecedores(categoria):
    con = conectar()
    rows = con.execute("""
        SELECT f.nome FROM fornecedores f
        JOIN categorias c ON c.id = f.categoria_id
        WHERE c.nome = ?
        ORDER BY f.nome
    """, (categoria,)).fetchall()
    con.close()
    print(json.dumps({"categoria": categoria, "fornecedores": [r["nome"] for r in rows]}, ensure_ascii=False))


def buscar_por_nif(nif):
    """Procura TODOS os fornecedores ja guardados com este NIF — pode haver
    mais do que um (ex.: duas lojas da mesma cadeia partilham o mesmo NIF
    da empresa, o NIF nao identifica o estabelecimento fisico)."""
    con = conectar()
    rows = con.execute("""
        SELECT f.nome as fornecedor, c.nome as categoria
        FROM fornecedores f
        JOIN categorias c ON c.id = f.categoria_id
        WHERE f.nif = ?
        ORDER BY f.nome
    """, (nif,)).fetchall()
    con.close()
    if len(rows) == 0:
        return {"encontrado": False, "correspondencias": []}
    correspondencias = [{"categoria": r["categoria"], "fornecedor": r["fornecedor"]} for r in rows]
    if len(rows) == 1:
        return {"encontrado": True, "ambiguo": False,
                "categoria": correspondencias[0]["categoria"],
                "fornecedor": correspondencias[0]["fornecedor"],
                "correspondencias": correspondencias}
    return {"encontrado": True, "ambiguo": True, "correspondencias": correspondencias}


def interpretar_qr(texto_qr):
    """Interpreta o texto de um codigo QR de fatura portuguesa (norma da AT)
    e devolve os campos uteis: NIF do emitente, data, valor total, tipo de
    documento — e se ja conhecemos esse NIF, tambem a categoria/fornecedor
    ja guardados."""
    padrao = re.compile(r'([A-Z][0-9]?):')
    posicoes = [(m.start(), m.group(1)) for m in padrao.finditer(texto_qr)]
    campos = {}
    for i, (pos, chave) in enumerate(posicoes):
        inicio_valor = pos + len(chave) + 1
        fim_valor = posicoes[i + 1][0] if i + 1 < len(posicoes) else len(texto_qr)
        # alguns emissores separam os campos com '*', outros nao usam nada —
        # limpamos sempre espacos e asteriscos nas pontas do valor
        campos[chave] = texto_qr[inicio_valor:fim_valor].strip().strip('*').strip()

    nif = campos.get("A", "")
    valor = campos.get("O", "").rstrip('*')
    data_bruta = campos.get("F", "")
    data_formatada = ""
    if len(data_bruta) >= 8 and data_bruta[0:8].isdigit():
        data_formatada = f"{data_bruta[0:4]}-{data_bruta[4:6]}-{data_bruta[6:8]}"

    resultado = {
        "ok": bool(nif and data_formatada and valor),
        "nif": nif,
        "data": data_formatada,
        "valor": valor,
        "tipo_documento": campos.get("D", ""),
        "numero_documento": campos.get("H", ""),
    }

    if nif:
        resultado.update(buscar_por_nif(nif))
    else:
        resultado["encontrado"] = False
        resultado["correspondencias"] = []

    print(json.dumps(resultado, ensure_ascii=False))


def totais():
    con = conectar()
    agora = datetime.now()
    inicio_hoje = agora.strftime("%Y-%m-%d")
    inicio_semana = (agora - timedelta(days=agora.weekday())).strftime("%Y-%m-%d")
    inicio_mes = agora.strftime("%Y-%m-01")
    inicio_ano = agora.strftime("%Y-01-01")

    def soma_desde(data_inicio):
        row = con.execute(
            "SELECT COALESCE(SUM(valor), 0) as total FROM despesas WHERE timestamp >= ?",
            (data_inicio,),
        ).fetchone()
        return round(row["total"], 2)

    resultado = {
        "hoje": soma_desde(inicio_hoje),
        "semana": soma_desde(inicio_semana),
        "mes": soma_desde(inicio_mes),
        "ano": soma_desde(inicio_ano),
    }
    con.close()
    print(json.dumps(resultado, ensure_ascii=False))


def pesquisar(termo):
    con = conectar()
    termo_like = f"%{termo}%"
    rows = con.execute("""
        SELECT d.id, d.timestamp, c.nome as categoria, f.nome as fornecedor, f.nif,
               d.valor, d.forma_pagamento, d.numero_documento
        FROM despesas d
        JOIN categorias c ON c.id = d.categoria_id
        JOIN fornecedores f ON f.id = d.fornecedor_id
        WHERE f.nome LIKE ? OR f.nif LIKE ?
        ORDER BY d.timestamp DESC
        LIMIT 200
    """, (termo_like, termo_like)).fetchall()
    con.close()
    print(json.dumps({"resultados": [dict(r) for r in rows]}, ensure_ascii=False))


def historico(limite=20):
    con = conectar()
    rows = con.execute("""
        SELECT d.id, d.timestamp, c.nome as categoria, f.nome as fornecedor,
               d.valor, d.forma_pagamento, d.numero_documento
        FROM despesas d
        JOIN categorias c ON c.id = d.categoria_id
        JOIN fornecedores f ON f.id = d.fornecedor_id
        ORDER BY d.timestamp DESC
        LIMIT ?
    """, (int(limite),)).fetchall()
    con.close()
    print(json.dumps({"historico": [dict(r) for r in rows]}, ensure_ascii=False))


def editar_fornecedor(categoria, nome_atual, novo_nome="", novo_nif=""):
    """Edita o nome e/ou NIF de um fornecedor já existente, mantendo o mesmo
    id interno — por isso todo o histórico de despesas já ligado a ele
    continua ligado, mesmo que o nome ou o NIF mudem."""
    con = conectar()
    cat_id = get_categoria_id(con, categoria)
    row = con.execute(
        "SELECT id, nome, nif FROM fornecedores WHERE categoria_id = ? AND nome = ?",
        (cat_id, nome_atual),
    ).fetchone()
    if not row:
        con.close()
        print(json.dumps({"ok": False, "erro": f"Fornecedor '{nome_atual}' não encontrado em '{categoria}'"}, ensure_ascii=False))
        return

    nome_final = novo_nome.strip() if novo_nome and novo_nome.strip() else row["nome"]
    nif_final = novo_nif.strip() if novo_nif and novo_nif.strip() else row["nif"]

    try:
        con.execute("UPDATE fornecedores SET nome = ?, nif = ? WHERE id = ?", (nome_final, nif_final, row["id"]))
        con.commit()
    except sqlite3.IntegrityError:
        con.close()
        print(json.dumps({"ok": False, "erro": f"Já existe outro fornecedor chamado '{nome_final}' nesta categoria"}, ensure_ascii=False))
        return

    con.close()
    print(json.dumps({
        "ok": True, "categoria": categoria, "nome_anterior": nome_atual,
        "nome": nome_final, "nif": nif_final,
    }, ensure_ascii=False))


def editar_despesa(id_despesa, novo_valor="", nova_data="", nova_forma_pagamento=""):
    """Edita o valor, a data e/ou a forma de pagamento de uma despesa ja
    registada — util para corrigir um erro na escolha inicial, sem teres
    de eliminar e criar tudo de novo."""
    con = conectar()
    row = con.execute("SELECT id, timestamp, valor, forma_pagamento FROM despesas WHERE id = ?", (int(id_despesa),)).fetchone()
    if not row:
        con.close()
        print(json.dumps({"ok": False, "erro": f"Não existe nenhum registo com o id {id_despesa}"}, ensure_ascii=False))
        return

    valor_final = float(novo_valor) if str(novo_valor).strip() else row["valor"]
    forma_final = nova_forma_pagamento.strip() if nova_forma_pagamento and nova_forma_pagamento.strip() else row["forma_pagamento"]
    if nova_data and nova_data.strip():
        hora_atual = row["timestamp"].partition("T")[2] or datetime.now().strftime("%H:%M:%S")
        timestamp_final = f"{nova_data.strip()}T{hora_atual}"
    else:
        timestamp_final = row["timestamp"]

    con.execute(
        "UPDATE despesas SET valor = ?, forma_pagamento = ?, timestamp = ? WHERE id = ?",
        (valor_final, forma_final, timestamp_final, row["id"]),
    )
    con.commit()
    con.close()
    print(json.dumps({
        "ok": True, "id": row["id"], "valor": valor_final,
        "forma_pagamento": forma_final, "timestamp": timestamp_final,
    }, ensure_ascii=False))


def eliminar_despesa(id_despesa):
    con = conectar()
    row = con.execute("""
        SELECT d.id, d.timestamp, c.nome as categoria, f.nome as fornecedor, d.valor
        FROM despesas d
        JOIN categorias c ON c.id = d.categoria_id
        JOIN fornecedores f ON f.id = d.fornecedor_id
        WHERE d.id = ?
    """, (int(id_despesa),)).fetchone()
    if not row:
        con.close()
        print(json.dumps({"ok": False, "erro": f"Não existe nenhum registo com o id {id_despesa}"}))
        return
    con.execute("DELETE FROM despesas WHERE id = ?", (int(id_despesa),))
    con.commit()
    con.close()
    print(json.dumps({"ok": True, "eliminado": dict(row)}, ensure_ascii=False))


def exportar_csv(caminho_destino=None):
    import csv
    if not caminho_destino:
        caminho_destino = os.path.join(os.path.dirname(__file__), "despesas_export.csv")

    pasta_destino = os.path.dirname(caminho_destino)
    if pasta_destino and not os.path.isdir(pasta_destino):
        os.makedirs(pasta_destino, exist_ok=True)

    con = conectar()
    rows = con.execute("""
        SELECT d.id, d.timestamp, c.nome as categoria, f.nome as fornecedor,
               f.nif, d.valor, d.forma_pagamento
        FROM despesas d
        JOIN categorias c ON c.id = d.categoria_id
        JOIN fornecedores f ON f.id = d.fornecedor_id
        ORDER BY d.timestamp ASC
    """).fetchall()
    con.close()

    with open(caminho_destino, "w", newline="", encoding="utf-8-sig") as f:
        escritor = csv.writer(f, delimiter=";")
        escritor.writerow(["ID", "Data", "Hora", "Categoria", "Fornecedor", "NIF", "Valor (€)", "Forma de Pagamento"])
        for r in rows:
            data_parte, _, hora_parte = r["timestamp"].partition("T")
            escritor.writerow([
                r["id"], data_parte, hora_parte, r["categoria"], r["fornecedor"],
                r["nif"] or "", f"{r['valor']:.2f}".replace(".", ","), r["forma_pagamento"],
            ])

    print(json.dumps({"ok": True, "ficheiro": caminho_destino, "total_registos": len(rows)}, ensure_ascii=False))


def add_categoria(nome):
    nome = nome.strip()
    con = conectar()
    existente = con.execute("SELECT id FROM categorias WHERE nome = ?", (nome,)).fetchone()
    if existente:
        con.close()
        print(json.dumps({"ok": False, "erro": f"A categoria '{nome}' já existe"}, ensure_ascii=False))
        return
    con.execute("INSERT INTO categorias (nome) VALUES (?)", (nome,))
    con.commit()
    con.close()
    print(json.dumps({"ok": True, "nome": nome}, ensure_ascii=False))


def editar_categoria(nome_atual, novo_nome):
    nome_atual = nome_atual.strip()
    novo_nome = novo_nome.strip()
    con = conectar()
    row = con.execute("SELECT id FROM categorias WHERE nome = ?", (nome_atual,)).fetchone()
    if not row:
        con.close()
        print(json.dumps({"ok": False, "erro": f"A categoria '{nome_atual}' não existe"}, ensure_ascii=False))
        return
    try:
        con.execute("UPDATE categorias SET nome = ? WHERE id = ?", (novo_nome, row["id"]))
        con.commit()
    except sqlite3.IntegrityError:
        con.close()
        print(json.dumps({"ok": False, "erro": f"Já existe uma categoria chamada '{novo_nome}'"}, ensure_ascii=False))
        return
    con.close()
    print(json.dumps({"ok": True, "nome_anterior": nome_atual, "nome": novo_nome}, ensure_ascii=False))


def listar_formas_pagamento():
    con = conectar()
    rows = con.execute("SELECT nome FROM formas_pagamento ORDER BY nome").fetchall()
    con.close()
    print(json.dumps({"formas_pagamento": [r["nome"] for r in rows]}, ensure_ascii=False))


def add_forma_pagamento(nome):
    nome = nome.strip()
    con = conectar()
    existente = con.execute("SELECT id FROM formas_pagamento WHERE nome = ?", (nome,)).fetchone()
    if existente:
        con.close()
        print(json.dumps({"ok": False, "erro": f"A forma de pagamento '{nome}' já existe"}, ensure_ascii=False))
        return
    con.execute("INSERT INTO formas_pagamento (nome) VALUES (?)", (nome,))
    con.commit()
    con.close()
    print(json.dumps({"ok": True, "nome": nome}, ensure_ascii=False))


def eliminar_forma_pagamento(nome):
    nome = nome.strip()
    con = conectar()
    total = con.execute("SELECT COUNT(*) as n FROM formas_pagamento").fetchone()["n"]
    if total <= 1:
        con.close()
        print(json.dumps({"ok": False, "erro": "Tem de sobrar pelo menos uma forma de pagamento"}, ensure_ascii=False))
        return
    row = con.execute("SELECT id FROM formas_pagamento WHERE nome = ?", (nome,)).fetchone()
    if not row:
        con.close()
        print(json.dumps({"ok": False, "erro": f"A forma de pagamento '{nome}' não existe"}, ensure_ascii=False))
        return
    con.execute("DELETE FROM formas_pagamento WHERE id = ?", (row["id"],))
    con.commit()
    con.close()
    print(json.dumps({"ok": True, "nome": nome}, ensure_ascii=False))


def totais_por_categoria(periodo="mes"):
    """Soma o total gasto em cada categoria, no periodo pedido
    (hoje / semana / mes / ano), para os graficos do dashboard."""
    con = conectar()
    agora = datetime.now()
    inicios = {
        "hoje": agora.strftime("%Y-%m-%d"),
        "semana": (agora - timedelta(days=agora.weekday())).strftime("%Y-%m-%d"),
        "mes": agora.strftime("%Y-%m-01"),
        "ano": agora.strftime("%Y-01-01"),
    }
    data_inicio = inicios.get(periodo, inicios["mes"])
    rows = con.execute("""
        SELECT c.nome as categoria, COALESCE(SUM(d.valor), 0) as total
        FROM categorias c
        LEFT JOIN despesas d ON d.categoria_id = c.id AND d.timestamp >= ?
        GROUP BY c.id
        HAVING total > 0
        ORDER BY total DESC
    """, (data_inicio,)).fetchall()
    con.close()
    resultado = [{"categoria": r["categoria"], "total": round(r["total"], 2)} for r in rows]
    print(json.dumps({"periodo": periodo, "categorias": resultado}, ensure_ascii=False))


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"ok": False, "erro": "comando em falta"}))
        sys.exit(1)

    comando = sys.argv[1]
    args = sys.argv[2:]

    if comando == "init":
        init_db()
    elif comando == "add_fornecedor":
        add_fornecedor(*args)
    elif comando == "add_despesa":
        add_despesa(*args)
    elif comando == "listar_categorias":
        listar_categorias()
    elif comando == "listar_fornecedores":
        listar_fornecedores(*args)
    elif comando == "totais":
        totais()
    elif comando == "pesquisar":
        pesquisar(*args)
    elif comando == "historico":
        historico(*(args or [20]))
    elif comando == "interpretar_qr":
        interpretar_qr(*args)
    elif comando == "eliminar_despesa":
        eliminar_despesa(*args)
    elif comando == "editar_fornecedor":
        editar_fornecedor(*args)
    elif comando == "editar_despesa":
        editar_despesa(*args)
    elif comando == "add_categoria":
        add_categoria(*args)
    elif comando == "editar_categoria":
        editar_categoria(*args)
    elif comando == "totais_por_categoria":
        totais_por_categoria(*(args or ["mes"]))
    elif comando == "listar_formas_pagamento":
        listar_formas_pagamento()
    elif comando == "add_forma_pagamento":
        add_forma_pagamento(*args)
    elif comando == "eliminar_forma_pagamento":
        eliminar_forma_pagamento(*args)
    elif comando == "exportar_csv":
        exportar_csv(*args)
    else:
        print(json.dumps({"ok": False, "erro": f"comando desconhecido: {comando}"}))
        sys.exit(1)


if __name__ == "__main__":
    main()