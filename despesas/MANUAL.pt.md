# Iris Despesas (Free) — Manual do utilizador

🇬🇧 [English version](MANUAL.en.md)

## 1. O que é

O Iris Despesas regista o dinheiro que gastas em casa, por **categoria** (Supermercados, Farmácias, Combustível…), **fornecedor** (a loja ou empresa), **valor**, **data** e **forma de pagamento** (cartão, dinheiro, MB Way…). Cada fornecedor pertence a uma categoria.

No ecrã inicial vês o total do mês e os últimos 15 registos.

## 2. Registar uma despesa

Abre o **Iris Despesas** no menu lateral do Home Assistant. O separador **Registar** é o ecrã inicial.

1. **Categoria**: escolhe uma da lista ou escreve uma nova.
2. **Fornecedor**: escreve o nome da loja. A lista sugere os fornecedores dessa categoria. Se for novo, fica criado ao registar.
3. **Valor (€)**: o total, por exemplo `23,50`.
4. **Forma de pagamento**: escolhe uma da lista.
5. Carrega em **Registar Despesa**. Aparece «Despesa registada com sucesso!» e o registo surge em **Últimos Registos**.

**Registo repetido:** se já existir um registo com o mesmo fornecedor, valor e dia, o Iris avisa e não grava. Se for mesmo uma segunda compra igual, carrega em **Registar mesmo assim**.

## 3. Categorias, fornecedores e pagamentos

Cada um tem o seu separador. Para o dia a dia não precisas deles, porque um fornecedor novo é criado quando registas a despesa.

| Separador | Para que serve |
| --- | --- |
| **Categorias** | Escreve o nome e carrega em **Adicionar**. |
| **Fornecedores** | Escolhe a **Categoria**: a lista mostra os fornecedores dela. Para criar um, escreve o nome, o NIF (opcional) e carrega em **Adicionar**. |
| **Pagamentos** | Escreve o nome da forma de pagamento e carrega em **Adicionar**. |

## 4. Corrigir fornecedores (novo na 2.1)

No separador **Fornecedores**, cada fornecedor tem o botão **⚙️ Gerir**. Abre uma janela com três ações. Antes de cada uma, o Iris pede confirmação.

| Quero… | O que faço |
| --- | --- |
| **Mudar o fornecedor para a categoria certa** | Em «Mover para a categoria», escolho a categoria e carrego em **Mover**. As despesas dele vão com ele. |
| **Juntar dois nomes do mesmo sítio** (ex.: «Pingo Doce» e «Pingo Doce Fafe») | Abro **Gerir** no que está errado, escolho o certo em «Juntar ao fornecedor» e carrego em **Juntar**. As despesas passam para o certo e o repetido desaparece. |
| **Apagar um que escrevi mal** | **Eliminar**. Só funciona se o fornecedor ainda não tiver despesas. Se tiver, o Iris diz quantas e deves usar **Juntar**. |

Nada se perde: mover e juntar mantêm todas as despesas.

## 5. Perguntas frequentes

**Registei na categoria errada.** Muda o fornecedor para a categoria certa com **Mover**. (A edição de registos individuais existe na versão Pro.)

**Posso mudar a língua?** Sim, no seletor no canto superior direito: português, inglês, espanhol, francês, alemão e russo.

**Onde ficam os dados?** Em `/data/despesas.db`, a pasta própria do addon. Entra nas cópias de segurança do Home Assistant e sobrevive a atualizações.

**Quero mais.** A versão Pro lê faturas por QR, tem histórico com pesquisa, gráficos, resumo para o IRS, edição de registos e exportação para Excel: https://ko-fi.com/s/fadc8f11ba

**Problemas?** Abre uma issue em https://github.com/Hollywoodchaos/despesas-addon/issues
