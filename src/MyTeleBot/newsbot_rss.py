
import asyncio
import logging
import os
import queue
import time

import aiohttp
import async_timeout
import feedparser
import html2text

from mytelebot_db import AsyncMyTeleBotDB

# путь к файлу с логами,
PATH_LOG = './log/'

if not os.path.exists(PATH_LOG):
    os.makedirs(PATH_LOG)

# конфигурация логгера
logging.basicConfig(
    # filename=PATH_LOG+'rss.log',
    handlers=[logging.FileHandler(PATH_LOG + 'rss.log', 'a', 'utf-8')],
    format='%(asctime)-15s %(message)s',
    level=logging.INFO)
logger = logging.getLogger('rss')

RSS_CHANNELS = {
    'echo': 'https://echo.msk.ru/interview/rss-fulltext.xml',
    'lenta': 'http://lenta.ru/rss/news',
    'rt': 'https://www.rt.com/rss/',
    # 'popular_science_science': 'https://www.popsci.com/rss-science.xml?loc=contentwell&lnk=science&dom=section-1',
    # 'popular_science_tech': 'https://www.popsci.com/rss-technology.xml?loc=contentwell&lnk=tech&dom=section-1',
    # 'popular_science_diy': 'https://www.popsci.com/rss-diy.xml?loc=contentwell&lnk=diy&dom=section-1'
}


class Rss_source(object):
    """
    класс храняций список источников, в дальнейшем сюда добавится последнняя
    прочитанная новость, чтобы избежать дублирования
    """
    def __init__(self, channels):
        self.channels = channels
        self.left_to_process = len(channels)


async def read_feed(db, feeds_queue, rss_source):
    """
    фунция, читающая полученный rss-файл (развибает его на записи) и передающая
    обработчику (processor), в качестве параметров принимает очередь rss-feeds,
    очередь новостей и объект хранящий список каналов
    """
    left_to_process = rss_source.left_to_process
    while (left_to_process > 0):
        if not feeds_queue.empty():
            channel, feed = feeds_queue.get()
            if feed:
                try:
                    rss = feedparser.parse(feed)
                    await process(db, channel, rss.entries)
                    left_to_process -= 1
                except Exception as e:
                    logger.exception('Error: %s in parsing feed (read_feed)', e)
        await asyncio.sleep(0)


async def process(db, channel, entries):
    """
    функция, обрабатывающая записии, формирующая новости и отправляющая новости
    в очередь новостей, принимает список записей и очередь новостей
    """
    last_published = await db.get_last_published(channel)
    news_count = 0
    for entry in entries:
        news = {}
        published = time.mktime(entry.published_parsed)
        if published > last_published:
            news['title'] = entry['title']
            news['link'] = entry['link']
            news['published'] = published
            news['summary'] = html2text.html2text(entry['summary'])
            news['base'] = channel
            try:
                await db.set_news(news)
                news_count += 1
            except Exception as e:
                logger.exception('Error: %s in db.set_news', e)
        else:
            break
    logger.info('Добавленно %d новостей из %s', news_count, channel)
    # print('Добавленно {} новостей из {}'.format(news_count, channel))


async def get_data2(channel, feeds_queue):
    """
    функция получающая rss-данные по Http и отравляющая их в очердеь feeds_queue
    """
    async with aiohttp.ClientSession() as session:
        async with async_timeout.timeout(5):
            try:
                async with session.get(channel) as response:
                    data = await response.read()
                    feeds_queue.put((channel, data))
            except TimeoutError as e:
                logger.exception('Error: %s in session.get', e)
                # print('Connection Timeout', e)
            except aiohttp.client_exceptions.ClientConnectorError as e:
                logger.exception('Connection error: %s in session.get', e)
                # print('Connection Error')


def main_cycle():
    """ основнй цикл """
    feeds_queue = queue.Queue()
    rss_source = Rss_source(RSS_CHANNELS)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    db = AsyncMyTeleBotDB(loop)


    tasks = [asyncio.Task(get_data2(channel, feeds_queue))
                for channel in rss_source.channels.values()]
    tasks.append(read_feed(db, feeds_queue, rss_source)) # db
    
    start = time.time()
    loop.run_until_complete(asyncio.wait(tasks))

    loop.close()
    elapsed = time.time() - start

    logger.info('Затраченное время: %.3f сек', elapsed)


if __name__ == '__main__':
    main_cycle()
