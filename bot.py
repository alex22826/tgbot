# -*- coding: utf-8 -*-

import json
import os
import shutil
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(BASE_DIR, ".env")
WORKSPACE = os.path.normpath(os.path.join(BASE_DIR, "..", "botspace"))
CLAUDE_EXE = (
    shutil.which("claude")
    or os.path.expanduser("~/.local/bin/claude.exe" if os.name == "nt" else "~/.local/bin/claude")
)
CLAUDE_TIMEOUT = 1800

HELP = (
    "Привет! Я мост к Claude Code на твоём компьютере.\n\n"
    "Просто напиши задачу, например:\n"
    "• создай репо coffee-site, сделай лендинг кофейни и запушь\n"
    "• какая погода в Москве?\n"
    "• добавь на сайт siteanal блок с отзывами\n\n"
    "Команды:\n"
    "/new — начать новый разговор (забыть контекст)\n"
    "/help — эта справка"
)


def load_env():
    env = {}
    if os.path.exists(ENV_PATH):
        with open(ENV_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    env[k.strip()] = v.strip()
    return env


def save_env(env):
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        for k, v in env.items():
            f.write(f"{k}={v}\n")


ENV = load_env()
TOKEN = ENV.get("TELEGRAM_BOT_TOKEN", "")
if not TOKEN or TOKEN == "PASTE_TOKEN_HERE":
    sys.exit("Заполните TELEGRAM_BOT_TOKEN в файле .env (токен выдаёт @BotFather).")
API = f"https://api.telegram.org/bot{TOKEN}/"


def tg(method, **params):
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(API + method, data=data)
    try:
        with urllib.request.urlopen(req, timeout=70) as r:
            return json.load(r)
    except Exception as e:
        print(f"[tg] {method} error: {e}", flush=True)
        return {"ok": False}


def send(chat_id, text):
    text = text.strip() or "(пустой ответ)"
    for i in range(0, len(text), 4000):
        tg("sendMessage", chat_id=chat_id, text=text[i:i + 4000])


def ask_claude(prompt, session_id):
    os.makedirs(WORKSPACE, exist_ok=True)
    cmd = [
        CLAUDE_EXE, "-p", prompt,
        "--output-format", "json",
        "--dangerously-skip-permissions",
    ]
    if session_id:
        cmd += ["--resume", session_id]
    env = dict(os.environ)
    for var in ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN"):
        val = ENV.get(var, "")
        if val and not val.startswith("PASTE"):
            env[var] = val
    try:
        res = subprocess.run(
            cmd, cwd=WORKSPACE, capture_output=True, stdin=subprocess.DEVNULL,
            encoding="utf-8", errors="replace", timeout=CLAUDE_TIMEOUT, env=env,
        )
    except subprocess.TimeoutExpired:
        return "Задача не уложилась в лимит времени и была прервана.", session_id
    out = (res.stdout or "").strip()
    try:
        data = json.loads(out)
        return data.get("result") or "(готово, но ответ пуст)", data.get("session_id") or session_id
    except json.JSONDecodeError:
        err = (res.stderr or "").strip()
        return out or f"Claude завершился с ошибкой:\n{err[:1500]}", session_id


def main():
    owner = int(ENV["OWNER_ID"]) if ENV.get("OWNER_ID", "").isdigit() else None
    session_id = None
    offset = 0
    me = tg("getMe")
    name = me.get("result", {}).get("username", "?") if me.get("ok") else "?"
    print(f"Бот @{name} запущен. Владелец: {owner or 'первый написавший'}.", flush=True)

    while True:
        upd = tg("getUpdates", offset=offset, timeout=50)
        if not upd.get("ok"):
            time.sleep(5)
            continue
        for u in upd["result"]:
            offset = u["update_id"] + 1
            msg = u.get("message") or {}
            chat_id = msg.get("chat", {}).get("id")
            user_id = msg.get("from", {}).get("id")
            text = (msg.get("text") or "").strip()
            if not chat_id or not text:
                continue

            if owner is None:
                owner = user_id
                ENV["OWNER_ID"] = str(owner)
                save_env(ENV)
                print(f"Владелец зафиксирован: {owner}", flush=True)
            if user_id != owner:
                tg("sendMessage", chat_id=chat_id, text="Это личный бот, доступ закрыт.")
                continue

            if text in ("/start", "/help"):
                send(chat_id, HELP)
                continue
            if text == "/new":
                session_id = None
                send(chat_id, "Начал новый разговор — прежний контекст забыт.")
                continue

            done = threading.Event()

            def typing(cid=chat_id):
                while not done.is_set():
                    tg("sendChatAction", chat_id=cid, action="typing")
                    done.wait(5)

            threading.Thread(target=typing, daemon=True).start()
            try:
                answer, session_id = ask_claude(text, session_id)
            finally:
                done.set()
            send(chat_id, answer)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Остановлен.")
