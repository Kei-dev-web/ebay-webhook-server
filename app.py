from flask import Flask, jsonify
import requests
from bs4 import BeautifulSoup
import os
import time
import json

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
    keyword = "fountain pen"
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
        "paginationInput.entriesPerPage": "5"
    }

    print(f"\n🔍 Sending request to eBay with keyword: {keyword}")
    response = requests.get(url, params=params)
    try:
        data = response.json()
    except Exception as e:
        print("❌ Failed to parse JSON:", e)
        return jsonify({"error": "Failed to parse JSON", "details": str(e)})

    # ✅ eBayレスポンスをまるごとログ出力
    print("📦 Raw eBay API response:")
    print(json.dumps(data, indent=2))

    # ✅ レスポンス全体をクライアントにも返す
    return jsonify(data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
