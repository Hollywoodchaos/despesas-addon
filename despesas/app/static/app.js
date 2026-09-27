// app.js — interface do addon Despesas
// Sem frameworks: JS simples, para o addon ficar leve e sem dependências
// externas (nada de CDN, tudo local).

const LINK_PRO = "https://ko-fi.com/SUBSTITUI_PELO_TEU_LINK"; // atualiza quando tiveres a loja pronta

let TRADUCOES = {};

function chaveIdiomaGuardada() {
  return localStorage.getItem("despesas_idioma") || (navigator.language || "pt").slice(0, 2);
}

async function carregarTraducoes(idioma) {
  const resp = await fetch(`api/traducoes/${idioma}`);
  TRADUCOES = await resp.json();
  aplicarTraducoes();
}

function t(chave) {
  return TRADUCOES[chave] || chave;
}

function aplicarTraducoes() {
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    el.textContent = t(el.getAttribute("data-i18n"));
  });
  document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    el.setAttribute("placeholder", t(el.getAttribute("data-i18n-placeholder")));
  });
  document.title = t("app_title");
}

function mostrarMensagem(texto, tipo) {
  const el = document.getElementById("mensagem");
  el.textContent = texto;
  el.className = "mensagem " + (tipo === "erro" ? "erro" : "sucesso");
  el.style.display = "block";
  clearTimeout(mostrarMensagem._timeout);
  mostrarMensagem._timeout = setTimeout(() => { el.style.display = "none"; }, 5000);
}

// ---------------------------------------------------------------------
// Navegação por separadores
// ---------------------------------------------------------------------

function configurarTabs() {
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach((s) => s.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
    });
  });
}

// ---------------------------------------------------------------------
// Categorias
// ---------------------------------------------------------------------

async function carregarCategorias() {
  const resp = await fetch("api/categorias");
  const dados = await resp.json();
  const categorias = dados.categorias || [];

  const datalist = document.getElementById("lista-categorias-datalist");
  datalist.innerHTML = categorias.map((c) => `<option value="${escapeHtml(c)}">`).join("");

  const selectForn = document.getElementById("select-categoria-fornecedores");
  const categoriaAtual = selectForn.value;
  selectForn.innerHTML = categorias.map((c) => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join("");
  if (categorias.includes(categoriaAtual)) selectForn.value = categoriaAtual;

  const ul = document.getElementById("lista-categorias-ul");
  ul.innerHTML = categorias.length
    ? categorias.map((c) => `<li>${escapeHtml(c)}</li>`).join("")
    : `<li>${t("lista_vazia")}</li>`;

  return categorias;
}

document.getElementById("btn-add-categoria").addEventListener("click", async () => {
  const input = document.getElementById("input-nova-categoria");
  const nome = input.value.trim();
  if (!nome) return;
  const resp = await fetch("api/categorias", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nome }),
  });
  const dados = await resp.json();
  if (dados.ok) {
    input.value = "";
    mostrarMensagem(t("msg_categoria_criada"), "sucesso");
    await carregarCategorias();
    await carregarFornecedoresDaCategoria();
  } else {
    const jaExiste = (dados.erro || "").includes("já existe");
    mostrarMensagem(jaExiste ? t("msg_categoria_existe") : t("msg_erro_generico"), "erro");
  }
});

// ---------------------------------------------------------------------
// Fornecedores
// ---------------------------------------------------------------------

async function carregarFornecedoresDaCategoria() {
  const categoria = document.getElementById("select-categoria-fornecedores").value;
  if (!categoria) return;
  const resp = await fetch(`api/fornecedores?categoria=${encodeURIComponent(categoria)}`);
  const dados = await resp.json();
  const fornecedores = dados.fornecedores || [];

  const ul = document.getElementById("lista-fornecedores-ul");
  ul.innerHTML = fornecedores.length
    ? fornecedores.map((f) => `<li>${escapeHtml(f)}</li>`).join("")
    : `<li>${t("lista_vazia")}</li>`;
}

document.getElementById("select-categoria-fornecedores").addEventListener("change", carregarFornecedoresDaCategoria);

document.getElementById("btn-add-fornecedor").addEventListener("click", async () => {
  const categoria = document.getElementById("select-categoria-fornecedores").value;
  const nomeInput = document.getElementById("input-novo-fornecedor");
  const nifInput = document.getElementById("input-novo-fornecedor-nif");
  const nome = nomeInput.value.trim();
  const nif = nifInput.value.trim();
  if (!categoria || !nome) return;

  const resp = await fetch("api/fornecedores", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ categoria, nome, nif }),
  });
  const dados = await resp.json();
  if (dados.ok) {
    nomeInput.value = "";
    nifInput.value = "";
    mostrarMensagem(t("msg_fornecedor_criado"), "sucesso");
    await carregarFornecedoresDaCategoria();
  } else {
    mostrarMensagem(t("msg_erro_generico"), "erro");
  }
});

