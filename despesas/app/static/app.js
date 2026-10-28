// Iris Despesas - interface (nucleo comum Free + Pro)
// JS simples, sem frameworks nem CDN: tudo local, funciona offline.
"use strict";

const Iris = {
  cfg: { edicao: "free", versao: "", link_pro: "#", pin_exigido: false },
  tr: {}, trPt: {},
  idioma: "pt",
  refrescos: [], // funcoes a correr quando muda o idioma
};
window.Iris = Iris;

const $ = (id) => document.getElementById(id);
const isPro = () => Iris.cfg.edicao === "pro";
const t = (k) => (k in Iris.tr ? Iris.tr[k] : (k in Iris.trPt ? Iris.trPt[k] : k));
const LOCALES = { pt: "pt-PT", en: "en-GB", es: "es-ES", fr: "fr-FR", de: "de-DE", ru: "ru-RU" };
const eur = (v) => Number(v || 0).toLocaleString(LOCALES[Iris.idioma] || "pt-PT", { style: "currency", currency: "EUR" });
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const dataCurta = (ts) => {
  const [d, h = ""] = String(ts).split("T");
  const [a, m, di] = d.split("-");
  return `${di}/${m}/${a}` + (h ? " " + h.slice(0, 5) : "");
};
Object.assign(Iris, { $, t, eur, esc, dataCurta, isPro });

async function api(caminho, corpo) {
  const opts = corpo === undefined ? {} : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(corpo),
  };
  const r = await fetch(caminho, opts);
  let j = {};
  try { j = await r.json(); } catch (e) { /* ignora */ }
  j._status = r.status;
  return j;
}
Iris.api = api;

// ---------------------------------------------------------------- idiomas

async function carregarTraducoes(idioma) {
  Iris.idioma = idioma;
  document.documentElement.lang = idioma;
  const [pt, tr] = await Promise.all([
    fetch("api/traducoes/pt").then((r) => r.json()),
    idioma === "pt" ? null : fetch("api/traducoes/" + idioma).then((r) => r.json()),
  ]);
  Iris.trPt = pt;
  Iris.tr = tr || pt;
  aplicarTraducoes();
}

function aplicarTraducoes(raiz) {
  (raiz || document).querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t(el.dataset.i18n); });
  (raiz || document).querySelectorAll("[data-i18n-placeholder]").forEach((el) => { el.placeholder = t(el.dataset.i18nPlaceholder); });
}
Iris.aplicarTraducoes = aplicarTraducoes;

// ---------------------------------------------------------------- UI base

function mostrarMensagem(texto, tipo) {
  const el = $("mensagem");
  el.textContent = texto;
  el.className = "mensagem " + tipo;
  el.style.display = "block";
  clearTimeout(mostrarMensagem._t);
  mostrarMensagem._t = setTimeout(() => { el.style.display = "none"; }, 6000);
  el.scrollIntoView({ behavior: "smooth", block: "nearest" });
}
Iris.mensagem = mostrarMensagem;

function irParaTab(nome) {
  document.querySelectorAll(".tab-btn").forEach((b) => b.classList.toggle("active", b.dataset.tab === nome));
  document.querySelectorAll(".tab-content").forEach((s) => s.classList.toggle("active", s.id === "tab-" + nome));
  const ev = new CustomEvent("iris-tab", { detail: nome });
  document.dispatchEvent(ev);
}
Iris.irParaTab = irParaTab;

function configurarTabs() {
  document.querySelectorAll(".tab-btn").forEach((b) => b.addEventListener("click", () => irParaTab(b.dataset.tab)));
  document.querySelectorAll(".link-pro").forEach((a) => { a.href = Iris.cfg.link_pro; });
}

// Modal simples (usado pelo Pro para editar/eliminar)
Iris.modal = {
  abrir(html) { $("modal").innerHTML = html; aplicarTraducoes($("modal")); $("modal-bg").classList.add("ver"); },
  fechar() { $("modal-bg").classList.remove("ver"); $("modal").innerHTML = ""; },
};

// ---------------------------------------------------------------- registos

function renderRegisto(r, acoes) {
  const li = document.createElement("li");
  li.className = "reg";
  const doc = r.numero_documento ? `<span class="tag">#${esc(r.numero_documento)}</span>` : "";
  li.innerHTML = `
    <div class="l1"><span class="forn">${esc(r.fornecedor)}</span><span class="val">${eur(r.valor)}</span></div>
    <div class="l2"><span>${dataCurta(r.timestamp)}</span><span class="cat">${esc(r.categoria)}</span><span>${esc(r.forma_pagamento)}</span>${doc}</div>`;
  if (acoes) {
    const box = document.createElement("div");
    box.className = "acoes";
    acoes.forEach((a) => {
      const b = document.createElement("button");
      b.className = "mini " + (a.cls || "");
      b.textContent = a.texto;
      b.addEventListener("click", () => a.fn(r));
      box.appendChild(b);
    });
    li.appendChild(box);
  }
  return li;
}
Iris.renderRegisto = renderRegisto;

