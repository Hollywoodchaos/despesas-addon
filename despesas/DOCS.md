# Documentação — Despesas

## Configuração

O addon tem uma única opção:

```yaml
idioma: pt
```

Valores possíveis: `pt`, `en`, `es`, `fr`, `de`, `ru`.

Esta opção define apenas o idioma inicial sugerido — cada pessoa que
usar o addon pode mudar de idioma a qualquer momento no seletor no
canto superior direito da interface (a escolha fica guardada no
browser de cada um).

## Onde ficam os dados

Os dados ficam em `/data/despesas.db`, dentro da pasta persistente
própria deste addon. Esta pasta é gerida automaticamente pelo
Supervisor do Home Assistant e não precisa de nenhum mapeamento
manual — os dados sobrevivem a reinícios, atualizações e mudanças de
versão do addon.

## Funcionalidades incluídas nesta versão (gratuita)

- Registar uma despesa (categoria, fornecedor, valor, forma de
  pagamento)
- Criar e consultar categorias
- Criar e consultar fornecedores, com NIF opcional
- Criar e consultar formas de pagamento

## Funcionalidades da versão Pro

- Leitura de faturas por câmara (código QR, norma da Autoridade
  Tributária portuguesa)
- Gráficos e estatísticas de despesa por categoria (dia/semana/mês/ano)
- Histórico completo e pesquisa por fornecedor ou NIF
- Edição e eliminação de registos
- Exportação para Excel/CSV

## Suporte

Encontraste um problema? Abre uma
[issue no GitHub](https://github.com/Hollywoodchaos/despesas-addon/issues).
