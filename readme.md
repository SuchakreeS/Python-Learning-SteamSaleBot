# SteamSaleBot

A Discord bot that watches Steam games for sales. Anyone in the server can submit a game — by link, appid, or even just a partial name — and get pinged (both by DM and in the channel of their choice) the moment it goes on sale.

Built as a project to learn Python from scratch, coming from a JavaScript/TypeScript background.

---

## What it does

- **`!watch <link | appid | name>`** — start watching a game. Accepts a Steam store link, a bare appid, or just typing part of the game's name.
- **`!unwatch <link | appid | name>`** — stop watching a game. If a name matches more than one watched game, the bot asks you to be more specific instead of guessing.
- **`!mylist`** — see every game you're currently watching.
- Every 60 seconds, the bot checks all watched games against Steam's live pricing data. If a discount is newly detected — or changes while a game is still on sale — everyone watching that game gets:
  - A direct message, and
  - One message in whichever channel they ran `!watch` from (deduplicated, so multiple watchers sharing a channel don't get spammed with repeats)

---

## A bug I found along the way

The first version of this project pulled wishlist data from an old, unofficial Steam endpoint (`store.steampowered.com/wishlist/profiles/.../wishlistdata/`). On day one of building, that endpoint started silently redirecting to the Steam homepage instead of returning data or an error — Valve had quietly killed it.

Rather than assume my code was broken, I dug into it, confirmed the endpoint was actually dead by testing it independently, and found Valve's real replacement: the official `IWishlistService/GetWishlist` Web API. That fix is what the current wishlist-fetching logic (in the project's history) is built on.

---

## Tech stack

- **Python** — `discord.py` (bot framework), `requests` (Steam API calls), `python-dotenv` (secrets management)
- **Steam Web API** — `IWishlistService/GetWishlist` and `appdetails` endpoints for live pricing data
- **JSON files** for persistence (watchlist data, last-known discount snapshots) — no database needed at this scale

---

## Project structure

```
├── bot.py              # Bot setup, core events (on_ready, on_message, on_command_error), loads cogs
├── storage.py           # Load/save helpers for watchlist + discount data, link/appid parsing
├── cogs/
│   ├── watchlist.py     # !watch, !unwatch, !mylist commands
│   └── sales.py          # Background loop checking prices every 60s
├── requirements.txt
└── .env                 # DISCORD_BOT_TOKEN (not committed)
```

Commands and the background price-checking loop are organized as **Cogs** — `discord.py`'s built-in pattern for splitting a bot's functionality into self-contained modules, similar in spirit to splitting routes into separate files in an Express app.

---

## Running it yourself

1. Clone the repo and set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/Scripts/activate   # Windows (Git Bash)
   # or: source venv/bin/activate   # Mac/Linux
   ```

2. Install dependencies:
   ```bash
   pip install discord.py requests python-dotenv
   ```

3. Create a `.env` file in the project root:
   ```
   DISCORD_BOT_TOKEN=your_bot_token_here
   ```

4. Set up a bot application in the [Discord Developer Portal](https://discord.com/developers/applications):
   - Enable **Message Content Intent** under Privileged Gateway Intents
   - Generate an invite link via OAuth2 → URL Generator, with the `bot` scope and `Send Messages` / `Read Message History` permissions
   - Invite the bot to your server

5. Run it:
   ```bash
   python bot.py
   ```

---

## What's next

- Migrate from `!` text commands to Discord slash commands with live autocomplete (e.g. `/unwatch` suggesting your watched games as you type)
- Notifications for when a sale *ends*, not just when one starts
- A simple frontend web UI as an alternate way to submit games
- Deploying somewhere for real 24/7 uptime (currently a local-only project)

---

## Why I built this

I came into this project knowing JavaScript/TypeScript but not Python. Rather than working through isolated exercises, I built something real end to end — which meant hitting actual production bugs (a dead API endpoint), learning `async`/`await` for a genuine reason (a bot has to handle multiple users without blocking), and making real architecture calls, like when to refactor and when to hold off. A lot of Python's core ideas ended up mapping cleanly to things I already knew from JS — the syntax was new, but the way of thinking about problems mostly wasn't.