
import asyncio
import queue
import time

import feedparser

import aiohttp
import async_timeout
import html2text
from mytelebot_db import AsyncMyTeleBotDB

RSS_CHANNELS = {
    'echo': 'https://echo.msk.ru/interview/rss-fulltext.xml',
    'lenta': 'http://lenta.ru/rss/news',
    # 'popular_science_science': 'https://www.popsci.com/rss-science.xml?loc=contentwell&lnk=science&dom=section-1',
    # 'popular_science_tech': 'https://www.popsci.com/rss-technology.xml?loc=contentwell&lnk=tech&dom=section-1',
    # 'popular_science_diy': 'https://www.popsci.com/rss-diy.xml?loc=contentwell&lnk=diy&dom=section-1'
}


class Rss_source(object):
    '''
    класс храняций список источников, в дальнейшем сюда добавится последнняя
    прочитанная новость, чтобы избежать дублирования
    '''
    def __init__(self, channels):
        self.channels = channels
        self.left_to_process = len(channels)


async def read_feed(db, feeds_queue, news_queue, rss_source):
    '''
    фунция, читающая полученный rss-файл (развибает его на записи) и передающая
    обработчику (processor), в качестве параметров принимает очередь rss-feeds,
    очередь новостей и объект хранящий список каналов
    '''
    while (rss_source.left_to_process > 0):
        if not feeds_queue.empty():
            feed = feeds_queue.get()
            if feed is not None:
                try:
                    rss = feedparser.parse(feed)
                    await process(db, rss.feed.link, rss.entries, news_queue)
                    rss_source.left_to_process -= 1
                except Exception as e:
                    print(e)
        await asyncio.sleep(0)


async def process(db, feed, entries, news_queue):
    '''
    функция, обрабатывающая записии, формирующая новости и отправляющая новости
    в очередь новостей, принимает список записей и очередь новостей
    '''
    
    for entry in entries:
        news = {}
        published = time.mktime(entry.published_parsed)
        news['title'] = entry['title']
        news['link'] = entry['link']
        news['published'] = published
        news['summary'] = html2text.html2text(entry['summary'])
        news['base'] = feed
        # news_queue.put(news)
        try:
            await db.set_news(news)
        except Exception as e:
            print(e)
        # await asyncio.sleep(0)


# async def send_to_db(db, news_queue, rss_source):
#     '''
#     функция отправляющая новости в базу данных, примнимает базу данных, очередь
#     новостей и список каналов
#     '''
#     while (rss_source.left_to_process > 0) or (not news_queue.empty()):
#         if news_queue.empty():
#             await asyncio.sleep(0)
#         else:
#             news = news_queue.get()
#             try:
#                 await db.set_news(news)
#             except Exception as e:
#                 print(e)


async def get_data2(channel, feeds_queue):
    '''
    функция получающая rss-данные по Http и отравляющая их в очердеь feeds_queue
    '''
    async with aiohttp.ClientSession() as session:
        async with async_timeout.timeout(5):
            try:
                async with session.get(channel) as response:
                    data = await response.read()
                    feeds_queue.put(data)
            except TimeoutError as e:
                print('Connection Timeout', e)
            except aiohttp.client_exceptions.ClientConnectorError as e:
                print('Connection Error')


def main_cycle():
    ''' основнй цикл '''
    news_queue = queue.Queue()
    feeds_queue = queue.Queue()
    rss_source = Rss_source(RSS_CHANNELS)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    db = AsyncMyTeleBotDB(loop)

    tasks = [asyncio.Task(get_data2(channel, feeds_queue))
                for channel in rss_source.channels.values()]
    tasks.append(read_feed(db, feeds_queue, news_queue, rss_source)) # db
    # tasks.append(send_to_db(db, news_queue, rss_source))

    try:
        loop.run_until_complete(asyncio.wait(tasks))
    except Exception as e:
        print(e)
    finally:
        loop.close()


if __name__ == '__main__':
    main_cycle()
