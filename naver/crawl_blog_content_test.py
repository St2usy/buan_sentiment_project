# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
import time
import random
import os
from multiprocessing import Pool
import numpy as np
import json
from datetime import datetime

def init_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0")
    return webdriver.Chrome(options=options)

def process_urls(url_chunk):
    driver = init_driver()
    results = []
    
    for _, row in url_chunk.iterrows():
        try:
            print(f"  처리 중: {row['title'][:30]}...")
            content = crawl_blog_content(driver, row['url'])
            
            # 감성 분석을 위한 데이터 구조
            blog_data = {
                "category": row['category'],
                "keyword": row['keyword'],
                "title": row['title'],
                "url": row['url'],
                "content": content,
                "crawled_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "sentiment_analysis": {
                    "positive_score": None,
                    "negative_score": None,
                    "neutral_score": None,
                    "overall_sentiment": None,
                    "keywords": [],
                    "analyzed_at": None
                }
            }
            results.append(blog_data)
            time.sleep(random.uniform(1, 2))
        except Exception as e:
            print(f"❌ 에러 발생: {e}")
            results.append({
                "category": row['category'],
                "keyword": row['keyword'],
                "title": row['title'],
                "url": row['url'],
                "content": "",
                "error": str(e)
            })
    
    driver.quit()
    return results

def crawl_blog_content(driver, url):
    try:
        driver.get(url)
        time.sleep(random.uniform(2, 4))
        driver.switch_to.frame("mainFrame")
        content = driver.find_element(By.CSS_SELECTOR, "div.se-main-container").text
        return content
    except Exception as e:
        print("❌ 에러 발생:", e)
        return ""

def process_category(cat):
    print(f"\n📂 카테고리: {cat}")
    input_path = os.path.join("result", cat, "blog_urls.csv")
    output_path = os.path.join("result", cat, "blog_data.json")  # JSON 형식으로 변경

    if not os.path.exists(input_path):
        print(f"❌ {input_path} 없음")
        return

    df = pd.read_csv(input_path)
    # 처음 4개의 URL만 처리
    df = df.head(4)
    
    # URL을 2개의 청크로 나눔 (각각 2개씩)
    url_chunks = np.array_split(df, 2)
    
    print(f"🔍 테스트 모드: {cat} 카테고리에서 4개의 URL만 처리합니다")
    # 2개의 프로세스로 병렬 처리
    with Pool(2) as pool:
        all_results = pool.map(process_urls, url_chunks)
    
    # 결과 병합
    results = [item for sublist in all_results for item in sublist]
    
    # JSON 형식으로 저장
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 테스트 데이터 저장 완료: {output_path}")

if __name__ == "__main__":
    print("🔍 테스트 모드: 각 카테고리에서 4개의 URL만 크롤링합니다")
    base_path = "result"
    categories = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]
    
    # 각 카테고리를 순차적으로 처리 (테스트용이므로 병렬 처리하지 않음)
    for cat in categories:
        process_category(cat)
    
    print("\n✅ 모든 테스트 크롤링이 완료되었습니다!") 