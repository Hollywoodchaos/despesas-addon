# Iris Despesas (Free) — User manual

🇵🇹 [Versão em português](MANUAL.pt.md)

## 1. What it is

Iris Despesas records what you spend at home, by **category** (Groceries, Pharmacies, Fuel…), **supplier** (the shop or company), **amount**, **date** and **payment method** (card, cash, MB Way…). Every supplier belongs to a category.

The home screen shows this month's total and your last 15 entries.

## 2. Adding an expense

Open **Iris Despesas** in the Home Assistant sidebar. The **Add** tab is the home screen.

1. **Category**: pick one from the list or type a new one.
2. **Supplier**: type the shop name. The list suggests the suppliers of that category. If it is new, it is created when you save.
3. **Amount (€)**: the total, for example `23.50`.
4. **Payment method**: pick one from the list.
5. Press **Add Expense**. You see "Expense added successfully!" and the entry appears under **Recent Entries**.

**Duplicate entry:** if an entry with the same supplier, amount and day already exists, Iris warns you and does not save. If it really is a second identical purchase, press **Add anyway**.

## 3. Categories, suppliers and payments

Each has its own tab. For everyday use you do not need them, because a new supplier is created when you add an expense.

| Tab | What it does |
| --- | --- |
| **Categories** | Type the name and press **Add**. |
| **Suppliers** | Pick the **Category**: the list shows its suppliers. To create one, type the name, the tax ID (optional) and press **Add**. |
| **Payments** | Type the payment method name and press **Add**. |

## 4. Fixing suppliers (new in 2.1)

In the **Suppliers** tab, each supplier has a **⚙️ Manage** button. It opens a window with three actions. Iris asks for confirmation before each one.

| I want to… | What I do |
| --- | --- |
| **Put a supplier in the right category** | Under "Move to category", pick the category and press **Move**. Its expenses go with it. |
| **Merge two names for the same place** (e.g. "Pingo Doce" and "Pingo Doce Fafe") | Open **Manage** on the wrong one, pick the right one under "Merge into supplier" and press **Merge**. The expenses move to the right one and the duplicate disappears. |
| **Delete one I misspelled** | **Delete**. It only works if the supplier has no expenses yet. If it has, Iris tells you how many and you should use **Merge**. |

Nothing is lost: moving and merging keep every expense.

## 5. FAQ

**I added it to the wrong category.** Put the supplier in the right category with **Move**. (Editing single entries is a Pro feature.)

**Can I change the language?** Yes, with the selector at the top right: Portuguese, English, Spanish, French, German and Russian.

**Where is my data?** In `/data/despesas.db`, the add-on's own folder. It is included in Home Assistant backups and survives updates.

**I want more.** The Pro edition reads invoices by QR, has searchable history, charts, a tax (IRS) summary, entry editing and Excel export: https://ko-fi.com/s/fadc8f11ba

**Problems?** Open an issue at https://github.com/Hollywoodchaos/despesas-addon/issues
