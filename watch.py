import os
import urllib.parse
import requests
from bs4 import BeautifulSoup

# ▼ 監視する6タイトル
TARGET_TITLES = [
    "ユニオンアリーナ",
    "ワンピースカード",
    "ポケモンカード",
    "フュージョンワールド",
    "デジモンカード",
    "遊戯王",
]

# ▼ 1. イオン北海道eショップの監視URL
AEON_URLS = [
    "https://es.aeon-hokkaido.jp/eshop/",
    "https://es.aeon-hokkaido.jp/eshop/item/list?kw=%E3%83%A6%E3%83%8B%E3%82%AA%E3%83%B3%E3%82%A2%E3%83%AA%E3%83%BC%E3%83%8A",
    "https://es.aeon-hokkaido.jp/eshop/item/list?kw=%E3%83%9D%E3%82%B1%E3%83%A2%E3%83%B3%E3%82%AB%E3%83%BC%E3%83%89",
    "https://es.aeon-hokkaido.jp/eshop/item/list?kw=%E3%83%AF%E3%83%B3%E3%83%94%E3%83%BC%E3%82%B9%E3%82%AB%E3%83%BC%E3%83%89",
    "https://es.aeon-hokkaido.jp/eshop/item/list?kw=%E3%83%95%E3%83%A5%E3%83%BC%E3%82%B8%E3%83%A7%E3%83%B3%E3%83%AF%E3%83%BC%E3%83%AB%E3%83%89",
    "https://es.aeon-hokkaido.jp/eshop/item/list?kw=%E3%83%87%E3%82%B8%E3%83%A2%E3%83%B3%E3%82%AB%E3%83%BC%E3%83%89",
    "https://es.aeon-hokkaido.jp/eshop/item/list?kw=%E9%81%8A%E6%88%AF%E7%8E%8B",
]

# ▼ 2. ヨドバシカメラの監視URL（トレカカテゴリー）
YODOBASHI_URLS = [
    "https://www.yodobashi.com/category/141001/141651/141662/",
]

# ▼ 3. ポケモンセンターオンラインの監視URL（カードゲーム一覧）
POKECEN_URLS = [
    "https://www.pokemoncenter-online.com/?main_page=product_list&cat1=card",
]

# ▼ 共通の除外ワード（サプライ・フィギュア・プラモ・ゲーム・雑貨・アイマスを徹底除外）
EXCLUDE_WORDS = [
    "ウエハース", "グミ", "チョコ", "スナック", "Tシャツ", "タオル", "マイナンバー", "ギフト",
    "スリーブ", "デッキシールド", "プレイマット", "ラバーマット", "ストレージ",
    "デッキケース", "カードボックス", "カードホルダー", "カードファイル",
    "ファイル", "バインダー", "ダメカン", "コイン", "プロテクター",
    "エネルギーカード", "ジャンボカード", "ディスプレイフレーム", "スタンド",
    "フィギュア", "プラモデル", "ねんどろいど", "Switch", "ゲーム", "ステッカー", "アクリル",
    "DESKTOP COLLECTION", "アイドルマスター",
]

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
CACHE_FILE = "last_data.txt"

def send_discord(message):
    if DISCORD_WEBHOOK_URL:
        requests.post(DISCORD_WEBHOOK_URL, json={"content": message}, timeout=5)

def is_valid_item(text):
    return bool(text) and not any(ng in text for ng in EXCLUDE_WORDS)

