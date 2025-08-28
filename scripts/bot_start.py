import json
import os
import time
import urllib.parse
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

API_ROOT = "https://api.telegram.org"
DEFAULT_WEBAPP_URL = "http://127.0.0.1:5000/"
POLL_INTERVAL_SEC = 1.0


def tg_api(token: str, method: str) -> str:
    return f"{API_ROOT}/bot{token}/{method}"


def http_post_json(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_get(url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def build_start_markup(webapp_url: str) -> Dict[str, Any]:
    return {
        "inline_keyboard": [
            [
                {"text": "Разместить объявление", "web_app": {"url": webapp_url}}
            ]
        ]
    }


def handle_update(token: str, update: Dict[str, Any], webapp_url: str):
    message = update.get("message") or update.get("channel_post")
    if not message:
        return

    chat = message.get("chat", {})
    chat_id = chat.get("id")
    text = message.get("text", "") or ""

    if text.strip().lower().startswith("/start"):
        payload = {
            "chat_id": chat_id,
            "text": "Приложение для создания объявлений",
            "reply_markup": build_start_markup(webapp_url),
        }
        http_post_json(tg_api(token, "sendMessage"), payload)


def run_bot():
    load_dotenv()
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN not set in environment/.env")
        raise SystemExit(1)

    webapp_url = os.environ.get("WEBAPP_URL", DEFAULT_WEBAPP_URL)
    print(f"Using WEBAPP_URL: {webapp_url}")

    offset: Optional[int] = None
    print("Bot polling started. Press Ctrl+C to stop.")
    while True:
        try:
            resp = http_get(tg_api(token, "getUpdates"), {"timeout": 25, "offset": offset} if offset else {"timeout": 25})
            if not resp.get("ok"):
                print("getUpdates error:", resp)
                time.sleep(POLL_INTERVAL_SEC)
                continue

            updates: List[Dict[str, Any]] = resp.get("result", [])
            for upd in updates:
                offset = max(offset or 0, upd.get("update_id", 0) + 1)
                handle_update(token, upd, webapp_url)

        except KeyboardInterrupt:
            print("\nBot stopped by user.")
            break
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            print("HTTPError:", e.code, body)
            time.sleep(POLL_INTERVAL_SEC)
        except Exception as ex:
            print("ERROR:", type(ex).__name__, str(ex))
            time.sleep(POLL_INTERVAL_SEC)


if __name__ == "__main__":
    run_bot()
