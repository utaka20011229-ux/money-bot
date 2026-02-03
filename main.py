import requests
import google.generativeai as genai
import json
from datetime import datetime
import os

# ==========================================
# 設定エリア (環境変数からキーを読み込む安全仕様)
# ==========================================
# ローカル実行時にエラーにならないよう、ない場合は空文字を入れる安全設計
PH_ACCESS_TOKEN = os.getenv("PH_ACCESS_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# キーが読み込めていない場合に警告を出す
if not PH_ACCESS_TOKEN or not GEMINI_API_KEY:
    print("【警告】APIキーが環境変数に見つかりません。")
    print("GitHub Actionsの設定、またはローカルの環境変数を確認してください。")
    # ここで処理を止めないと、後の処理でエラーになる
    # ただし、ローカルテスト用に直書きしたい誘惑には勝ってください

# ==========================================
# 1. Product Huntからデータ取得
# ==========================================
def get_top_product():
    url = "https://api.producthunt.com/v2/api/graphql"
    headers = {"Authorization": f"Bearer {PH_ACCESS_TOKEN}"}
    
    query = """
    {
      posts(first: 1, order: VOTES) {
        edges {
          node {
            name
            tagline
            description
            url
            votesCount
            website
          }
        }
      }
    }
    """
    
    print("Fetching data from Product Hunt...")
    try:
        response = requests.post(url, json={'query': query}, headers=headers)
        response.raise_for_status() # エラーならここで止める
        
        data = response.json()
        product = data['data']['posts']['edges'][0]['node']
        return product
    except Exception as e:
        print(f"データ取得エラー: {e}")
        # 詳細なエラーレスポンスを表示（デバッグ用）
        if 'response' in locals():
            print(response.text)
        return None

# ==========================================
# 2. Geminiで記事生成
# ==========================================
def generate_article(product_info):
    # APIキーの余計な空白を削除して設定
    clean_key = GEMINI_API_KEY.strip()
    genai.configure(api_key=clean_key)
    
    # ★ここでモデルを指定！ リストにあった最強コスパモデルを使用
    model = genai.GenerativeModel('gemini-flash-latest')
    
    print(f"Generating article for: {product_info['name']}...")

    prompt = f"""
    あなたはプロのガジェット/SaaS紹介ブロガーです。
    以下のツールについて、日本の読者が「今すぐ使いたい！」と思うような魅力的なブログ記事をMarkdown形式で書いてください。

    【ツール情報】
    - 名前: {product_info['name']}
    - キャッチコピー: {product_info['tagline']}
    - 説明: {product_info['description']}
    - 人気度: {product_info['votesCount']} votes
    - URL: {product_info['website']}

    【記事構成】
    1. タイトル: 30文字以内、キャッチーに。
    2. 導入: 読者の悩みに寄り添う。
    3. 概要: 何ができるツールか簡潔に。
    4. 使い方/メリット: 具体的な利用シーンを想像させる。
    5. まとめ: 公式サイトへの誘導。
    
    ※出力はMarkdownのみにしてください。
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"AI生成エラー: {e}")
        return None

# ==========================================
# メイン処理
# ==========================================
if __name__ == "__main__":
    # 1. データ取得
    product = get_top_product()
    
    if product:
        # 2. 記事生成
        article_content = generate_article(product)
        
        if article_content:
            # 3. ファイル保存
            # ファイル名に日付と製品名を入れる
            safe_name = "".join([c for c in product['name'] if c.isalnum()])
            filename = f"article_{datetime.now().strftime('%Y%m%d')}_{safe_name}.md"
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(article_content)
                
            print(f"\nSUCCESS! 記事生成完了: {filename}")
            print("=========================================")
            print("不労所得の第一歩目が完成しました。")
            print("フォルダを確認してください。")