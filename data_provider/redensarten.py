import os
import re
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup


def redensarten(word):
    if len(word) < 3:
        return [], ['', '']

    url = 'https://www.redensarten-index.de/suche.php?suchbegriff=' + quote(
        word) + '&bool=relevanz&gawoe=an&suchspalte%5B%5D=rart_ou&suchspalte%5B%5D=rart_varianten_ou&suchspalte%5B%5D=erl_ou&suchspalte%5B%5D=erg_ou'

    pairs = []
    fname = 'urls/' + url.replace('/', "-")
    try:
        p = open(fname).read().split('=====/////-----')
        try:
            word_descr = p[1].strip()
        except:
            word_descr = ''

        if len(p[0].strip()):
            for pi in p[0].strip().split('\n\n'):
                pi = pi.split('\n')
                pairs.append([pi[0], pi[1]])
    except:
        p = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36'})
        p.encoding = 'utf-8'
        p = p.text

        soup = BeautifulSoup(p, "lxml")

        for a in soup.find_all('a', class_='autosyn-icon'):
            a.decompose()

        try:
            table = soup.find_all('table', id='tabelle')[0]
            trs = table.find_all('tr')

            for tr in trs[1:]:
                tds = tr.find_all('td')
                if len(tds) > 1:
                    pairs.append(
                        [re.sub(' +', ' ', tds[0].get_text()).strip(), re.sub(' +', ' ', tds[1].get_text()).strip()])
        except:
            pass

        word_descr = ''

        # extra check against double-writing from rouge threads
        if not os.path.isfile(fname):
            print('\n\n'.join(e[0] + '\n' + e[1] for e in pairs), file=open(fname, 'a'))
            print('\n' + '=====/////-----' + '\n', file=open(fname, 'a'))
            print(word_descr, file=open(fname, 'a'))

    return pairs, ['', '']