async function carregarUltimos() {
  const j = await api("api/ultimos_registos" + (isPro() ? "?limite=8" : ""));
  const ul = $("lista-ultimos-ul");
  ul.innerHTML = "";
  const lista = j.historico || [];
  if (!lista.length) { ul.innerHTML = `<li class="vazio" style="justify-content:center">${esc(t("lista_vazia"))}</li>`; return; }
  lista.forEach((r) => ul.appendChild(renderRegisto(r)));
}

async function carregarTotais() {
  if (isPro()) {
    const j = await api("api/totais");
    ["hoje", "semana", "mes", "ano"].forEach((k) => { $("tot-" + k).textContent = eur(j[k]); });
  } else {
    const j = await api("api/total_mes");
    $("tot-mes").textContent = eur(j.mes);
  }
}

// ---------------------------------------------------------------- listas

async function carregarCategorias() {
  const j = await api("api/categorias");
  const cats = j.categorias || [];
  Iris.categorias = cats;
  $("lista-categorias-datalist").innerHTML = cats.map((c) => `<option value="${esc(c)}">`).join("");
  const sel = $("select-categoria-fornecedores");
  const atual = sel.value;
  sel.innerHTML = cats.map((c) => `<option>${esc(c)}</option>`).join("");
  if (atual && cats.includes(atual)) sel.value = atual;
  const ul = $("lista-categorias-ul");
  ul.innerHTML = "";
  cats.forEach((c) => {
    const li = document.createElement("li");
    li.innerHTML = `<span>${esc(c)}</span>`;
    if (isPro() && Iris.pro) {
      const b = document.createElement("button");
      b.className = "mini"; b.textContent = "✏️ " + t("btn_editar");
      b.addEventListener("click", () => Iris.pro.editarCategoria(c));
      li.appendChild(b);
    }
    ul.appendChild(li);
  });
  if (isPro() && Iris.pro && Iris.pro.categoriasMudaram) Iris.pro.categoriasMudaram(cats);
}

async function carregarFormas() {
  const j = await api("api/formas_pagamento");
  const formas = j.formas_pagamento || [];
  const sel = $("input-forma-pagamento");
  const atual = sel.value;
  sel.innerHTML = formas.map((f) => `<option>${esc(f)}</option>`).join("");
  if (atual && formas.includes(atual)) sel.value = atual;
  Iris.formas = formas;
  const ul = $("lista-formas-ul");
  ul.innerHTML = "";
  formas.forEach((f) => {
    const li = document.createElement("li");
    li.innerHTML = `<span>${esc(f)}</span>`;
    if (isPro() && Iris.pro) {
      const b = document.createElement("button");
      b.className = "mini del"; b.textContent = "🗑";
      b.addEventListener("click", () => Iris.pro.eliminarForma(f));
      li.appendChild(b);
    }
    ul.appendChild(li);
  });
}

async function carregarFornecedoresDaCategoria() {
  const cat = $("select-categoria-fornecedores").value;
  const ul = $("lista-fornecedores-ul");
  ul.innerHTML = "";
  if (!cat) return;
  const j = await api("api/fornecedores?categoria=" + encodeURIComponent(cat));
  const det = j.detalhe || [];
  if (!det.length) { ul.innerHTML = `<li class="vazio" style="justify-content:center">${esc(t("lista_vazia"))}</li>`; return; }
  det.forEach((f) => {
    const li = document.createElement("li");
    li.innerHTML = `<span>${esc(f.nome)} ${f.nif ? `<span class="nif">· NIF ${esc(f.nif)}</span>` : ""}</span>`;
    if (isPro() && Iris.pro) {
      const b = document.createElement("button");
      b.className = "mini"; b.textContent = "✏️ " + t("btn_editar");
      b.addEventListener("click", () => Iris.pro.editarFornecedor(cat, f));
      li.appendChild(b);
    }
    ul.appendChild(li);
  });
}

