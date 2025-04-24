# -*- coding: utf-8 -*-

import json
import os
from datetime import datetime
from konlpy.tag import Okt
from collections import Counter
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

class SentimentAnalyzer:
    def __init__(self):
        # KcELECTRA 기반 감성 분석 모델 로드
        self.model_name = "beomi/KcELECTRA-base"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        
        self.sentiment_pipeline = pipeline(
            "sentiment-analysis",
            model=self.model,
            tokenizer=self.tokenizer
        )
        self.okt = Okt()
        
    def split_text(self, text, max_length=500):
        if not text:
            return []
            
        # 텍스트를 토큰화하여 분할
        try:
            tokens = self.tokenizer.tokenize(text)
            chunks = []
            current_chunk = []
            current_length = 0
            
            for token in tokens:
                current_chunk.append(token)
                current_length += 1
                
                if current_length >= max_length:
                    chunks.append(self.tokenizer.convert_tokens_to_string(current_chunk))
                    current_chunk = []
                    current_length = 0
            
            if current_chunk:
                chunks.append(self.tokenizer.convert_tokens_to_string(current_chunk))
                
            return chunks
        except Exception as e:
            print(f"❌ 텍스트 분할 중 에러: {e}")
            return [text]  # 분할 실패 시 전체 텍스트를 하나의 청크로 처리
        
    def preprocess_text(self, text):
        if not text:
            return ""
            
        try:
            # 텍스트 전처리
            words = self.okt.morphs(text, stem=True)
            return ' '.join(words)
        except Exception as e:
            print(f"❌ 텍스트 전처리 중 에러: {e}")
            return text
    
    def analyze_sentiment(self, text):
        if not text:
            return {"label": "neutral", "score": 0.5}
            
        # 긴 텍스트를 분할하여 처리
        chunks = self.split_text(text)
        sentiments = []
        
        for chunk in chunks:
            try:
                result = self.sentiment_pipeline(chunk)[0]
                sentiments.append({
                    "label": result['label'],
                    "score": result['score']
                })
            except Exception as e:
                print(f"❌ 청크 처리 중 에러: {e}")
                continue
        
        if not sentiments:
            return {"label": "neutral", "score": 0.5}
            
        # 전체 감성 점수 평균 계산
        positive_scores = [s['score'] for s in sentiments if s['label'] == 'positive']
        negative_scores = [s['score'] for s in sentiments if s['label'] == 'negative']
        
        if positive_scores and negative_scores:
            avg_positive = sum(positive_scores) / len(positive_scores)
            avg_negative = sum(negative_scores) / len(negative_scores)
            if avg_positive > avg_negative:
                return {"label": "positive", "score": avg_positive}
            else:
                return {"label": "negative", "score": avg_negative}
        elif positive_scores:
            return {"label": "positive", "score": sum(positive_scores) / len(positive_scores)}
        elif negative_scores:
            return {"label": "negative", "score": sum(negative_scores) / len(negative_scores)}
        else:
            return {"label": "neutral", "score": 0.5}
    
    def extract_keywords(self, text, n=10):
        if not text:
            return []
            
        try:
            # 키워드 추출
            words = self.okt.nouns(text)
            word_counts = Counter(words)
            return [word for word, _ in word_counts.most_common(n)]
        except Exception as e:
            print(f"❌ 키워드 추출 중 에러: {e}")
            return []
    
    def process_category(self, category_path):
        print(f"\n📊 카테고리 분석 중: {os.path.basename(category_path)}")
        
        try:
            # JSON 파일 읽기
            with open(os.path.join(category_path, "blog_data.json"), 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"❌ 파일 읽기 중 에러: {e}")
            return
        
        results = []
        for item in data:
            if not item.get('content'):
                continue
                
            try:
                # 텍스트 전처리
                processed_text = self.preprocess_text(item['content'])
                
                # 감성 분석
                sentiment = self.analyze_sentiment(processed_text)
                
                # 키워드 추출
                keywords = self.extract_keywords(processed_text)
                
                # 결과 업데이트
                item['sentiment_analysis'] = {
                    "positive_score": sentiment['score'] if sentiment['label'] == 'positive' else 1 - sentiment['score'],
                    "negative_score": sentiment['score'] if sentiment['label'] == 'negative' else 1 - sentiment['score'],
                    "neutral_score": 1 - abs(sentiment['score'] - 0.5) * 2,
                    "overall_sentiment": sentiment['label'],
                    "keywords": keywords,
                    "analyzed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                results.append(item)
            except Exception as e:
                print(f"❌ 항목 처리 중 에러: {e}")
                continue
        
        if not results:
            print(f"⚠️ 처리된 결과가 없습니다: {category_path}")
            return
            
        # 결과 저장
        try:
            with open(os.path.join(category_path, "blog_data_analyzed.json"), 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 결과 저장 중 에러: {e}")
            return
        
        # 통계 정보 생성
        self.generate_statistics(results, category_path)
        
    def generate_statistics(self, data, category_path):
        if not data:
            print(f"⚠️ 통계 생성할 데이터가 없습니다: {category_path}")
            return
            
        try:
            # 감성 분석 통계 생성
            sentiment_counts = Counter(item['sentiment_analysis']['overall_sentiment'] for item in data)
            total = len(data)
            
            if total == 0:
                print(f"⚠️ 데이터가 없어 통계를 생성할 수 없습니다: {category_path}")
                return
            
            stats = {
                "total_posts": total,
                "sentiment_distribution": {
                    sentiment: {
                        "count": count,
                        "percentage": (count / total) * 100
                    }
                    for sentiment, count in sentiment_counts.items()
                },
                "average_scores": {
                    "positive": sum(item['sentiment_analysis']['positive_score'] for item in data) / total,
                    "negative": sum(item['sentiment_analysis']['negative_score'] for item in data) / total,
                    "neutral": sum(item['sentiment_analysis']['neutral_score'] for item in data) / total
                }
            }
            
            # 통계 정보 저장
            with open(os.path.join(category_path, "sentiment_stats.json"), 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 통계 생성 중 에러: {e}")

if __name__ == "__main__":
    analyzer = SentimentAnalyzer()
    base_path = "result"
    
    # 각 카테고리별로 감성 분석 수행
    for category in os.listdir(base_path):
        category_path = os.path.join(base_path, category)
        if os.path.isdir(category_path):
            analyzer.process_category(category_path)
    
    print("\n✅ 모든 감성 분석이 완료되었습니다!") 