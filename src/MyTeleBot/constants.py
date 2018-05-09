from mytoken import TOKEN

#webhooks of pooling
WEBHOOK = 'YES'


GREET = 'Рад Вас приветствовать! Напишите мне что-нибудь и я Вам пришлю 10' \
        ' последних новостей.'

BASE_EMPTY = 'На данный момент база новостей пуста, но она еще наполнится!'

TEMPLATE = ' {title} <a href="{link}">читать...</a>'

#server config
WEBHOOK_HOST = '95.163.248.15' #static server ip
WEBHOOK_PORT = 443 # port 443, 80, 88 or 8443
WEBHOOK_LISTEN = '0.0.0.0' #listen from everywhere
WEBHOOK_SSL_CERT = './webhook_cert.pem' #cert
WEBHOOK_SSL_PRIV = './webhook_pkey.pem' #privat cert
WEBHOOK_URL_BASE = "https://%s:%s" % (WEBHOOK_HOST, WEBHOOK_PORT)
WEBHOOK_URL_PATH = "/%s/" % (TOKEN)
