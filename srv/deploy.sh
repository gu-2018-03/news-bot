apt install python3-pip mongodb
mkdir /var/www
cd /var/www
git clone https://github.com/gu-2018-03/news-bot.git
pip3 install -r requirements.txt
cp -r ./news-bot/srv /
systemctl start news-bot

