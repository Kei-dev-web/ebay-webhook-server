from flask import Flask, jsonify
import requests
import os

app = Flask(__name__)

@app.route("/webhook", methods=["GET"])
def get_items():
    app_id = "KosukeKa-spreadsh-PRD-8b020a690-15abf660"
    keywords = ["fountain pen", "ink cartridge", "converter", "fountain pen ink", "calligraphy pen"]
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
            "categoryId": "14024",  # Collectibles > Pens
            "itemFilter(0).name": "SoldItemsOnly",
            "itemFilter(0).value": "true",
            "itemFilter(1).name": "LocatedIn",
            "itemFilter(1).value": "JP",
            "paginationInput.entriesPerPage": "20",
        }

        response = requests.get(url, params=params)
        data = response.json()

        try:
            items = data["findCompletedItemsResponse"][0]["searchResult"][0]["item"]
        except KeyError:
            continue

        for item in items:
            title = item.get("title", [""])[0]
            item_id = item.get("itemId", [""])[0]
            price = float(item["sellingStatus"][0]["convertedCurrentPrice"][0]["__value__"])
            currency = item["sellingStatus"][0]["convertedCurrentPrice"][0]["@currencyId"]
            view_url = item.get("viewItemURL", [""])[0]

            if title not in seen_titles and currency == "USD":
                seen_titles.add(title)

                collected_items.append({
                    "url": view_url,
                    "name": title,
                    "cost_yen": 3000,  # 仮の仕入れ値（次フェーズでAmazon連携）
                    "price_usd": round(price, 2),
                    "shipping_yen": 700,
                })

            if len(collected_items) >= max_entries:
                break
        if len(collected_items) >= max_entries:
            break

    # 粗利益・利益率計算
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
