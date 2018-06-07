from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import numpy as np
import threading
import argparse
import telegram
import sys
import os
import pickle
import utils
import json
import time
from emoji import emojize

# sys.argv = ['--proxy 1']
pause = 10.0

if os.path.exists(utils.PKL) is False:
    data = list()
    with open(utils.PKL, 'wb') as f:
        pickle.dump(data, f)


parser = argparse.ArgumentParser(description="Bot to parse news from FPMI's site")
parser.add_argument('--proxy', dest='proxy', type=int,
                    default=1, help='use proxy or not')


class Looper(threading.Thread):
    def __init__(self, loop_func, pause=5):
        super(Looper, self).__init__()
        self.stop_event = threading.Event()
        self.loop_func = loop_func
        self.pause = pause

    def run(self):
        while not self.stop_event.is_set():
            self.loop_func()
            time.sleep(self.pause)

    def stop(self):
        self.stop_event.set()


bot = None
info_text = 'NOT IMPLEMENTED'
fpmi_url = 'https://mipt.ru/education/departments/fpmi/'
channel_id = -1001180214136  # FPMI_announcements.


def announce():
    news_list = utils.get_info(fpmi_url)

    news = news_list[np.random.randint(len(news_list))]

    # Get all news from site.
    fresh_news = utils.get_info(fpmi_url)
    # Load dumped news from .pkl file.
    loaded_news = utils.load_news()

    # Find difference between fresh and dumped news.
    news_list = utils.diff_news(fresh_news, loaded_news)
    news_list = sorted(news_list, key=lambda x: x['timestamp'])

    # If there is at least one fresh announcement -- post it.
    if len(news_list) > 0:
        print('-> announce')

        try:
            to_announce = news_list[0]
            text = utils.compose_announcement(to_announce)
            # Make announcement.
            bot.send_message(chat_id=channel_id, text=text, parse_mode=telegram.ParseMode.MARKDOWN)
            # Save updated news.
            loaded_news.append(to_announce)
            utils.save_news(loaded_news)
            print('-> done')
        except telegram.error.TimedOut as e:
            print(e)


def help(bot, update):
    update.message.reply_text(info_text)
    return


announcer = Looper(announce, pause=pause)  # Seconds.


def main():
    global bot
    token = utils.get_token('res/token.json')

    args = parser.parse_args()
    if args.proxy == 1:
        print('-> USE PROXY')
        req = telegram.utils.request.Request(proxy_url='socks5://127.0.0.1:9050',
                                             read_timeout=30, connect_timeout=20,
                                             con_pool_size=10)
        bot = telegram.Bot(token=token, request=req)
    elif args.proxy == 0:
        print('-> NO PROXY')
        bot = telegram.Bot(token=token)
    else:
        raise ValueError('Wrong proxy.')

    announcer.start()
    updater = Updater(bot=bot)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler('start', help))
    dp.add_handler(MessageHandler(Filters.text, help))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
