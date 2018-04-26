import telebot
import cherrypy
from mytoken import TOKEN
import constants
from mytelebot_db import MyTeleBotDB
from emoji import emojize
from datetime import datetime

#server config
WEBHOOK_HOST = '95.163.248.15' #static server ip
WEBHOOK_PORT = 443 # port 443, 80, 88 or 8443
WEBHOOK_LISTEN = '0.0.0.0' #listen from everywhere

WEBHOOK_SSL_CERT = './webhook_cert.pem' #cert
WEBHOOK_SSL_PRIV = './webhook_pkey.pem' #privat cert

WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (TOKEN)

bot = telebot.TeleBot(TOKEN)

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



db = MyTeleBotDB()
@bot.message_handler(commands=['start', 'help'])
def command_help(message):
    bot.send_message(message.chat.id, constants.GREET)

@bot.message_handler(content_types=['text'])
def handle_message(message):
    bot.send_message(
            message.chat.id,
            format_news(),
            parse_mode='HTML',
            disable_web_page_preview=1
            )

def format_news():
    news = db.get_news()
    if len(news) == 0:
        return (constants.BASE_EMPTY)
    answer = '\n\n'
    for i in news:
        date = datetime.utcfromtimestamp(i['published']).strftime("%Y-%m-%d %H:%M:%S")
        payload = constants.TEMPLATE.format(**i)
        answer = '{} {} {} {} \n\n'.format(answer, emojize(":arrow_right:", use_aliases=True), str(date), payload)

    return answer




# remove webhook before started
bot.remove_webhook()

# setup webhook
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,
                certificate=open(WEBHOOK_SSL_CERT, 'r'))


# CherryPy server config
cherrypy.config.update({
    'server.socket_host': WEBHOOK_LISTEN,
    'server.socket_port': WEBHOOK_PORT,
    'server.ssl_module': 'builtin',
    'server.ssl_certificate': WEBHOOK_SSL_CERT,
    'server.ssl_private_key': WEBHOOK_SSL_PRIV
})


cherrypy.quickstart(WebhookServer(), WEBHOOK_URL_PATH, {'/': {}})
