import os
import requests
from bs4 import BeautifulSoup

# 監視するURL（イオン北海道eショップ）
TARGET_URL = "https://es.aeon-hokkaido.jp/eshop/"

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
CACHE_FILE = "last_data.txt"

def send_discord(message):
    if DISCORD_WEBHOOK_URL:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": message})

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    }
    try:
        res = requests.get(TARGET_URL, headers=headers, timeout=15)
        res.encoding = res.apparent_encoding
        soup = BeautifulSoup(res.text, "html.parser")

        items = []
        # ページ内のリンクとテキストからトレカ関連を抽出
        keywords = ["ポケモン", "ポケカ", "ワンピース", "遊戯王", "デュエマ", "カード", "BOX", "パック", "トレカ"]
        for a in soup.find_all("a"):
            text = a.get_text(strip=True)
            href = a.get("href", "")
            if any(k in text for k in keywords):
                # 相対URLならフルURLに変換
                if href.startswith("/"):
                    href = "https://es.aeon-hokkaido.jp" + href
                entry = f"{text} ({href})" if href else text
                if entry not in items:
                    items.append(entry)

        current_data = "\n".join(items)

        old_data = ""
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                old_data = f.read()

        # 前回と内容が変わっていたら新しい項目をDiscordへ通知
        if old_data and current_data != old_data:
            old_lines = set(old_data.splitlines())
            new_lines = [line for line in items if line not in old_lines]
            if new_lines:
                msg = (
                    "🚨 **イオン北海道eショップでトレカ新着/変動あり！**\n\n"
                    + "\n".join(f"・{x}" for x in new_lines[:10])
                    + f"\n\n▼ショップトップ\n{TARGET_URL}"
                )
                send_discord(msg)

        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(current_data)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
