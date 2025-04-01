from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import openai
import os
import time

app = Flask(__name__)

# OpenAI APIキー（環境変数 OPENAI_API_KEY で設定）
openai.api_key = os.environ.get("OPENAI_API_KEY")

def generate_product_names():
    prompt = (
        "日本で売れている、万年筆・万年筆用インク・コンバーターなどの関連商品を"
        "英語の商品名で30個リストアップしてください。"
    )
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        content = response.choices[0].message.content
        names = [line.strip("0123456789. ").strip() for line in content.split("\n") if line.strip()]
        return names[:30]
    except Exception as e:
        print("❌ GPT error:", e)
        return ["PILOT Kakuno Fountain Pen", "Sailor Ink Bottle"]  # fallback

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
    product_names = generate_product_names()
    results = []
    exchange_rate = 145

    for name in product_names:
        amazon_url = search_amazon_url(name)
        time.sleep(1.5)

        cost_yen = 3000
        price_usd = 45.0
        shipping_yen = 700

        fee_yen = price_usd * 0.2 * exchange_rate
        revenue_yen = price_usd * 0.8 * exchange_rate
        profit = revenue_yen - cost_yen - shipping_yen
        margin = (profit / revenue_yen) * 100 if revenue_yen > 0 else 0

        results.append({
            "url": amazon_url or "https://www.amazon.co.jp",
            "name": name,
            "cost_yen": cost_yen,
            "price_usd": price_usd,
            "shipping_yen": shipping_yen,
            "fee_yen": round(fee_yen),
            "profit_yen": round(profit),
            "margin_pct": round(margin, 1)
        })

    return jsonify(results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
