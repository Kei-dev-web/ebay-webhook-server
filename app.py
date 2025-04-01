from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/webhook", methods=["GET"])
def get_items():
    exchange_rate = 145

    items = [
        {
            "url": "https://www.amazon.co.jp/dp/B000FQ7SZO",
            "name": "Sailor Profit Fountain Pen Black MF",
            "cost_yen": 3500,
            "price_usd": 49.99,
            "shipping_yen": 700,
        },
        {
            "url": "https://www.amazon.co.jp/dp/B000FA3L3A",
            "name": "Pilot Kakuno Fountain Pen F Transparent",
            "cost_yen": 1000,
            "price_usd": 21.99,
            "shipping_yen": 500,
        }
    ]

    for item in items:
        fee_yen = item["price_usd"] * 0.2 * exchange_rate
        revenue_yen = item["price_usd"] * 0.8 * exchange_rate
        profit = revenue_yen - item["cost_yen"] - item["shipping_yen"]
        margin = (profit / revenue_yen) * 100 if revenue_yen > 0 else 0
        item["fee_yen"] = round(fee_yen)
        item["profit_yen"] = round(profit)
        item["margin_pct"] = round(margin, 1)

    return jsonify(items)

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # RenderがPORT環境変数を使う
    app.run(host="0.0.0.0", port=port)