def main():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
    }
    items = []
    sold_out_words = ["販売休止中", "予定数の販売を終了", "在庫なし", "販売終了", "お取り寄せ", "SOLD OUT", "在庫切れ", "受付終了"]

    # ① イオン北海道の巡回
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
    for url in AEON_URLS:
        try:
            res = requests.get(url, headers=headers, timeout=5)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.find_all("a"):
                text = a.get_text(strip=True)
                href = a.get("href", "")
                if any(k in text for k in aeon_keywords) and is_valid_item(text):
                    if href.startswith("/"):
                        href = "https://es.aeon-hokkaido.jp" + href
                    entry = f"[イオン] {text} ({href})" if href else f"[イオン] {text}"
                    if entry not in items:
                        items.append(entry)
        except Exception as e:
            print(f"Aeon Error: {e}")

    # ② あみあみ公式APIの巡回（CARD-コード＝純粋なトレカ商品のみに限定）
    amiami_headers = {
        "User-Agent": headers["User-Agent"],
        "X-User-Key": "amiami_dev",
        "Referer": "https://slist.amiami.jp/"
    }
    for kw in TARGET_TITLES:
        try:
            res = requests.get(
                "https://api.amiami.com/api/v1.0/items",
                headers=amiami_headers,
                params={
                    "s_keywords": kw,
                    "s_st_list_preorder_available": 1,
                    "s_st_list_backorder_available": 1,
                    "s_st_list_newitem_available": 1,
                    "s_st_condition_flg": 1,
                    "pagemax": 30,
                    "pagecnt": 1,
                    "lang": "ja"
                },
                timeout=5
            )
            for item in res.json().get("items", []):
                gname = item.get("gname", "")
                gcode = item.get("gcode", "")
                if gcode.startswith("CARD-") and is_valid_item(gname):
                    entry = f"[あみあみ] {gname} (https://www.amiami.jp/top/detail/detail?gcode={gcode})"
                    if entry not in items:
                        items.append(entry)
        except Exception as e:
            print(f"AmiAmi Error ({kw}): {e}")

    # ③ ヨドバシカメラの巡回
    for url in YODOBASHI_URLS:
        try:
            res = requests.get(url, headers=headers, timeout=4)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, "html.parser")
            for box in soup.select(".srcResultItem_block, .pListBlock"):
                full_text = box.get_text(" ", strip=True)
                if any(so in full_text for so in sold_out_words) or not is_valid_item(full_text):
                    continue
                a = box.find("a", href=True)
                if a and "/product/" in a["href"]:
                    href = "https://www.yodobashi.com" + a["href"] if a["href"].startswith("/") else a["href"]
                    name_el = box.select_one(".pName, .js_sltGoodsName")
                    name = name_el.get_text(" ", strip=True) if name_el else a.get_text(" ", strip=True)
                    if is_valid_item(name):
                        entry = f"[ヨドバシ] {name} ({href})"
                        if entry not in items:
                            items.append(entry)
        except Exception as e:
            print(f"Yodobashi Error: {e}")

    # ④ ポケモンセンターオンラインの巡回
    for url in POKECEN_URLS:
        try:
            res = requests.get(url, headers=headers, timeout=4)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, "html.parser")
            for box in soup.select(".product_list li, .item_box"):
                full_text = box.get_text(" ", strip=True)
                if any(so in full_text for so in sold_out_words) or not is_valid_item(full_text):
                    continue
                a = box.find("a", href=True)
                if a:
                    href = "https://www.pokemoncenter-online.com" + a["href"] if a["href"].startswith("/") else a["href"]
                    name = a.get_text(" ", strip=True) or (a.find("img").get("alt", "") if a.find("img") else "")
                    if is_valid_item(name):
                        entry = f"[ポケセン] {name} ({href})"
                        if entry not in items:
                            items.append(entry)
        except Exception as e:
            print(f"Pokecen Error: {e}")

    # ⑤ プレミアムバンダイの巡回（トレカ関連ワード必須）
    pbandai_must = ["カード", "ブースター", "スタートデッキ", "BOX", "パック"]
    for kw in TARGET_TITLES:
        try:
            q = urllib.parse.quote(kw)
            url = f"https://p-bandai.jp/search/?character=&q={q}&sale_status=1"
            res = requests.get(url, headers=headers, timeout=4)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.find_all("a", href=True):
                if "/item/item-" in a["href"]:
                    text = a.get_text(" ", strip=True)
                    if any(m in text for m in pbandai_must) and is_valid_item(text):
                        href = "https://p-bandai.jp" + a["href"] if a["href"].startswith("/") else a["href"]
                        entry = f"[プレバン] {text} ({href})"
                        if entry not in items:
                            items.append(entry)
        except Exception as e:
            print(f"P-Bandai Error ({kw}): {e}")

    # ⑥ ビックカメラ.comの巡回
    for kw in TARGET_TITLES:
        try:
            q = urllib.parse.quote(kw)
            url = f"https://www.biccamera.com/bc/category/?q={q}&sold_out_tp2=2"
            res = requests.get(url, headers=headers, timeout=4)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, "html.parser")
            for box in soup.select(".prod_box"):
                full_text = box.get_text(" ", strip=True)
                if any(so in full_text for so in sold_out_words) or not is_valid_item(full_text):
                    continue
                a = box.select_one("a.bcs_item, .bcs_title a")
                if a and a.get("href"):
                    href = "https://www.biccamera.com" + a["href"] if a["href"].startswith("/") else a["href"]
                    name = a.get_text(" ", strip=True)
                    if is_valid_item(name):
                        entry = f"[ビック] {name} ({href})"
                        if entry not in items:
                            items.append(entry)
        except Exception as e:
            print(f"BicCamera Error ({kw}): {e}")

    # ⑦ ヤマダウェブコムの巡回
    for kw in TARGET_TITLES:
        try:
            q = urllib.parse.quote(kw)
            url = f"https://www.yamada-denkiweb.com/search/{q}/?stock=1"
            res = requests.get(url, headers=headers, timeout=4)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, "html.parser")
            for a in soup.find_all("a", href=True):
                if "/product/" in a["href"] or "/item/" in a["href"]:
                    text = a.get_text(" ", strip=True)
                    if kw in text and is_valid_item(text):
                        href = "https://www.yamada-denkiweb.com" + a["href"] if a["href"].startswith("/") else a["href"]
                        entry = f"[ヤマダ] {text} ({href})"
                        if entry not in items:
                            items.append(entry)
        except Exception as e:
            print(f"Yamada Error ({kw}): {e}")

    # ⑧ 楽天ブックスの巡回（在庫あり・予約受付中のみ）
    for kw in TARGET_TITLES:
        try:
            q = urllib.parse.quote(kw)
            url = f"https://books.rakuten.co.jp/search?sitem={q}&g=006&l-id=search-c-stock&x=0&y=0&v=2&s=1&e=0"
            res = requests.get(url, headers=headers, timeout=4)
            res.encoding = res.apparent_encoding
            soup = BeautifulSoup(res.text, "html.parser")
            for box in soup.select(".rbcomp__item-list__item"):
                full_text = box.get_text(" ", strip=True)
                if any(so in full_text for so in sold_out_words) or not is_valid_item(full_text):
                    continue
                a = box.select_one(".rbcomp__item-list__item__title a")
                if a and a.get("href"):
                    name = a.get_text(" ", strip=True)
                    if is_valid_item(name):
                        entry = f"[楽天ブックス] {name} ({a['href']})"
                        if entry not in items:
                            items.append(entry)
        except Exception as e:
            print(f"Rakuten Error ({kw}): {e}")

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
                + "\n".join(f"・{x}" for x in new_lines[:15])
            )
            send_discord(msg)

    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        f.write(current_data)

if __name__ == "__main__":
    main()
