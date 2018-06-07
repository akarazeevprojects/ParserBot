from datetime import datetime as dt
from bs4 import BeautifulSoup
from emoji import emojize
import requests
import pickle
import json
import os


weekdays_mapping = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
PKL = 'data/real_data.pkl'


def save_news(data):
    with open(PKL, 'wb') as f:
        pickle.dump(data, f)


def load_news():
    data = None

    with open(PKL, 'rb') as f:
        data = pickle.load(f)
    return data


def diff_news(fresh_news, old_news):
    difference_list = list()

    for news in fresh_news:
        if news not in old_news:
            difference_list.append(news)

    return difference_list


def compose_announcement(news):
    """
    Args:
        news (dict): Dict with information about event.

    """
    text = list()
    text.append('*{}* \[[url]({})]'.format(news['title'], news['news_url']))
    text.append(news['content'])

    weekday = weekdays_mapping[dt.fromtimestamp(news['timestamp']).weekday()]
    text.append(emojize(":spiral_calendar: *{}* ({})".format(news['date'], weekday), use_aliases=True))
    text = '\n'.join(text)

    return text


def get_token(path):
    with open(path) as jsn:
        data = json.load(jsn)
    return data['token']


def get_info(url, verbose=False):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    news_events = soup.find('div', attrs={'id': 'news-events-list'})
    item_cells = news_events.find_all('div', attrs={'class': 'item cell'})

    res = list()

    for tmp in item_cells:
        title_html = tmp.select('a')[0]

        news_url = url + title_html.get('href')
        title = title_html.text
        content = tmp.find('div', attrs={'class': 'description'}).text.strip()
        date = tmp.find('span', attrs={'class': 'date'}).text
        timestamp = dt.strptime(date.split(' ')[0], "%d.%m.%Y").timestamp()

        res.append(dict(title=title, news_url=news_url, content=content, date=date, timestamp=timestamp))

        if verbose:
            print('*Date:', date)
            print('*Url:', news_url)
            print('*Title:', title)
            print('*Content:', content)
            print('---')

    return res
