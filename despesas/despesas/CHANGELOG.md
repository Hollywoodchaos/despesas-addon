# Changelog

## 1.0.1

- Corrige o arranque do addon: o Flask passa a correr como serviço
  gerido pelo s6-overlay (`rootfs/etc/services.d/despesas/run`), em
  vez de um `CMD` direto — resolve o erro
  `s6-overlay-suexec: fatal: can only run as pid 1`.

## 1.0.0

- Primeira versão pública.
- Registo de despesas por categoria, fornecedor e forma de pagamento.
- Gestão de categorias, fornecedores (com NIF) e formas de pagamento.
- Interface própria via Ingress, em pt/en/es/fr/de/ru.
