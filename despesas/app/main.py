#!/usr/bin/env python3
"""
Iris Despesas - servidor web do addon para Home Assistant.

A mesma base serve as duas edicoes:
  * Free: so este ficheiro (registo, categorias, fornecedores, pagamentos)
  * Pro : este ficheiro + pro_routes.py (QR, historico, edicao, analise, IRS...)

A base de dados vive em /data/despesas.db (pasta persistente do addon).
"""
import io
import os
import json
import contextlib

os.environ.setdefault("DESPESAS_DB_PATH", "/data/despesas.db")

import despesas_db as db  # noqa: E402

from flask import Flask, request, jsonify, send_from_directory  # noqa: E402

VERSAO = "2.0.2"
LINK_PRO = "https://ko-fi.com/s/fadc8f11ba"
LIMITE_GRATIS = 15

app = Flask(__name__, static_folder="static", template_folder="templates")
IDIOMAS_SUPORTADOS = ["pt", "en", "es", "fr", "de", "ru"]


def carregar_opcoes():
    """Opcoes do addon: o Supervisor grava-as em /data/options.json."""
    try:
        with open(os.environ.get("DESPESAS_OPTIONS", "/data/options.json"), "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


OPCOES = carregar_opcoes()


def chamar(fn, *args, **kwargs):
    """Corre uma funcao do despesas_db.py (que imprime JSON) e devolve o dict."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn(*args, **kwargs)
    for linha in reversed(buf.getvalue().strip().splitlines()):
        linha = linha.strip()
        if not linha:
            continue
        try:
            return json.loads(linha)
        except json.JSONDecodeError:
            continue
    return {"ok": False, "erro": "sem resposta do motor de despesas"}


def garantir_base_dados():
    chamar(db.init_db)  # idempotente: aplica migracoes em bases antigas


try:
    import pro_routes  # so existe na edicao Pro
    EDICAO = "pro"
except ImportError:
    pro_routes = None
    EDICAO = "free"


# ---------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(app.template_folder, "index.html")


@app.route("/api/config")
def api_config():
    return jsonify({
        "edicao": EDICAO, "versao": VERSAO, "link_pro": LINK_PRO,
        "idioma": OPCOES.get("idioma", "pt"),
        "pin_exigido": bool(str(OPCOES.get("pin_administrador", "") or "").strip()),
    })


@app.route("/api/traducoes/<idioma>")
def api_traducoes(idioma):
    if idioma not in IDIOMAS_SUPORTADOS:
        idioma = "pt"
    with open(os.path.join(app.root_path, "translations", f"{idioma}.json"), "r", encoding="utf-8") as f:
        return jsonify(json.load(f))


# ---------------------------------------------------------------------
# Funcionalidades comuns (Free e Pro)
# ---------------------------------------------------------------------

@app.route("/api/categorias", methods=["GET"])
def api_listar_categorias():
    return jsonify(chamar(db.listar_categorias))


@app.route("/api/categorias", methods=["POST"])
def api_add_categoria():
    nome = ((request.get_json(force=True) or {}).get("nome") or "").strip()
    if not nome:
        return jsonify({"ok": False, "erro": "nome em falta"}), 400
    return jsonify(chamar(db.add_categoria, nome))


@app.route("/api/fornecedores", methods=["GET"])
def api_listar_fornecedores():
    categoria = request.args.get("categoria", "")
    if not categoria:
        return jsonify({"ok": False, "erro": "categoria em falta"}), 400
    con = db.conectar()
    rows = con.execute("""SELECT f.nome, f.nif FROM fornecedores f
        JOIN categorias c ON c.id = f.categoria_id WHERE c.nome = ? ORDER BY f.nome""", (categoria,)).fetchall()
    con.close()
    return jsonify({"categoria": categoria, "fornecedores": [r["nome"] for r in rows],
                    "detalhe": [{"nome": r["nome"], "nif": r["nif"] or ""} for r in rows]})


@app.route("/api/fornecedores", methods=["POST"])
def api_add_fornecedor():
    d = request.get_json(force=True) or {}
    categoria = (d.get("categoria") or "").strip()
    nome = (d.get("nome") or "").strip()
    nif = (d.get("nif") or "").strip() or None
    if not categoria or not nome:
        return jsonify({"ok": False, "erro": "categoria e nome sao obrigatorios"}), 400
    return jsonify(chamar(db.add_fornecedor, categoria, nome, nif))


@app.route("/api/formas_pagamento", methods=["GET"])
def api_listar_formas_pagamento():
    return jsonify(chamar(db.listar_formas_pagamento))


@app.route("/api/formas_pagamento", methods=["POST"])
def api_add_forma_pagamento():
    nome = ((request.get_json(force=True) or {}).get("nome") or "").strip()
    if not nome:
        return jsonify({"ok": False, "erro": "nome em falta"}), 400
    return jsonify(chamar(db.add_forma_pagamento, nome))


@app.route("/api/despesa", methods=["POST"])
def api_add_despesa():
    """Registo de uma despesa. Na edicao Pro aceita tambem data e numero de
    documento (vindos da leitura do QR da fatura)."""
    d = request.get_json(force=True) or {}
    categoria = (d.get("categoria") or "").strip()
    fornecedor = (d.get("fornecedor") or "").strip()
    forma = (d.get("forma_pagamento") or "").strip()
    valor = d.get("valor")
    if not categoria or not fornecedor or not forma or valor in (None, ""):
        return jsonify({"ok": False, "erro": "campos_obrigatorios"}), 400
    try:
        valor = float(str(valor).replace(",", "."))
    except ValueError:
        return jsonify({"ok": False, "erro": "valor_invalido"}), 400
    data = numero = ""
    nif = None
    if EDICAO == "pro":
        data = (d.get("data") or "").strip() or None
        numero = (d.get("numero_documento") or "").strip()
        nif = (d.get("nif") or "").strip() or None
        if nif:
            chamar(db.add_fornecedor, categoria, fornecedor, nif)
    forcar = "1" if d.get("forcar") else "0"
    return jsonify(chamar(db.add_despesa, categoria, fornecedor, valor, forma, data or None, forcar, numero))


@app.route("/api/ultimos_registos", methods=["GET"])
def api_ultimos_registos():
    """Ultimos registos (a edicao Free mostra os ultimos 15, sem pesquisa)."""
    limite = LIMITE_GRATIS
    if EDICAO == "pro":
        try:
            limite = max(1, min(int(request.args.get("limite", 10)), 200))
        except ValueError:
            limite = 10
    r = chamar(db.historico, limite)
    return jsonify(r)


@app.route("/api/total_mes")
def api_total_mes():
    t = chamar(db.totais)
    return jsonify({"mes": t.get("mes", 0)})


# ---------------------------------------------------------------------
# Funcionalidades Pro
# ---------------------------------------------------------------------

if pro_routes:
    pro_routes.registar(app, db, chamar, OPCOES)
else:
    ENDPOINTS_PRO = [
        "totais", "totais_por_categoria", "totais_mensais", "historico", "pesquisar",
        "interpretar_qr", "editar_despesa", "eliminar_despesa", "editar_categoria",
        "editar_fornecedor", "eliminar_forma_pagamento", "exportar_csv", "irs",
    ]

    def _pro_bloqueado():
        return jsonify({"ok": False, "erro": "pro_only",
                        "mensagem": "Disponivel apenas na versao Pro."}), 402

    for _nome in ENDPOINTS_PRO:
        app.add_url_rule(f"/api/{_nome}", endpoint=f"pro_{_nome}", view_func=_pro_bloqueado,
                         methods=["GET", "POST", "PUT", "DELETE"])


if __name__ == "__main__":
    garantir_base_dados()
    app.run(host="0.0.0.0", port=int(os.environ.get("DESPESAS_PORT", "8099")))
