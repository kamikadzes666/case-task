from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import sqlite3
import datetime
from typing import List
from enum import Enum


app = FastAPI()


DATABASE = "reviews.db"

POSITIVE_WORDS= [
    'отличн', 'хорош', 'прекрасн', 'замечательн', 'великолепн', 'превосходн', 'идеальн',
    'супер', 'классн', 'удобн', 'легк', 'прост', 'быстр', 'надежн', 'качественн', 'приятн',
    'рад', 'довол', 'восхитительн', 'потрясающ',
    'любл', 'нрав', 'рекоменд', 'совет', 'благодар', 'восхища', 'наслажда', 'обожа',
    'восторг', 'удовольствие', 'радость', 'позитивн', 'удовлетвор',
    'топ', 'крут', 'шикарн', 'безупречн', 'неплох', 'лучш', 'балд', 'чуд'
]
NEGATIVE_WORDS = ['плох', 'ужасн', 'отвратительн', 'ненавиж', 'кошмар',
                      'разочарован', 'неудобн', 'не рекоменд', 'отстой',
                      'лажа', 'мерзк', 'гадк', 'скверн', 'недовол', 'беси',
                      'зли', 'раздража', 'жале', 'терпе', 'возмуща', 'обман']


def init_db():
    """Инициализация базы"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


init_db()


class Sentiment(Enum):
    POSITIVE = 'positive'
    NEGATIVE = 'negative'
    NEUTRAL = 'neutral'


class ReviewCreateModel(BaseModel):
    text: str


class ReviewResponseModel(BaseModel):
    id: int
    text: str
    sentiment: str
    created_at: str


class ReviewDAO:
    @staticmethod
    def get_reviews_by_sentiment(sentiment: Sentiment):
        """Получение всех отзывов по определенному типу"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, text, sentiment, created_at FROM reviews WHERE sentiment = ?",
            (sentiment.value,)
        )
        results = cursor.fetchall()
        conn.close()

        return results

    @staticmethod
    def add_review(review_text: str, sentiment: str, created_at: str):
        """Добавление отзыва"""
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reviews (text, sentiment, created_at) VALUES (?, ?, ?)",
            (review_text, sentiment, created_at)
        )
        review_id = cursor.lastrowid
        conn.commit()

        return review_id


def analyze_sentiment(text: str) -> str:
    """Простой анализатор тональности на основе ключевых слов"""
    text_lower = text.lower()

    for word in NEGATIVE_WORDS:
        if word in text_lower:
            return Sentiment.NEGATIVE.value

    for word in POSITIVE_WORDS:
        if word in text_lower:
            if f"не {word}" in text_lower:
                return Sentiment.NEGATIVE.value
            return Sentiment.POSITIVE.value


    return Sentiment.NEUTRAL.value


@app.post("/reviews", response_model=ReviewResponseModel)
async def create_review(review: ReviewCreateModel):
    """Создание нового отзыва с анализом тональности"""
    if not review.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    sentiment = analyze_sentiment(review.text)
    created_at = datetime.datetime.utcnow().isoformat()

    review_id = ReviewDAO.add_review(review.text, sentiment, created_at)

    result_data = {'id': review_id,
                   'text': review.text,
                   'sentiment': sentiment,
                   'created_at': created_at}

    return result_data


@app.get("/reviews", response_model=List[ReviewResponseModel])
async def get_reviews(sentiment: Sentiment = Query(..., description="Filter by sentiment: 'positive', 'negative' or 'neutral'")):
    """Получение отзывов по тональности"""
    if sentiment not in Sentiment:
        raise HTTPException(status_code=400, detail="Invalid sentiment value. Use 'positive', 'negative' or 'neutral'")

    results = ReviewDAO.get_reviews_by_sentiment(sentiment)

    return [
        {
            "id": row[0],
            "text": row[1],
            "sentiment": row[2],
            "created_at": row[3]
        }
        for row in results
    ]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)