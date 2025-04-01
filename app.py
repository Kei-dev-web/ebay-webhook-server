from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import os
import time

app = Flask(__name__)

def search_amazon_url(query):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    search_url = f"https://www.amazon.co.jp/s?k={query.replace(' ', '+')}"
    try:
        res = requests.get(search_url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")
        link = soup.select_one('a.a-link-normal.s-no-outline')
        if link:
            return "https://www.amazon.co.jp" + link.get("href").split("?")[0]
    except:
        pass
    return ""

@app.route("/webhook", methods=["GET"])
def get_items():
    app_id = "KosukeKa-spreadsh-PRD-8b020a690-15abf660"
    keywords = ["fountain pen"]  # ← まずは1キーワードでテスト
    max_entries = 30
    collected_items = []
    seen_titles = set()

    for keyword in keywords:
        url = "https://svcs.ebay.com/services/search/FindingService/v1"
        params = {
            "OPERATION-NAME": "findCompletedItems",
            "SERVICE-VERSION": "1.13.0",
            "SECURITY-APPNAME": app_id,
            "RESPONSE-DATA-FORMAT": "JSON",
            "REST-PAYLOAD": "",
            "keywords": keyword,
            "itemFilter(0).name": "SoldItemsOnly",
            "itemFilter(0).value": "true",
            "itemFilter(1).name": "LocatedIn",
            "itemFilter(1).value": "JP",
            "paginationInput.entriesPerPage": "20",
            # "categoryId": "14024",  ← いったんカテゴリ指定なしで
        }

        print(f"\n🔍 Searching eBay for: {keyword}")
        response = requests.get(url, params=params)
        data = response.json()

        # ✅ レスポンス全体をログに出力（Renderログで確認可能）
        print("📦 eBay API response:")
        print(data)

        try:
            items = data["findCompletedItemsResponse"][0]["searchResult"][0]["item"]
        except KeyError:
            print("❌ No items found for keyword:", keyword)
            continue

        for item in items:
            title = item.get("title", [""])[0]
            price = float(item["sellingStatus"][0]["convertedCurrentPrice"][0]["__value__"])
            currency = item["sellingStatus"][0]["convertedCurrentPrice"][0]["@currencyId"]

            if title not in seen_titles and currency == "USD":
                seen_titles.add(title)

                amazon_url = search_amazon_url(title)
                time.sleep(1.5)

                collected_items.append({
                    "url": amazon_url or "https://www.amazon.co.jp",
                    "name": title,
                    "cost_yen": 3000,
                    "price_usd": round(price, 2),
                    "shipping_yen": 700,
                })

            if len(collected_items) >= max_entries:
                break
        if len(collected_items) >= max_entries:
            break

    # 利益計算
    exchange_rate = 145
    for item in collected_items:
        fee_yen = item["price_usd"] * 0.2 * exchange_rate
        revenue_yen = item["price_usd"] * 0.8 * exchange_rate
        profit = revenue_yen - item["cost_yen"] - item["shipping_yen"]
        margin = (profit / revenue_yen) * 100 if revenue_yen > 0 else 0
        item["fee_yen"] = round(fee_yen)
        item["profit_yen"] = round(profit)
        item["margin_pct"] = round(margin, 1)

    return jsonify(collected_items)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
