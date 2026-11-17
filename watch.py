import os
import requests
from bs4 import BeautifulSoup

# ▼ 監視したいURLをここに並べる（何個でも追加できます）
TARGET_URLS = [
    "https://es.aeon-hokkaido.jp/eshop/",
    "https://es.aeon-hokkaido.jp/eshop/item/list?kw=%E3%83%A6%E3%83%8B%E3%82%AA%E3%83%B3%E3%82%A2%E3%83%AA%E3%83%BC%E3%83%8A",


"https://es.aeon-hokkaido.jp/eshop/item/list?kw=%E3%83%9D%E3%82%B1%E3%83%A2%E3%83%B3%E3%82%AB%E3%83%BC%E3%83%89",

"https://es.aeon-hokkaido.jp/eshop/item/list?kw=%E3%83%AF%E3%83%B3%E3%83%94%E3%83%BC%E3%82%B9%E3%82%AB%E3%83%BC%E3%83%89",

"https://es.aeon-hokkaido.jp/eshop/item/list?kw=%E3%83%95%E3%83%A5%E3%83%BC%E3%82%B8%E3%83%A7%E3%83%B3%E3%83%AF%E3%83%BC%E3%83%AB%E3%83%89",
# ↓ 例：2つ目以降はこんな風にダブルクォーテーションとカンマで囲んで追加します
    # "https://es.aeon-hokkaido.jp/eshop/goods/...",
]

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
CACHE_FILE = "last_data.txt"

def send_discord(message):
    if DISCORD_WEBHOOK_URL:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": message})

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    }
    items = []
    keywords = ["ポケモン", "ポケカ", "ワンピース", "遊戯王", "ユニオンアリーナ", "カード", "BOX", "パック", "トレカ","ドラゴンボール",]

    try:
        for url in TARGET_URLS:
            res = requests.get(url, headers=headers, timeout=15)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, "html.parser")

            for a in soup.find_all("a"):
                text = a.get_text(strip=True)
                href = a.get("href", "")
                if any(k in text for k in keywords):
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

        if old_data and current_data != old_data:
            old_lines = set(old_data.splitlines())
            new_lines = [line for line in items if line not in old_lines]
            if new_lines:
                msg = (
                    "🚨 **イオン北海道eショップでトレカ新着/変動あり！**\n\n"
                    + "\n".join(f"・{x}" for x in new_lines[:10])
                )
                send_discord(msg)

        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(current_data)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
