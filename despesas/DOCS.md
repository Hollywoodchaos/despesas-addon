# Iris Despesas — Documentação

## Configuração

```yaml
idioma: pt
```

Valores possíveis: `pt`, `en`, `es`, `fr`, `de`, `ru`. Define o idioma inicial sugerido; cada pessoa pode mudar no seletor no canto superior direito (a escolha fica guardada no browser).

## Como usar

1. **Registar**: escolhe (ou escreve) a categoria e o fornecedor, indica o valor e a forma de pagamento.
2. **Categorias / Fornecedores / Pagamentos**: cria os teus próprios. O NIF do fornecedor é opcional.
3. No ecrã principal vês o total do mês e os últimos 15 registos.

## Onde ficam os dados

`/data/despesas.db`, a pasta persistente própria deste addon. Está incluída nas cópias de segurança do Home Assistant e sobrevive a reinícios e atualizações.

## Versão Pro

Leitura de faturas por QR code, proteção contra duplicados, gráficos, resumo para o IRS, histórico com pesquisa, edição e eliminação (com PIN opcional) e exportação para Excel/CSV.
Mais informação: https://ko-fi.com/hollywoodchaos/shop

## Suporte

Encontraste um problema? Abre uma [issue no GitHub](https://github.com/Hollywoodchaos/despesas-addon/issues).
