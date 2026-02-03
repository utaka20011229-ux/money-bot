import requests
import google.generativeai as genai
import os
from datetime import datetime

PH_ACCESS_TOKEN = os.getenv("PH_ACCESS_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

def setup_directories():
    os.makedirs("content/posts", exist_ok=True)

def get_top_product():
    url = "https://api.producthunt.com/v2/api/graphql"
    headers = {"Authorization": f"Bearer {PH_ACCESS_TOKEN}"}
    query = """{ posts(first: 1, order: VOTES) { edges { node { name tagline description url votesCount website } } } }"""
    try:
        response = requests.post(url, json={'query': query}, headers=headers)
        response.raise_for_status()
        return response.json()['data']['posts']['edges'][0]['node']
    except Exception as e:
        print(f"Error: {e}")
        return None

def generate_article(product_info):
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-flash-latest')
    print(f"Generating: {product_info['name']}...")
    prompt = f"""
    ---
    title: "{product_info['name']} - {product_info['tagline']}"
    date: {datetime.now().strftime('%Y-%m-%dT%H:%M:%S+09:00')}
    draft: false
    description: "{product_info['description'][:100]}..."
    ---
    # {product_info['name']}
    {product_info['description']}
    
    [公式サイトへ]({product_info['website']})
    (魅力的な日本語紹介記事をMarkdownで書いてください)
    """
    try:
        response = model.generate_content(prompt)
        return response.text.replace("```markdown", "").replace("```", "").strip()
    except Exception as e:
        return None

if __name__ == "__main__":
    if not PH_ACCESS_TOKEN or not GEMINI_API_KEY: exit(1)
    setup_directories()
    p = get_top_product()
    if p:
        c = generate_article(p)
        if c:
            safe = "".join([x for x in p['name'] if x.isalnum()])
            with open(f"content/posts/{datetime.now().strftime('%Y-%m-%d')}-{safe}.md", "w", encoding="utf-8") as f:
                f.write(c)
