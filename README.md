# GIF Blocker Bot — Setup Guide Copyright (c) 2026 Quietcore

So you want to run our bot. Nice. This guide assumes you know basically nothing — if you can install a program and copy-paste, you're qualified. Work through it in order and don't skip steps, because half the problems people run into come from skipped steps (we know because we ran into all of them ourselves while building this).

## What you need

- A Discord account
- Any computer (Windows / Mac / Linux)
- ~15-20 minutes

## Folder layout

Don't rename or move things around. The bot expects this exact structure:

```
gif-blocker/
├── app.py              <- bot + web panel, the main program
├── config.json         <- stores the blocklist
├── templates/
│   ├── index.html      <- control panel page
│   └── login.html      <- password page
└── static/
    ├── style.css
    └── script.js
```

The two HTML files live in `templates` and the css/js live in `static` — Flask looks for them there by name, so if they're sitting loose in the main folder you'll get template-not-found errors. Keep the whole folder somewhere easy like your Desktop.

## Installing Python

If you already have Python 3.9+, skip ahead.

1. Go to **https://www.python.org/downloads/**
2. Hit the download button, run the installer.
3. **Windows users:** there's a checkbox on the first screen called **"Add Python to PATH"**. Tick it. We're serious. This one checkbox is responsible for about 90% of the setup problems we get asked about.
4. Install, then open a terminal (Windows key → type `cmd` → Enter) and check:

```
python --version
```

Should print something like `Python 3.12.4`. If it says "'python' is not recognized", you missed the checkbox — reinstall.

## Installing the bits the bot depends on

The bot runs on `discord.py` and `flask`. In the same terminal:

```
pip install discord.py flask flask-cors
```

Loads of text scrolls past, that's fine. You're looking for the absence of red ERROR at the end.

If `pip` isn't a thing on your machine, try `python -m pip install discord.py flask flask-cors`.

## Making the bot on Discord's side

The bot needs its own "application" registered with Discord. Sounds scary, it's just forms.

1. Head to **https://discord.com/developers/applications** and log in.
2. **New Application** (top right), name it, create it.

**Getting the token:**

3. Left sidebar → **Bot**.
4. **Reset Token**, confirm, and a long nonsense string appears. Copy it **now** — Discord hides it afterwards.
5. Guard that token with your life. Anyone holding it controls your bot. Don't post it, don't screenshot it, don't commit it to GitHub. If it ever leaks, come back here and Reset Token.

**Flipping the intents on:**

6. Same Bot page, scroll to **Privileged Gateway Intents** and enable:
   - **Server Members Intent**
   - **Message Content Intent**

If you skip these the bot connects fine but can't see anything — it just sits there while GIFs fly past. We may have done this. Twice.

**Inviting it to your server:**

7. Sidebar → **OAuth2 → URL Generator**.
8. Under Scopes: tick `bot` and `applications.commands`.
9. Under Bot Permissions: tick **Manage Messages**, **Send Messages**, **Read Message History**.
10. Copy the generated URL at the bottom, open it in your browser, pick your server, authorize.

The bot shows up in your member list, offline. Not for long.

One more thing: in Server Settings → Roles, drag the bot's role **above** everyone it's supposed to moderate. Discord won't let it delete messages from people who outrank it.

## Wiring in your token and password

Open `app.py` in any text editor (Notepad does the job) and find this near the top:

```python
BOT_TOKEN = ""   # <--- PASTE YOUR TOKEN HERE
ADMIN_PASSWORD = "changeme"  # <--- CHANGE THIS
```

Paste your token between the quotes, and change the password — that password is what stands between random people and your control panel, so don't leave the default.

## Running it

Terminal → into your folder. Easiest way on Windows: type `cd ` (with the space), drag the folder from Explorer into the terminal window so the path fills itself in, press Enter.

Then:

```
python app.py
```

You want to see:

```
[21:05:12] Portal: http://localhost:5000 (login: /login)
[21:05:15] Bot online as GIF Blocker | Guilds: 1 | Blocklist: 0
```

Bot's live. Green dot and everything.

## The control panel

Browser → **http://localhost:5000** → log in with your password.

From the panel you can:
- turn the bot on/off
- add a user ID to the blocklist
- remove one

To grab someone's ID: Discord Settings → Advanced → **Developer Mode on**, then right-click the person → **Copy User ID**. Paste that in.

Anyone on the blocklist who posts a GIF, sticker, image or blocked link gets their message insta-deleted, with a warning message that disappears after a few seconds.

Quick note on how the blocklist works: the bot only polices people you've actually blocked. It's not a server-wide rule — it's targeted. Also leave `config.json` mostly alone; the panel writes to it automatically, and the empty-looking entries in a fresh install are normal.

## When it breaks

| What you see | What it means |
|---|---|
| `'python' is not recognized` | No PATH. Reinstall Python, tick the box, reopen terminal. |
| `Improper token has been passed` | Token is wrong — missing characters or extra spaces. Reset it and repaste. |
| Bot online, deletes nothing | Intents are off (see the Bot page step) or the user isn't on the blocklist. |
| `MISSING PERMISSIONS` in the console | Bot lacks Manage Messages, or its role is under the person it tried to moderate. |
| Browser says "refused to connect" | The bot isn't running — check the terminal for errors. |
| "user not found" when removing | The panel reloads config on every page visit, so just refresh (F5) and try again. |
| Edits getting through | They shouldn't — edit-detection is built in. Make sure the bot's running the latest `app.py`. |

## One last thing about the token

Doesn't matter how many times we say it, someone will paste their token into a public repo. Don't. Keep the token in `app.py` on your machine only, and if you fork/redistribute this project, blank the token line first.

That's everything. If you get stuck, read the troubleshooting table again before assuming the bot's broken — it's usually one checkbox.

— Devs of the bot
