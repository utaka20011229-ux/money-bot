import requests
import google.generativeai as genai
import os
from datetime import datetime

# ==========================================
# 設定エリア
# ==========================================
PH_ACCESS_TOKEN = os.getenv("PH_ACCESS_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# ディレクトリ作成関数
def setup_directories():
    os.makedirs("content/posts", exist_ok=True)

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
    try:
        response = requests.post(url, json={'query': query}, headers=headers)
        response.raise_for_status()
        return response.json()['data']['posts']['edges'][0]['node']
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

# ==========================================
# 2. Geminiで記事生成 (Hugo対応版)
# ==========================================
def generate_article(product_info):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-flash-latest')
    
    print(f"Generating article for: {product_info['name']}...")

    # Hugo用のFrontmatter（記事の管理情報）を含めたプロンプト
    prompt = f"""
    あなたは人気テックブロガーです。以下のツールを紹介する記事を書いてください。
    出力は以下の形式（Frontmatter付きMarkdown）を厳守してください。
    
    ---
    title: "{product_info['name']} - {product_info['tagline']}"
    date: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S+09:00')}
    draft: false
    description: "{product_info['description'][:100]}..."
    tags: ["ProductHunt", "AI", "Tools"]
    ---

    # {product_info['name']} とは？
    （以下、本文をMarkdownで記述。見出しは ## から始めてください。
    読者が「使ってみたい！」と思うようなメリット、使い方、まとめを書いてください。
    最後に公式サイトへのリンク {product_info['website']} を目立つように配置してください。）
    """

    try:
        response = model.generate_content(prompt)
        # 余計な ```markdown 等の記号を削除するクリーニング
        text = response.text.replace("```markdown", "").replace("```", "").strip()
        return text
    except Exception as e:
        print(f"AI Error: {e}")
        return None

# ==========================================
# メイン処理
# ==========================================
if __name__ == "__main__":
    if not PH_ACCESS_TOKEN or not GEMINI_API_KEY:
        print("API Keys not found.")
        exit(1)

    setup_directories()
    product = get_top_product()
    
    if product:
        content = generate_article(product)
        if content:
            # ファイル名を安全にする
            safe_name = "".join([c for c in product['name'] if c.isalnum()])
            filename = f"content/posts/{datetime.now().strftime('%Y-%m-%d')}-{safe_name}.md"
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"Saved: {filename}")
