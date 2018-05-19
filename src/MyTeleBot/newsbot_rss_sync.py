import logging
import os
import time

import feedparser

from mytelebot_db import MyTeleBotDB

RSS_CHANNELS = [
    'https://echo.msk.ru/interview/rss-fulltext.xml',
    'http://lenta.ru/rss/news',
    'https://www.rt.com/rss/',
    'https://3dnews.ru/news/rss/',
    'https://3dnews.ru/software-news/rss/',
]

PATH_LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log/')
if not os.path.exists(PATH_LOG):
    os.makedirs(PATH_LOG)

logging.basicConfig(
    handlers=[logging.FileHandler(PATH_LOG + 'sync_rss.log', 'a', 'utf-8')],
    format='%(asctime)-15s %(message)s',
    level=logging.INFO,
)
logger = logging.getLogger('sync_rss')


class MyTeleBotRSS:
    def __init__(self):
        self.db = MyTeleBotDB()

    def process(self, channel, entries):
        """Обработка новостей и отправка их в бд.
        Принимает:
        channel - веб-адрес канала rss,
        entries - список новостей
        """
        last_published = self.db.get_last_published(channel)
        news_count = 0
        for entry in entries:
            news = {}
            published = time.mktime(entry.published_parsed)
            if published > last_published:
                news['title'] = entry['title']
                news['link'] = entry['link']
                news['published'] = published
                news['summary'] = entry['summary']
                news['base'] = channel
                try:
                    self.db.set_news(news)
                    news_count += 1
                except Exception as err:
                    logger.exception('Error: %s in db.set_news', err)
            else:
                break
        logger.info('Добавленно %d новостей из %s', news_count, channel)

    def run(self, channels):
        """Метод обработки каналов rss.
        Принимает:
        channels - список веб-адресов каналов rss.
        """
        for channel in RSS_CHANNELS:
            rss = feedparser.parse(channel)
            if rss.bozo:
                logger.warning('rss error for %s, bozo_exception: %s', channel,
                               rss.bozo_exception)
                continue
            self.process(channel, rss.entries)
        self.db.close()
        logger.info('MyTeleBotRSS client is closed')


if __name__ == '__main__':
    bot_rss = MyTeleBotRSS()
    try:
        bot_rss.run(RSS_CHANNELS)
    except Exception as err:
        logger.exception('Error: %s', err)