// ---------------------------------------------------------------------
// Formas de pagamento
// ---------------------------------------------------------------------

async function carregarFormasPagamento() {
  const resp = await fetch("api/formas_pagamento");
  const dados = await resp.json();
  const formas = dados.formas_pagamento || [];

  const select = document.getElementById("input-forma-pagamento");
  select.innerHTML = formas.map((f) => `<option value="${escapeHtml(f)}">${escapeHtml(f)}</option>`).join("");

  const ul = document.getElementById("lista-formas-ul");
  ul.innerHTML = formas.length
    ? formas.map((f) => `<li>${escapeHtml(f)}</li>`).join("")
    : `<li>${t("lista_vazia")}</li>`;
}

document.getElementById("btn-add-forma").addEventListener("click", async () => {
  const input = document.getElementById("input-nova-forma");
  const nome = input.value.trim();
  if (!nome) return;
  const resp = await fetch("api/formas_pagamento", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nome }),
  });
  const dados = await resp.json();
  if (dados.ok) {
    input.value = "";
    mostrarMensagem(t("msg_forma_criada"), "sucesso");
    await carregarFormasPagamento();
  } else {
    const jaExiste = (dados.erro || "").includes("já existe");
    mostrarMensagem(jaExiste ? t("msg_forma_existe") : t("msg_erro_generico"), "erro");
  }
});

async function carregarUltimosRegistos() {
  const resp = await fetch("api/ultimos_registos");
  const dados = await resp.json();
  const registos = dados.historico || [];

  const ul = document.getElementById("lista-ultimos-ul");
  ul.innerHTML = registos.length
    ? registos.map((r) => {
        const data = (r.timestamp || "").replace("T", " ").slice(0, 16);
        const valor = Number(r.valor).toFixed(2).replace(".", ",");
        return `<li>${escapeHtml(data)} — ${escapeHtml(r.categoria)} — ${escapeHtml(r.fornecedor)} — ${valor} € — ${escapeHtml(r.forma_pagamento)}</li>`;
      }).join("")
    : `<li>${t("lista_vazia")}</li>`;
}

// ---------------------------------------------------------------------
// Registar despesa
// ---------------------------------------------------------------------

document.getElementById("form-despesa").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const categoria = document.getElementById("input-categoria").value.trim();
  const fornecedor = document.getElementById("input-fornecedor").value.trim();
  const valor = document.getElementById("input-valor").value;
  const forma_pagamento = document.getElementById("input-forma-pagamento").value;

  if (!categoria || !fornecedor || !valor || !forma_pagamento) {
    mostrarMensagem(t("msg_campos_obrigatorios"), "erro");
    return;
  }

  const resp = await fetch("api/despesa", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ categoria, fornecedor, valor, forma_pagamento }),
  });
  const dados = await resp.json();

  if (dados.ok) {
    mostrarMensagem(t("msg_sucesso_despesa"), "sucesso");
    document.getElementById("input-categoria").value = "";
    document.getElementById("input-fornecedor").value = "";
    document.getElementById("input-valor").value = "";
    await carregarCategorias();
    await carregarUltimosRegistos();
  } else if (dados.duplicado) {
    mostrarMensagem(t("msg_duplicado"), "erro");
  } else {
    mostrarMensagem(t("msg_erro_generico"), "erro");
  }
});

// ---------------------------------------------------------------------
// Utilitários
// ---------------------------------------------------------------------

function escapeHtml(texto) {
  const div = document.createElement("div");
  div.textContent = texto;
  return div.innerHTML;
}

// ---------------------------------------------------------------------
// Arranque
// ---------------------------------------------------------------------

async function iniciar() {
  const idioma = chaveIdiomaGuardada();
  document.getElementById("seletor-idioma").value = idioma;
  await carregarTraducoes(idioma);

  document.getElementById("seletor-idioma").addEventListener("change", async (ev) => {
    const novoIdioma = ev.target.value;
    localStorage.setItem("despesas_idioma", novoIdioma);
    await carregarTraducoes(novoIdioma);
    await carregarCategorias();
    await carregarFormasPagamento();
    await carregarFornecedoresDaCategoria();
    await carregarUltimosRegistos();
  });

  document.getElementById("link-pro-cta").href = LINK_PRO;

  configurarTabs();
  await carregarCategorias();
  await carregarFormasPagamento();
  await carregarFornecedoresDaCategoria();
  await carregarUltimosRegistos();
}

iniciar();
