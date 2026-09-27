# Despesas Add-on para Home Assistant

Um addon simples para registares despesas domésticas diretamente do
Home Assistant — sem depender de cartões Lovelace nem de scripts YAML
espalhados. Interface própria, acessível pelo menu lateral (Ingress),
disponível em **Português, English, Español, Français, Deutsch e
Русский**.

## Instalação

1. Em **Definições → Add-ons → Loja de Add-ons → ⋮ → Repositórios**,
   adiciona:
   ```
   https://github.com/Hollywoodchaos/despesas-addon
   ```
2. Procura por **"Despesas"** na loja, instala e inicia.
3. Aparece um item **"Despesas"** no menu lateral do Home Assistant.

## Funcionalidades (versão gratuita)

- Registar despesas por categoria, fornecedor e forma de pagamento
- Criar e listar categorias
- Criar e listar fornecedores (com NIF opcional)
- Criar e listar formas de pagamento
- Interface em 6 idiomas

## Versão Pro

Desbloqueia leitura de faturas por câmara (QR code), gráficos e
estatísticas por categoria, histórico completo e pesquisa, edição e
eliminação de registos, e exportação para Excel/CSV.
Mais informação: *(link a adicionar quando a loja estiver pronta)*.

50% do valor de cada licença Pro é doado a uma instituição de
solidariedade portuguesa.

## Onde ficam os dados

A base de dados (`despesas.db`) fica na pasta persistente própria do
addon (`/data`), gerida automaticamente pelo Supervisor do Home
Assistant — sobrevive a reinícios e atualizações do addon.

## Licença

MIT — ver [LICENSE](LICENSE).