async function sugerirFornecedores() {
  const cat = $("input-categoria").value.trim();
  const dl = $("lista-fornecedores-datalist");
  if (!cat) { dl.innerHTML = ""; return; }
  const j = await api("api/fornecedores?categoria=" + encodeURIComponent(cat));
  dl.innerHTML = (j.fornecedores || []).map((f) => `<option value="${esc(f)}">`).join("");
}

Iris.recarregar = async function () {
  await carregarCategorias();
  await carregarFormas();
  await carregarFornecedoresDaCategoria();
  await carregarUltimos();
  await carregarTotais();
};

// ---------------------------------------------------------------- ações

function ligarAcoes() {
  $("select-categoria-fornecedores").addEventListener("change", carregarFornecedoresDaCategoria);
  $("input-categoria").addEventListener("change", sugerirFornecedores);
  $("input-categoria").addEventListener("input", sugerirFornecedores);

  $("btn-add-categoria").addEventListener("click", async () => {
    const nome = $("input-nova-categoria").value.trim();
    if (!nome) return;
    const j = await api("api/categorias", { nome });
    if (j.ok) { $("input-nova-categoria").value = ""; } else { alert(t("msg_categoria_existe")); }
    await carregarCategorias();
  });

  $("btn-add-fornecedor").addEventListener("click", async () => {
    const categoria = $("select-categoria-fornecedores").value;
    const nome = $("input-novo-fornecedor").value.trim();
    const nif = $("input-novo-fornecedor-nif").value.trim();
    if (!categoria || !nome) return;
    await api("api/fornecedores", { categoria, nome, nif });
    $("input-novo-fornecedor").value = "";
    $("input-novo-fornecedor-nif").value = "";
    await carregarFornecedoresDaCategoria();
  });

  $("btn-add-forma").addEventListener("click", async () => {
    const nome = $("input-nova-forma").value.trim();
    if (!nome) return;
    const j = await api("api/formas_pagamento", { nome });
    if (j.ok) { $("input-nova-forma").value = ""; } else { alert(t("msg_forma_existe")); }
    await carregarFormas();
  });

  let ultimoCorpo = null;
  async function registar(forcar) {
    const categoria = $("input-categoria").value.trim();
    const fornecedor = $("input-fornecedor").value.trim();
    const valor = $("input-valor").value;
    const forma_pagamento = $("input-forma-pagamento").value;
    if (!forcar && (!categoria || !fornecedor || !valor || !forma_pagamento)) {
      mostrarMensagem(t("msg_campos_obrigatorios"), "erro");
      return;
    }
    const corpo = forcar ? ultimoCorpo : { categoria, fornecedor, valor, forma_pagamento };
    if (!forcar && $("input-data") && $("input-data").value) corpo.data = $("input-data").value;
    ultimoCorpo = Object.assign({}, corpo);
    if (forcar) corpo.forcar = true;
    const j = await api("api/despesa", corpo);
    $("btn-forcar").style.display = "none";
    if (j.ok) {
      mostrarMensagem(t("msg_sucesso_despesa"), "sucesso");
      $("input-categoria").value = ""; $("input-fornecedor").value = ""; $("input-valor").value = "";
      await Iris.recarregar();
    } else if (j.duplicado) {
      mostrarMensagem(t("msg_duplicado"), "erro");
      if (j.duplicado_tipo === "heuristica") $("btn-forcar").style.display = "block";
    } else {
      mostrarMensagem(t("msg_erro_generico"), "erro");
    }
  }
  $("form-despesa").addEventListener("submit", (ev) => { ev.preventDefault(); registar(false); });
  $("btn-forcar").addEventListener("click", () => registar(true));
}

// ---------------------------------------------------------------- arranque

async function iniciar() {
  Iris.cfg = await api("api/config");
  $("ver").textContent = Iris.cfg.versao;
  let idioma = null;
  try { idioma = localStorage.getItem("despesas_idioma"); } catch (e) { /* ignora */ }
  idioma = idioma || Iris.cfg.idioma || "pt";
  $("seletor-idioma").value = idioma;
  await carregarTraducoes(idioma);

  $("seletor-idioma").addEventListener("change", async (ev) => {
    try { localStorage.setItem("despesas_idioma", ev.target.value); } catch (e) { /* ignora */ }
    await carregarTraducoes(ev.target.value);
    await Iris.recarregar();
    Iris.refrescos.forEach((fn) => fn());
  });

  configurarTabs();
  ligarAcoes();
  if (isPro() && Iris.initPro) Iris.initPro();
  if ($("input-data")) {
    const d = new Date();
    $("input-data").value = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
  }
  await Iris.recarregar();
  document.dispatchEvent(new CustomEvent("iris-pronto"));
}

iniciar();
