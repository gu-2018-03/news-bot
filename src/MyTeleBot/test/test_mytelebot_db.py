import pytest
import pymongo
import random

from MyTeleBot.mytelebot_db import MyTeleBotDB


@pytest.fixture
def db():
    news_db = MyTeleBotDB()
    ex_db = news_db.db
    news_db.db = news_db.client.test_db
    yield news_db
    news_db.db.news.drop()
    news_db.db = ex_db


def test_set_news_err_dict(db):
    with pytest.raises(TypeError):
        db.set_news('')


def test_set_news_err_required_fields(db):
    news = {
        'title': 'First news',
        'published': 1234.55,
        'summary': 'lorem ipsum',
        'base': 'https://bla.bla/rss',
    }
    with pytest.raises(TypeError):
        db.set_news(news)


def test_set_news_err_published_float(db):
    news = {
        'title': 'First news',
        'published': '1234.55',
        'link': 'https://bla.bla/novost_dnja',
        'summary': 'lorem ipsum',
        'base': 'https://bla.bla/rss',
    }
    with pytest.raises(TypeError):
        db.set_news(news)


def test_get_news_empty(db):
    news = db.get_news()
    assert not news


def test_get_news_returned_type(db):
    news = db.get_news()
    assert isinstance(news, list)


def test_set_news(db):
    news = {
        'title': 'First news',
        'published': 1234.55,
        'link': 'https://bla.bla/novost_dnja',
        'summary': 'lorem ipsum',
        'base': 'https://bla.bla/rss',
    }
    db.set_news(news)
    result = db.get_news()
    assert len(result) == 1
    assert result[0] == news


def test_get_news_return_sorted(db):
    for i in range(15):
        news = {
            'title': 'First news',
            'link': 'https://bla.bla/novost_dnja',
            'published': random.random() * 1000,
            'summary': 'lorem ipsum',
            'base': 'https://bla.bla/rss',
        }
        db.set_news(news)

    result = db.get_news(count=15)
    assert len(result) == 15
    assert all(result[i]['published'] >= result[i + 1]['published']
               for i in range(len(result) - 1))


def test_get_last_published_for_empty(db):
    assert db.get_last_published('https://some_rss') == 0.0


def test_get_last_published(db):
    for i in range(10):
        news = {
            'title': 'First news',
            'link': 'https://bla.bla/novost_dnja',
            'published': float(i),
            'summary': 'lorem ipsum',
            'base': 'https://bla.bla/rss',
        }
        db.set_news(news)
        news = {
            'title': 'First news',
            'link': 'https://bla.bla/novost_dnja',
            'published': float(i) + 10.0,
            'summary': 'lorem ipsum',
            'base': 'https://another/rss',
        }
        db.set_news(news)

    assert db.get_last_published('https://bla.bla/rss') == 9
    assert db.get_last_published('https://another/rss') == 19
