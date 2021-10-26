import os
import re
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

import config


def dict_cc(word):
    url = 'https://%s-%s.dict.cc/?s=%s' % (config.lang_from, config.lang_to, quote(word))

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
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36'}).text

        p = re.sub('<div style="float:right;color:#999">\d*</div>', '', p)
        p = re.sub('<span style="color:#666;font-size:10px;padding:0 2px;position:relative;top:-3px">\d*</span>', '', p)

        soup = BeautifulSoup(p, "lxml")
        trs = soup.find_all('tr', id=re.compile('tr\d*'))

        for tr in trs:
            tr2 = tr.find_all('td', class_='td7nl')
            pairs.append([tr2[1].get_text(), tr2[0].get_text()])

            if config.number_of_translations_to_save and len(pairs) > config.number_of_translations_to_save:
                break

        word_descr = ''

        # extra check against double-writing from rouge threads
        if not os.path.isfile(fname):
            print('\n\n'.join(e[0] + '\n' + e[1] for e in pairs), file=open(fname, 'a'))
            print('\n' + '=====/////-----' + '\n', file=open(fname, 'a'))
            print(word_descr, file=open(fname, 'a'))

    return pairs, ['', '']
