# 🚀 Telegram GiftBuyer Bot

[![Python 3.12](https://img.shields.io/badge/python-3.12.10-blue.svg)](https://www.python.org/downloads/release/python-3120/)  
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)  

> Для использованя RU документации, откройте Readme.md
> Automatic and manual purchasing of Telegram gifts based on **Aiogram**.  
> Implemented using **Clean Architecture** principles.

---

## ❗️ Disclaimer

The **official bot** for this repository is **not ready yet**. Any bot using this codebase **is not official**. Use at your own risk.

**Sending gifts to Telegram *channels* is not supported.**

Because Telegram keeps throttling the Bot API whenever new gifts are released, this project’s capabilities may be limited in some situations. Unfortunately, user‑bot solutions are also blocked from time to time. There is no universal alternative at the moment — you will need to search and test on your own.

---

## 💖 Support / Donations

| **Network**            | **Token** | **Address / Tag**                                                                                    |
|------------------------|-----------|-----------------------------------------------------------------------------------------------------|
| 🟥 **TRON (TRC20)**     | USDT      | `TPoRfLVf4bYhZhcqLaY1UXneWD7FsP8n9U`                                                                 |
| 🌐 **TON**             | ANY_TOKEN | `EQBVXzBT4lcTA3S7gxrg4hnl5fnsDKj4oNEzNp09aQxkwj1f`<br>**TAG**: `845065`                              |
| 🪐 **Solana**          | USDT      | `6Y5Ke1iudDqSVFMD6iRw6rVNaG61oeiMhuNfpz4tXWb8`                                                        |
| 🐬 **BSC (BEP20)**     | USDT      | `0xe2ea80596e8d2cca8353c0c54753b15f03d11a4b`                                                         |
| 🏗️ **Polygon**         | USDT      | `0xe2ea80596e8d2cca8353c0c54753b15f03d11a4b`                                                         |
| 🔥 **Ethereum (ERC20)** | USDT      | `0xe2ea80596e8d2cca8353c0c54753b15f03d11a4b`                                                         |

🙏 **Thank you for your support!**

---

## 📋 Table of Contents

- [✨ Features](#-features)  
- [🛠 Tech Stack](#-tech-stack)  
- [📂 Project Structure](#-project-structure)  
- [⚙️ Environment Setup](#️-environment-setup)  
- [⬇️ Installation](#️-installation)  
- [🔧 Configuration](#-configuration)  
- [⚙️ Auto‑Buy Settings](#️-auto-buy-settings)  
- [▶️ Running](#️-running)  
- [📱 Commands & Buttons](#-commands--buttons)  
- [💡 Usage Examples](#-usage-examples)  
- [🌐 Localisation](#-localisation)  
- [👤 Author](#-author)  
- [📝 Licence](#-licence)  

---

## ✨ Features

- **💳 Deposit** — top‑up your balance  
- **🎁 Manual purchase** — specify Gift ID, Telegram ID and quantity  
- **🤖 Auto‑buy** — automatically scan and buy gifts using filters  
- **🕓 History** — full list of transactions  
- **🔕 Do Not Disturb** — enable/disable new‑gift notifications  

---

## 🛠 Tech Stack

- **Python** 3.12.10  
- **Aiogram** 3.21.0  
- **aiohttp** 3.12.14  
- **aiosqlite** 0.21.0  
- **APScheduler** 3.11.0  
- **Loguru** 0.7.3  
- **Pydantic** 2.11.7 + **pydantic‑settings** 2.10.1  
- **SQLAlchemy** 2.0.41  

---

## 📂 Project Structure

```text
app/
├── application/                # use_cases: business logic
│   └── use_cases/
├── core/                       # configuration & logging
│   ├── config.py
│   └── logger.py
├── domain/                     # domain entities & DTOs
│   └── entities/
├── infrastructure/             # integrations & storage
│   ├── db/                     # SQLAlchemy + SQLite
│   ├── scheduler/              # APScheduler
│   ├── services/               # HTTP clients, external APIs
│   └── telegram/               # low‑level Telegram API
├── interfaces/                 # repository & service abstractions
│   ├── repositories/
│   ├── services/
│   └── telegram/               # bot logic
└── main.py                     # entry point (python -m app.main)
```

---

## ⚙️ Environment Setup

1. Install **Python 3.12.10**  
2. Clone the repository and `cd` into it  
3. Create a `.env` file in the root:

| Variable                      | Description                                   |
|-------------------------------|-----------------------------------------------|
| `BOT_TOKEN`                   | Your bot token (no quotes)                    |
| `DATABASE_URL`                | `sqlite+aiosqlite:///user_data.db`            |
| `CHECK_GIFTS_DELAY_SECONDS`   | Gift‑scan interval (seconds)                  |

## EXAMPLE:
BOT_TOKEN=**YOUR_TOKEN**  
DATABASE_URL=**sqlite+aiosqlite:///user_data.db**  
CHECK_GIFTS_DELAY_SECONDS=**3**  

---

## ⬇️ Installation

**Youtube video, how to install repository to your pc RU: [Click](https://www.youtube.com/watch?v=30aBa2Z8fnA)**

```bash
# If you are not familiar with Git:
# 1. Download the ZIP archive:
#    https://github.com/neverwasbored/TgGiftBuyerBot/archive/refs/heads/main.zip
# 2. Extract it:
#    Windows: Right click → “Extract All…”
#    Linux/macOS: unzip main.zip
# 3. Move into the folder:
#    cd TgGiftBuyerBot-main

# Or clone the repository:
git clone https://github.com/neverwasbored/TgGiftBuyerBot.git
cd TgGiftBuyerBot

# Quick Start!
Run `setup_and_run` for your system!

# Create virtual environment (Windows)
python -m venv venv
venv\Scripts\activate

# Or (Linux/macOS)
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## 🔧 Configuration

- **No migrations are used** — tables are created automatically on first run.  
- In `.env` provide **only** your `BOT_TOKEN`; the defaults are fine for the rest.

---

## 🖥️ Local Run Recommended

For security, privacy and easier debugging **it is recommended to run the bot locally** on your own computer.

---

## ⚙️ Auto‑Buy Settings

Auto‑buy lets the bot find and purchase new gifts that match your criteria — no extra commands needed!

### Parameters

- **Price (from / to)**  
  Define a price range in stars. The bot will consider only gifts whose price falls within this range.

- **Supply**  
  Total supply of the gift. The bot will consider only gifts with the specified supply.

- **Auto‑buy cycles**  
  Number of passes through the list of new gifts.  
  Example: with 3 new gifts, where 2 fit the filters, and 2 cycles, the bot will make 4 purchases (2x2), as long as there is enough balance.

---

## ▶️ Running

```bash
# With the virtual environment activated
python -m app.main
```

---

## 📱 Commands & Buttons

### Commands

| Command   | Description      |
|-----------|------------------|
| `/start`  | Start the bot    |
| `/help`   | Help & FAQ       |

### Menu Buttons

| Item                      | Action                                                                                                      |
|---------------------------|-------------------------------------------------------------------------------------------------------------|
| 💳 **Deposit**            | Top‑up balance                                                                                              |
| 🎁 **Buy Gift**           | Manual purchase (input: `GIFT_ID, Telegram_ID, quantity`)                                                  |
| 🤖 **Auto‑Buy**           | Enable/disable auto‑buy; set filters: <br>– Price from/to <br>– Supply <br>– Auto‑buy cycles               |
| 🕓 **History**            | Show all transactions                                                                                       |
| 🔕 **Do Not Disturb**     | Toggle new‑gift notifications                                                                               |

---

## 💡 Usage Examples

1. **Start** the bot:  
   ```text
   /start
   ```
2. **Manual purchase**: press 🎁 and enter, for example:  
   ```
   12345, 67890, 2
   ```
3. **Auto‑buy**: press 🤖, set:  
   - Price: 50 – 200 stars  
   - Supply: 10  
   - Cycles: 3  
4. **View history**: press 🕓  
5. **Notification control**: 🔕 “Do Not Disturb”

---

## 🌐 Localisation

Supported languages: **Russian** and **English**.  
The language is detected automatically from your Telegram settings or via `/help`.

---

## 🔄 `/refund` Command

To use the `/refund` command:

1. Open the database (`user_data.db` in the project root).  My choice is Sqlite Browser (A database editing program)
2. In the `users` table change your account’s `status` from `USER` to `ADMIN`.  
3. Open the `transactions` table and copy the `telegram_payment_charge_id` of the desired transaction.  
4. Return to the bot and execute:  
   ```
   /refund <telegram_payment_charge_id>
   ```

⚠️ **Important:** the refund **will fail** if the bot’s balance in stars is less than the amount in that transaction.

Alternative: withdraw funds via the Telegram bot. You need **at least 1000 stars** on balance to withdraw.

---

## 👤 Author

[neverwasbored](https://github.com/neverwasbored)

---

## 📝 Licence

This project is licensed under the **MIT License**.
