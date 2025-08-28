import os
import json
import sys
import urllib.request
import urllib.error
from urllib.parse import urlencode
from dotenv import load_dotenv

"""
Usage:
  python scripts/send_webapp_button.py <CHAT_ID> [WEBAPP_URL]

Reads TELEGRAM_BOT_TOKEN from environment (.env is auto-loaded by app.py during runtime, but here we read from OS env only).
You can set env in PowerShell before running:
  $env:TELEGRAM_BOT_TOKEN="<your-token>"

If WEBAPP_URL is omitted, defaults to http://127.0.0.1:5000/
Note: Telegram requires HTTPS for WebApps in production. For local testing use an HTTPS tunnel (e.g., ngrok).
"""

DEFAULT_URL = "http://127.0.0.1:5000/"


def post_json(url: str, payload: dict):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status, resp.read().decode("utf-8")


def main():
    load_dotenv()
    if len(sys.argv) < 2:
        print("ERROR: CHAT_ID is required. Usage: python scripts/send_webapp_button.py <CHAT_ID> [WEBAPP_URL]")
        sys.exit(1)

    chat_id = int(sys.argv[1])
    webapp_url = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_URL

    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("ERROR: TELEGRAM_BOT_TOKEN env var not set. Set it in your shell or .env and reload the shell.")
        sys.exit(2)

    api = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": "Открыть мини‑приложение",
        "reply_markup": {
            "inline_keyboard": [
                [
                    {"text": "Открыть мини‑приложение", "web_app": {"url": webapp_url}}
                ]
            ]
        }
    }

    try:
        status, body = post_json(api, payload)
        print("HTTP:", status)
        print(body)
    except urllib.error.HTTPError as e:
        print("HTTPError:", e.code, e.read().decode("utf-8", errors="ignore"))
        sys.exit(3)
    except Exception as e:
        print("ERROR:", e)
        sys.exit(4)


if __name__ == "__main__":
    main()
