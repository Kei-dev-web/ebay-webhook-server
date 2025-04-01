from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import openai
import os
import time

app = Flask(__name__)

# OpenAIのAPIキーをRenderの環境変数から取得
openai.api_key = os.environ.get("OPENAI_API_KEY")

def generate_product_names():
    prompt = (
        "日本で売れている、万年筆・万年筆用インク・コンバーターなどの関連商品を"
        "英語の商品名で30個、1行に1つずつ箇条書きでリストアップしてください。"
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
        # GPTの出力から30行をしっかり抽出
        names = [line.strip("0123456789.・- ").strip() for line in content.splitlines() if line.strip()]
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

        # Amazon商品リンクの候補を広めに取得
        for a in soup.select('a'):
            href = a.get('href', '')
            if '/dp/' in href:
                return "https://www.amazon.co.jp" + href.split("?")[0]
    except Exception as e:
        print(f"❌ Amazon search error for '{query}':", e)
    return "https://www.amazon.co.jp"  # fallback


@app.route("/webhook", methods=["GET"])
def get_items():
    product_names = generate_product_names()
    results = []
    exchange_rate = 145

    for name in product_names:
        amazon_url = search_amazon_url(name)
        time.sleep(1.5)

        # 商品ごとにランダムに価格設定（テスト用）
        cost_yen = 2500 + hash(name) % 1500  # 2500〜3999
        price_usd = round(35 + (hash(name[::-1]) % 2000) / 100, 2)  # $35〜$54.99
        shipping_yen = 700

        fee_yen = price_usd * 0.2 * exchange_rate
        revenue_yen = price_usd * 0.8 * exchange_rate
        profit = revenue_yen - cost_yen - shipping_yen
        margin = (profit / revenue_yen) * 100 if revenue_yen > 0 else 0

        results.append({
            "url": amazon_url,
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
