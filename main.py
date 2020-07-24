import requests
import re
from bs4 import BeautifulSoup
import time
import redis
import telebot
from apscheduler.schedulers.background import BackgroundScheduler

TOKEN = ""
TGflag = False
chatidList = []
bot = telebot.TeleBot(TOKEN)
redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)
session = requests.session()
header = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36"
}


def login(username, password):
    try:
        url = "https://www.hostloc.com/member.php?mod=logging&action=login&loginsubmit=yes&infloat=yes&lssubmit=yes&inajax=1"
        data = {
            'fastloginfield': 'username',
            'username': username,
            'password': password,
            'quickforward': 'yes',
            'handlekey': 'ls'
        }
        html = session.post(url, data, header)
        print(html.text)

    except Exception as e:
        print(e)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    global TGflag
    global chatidList
    TGflag = True
    try:
        chatidList.append(message.chat.id)
        bot.reply_to(message, '采集开始')
        time.sleep(1)
    except Exception as e:
        print(e)

def sendMsg(msg):
    if TGflag:
        for chatid in chatidList:
            try:
                bot.send_message(chatid, msg)
                time.sleep(1)
            except Exception as e:
                time.sleep(5)
                bot.send_message(chatid, msg)

def rollMarch():
    pageNum = 1
    flag = False
    while True:
        url = "https://www.hostloc.com/forum.php?mod=forumdisplay&fid=45&orderby=dateline&orderby=dateline&filter=author&page=" + str(
            pageNum)
        forumHtml = session.get(url, headers=header).text
        print("爬了一次列表")
        try:
            bsData = BeautifulSoup(forumHtml, 'html.parser')
            normalthreadlist = bsData.findAll(name='tbody', attrs={"id": re.compile("normalthread_.*")})
            for normalthread in normalthreadlist:
                # print(normalthreadlist[i])
                forumid = normalthread['id']
                if not redis_client.exists(forumid) and pageNum <= 3:
                    # print(forumid)
                    forum = normalthread.th
                    forum = forum.find(name="a", attrs={"class": "s xst"})
                    title = forum.text
                    forumUrl = "https://www.hostloc.com/" + forum['href']
                    redis_client.set(forumid, title, ex=1200)
                    sendMsg(title + "\n" + forumUrl)
                else:
                    flag = True
                    break

            if flag:
                break

            pageNum += 1
            time.sleep(2)
        except Exception as e:
            pass


def start():
    if TGflag:
        rollMarch()


if __name__ == '__main__':
    redis_client.flushall()
    redis_client.flushdb()
    scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
    scheduler.add_job(start, 'interval', seconds=20)
    scheduler.start()
    bot.polling()
