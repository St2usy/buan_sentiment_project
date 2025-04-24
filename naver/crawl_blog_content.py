# -*- coding: utf-8 -*-

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
import time
import random
import os
from multiprocessing import Pool, cpu_count
import numpy as np

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
            results.append([row['category'], row['keyword'], row['title'], row['url'], content])
            time.sleep(random.uniform(1, 2))
        except Exception as e:
            print(f"❌ 에러 발생: {e}")
            results.append([row['category'], row['keyword'], row['title'], row['url'], ""])
    
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
    output_path = os.path.join("result", cat, "blog_contents.csv")

    if not os.path.exists(input_path):
        print(f"❌ {input_path} 없음")
        return

    df = pd.read_csv(input_path)
    # URL을 4개의 청크로 나눔
    url_chunks = np.array_split(df, 4)
    
    # 4개의 프로세스로 병렬 처리
    with Pool(4) as pool:
        all_results = pool.map(process_urls, url_chunks)
    
    # 결과 병합
    results = [item for sublist in all_results for item in sublist]
    
    # 결과 저장
    pd.DataFrame(results, columns=["category", "keyword", "title", "url", "content"]).to_csv(
        output_path, index=False, encoding="utf-8-sig"
    )
    print(f"✅ 저장 완료: {output_path}")

if __name__ == "__main__":
    base_path = "result"
    categories = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]
    
    # 각 카테고리를 병렬로 처리
    with Pool(4) as pool:
        pool.map(process_category, categories)
