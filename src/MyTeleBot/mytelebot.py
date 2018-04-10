import telebot

import constants
from mytelebot_db import MyTeleBotDB
from mytoken import TOKEN


class MyTeleBot:
    def __init__(self):
        self.bot = telebot.TeleBot(TOKEN)
        self.db = MyTeleBotDB()
        self.init_handlers()

    def init_handlers(self):
        ''' Инициализация обработчиков событий telegram '''

        @self.bot.message_handler(commands=['start', 'help'])
        def command_help(message):
            self.bot.send_message(message.chat.id, constants.GREET)

        @self.bot.message_handler(content_types=['text'])
        def handle_message(message):
            self.bot.send_message(message.chat.id, self.format_news(), parse_mode='HTML')

    def format_news(self):
        news = self.db.get_news()
        if len(news)==0:
            return (constants.BASE_EMPTY)
        return '\n\n'.join(
            [constants.TEMPLATE.format(**n) for n in news])

    
    def run(self):
        
        self.bot.polling(none_stop=True, interval=0)


if __name__ == '__main__':
    bot = MyTeleBot()
    bot.run()
