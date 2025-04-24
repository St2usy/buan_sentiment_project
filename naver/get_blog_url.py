import requests
import time
import csv
from urllib.parse import quote
import os
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")


headers = {
    "X-Naver-Client-Id": CLIENT_ID,
    "X-Naver-Client-Secret": CLIENT_SECRET
}

def fetch_blog_urls(query):
    blog_urls = []
    for start in range(1, 1000, 100):
        url = f"https://openapi.naver.com/v1/search/blog.json?query={quote(query)}&display=100&start={start}"
        res = requests.get(url, headers=headers)
        if res.status_code != 200:
            print(f"[ERROR] API 실패 ({res.status_code})")
            break
        data = res.json().get("items", [])
        for item in data:
            blog_urls.append((query, item["title"], item["link"]))
        time.sleep(0.5)
    return blog_urls

def load_keywords(filename):
    keywords_by_category = {}
    current_cat = None
    with open(filename, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                current_cat = line[1:-1]
                keywords_by_category[current_cat] = []
            elif line and current_cat:
                keywords_by_category[current_cat].append(line)
    return keywords_by_category

if __name__ == "__main__":
    all_keywords = load_keywords("keyword_list.txt")

    for category, keywords in all_keywords.items():
        os.makedirs(f"result/{category}", exist_ok=True)
        category_results = []

        for kw in keywords:
            print(f"🔍 [{category}] {kw} 수집 중...")
            urls = fetch_blog_urls(kw)
            for result in urls:
                category_results.append([category] + list(result))

        # 저장
        with open(f"result/{category}/blog_urls.csv", "w", encoding="utf-8-sig", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["category", "keyword", "title", "url"])
            writer.writerows(category_results)

    print("✅ 모든 카테고리 URL 저장 완료!")
