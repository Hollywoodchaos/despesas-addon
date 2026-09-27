#!/usr/bin/env python3
"""
main.py — Servidor web do addon "Despesas" para Home Assistant.

Reaproveita o despesas_db.py tal como está (todas as funções imprimem
JSON, não fazem "return") — por isso aqui capturamos essa saída em vez
de reescrever a lógica de base de dados, para não arriscar introduzir
bugs numa lógica já testada e em uso.

A base de dados vive em /data/despesas.db — a pasta /data é fornecida
automaticamente pelo Supervisor do Home Assistant a cada addon, de forma
persistente e isolada, sem precisar de nenhuma configuração adicional.
"""
import io
import os
import json
import contextlib

# A base de dados fica dentro da pasta persistente do próprio addon.
os.environ.setdefault("DESPESAS_DB_PATH", "/data/despesas.db")

import despesas_db as db  # noqa: E402  (tem de vir depois de definir a env var)

from flask import Flask, request, jsonify, send_from_directory

app = Flask(__name__, static_folder="static", template_folder="templates")

IDIOMAS_SUPORTADOS = ["pt", "en", "es", "fr", "de", "ru"]


def chamar(fn, *args, **kwargs):
    """Corre uma função do despesas_db.py, captura o JSON que ela imprime
    e devolve-o como dict Python. Ignora linhas vazias/lixo, usa a última
    linha que for JSON válido (protege contra o print() duplicado que
    existe em init_db, e contra qualquer aviso acidental que apareça)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn(*args, **kwargs)
    saida = buf.getvalue().strip()
    for linha in reversed(saida.splitlines()):
        linha = linha.strip()
        if not linha:
            continue
        try:
            return json.loads(linha)
        except json.JSONDecodeError:
            continue
    return {"ok": False, "erro": "sem resposta do motor de despesas"}


def garantir_base_dados():
    if not os.path.exists(os.environ["DESPESAS_DB_PATH"]):
        chamar(db.init_db)
    else:
        # corre sempre o init (é idempotente — usa "IF NOT EXISTS"/"INSERT OR
        # IGNORE") para aplicar migrações novas em bases de dados antigas
        chamar(db.init_db)


# ---------------------------------------------------------------------
# Idioma / interface
# ---------------------------------------------------------------------

@app.route("/")
def index():
    return send_from_directory(app.template_folder, "index.html")


@app.route("/api/idiomas")
def api_idiomas():
    return jsonify({"suportados": IDIOMAS_SUPORTADOS})


@app.route("/api/traducoes/<idioma>")
def api_traducoes(idioma):
    if idioma not in IDIOMAS_SUPORTADOS:
        idioma = "pt"
    caminho = os.path.join(app.root_path, "translations", f"{idioma}.json")
    with open(caminho, "r", encoding="utf-8") as f:
        return jsonify(json.load(f))


# ---------------------------------------------------------------------
# Funcionalidades GRÁTIS
# ---------------------------------------------------------------------

@app.route("/api/categorias", methods=["GET"])
def api_listar_categorias():
    return jsonify(chamar(db.listar_categorias))


@app.route("/api/categorias", methods=["POST"])
def api_add_categoria():
    dados = request.get_json(force=True) or {}
    nome = (dados.get("nome") or "").strip()
    if not nome:
        return jsonify({"ok": False, "erro": "nome em falta"}), 400
    return jsonify(chamar(db.add_categoria, nome))


@app.route("/api/fornecedores", methods=["GET"])
def api_listar_fornecedores():
    categoria = request.args.get("categoria", "")
    if not categoria:
        return jsonify({"ok": False, "erro": "categoria em falta"}), 400
    return jsonify(chamar(db.listar_fornecedores, categoria))


@app.route("/api/fornecedores", methods=["POST"])
def api_add_fornecedor():
    dados = request.get_json(force=True) or {}
    categoria = (dados.get("categoria") or "").strip()
    nome = (dados.get("nome") or "").strip()
    nif = (dados.get("nif") or "").strip() or None
    if not categoria or not nome:
        return jsonify({"ok": False, "erro": "categoria e nome são obrigatórios"}), 400
    return jsonify(chamar(db.add_fornecedor, categoria, nome, nif))


@app.route("/api/formas_pagamento", methods=["GET"])
def api_listar_formas_pagamento():
    return jsonify(chamar(db.listar_formas_pagamento))


@app.route("/api/formas_pagamento", methods=["POST"])
def api_add_forma_pagamento():
    dados = request.get_json(force=True) or {}
    nome = (dados.get("nome") or "").strip()
    if not nome:
        return jsonify({"ok": False, "erro": "nome em falta"}), 400
    return jsonify(chamar(db.add_forma_pagamento, nome))


@app.route("/api/despesa", methods=["POST"])
def api_add_despesa():
    """Registo manual de uma despesa (funcionalidade grátis). A leitura
    automática por QR code e a deteção de duplicado por documento ficam
    reservadas à versão Pro — aqui aceitamos apenas o registo direto,
    com a deteção de duplicado simples (mesmo fornecedor+valor+dia)."""
    dados = request.get_json(force=True) or {}
    categoria = (dados.get("categoria") or "").strip()
    fornecedor = (dados.get("fornecedor") or "").strip()
    valor = dados.get("valor")
    forma_pagamento = (dados.get("forma_pagamento") or "").strip()

    if not categoria or not fornecedor or not forma_pagamento or valor in (None, ""):
        return jsonify({"ok": False, "erro": "campos_obrigatorios"}), 400

    try:
        valor = float(str(valor).replace(",", "."))
    except ValueError:
        return jsonify({"ok": False, "erro": "valor_invalido"}), 400

    forcar = "1" if dados.get("forcar") else "0"
    return jsonify(chamar(db.add_despesa, categoria, fornecedor, valor, forma_pagamento, None, forcar, ""))


@app.route("/api/ultimos_registos", methods=["GET"])
def api_ultimos_registos():
    """Versão grátis e "arcaica" do histórico: só os últimos registos,
    sem pesquisa, sem edição/eliminação, sem filtros por data. A versão
    Pro acrescenta pesquisa completa, edição e eliminação em cima disto
    através de /api/historico e /api/pesquisar."""
    LIMITE_GRATIS = 15
    return jsonify(chamar(db.historico, LIMITE_GRATIS))


# ---------------------------------------------------------------------
# Funcionalidades PRO (bloqueadas nesta versão gratuita)
# ---------------------------------------------------------------------

ENDPOINTS_PRO = [
    "interpretar_qr", "totais", "totais_por_categoria", "pesquisar",
    "historico", "editar_despesa", "eliminar_despesa", "editar_categoria",
    "editar_fornecedor", "eliminar_forma_pagamento", "exportar_csv",
]


def _resposta_pro_bloqueado():
    return jsonify({
        "ok": False,
        "erro": "pro_only",
        "mensagem": "Esta funcionalidade está disponível apenas na versão Pro.",
    }), 402


for _nome in ENDPOINTS_PRO:
    app.add_url_rule(
        f"/api/{_nome}",
        endpoint=f"pro_{_nome}",
        view_func=_resposta_pro_bloqueado,
        methods=["GET", "POST", "PUT", "DELETE"],
    )


if __name__ == "__main__":
    garantir_base_dados()
    app.run(host="0.0.0.0", port=8099)
