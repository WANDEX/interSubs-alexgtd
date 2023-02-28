import os
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup


# unfinished; site blocks frequent requests
def linguee(word):
    url = 'https://www.linguee.com/german-english/search?source=german&query=%s' % quote(word)

    pairs = []
    fname = config.FDHSN + url.replace('/', "-")
    try:
        p = open(fname).read().split('=====/////-----')
        try:
            word_descr = p[1].strip()
        except:
            word_descr = ''

        for pi in p[0].strip().split('\n\n'):
            pi = pi.split('\n')
            pairs.append([pi[0], pi[1]])
    except:
        # p = open('/home/lom/d/1.html', encoding="ISO-8859-15").read()
        p = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36'}).text

        soup = BeautifulSoup(p, "lxml")
        trs = soup.find_all('div', class_="lemma featured")

        for tr in trs:
            pairs.append([tr.find_all('a')[0].get_text(), '-'])
            for tr2 in tr.find_all('a')[1:]:
                if len(tr2.get_text()):
                    # print(tr2.get_text())
                    pairs.append(['-', tr2.get_text()])
        word_descr = ''

        # extra check against double-writing from rouge threads
        if not os.path.isfile(fname):
            print('\n\n'.join(e[0] + '\n' + e[1] for e in pairs), file=open(fname, 'a'))
            print('\n' + '=====/////-----' + '\n', file=open(fname, 'a'))
            print(word_descr, file=open(fname, 'a'))

    return pairs, ['', '']
