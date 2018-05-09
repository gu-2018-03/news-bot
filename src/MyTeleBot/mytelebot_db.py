import pymongo
from motor import motor_asyncio
import time


class AlreadyExistsError(Exception):
    """ Класс исключения.
    Генерируется при попытке сохранения в бд поля, помеченного как уникальное,
    если в бд уже существует запись с таким полем.
    
    """
    pass


class DoesNotExistsError(Exception):
    """ Класс исключения.
    Генерируется при попытке обновления документа, которого несуществует в бд.

    """
    pass


class MyTeleBotDB:
    """
    класс для работы с БД.
    """

    def __init__(self):
        self.client = pymongo.MongoClient(serverSelectionTimeoutMS=2000)
        try:
            self.client.admin.command('ismaster')
        except pymongo.errors.ServerSelectionTimeoutError:
            raise

        self.db = self.client.telebot
        self.news = self.db.news
        self.news.create_index('published')
        self.news.create_index(
            [('title', pymongo.TEXT), ('summary', pymongo.TEXT)],
            default_language='russian')
        
        self.rss = self.db.rss
        self.rss.create_index('name', unique=True)
        self.rss.create_index('channel', unique=True)
        self.required = {'title', 'published', 'link', 'summary', 'base'}

    def get_news(self, key='', count=10) -> []:
        """
        Принимает на вход:
        key   - строка для поиска по новостям
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
        """
        if key:
            news = self.news.find(
                {'$text' : {'$search': key}}
            )
        else:
            news = self.news.find()
        return list(news.sort('published', pymongo.DESCENDING).limit(count))

    def set_news(self, news: dict):
        """
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
        """
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

        self.news.insert_one(news)

    def get_last_published(self, base):
        """
        Возвращает время публикации последней новости для данного rss-канала.
        Если в БД для канала еще нет новостей, возвращает 0.0
        base - адрес rss-канала.
        """
        try:
            last_news = self.news.find({'base': base}, {'published': 1}) \
                .sort('published', pymongo.DESCENDING) \
                .limit(1) \
                .next()
        except StopIteration:
            return 0.0
        last_time = last_news['published']
        return last_time

    def add_rss(self, short_name, channel, **kwargs):
        """ Добавить в бд запись о rss-канале
        
        Args:
            short_name (str): короткое уникальное имя.
            channel (str): web-адрес канала.
            **kwargs: поля с дополнительной информацией.

        Raises:
            AlreadyExistsError: при попытке сохранить в бд, если запись
                с таким short_name или channel уже существует в бд.
        
        """
        rss_item = {**kwargs}
        rss_item['name'] = short_name
        rss_item['channel'] = channel
        try:
            self.rss.insert_one(rss_item)
        except pymongo.errors.DuplicateKeyError as err:
            raise AlreadyExistsError(err)

    def check_rss_name(self, short_name) -> bool:
        """ Проверить наличие rss-канала по имени.

        Args:
            short_name (str): короткое уникальное имя канала.

        Returns:
            bool: True - имеется в бд, False - нет.

        """
        return bool(self.rss.find_one({'name': short_name}))

    def check_rss_channel(self, channel) -> bool:
        """ Проверить наличие в бд канала по его web-адресу.
        
        Args:
            channel (str): web-адрес канала
        
        Returns:
            bool: True - имеется в бд, False - нет.

        """
        return bool(self.rss.find_one({'channel': channel}))
    
    def update_rss(self, short_name, **kwargs):
        """ Обновить запись о rss-канале в бд.
        
        Args:
            short_name (str): короткое уникальное имя для канала.
            **kwargs: поля с новым значением.
        
        Raises:
            DoesNotExistsError: при попытке обновить несуществующую запись в бд.

        """
        if not self.check_rss_name(short_name):
            raise DoesNotExistsError('Документа с short_name {} не существует' \
                .format(short_name))
        self.rss.update_one({'name': short_name}, {'$set': kwargs})


    def delete_rss(self, short_name):
        """ Удалить из бд запись о rss-канале.
        
        Args:
            short_name (str): короткое уникальное имя для канала.

        """
        self.rss.delete_one({'name': short_name})

    def get_rss_channels(self):
        """ Получить список rss-каналов.

        Returns:
            Возвращает словарь вида:
            {
                short_name: channel,
                ...
            }

        """
        result = {}
        for item in self.rss.find():
            result[item['name']] = item['channel']
        return result

    def get_rss(self, key):
        """ Получить данные rss-канала из бд.
        
        Args:
            key (str): короткое имя канала или web-адрес.

        Returns:
            Возвращает словарь с данными канала:
            {
                'name': уникальное короткое имя,
                'channel': web-адрес канала,
                ... (дополнительные данные),
            }
            или None, если ничего не нашлось.
            
        """
        result = (self.rss.find_one({'name': key})
                  or self.rss.find_one({'channel': key}))
        return result



class AsyncMyTeleBotDB:
    """
    класс для работы с БД.
    """

    def __init__(self, loop):
        self.client = motor_asyncio.AsyncIOMotorClient(io_loop=loop)

        self.db = self.client.telebot
        self.news = self.db.news
        self.news.create_index('published')
        self.news.create_index(
            [('title', pymongo.TEXT), ('summary', pymongo.TEXT)],
            default_language='russian')
        
        self.rss = self.db.rss
        self.rss.create_index('name', unique=True)
        self.rss.create_index('channel', unique=True)
        self.required = {'title', 'published', 'link', 'summary', 'base'}

    async def get_news(self, key='', count=10) -> []:
        """
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
        """
        cursor = self.news.find() \
            .sort('published', pymongo.DESCENDING)
        news = await cursor.to_list(count)
        return news

    async def set_news(self, news: dict):
        """
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
        """
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

        await self.news.insert_one(news)

    async def get_last_published(self, base):
        """
        Возвращает время публикации последней новости для данного rss-канала.
        Если в БД для канала еще нет новостей, возвращает 0.0
        base - адрес rss-канала.
        """
        cursor = self.news.find({'base': base}, {'published': 1}) \
            .sort('published', pymongo.DESCENDING) \
            .limit(1)
        last_news = await cursor.to_list(1)
        if not last_news:
            return 0.0
        last_time = last_news[0]['published']
        return last_time


if __name__ == '__main__':
    pass
