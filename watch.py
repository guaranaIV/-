import os
import requests
from bs4 import BeautifulSoup

# ▼ 1. イオン北海道eショップの監視URL（指定タイトルの検索一覧をすべて追加）
AEON_URLS = [
    "https://es.aeon-hokkaido.jp/eshop/",
    "https://es.aeon-hokkaido.jp/eshop/item/list?kw=%E3%83%A6%E3%83%8B%E3%82%AA%E3%83%B3%E3%82%A2%E3%83%AA%E3%83%BC%E3%83%8A",
    "https://es.aeon-hokkaido.jp/eshop/item/list?kw=%E3%83%9D%E3%82%B1%E3%83%A2%E3%83%B3%E3%82%AB%E3%83%BC%E3%83%89",
    "https://es.aeon-hokkaido.jp/eshop/item/list?kw=%E3%83%AF%E3%83%B3%E3%83%94%E3%83%BC%E3%82%B9%E3%82%AB%E3%83%BC%E3%83%89",
    "https://es.aeon-hokkaido.jp/eshop/item/list?kw=%E3%83%95%E3%83%A5%E3%83%BC%E3%82%B8%E3%83%A7%E3%83%B3%E3%83%AF%E3%83%BC%E3%83%AB%E3%83%89",
    "https://es.aeon-hokkaido.jp/eshop/item/list?kw=%E3%83%87%E3%82%B8%E3%83%A2%E3%83%B3%E3%82%AB%E3%83%BC%E3%83%89",
    "https://es.aeon-hokkaido.jp/eshop/item/list?kw=%E9%81%8A%E6%88%AF%E7%8E%8B",
]

# ▼ 2. あみあみ監視キーワード（全6タイトル）
AMIAMI_KEYWORDS = [
    "ユニオンアリーナ",
    "ワンピースカード",
    "ポケモンカード",
    "フュージョンワールド",
    "デジモンカード",
    "遊戯王",
]

# ▼ 3. ヨドバシカメラの監視URL（トレカカテゴリー）
YODOBASHI_URLS = [
    "https://www.yodobashi.com/category/141001/141651/141662/",
]

# ▼ 4. 共通の除外ワード（スタートデッキは通知・アイドルマスターやサプライは除外）
EXCLUDE_WORDS = [
    "ウエハース", "グミ", "チョコ", "スナック", "Tシャツ", "タオル", "マイナンバー", "ギフト",
    "スリーブ", "プレイマット", "ストレージ", "デッキケース",
    "アイドルマスター",
]

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
CACHE_FILE = "last_data.txt"

def send_discord(message):
    if DISCORD_WEBHOOK_URL:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": message})

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    }
    items = []

    aeon_keywords = [
        "ポケモンカード", "ポケカ", "拡張パック", "強化拡張パック", "ハイクラスパック",
        "ワンピースカード", "ONE PIECEカード",
        "遊戯王", "OCG",
        "ユニオンアリーナ", "UNION ARENA",
        "フュージョンワールド", "ドラゴンボールスーパーカード",
        "ロルカナ", "LORCANA",
        "デュエル・マスターズ", "デュエマ",
        "デジモンカード",
    ]

    # ① イオン北海道の巡回
    for url in AEON_URLS:
        try:
            res = requests.get(url, headers=headers, timeout=15)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, "html.parser")

            for a in soup.find_all("a"):
                text = a.get_text(strip=True)
                href = a.get("href", "")
                if any(k in text for k in aeon_keywords) and not any(ng in text for ng in EXCLUDE_WORDS):
                    if href.startswith("/"):
                        href = "https://es.aeon-hokkaido.jp" + href
                    entry = f"[イオン] {text} ({href})" if href else f"[イオン] {text}"
                    if entry not in items:
                        items.append(entry)
        except Exception as e:
            print(f"Aeon Error ({url}): {e}")

    # ② あみあみ公式検索APIの巡回
    amiami_headers = {
        "User-Agent": headers["User-Agent"],
        "X-User-Key": "amiami_dev",
        "Referer": "https://slist.amiami.jp/"
    }
    for kw in AMIAMI_KEYWORDS:
        try:
            api_url = "https://api.amiami.com/api/v1.0/items"
            params = {
                "s_keywords": kw,
                "s_st_list_preorder_available": 1,
                "s_st_list_backorder_available": 1,
                "s_st_list_newitem_available": 1,
                "s_st_condition_flg": 1,
                "pagemax": 30,
                "pagecnt": 1,
                "lang": "ja"
            }
            res = requests.get(api_url, headers=amiami_headers, params=params, timeout=15)
            data = res.json()
            for item in data.get("items", []):
                gname = item.get("gname", "")
                gcode = item.get("gcode", "")
                if gname and gcode and not any(ng in gname for ng in EXCLUDE_WORDS):
                    item_url = f"https://www.amiami.jp/top/detail/detail?gcode={gcode}"
                    entry = f"[あみあみ] {gname} ({item_url})"
                    if entry not in items:
                        items.append(entry)
        except Exception as e:
            print(f"AmiAmi API Error ({kw}): {e}")

    # ③ ヨドバシカメラの巡回（購入・予約可能な商品のみ抽出）
    sold_out_words = ["販売休止中", "予定数の販売を終了", "在庫なし", "販売終了", "お取り寄せ"]
    for url in YODOBASHI_URLS:
        try:
            res = requests.get(url, headers=headers, timeout=15)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, "html.parser")

            for box in soup.select(".srcResultItem_block, .pListBlock"):
                full_text = box.get_text(" ", strip=True)
                if any(so in full_text for so in sold_out_words):
                    continue
                if any(ng in full_text for ng in EXCLUDE_WORDS):
                    continue

                a = box.find("a", href=True)
                if a:
                    href = a["href"]
                    if href.startswith("/"):
                        href = "https://www.yodobashi.com" + href
                    name_el = box.select_one(".pName, .js_sltGoodsName")
                    name = name_el.get_text(" ", strip=True) if name_el else a.get_text(" ", strip=True)
                    if name and "/product/" in href:
                        entry = f"[ヨドバシ] {name} ({href})"
                        if entry not in items:
                            items.append(entry)
        except Exception as e:
            print(f"Yodobashi Error ({url}): {e}")

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
