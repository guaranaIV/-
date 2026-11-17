import os
import requests
from bs4 import BeautifulSoup

# ▼ 1. イオン北海道eショップの監視URL（そのまま残してあります）
AEON_URLS = [
    "https://es.aeon-hokkaido.jp/eshop/item/list?kw=%E3%83%88%E3%83%AC%E3%83%BC%E3%83%87%E3%82%A3%E3%83%B3%E3%82%B0%E3%82%AB%E3%83%BC%E3%83%89",
    "https://es.aeon-hokkaido.jp/eshop/item/list?kw=%E3%83%A6%E3%83%8B%E3%82%AA%E3%83%B3%E3%82%A2%E3%83%AA%E3%83%BC%E3%83%8A",
    "https://es.aeon-hokkaido.jp/eshop/item/list?kw=%E3%83%9D%E3%82%B1%E3%83%A2%E3%83%B3%E3%82%AB%E3%83%BC%E3%83%89",
    "https://es.aeon-hokkaido.jp/eshop/item/list?kw=%E3%83%AF%E3%83%B3%E3%83%94%E3%83%BC%E3%82%B9%E3%82%AB%E3%83%BC%E3%83%89",
    "https://es.aeon-hokkaido.jp/eshop/item/list?kw=%E3%83%95%E3%83%A5%E3%83%BC%E3%82%B8%E3%83%A7%E3%83%B3%E3%83%AF%E3%83%BC%E3%83%AB%E3%83%89",
]

# ▼ 2. あみあみの監視URL（ユニオンアリーナ在庫あり・予約受付中）
AMIAMI_URLS = [
    "https://slist.amiami.jp/top/search/list?s_keywords=%E3%83%A6%E3%83%8B%E3%82%AA%E3%83%B3%E3%82%A2%E3%83%AA%E3%83%BC%E3%83%8A&s_st_list_preorder_available=1&s_st_list_backorder_available=1&s_st_list_newitem_available=1&s_st_condition_flg=1&pagemax=15",
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
    keywords = ["ポケモン", "ポケカ", "ワンピース", "遊戯王", "ユニオンアリーナ", "カード", "BOX", "トレカ", "ドラゴンボール"]

    # ① イオン北海道の巡回
    for url in AEON_URLS:
        try:
            res = requests.get(url, headers=headers, timeout=15)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, "html.parser")

            for a in soup.find_all("a"):
                text = a.get_text(strip=True)
                href = a.get("href", "")
                if any(k in text for k in keywords):
                    if href.startswith("/"):
                        href = "https://es.aeon-hokkaido.jp" + href
                    entry = f"[イオン] {text} ({href})" if href else f"[イオン] {text}"
                    if entry not in items:
                        items.append(entry)
        except Exception as e:
            print(f"Aeon Error ({url}): {e}")

    # ② あみあみの巡回
    for url in AMIAMI_URLS:
        try:
            res = requests.get(url, headers=headers, timeout=15)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, "html.parser")

            for a in soup.find_all("a", href=True):
                href = a["href"]
                if "gcode=" in href:
                    text = a.get_text(strip=True)
                    if not text:
                        img = a.find("img")
                        if img and img.get("alt"):
                            text = img["alt"].strip()
                    if text:
                        if href.startswith("/"):
                            href = "https://slist.amiami.jp" + href
                        clean_href = href.split("&")[0]
                        entry = f"[あみあみ] {text} ({clean_href})"
                        if entry not in items:
                            items.append(entry)
        except Exception as e:
            print(f"AmiAmi Error ({url}): {e}")

    if not items:
        return

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
                "🚨 **新着・在庫復活を検知しました！**\n\n"
                + "\n".join(f"・{x}" for x in new_lines[:10])
            )
            send_discord(msg)

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        f.write(current_data)

if __name__ == "__main__":
    main()
