import telebot
import cherrypy
from mytoken import TOKEN
import constants
from mytelebot_db import MyTeleBotDB
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
                self.format_news(),
                parse_mode='HTML',
                disable_web_page_preview=1
            )

    def format_news(self):
        news = self.db.get_news()
        if len(news) == 0:
            return (constants.BASE_EMPTY)
        answer = '\n\n'
        for i in news:
            date = datetime.utcfromtimestamp(i['published']).strftime("%Y-%m-%d %H:%M:%S")
            payload = constants.TEMPLATE.format(**i)
            answer = '{} {} {} {} \n\n'.format(answer, emojize(":arrow_right:", use_aliases=True), str(date), payload)

        return answer

    #webhook handler
    def process_new_updates(self, *args):
        self.bot.process_new_updates(*args)



    def run(self):

        # remove webhook before started
        self.bot.remove_webhook()
        if constants.WEBHOOK=='YES':
            # setup webhook 
            self.bot.set_webhook(url=constants.WEBHOOK_URL_BASE + constants.WEBHOOK_URL_PATH,
                      certificate=open(constants.WEBHOOK_SSL_CERT, 'r'))
            # CherryPy server config
            cherrypy.config.update({
                'server.socket_host': constants.WEBHOOK_LISTEN,
                'server.socket_port': constants.WEBHOOK_PORT,
                'server.ssl_module': 'builtin',
                'server.ssl_certificate': constants.WEBHOOK_SSL_CERT,
                'server.ssl_private_key': constants.WEBHOOK_SSL_PRIV
            })


            cherrypy.quickstart(WebhookServer(), constants.WEBHOOK_URL_PATH, {'/': {}})

        else:
            self.bot.polling(none_stop=True, interval=0)
        


# webhook-server
class WebhookServer(object):
    @cherrypy.expose
    def index(self):
        if 'content-length' in cherrypy.request.headers and \
                        'content-type' in cherrypy.request.headers and \
                        cherrypy.request.headers['content-type'] == 'application/json':
            length = int(cherrypy.request.headers['content-length'])
            json_string = cherrypy.request.body.read(length).decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            # message handler
            bot.process_new_updates([update])
            return ''
        else:
            raise cherrypy.HTTPError(403)






if __name__ == '__main__':
    bot = MyTeleBot()
    bot.run()




