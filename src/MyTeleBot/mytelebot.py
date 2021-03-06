import telebot

import constants
from mytelebot_db import MyTeleBotDB
from mytoken import TOKEN
from emoji import emojize
from datetime import datetime

class MyTeleBot:
    def __init__(self):
        self.bot = telebot.TeleBot(TOKEN)
        self.db = MyTeleBotDB()
        self.init_handlers()

    def init_handlers(self):
        """
        Инициализация обработчиков событий telegram
        """

        @self.bot.message_handler(commands=['start', 'help'])
        def command_help(message):
            self.bot.send_message(message.chat.id, constants.GREET)

        @self.bot.message_handler(content_types=['text'])
        def handle_message(message):
            self.bot.send_message(
                message.chat.id,
                self.format_news(message.text),
                parse_mode='HTML',
                disable_web_page_preview=1
            )

    def format_news(self, key=''):
        if key == '*':
            news = self.db.get_news()
        else:
            news = self.db.get_news(key=key)
        if len(news) == 0:
            return (constants.BASE_EMPTY)
        answer = '\n\n'
        for i in news:
            date = datetime.utcfromtimestamp(i['published']).strftime("%Y-%m-%d %H:%M:%S")
            payload = constants.TEMPLATE.format(**i)
            answer = '{} {} {} {} \n\n'.format(answer, emojize(":arrow_right:", use_aliases=True), str(date), payload)

        return answer

    def run(self):
        self.bot.polling(none_stop=True, interval=0)


if __name__ == '__main__':
    bot = MyTeleBot()
    bot.run()
