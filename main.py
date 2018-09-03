from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import argparse
import telegram
import sys
import os
import pickle
import utils

sys.argv = ['--proxy 1']
parser = argparse.ArgumentParser(description="Bot to parse news from FPMI's site")
parser.add_argument('--proxy', dest='proxy', type=int,
                    default=1, help='use proxy or not')

bot = None
info_text = 'NOT IMPLEMENTED'
fpmi_url = 'https://mipt.ru/education/departments/fpmi/'
channel_id = -1001180214136  # FPMI_announcements.
pause = 60.0


if os.path.exists(utils.PKL) is False:
    data = list()
    with open(utils.PKL, 'wb') as f:
        pickle.dump(data, f)


def announce():
    # Get all news from site.
    fresh_news = utils.get_info(fpmi_url)
    # Load dumped news from .pkl file.
    loaded_news = utils.load_news()
    # Find difference between fresh and dumped news.
    news_list = utils.diff_news(fresh_news, loaded_news)

    news_list = utils.get_sorted(news_list)

    # If there is at least one fresh announcement -- post it.
    if len(news_list) == 0:
        print('-> nothing new :(')
    else:
        print('-> announce')
        to_announce = news_list[0]
        try:
            if to_announce not in loaded_news:
                text = utils.compose_announcement(to_announce)
                # Make announcement.
                bot.send_message(chat_id=channel_id, text=text, parse_mode=telegram.ParseMode.MARKDOWN, timeout=9999)
                # Save updated news.

                loaded_news.append(to_announce)
                print('-> appended')
                utils.save_news(loaded_news)
                print('-> done')
            else:
                print('-> duplicate :(')
        except telegram.error.TimedOut as e:
            print('-> skipping this event due to Timed Out')
            print(e)


announcer = utils.Looper(announce, pause=pause)  # `pause` == seconds.


def help(bot, update):
    update.message.reply_text(info_text)
    return


def main():
    global bot
    token = utils.get_token('res/token.json')

    args = parser.parse_args()
    if args.proxy == 1:
        print('-> USE PROXY')
        req = telegram.utils.request.Request(proxy_url='socks5h://127.0.0.1:9050',
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
