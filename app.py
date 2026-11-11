# Copyright (c) 2026 Quietcore

import os
import json
import discord
from discord.ext import commands
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import threading
from functools import wraps
from datetime import datetime

# ================= CONFIGURATION =================
BOT_TOKEN = ""   # <--- PASTE YOUR TOKEN HERE
ADMIN_PASSWORD = "changeme"  # <--- CHANGE THIS
PORT = 5000
CONFIG_FILE = "config.json"
DEBUG = False  # Set True to see verbose detection logs

# Users who are EXEMPT from filtering (mods you trust, etc.)
EXEMPT_USERS = []  # e.g. ["123456789012345678"]

# Blocked file extensions (lowercase)
BLOCKED_EXTENSIONS = (
    '.jpg', '.jpeg', '.png', '.gif', '.webp',
    '.bmp', '.mp4', '.mov', '.avi', '.mkv', '.webm',
    '.gi'
)

# Blocked link fragments
BLOCKED_LINK_FRAGMENTS = (
    'tenor.com', 'giphy.com', 'media.discordapp.net',
    'media.tenor.co', 'media.tenor.com', 'imgur.com'
)

# ================= CONFIG MANAGEMENT =================
_config_lock = threading.Lock()

def load_config():
    if not os.path.exists(CONFIG_FILE):
        config = {"blocked_users": [], "enabled": True}
        save_config(config)
        return config
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(cfg):
    with _config_lock:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=4)

config = load_config()

def get_blocklist_ints():
    """Returns the blocklist as ints, safely ignoring bad entries."""
    result = []
    for uid in config.get("blocked_users", []):
        try:
            result.append(int(str(uid).strip()))
        except ValueError:
            print(f"Skipping invalid ID in config: {uid}")
    return result

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")

# ================= FLASK APP =================
app = Flask(__name__)
app.secret_key = os.urandom(24)  # Random session key each boot

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        if request.form["password"] == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        error = "ACCESS DENIED: INCORRECT KEY."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route("/")
@login_required
def index():
    global config
    config = load_config()
    return render_template("index.html", config=config)

@app.route("/api/add_user", methods=["POST"])
@login_required
def add_user():
    global config
    data = request.json
    user_id = str(data.get("user_id") or "").strip()

    # Validate: digits only, sensible length
    if not user_id.isdigit() or not (17 <= len(user_id) <= 20):
        return jsonify({"status": "error", "message": "Invalid Discord ID format (must be 17-20 digits)."}), 400

    current_list = [str(u).strip() for u in config["blocked_users"]]
    if user_id in current_list:
        return jsonify({"status": "error", "message": "User already blocked."}), 400

    config["blocked_users"].append(user_id)
    save_config(config)
    log(f"User {user_id} added to blocklist.")
    return jsonify({"status": "success", "message": f"User {user_id} added."})

@app.route("/api/remove_user", methods=["POST"])
@login_required
def remove_user():
    global config
    data = request.json
    user_id = str(data.get("user_id") or "").strip()

    current_list = [str(u).strip() for u in config["blocked_users"]]
    if user_id not in current_list:
        return jsonify({"status": "error", "message": f"User {user_id} not found."}), 404

    config["blocked_users"] = [u for u in config["blocked_users"] if str(u).strip() != user_id]
    save_config(config)
    log(f"User {user_id} removed from blocklist.")
    return jsonify({"status": "success", "message": f"User {user_id} removed."})

@app.route("/api/toggle_bot", methods=["POST"])
@login_required
def toggle_bot():
    global config
    data = request.json
    config["enabled"] = bool(data.get("enabled", False))
    save_config(config)
    log(f"Bot {'ENABLED' if config['enabled'] else 'DISABLED'} via portal.")
    return jsonify({"status": "success", "message": "Bot status updated."})

# ================= DISCORD BOT =================
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

