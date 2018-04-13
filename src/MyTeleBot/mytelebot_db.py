import pymongo
from motor import motor_asyncio
import time


class MyTeleBotDB:
    '''
    класс для работы с БД.
    '''
    def __init__(self):
        self.client = pymongo.MongoClient(serverSelectionTimeoutMS=2000)
        try:
            self.client.admin.command('ismaster')
        except pymongo.errors.ServerSelectionTimeoutError:
            raise

        self.db = self.client.telebot
        self.required = {'title', 'published', 'link', 'summary', 'base'}
        
    def get_news(self, key='', count=10) -> []:
        '''
        Принимает на вход:
        key   - (пока не используется)
        count - количество возвращаемых новостей

        Возвращает список из словарей, каждый словарь - отдельная новость.
        Список отсортирован по времени публикации - от более новой новости
        к более старой.
        Словарь имеет следующие поля:
        {
            'title':     -заголовок новости,
            'published': -таймстамп времени публикации - тип float,
            'link':      -адрес новости,
            'summary':   -краткое изложение новости,
            'base':      -адрес rss-канала
        }
        '''
        news = self.db.news.find() \
                   .sort('published', pymongo.DESCENDING) \
                   .limit(count)
        return list(news)

    def set_news(self, news: dict):
        '''
        Принимает обязательный параметр news типа dict.
        Обязательные поля в словаре:
        {
            'title':     -заголовок новости,
            'published': -таймстамп времени публикации - тип float,
            'link':      -адрес новости,
            'summary':   -краткое изложение новости,
            'base':      -адрес rss-канала
        }
        Также можно добавлять другие поля с дополнительной информацией.
        '''
        if not isinstance(news, dict):
            error = 'expected dict instance, {} found'.format(type(news))
            raise TypeError(error)

        if not self.required <= set(news):
            error = 'not found required key(s) {}' \
                .format(self.required - set(news))
            raise TypeError(error)

        if not isinstance(news['published'], float):
            error = "a float is required for 'published' (got type {})" \
                .format(type(news['published']))
            raise TypeError(error)

        self.db.news.insert_one(news)

    def get_last_published(self, base):
        '''
        Возвращает время публикации последней новости для данного rss-канала.
        Если в БД для канала еще нет новостей, возвращает 0.0
        base - адрес rss-канала.
        '''
        try:
            last_news = self.db.news.find({'base': base}, {'published': 1}) \
                            .sort('published', pymongo.DESCENDING) \
                            .limit(1) \
                            .next()
        except StopIteration:
            return 0.0
        last_time = last_news['published']
        return last_time


class AsyncMyTeleBotDB:
    '''
    класс для работы с БД.
    '''
    def __init__(self, loop):
        self.client = motor_asyncio.AsyncIOMotorClient(io_loop=loop)
        self.db = self.client.telebot
        self.required = {'title', 'published', 'link', 'summary', 'base'}
        
    async def get_news(self, key='', count=10) -> []:
        '''
        Принимает на вход:
        key   - (пока не используется)
        count - количество возвращаемых новостей

        Возвращает список из словарей, каждый словарь - отдельная новость.
        Список отсортирован по времени публикации - от более новой новости
        к более старой.
        Словарь имеет следующие поля:
        {
            'title':     -заголовок новости,
            'published': -таймстамп времени публикации - тип float,
            'link':      -адрес новости,
            'summary':   -краткое изложение новости,
            'base':      -адрес rss-канала
        }
        '''
        cursor = self.db.news.find() \
                   .sort('published', pymongo.DESCENDING) 
        news = await cursor.to_list(count)
        return news

    async def set_news(self, news: dict):
        '''
        Принимает обязательный параметр news типа dict.
        Обязательные поля в словаре:
        {
            'title':     -заголовок новости,
            'published': -таймстамп времени публикации - тип float,
            'link':      -адрес новости,
            'summary':   -краткое изложение новости,
            'base':      -адрес rss-канала
        }
        Также можно добавлять другие поля с дополнительной информацией.
        '''
        if not isinstance(news, dict):
            error = 'expected dict instance, {} found'.format(type(news))
            raise TypeError(error)

        if not self.required <= set(news):
            error = 'not found required key(s) {}' \
                .format(self.required - set(news))
            raise TypeError(error)

        if not isinstance(news['published'], float):
            error = "a float is required for 'published' (got type {})" \
                .format(type(news['published']))
            raise TypeError(error)

        await self.db.news.insert_one(news)

    async def get_last_published(self, base):
        '''
        Возвращает время публикации последней новости для данного rss-канала.
        Если в БД для канала еще нет новостей, возвращает 0.0
        base - адрес rss-канала.
        '''
        cursor = self.db.news.find({'base': base}, {'published': 1}) \
                             .sort('published', pymongo.DESCENDING) \
                             .limit(1)
        last_news = await cursor.to_list(1)
        if not last_news:
            return 0.0
        last_time = last_news[0]['published']
        return last_time


if __name__ == '__main__':
    pass