def is_content_blocked(message):
    """
    Complex filter: returns (blocked: bool, reason: str).
    Checks stickers, attachments (filename + content_type), links, and embeds.
    """
    author_id = message.author.id

    # Exempt trusted users entirely
    if str(author_id) in EXEMPT_USERS:
        return False, None

    # 1. Stickers
    stickers = getattr(message, 'stickers', None)
    if stickers:
        if DEBUG: log(f"   -> Detected STICKER from {author_id}")
        return True, "STICKER"

    # 2. Attachments — check BOTH filename and content_type
    for att in (message.attachments or []):
        filename = (att.filename or "").lower()
        content_type = (att.content_type or "").lower()

        # Filename extension check
        if any(filename.endswith(ext) for ext in BLOCKED_EXTENSIONS):
            if DEBUG: log(f"   -> Detected ATTACHMENT (ext): {filename}")
            return True, "IMAGE/VIDEO"

        # Content type check — catches renamed files
        if content_type.startswith(("image/", "video/")):
            if DEBUG: log(f"   -> Detected ATTACHMENT (type): {filename} [{content_type}]")
            return True, "IMAGE/VIDEO"

    # 3. Links in text
    content = (message.content or "").lower()
    if any(fragment in content for fragment in BLOCKED_LINK_FRAGMENTS):
        if DEBUG: log(f"   -> Detected LINK from {author_id}")
        return True, "LINK"

    # 4. Embeds (Tenor/Giphy auto-generate these)
    for embed in (message.embeds or []):
        etype = str(embed.type or "").lower()
        if etype in ("image", "gifv", "video", "gif"):
            if DEBUG: log(f"   -> Detected EMBED ({etype}) from {author_id}")
            return True, "EMBED"
        if embed.image or embed.video or embed.thumbnail:
            if DEBUG: log(f"   -> Detected EMBED MEDIA from {author_id}")
            return True, "EMBED MEDIA"

    return False, None

async def enforce(message, reason_prefix=""):
    """Deletes the message and sends a warning. Returns True if handled."""
    author_id = message.author.id
    if author_id not in get_blocklist_ints():
        return False

    blocked, reason = is_content_blocked(message)
    if not blocked:
        return False

    try:
        await message.delete()
        log(f"BLOCKED {reason} from {message.author} ({author_id}) in #{getattr(message.channel, 'name', 'DM')}")
    except discord.Forbidden:
        log(f"MISSING PERMISSIONS to delete in #{getattr(message.channel, 'name', '?')} — check Manage Messages + role hierarchy.")
        return True
    except discord.NotFound:
        return True

    try:
        await message.channel.send(
            f">> ERROR 403: {reason_prefix}{reason} TRANSMISSION DENIED. USER @{message.author.name} FLAGGED.",
            delete_after=5
        )
    except discord.Forbidden:
        pass  # Can't send warnings, but deletion already succeeded
    return True

@bot.event
async def on_ready():
    global config
    config = load_config()
    log(f"Bot online as {bot.user} | Guilds: {len(bot.guilds)} | Blocklist: {len(get_blocklist_ints())}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if not config.get("enabled", True):
        await bot.process_commands(message)
        return

    if DEBUG and message.guild:
        log(f"MSG {message.author} in #{getattr(message.channel, 'name', '?')}: {(message.content or '')[:40]}")

    await enforce(message)
    await bot.process_commands(message)

@bot.event
async def on_message_edit(before, after):
    """Catches users editing messages to sneak in GIFs/links."""
    if after.author == bot.user:
        return
    if not config.get("enabled", True):
        return

    # Skip no-op edits
    if (before.content == after.content
            and len(before.attachments or []) == len(after.attachments or [])
            and len(before.embeds or []) == len(after.embeds or [])
            and not getattr(after, 'stickers', None)):
        return

    if DEBUG: log(f"EDIT by {after.author}: {(after.content or '')[:40]}")
    await enforce(after, reason_prefix="EDITED MESSAGE: ")

# ================= LAUNCH =================
def run_flask():
    app.run(host="0.0.0.0", port=PORT, debug=False)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    log(f"Portal: http://localhost:{PORT} (login: /login)")
    bot.run(BOT_TOKEN)