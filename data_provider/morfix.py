import os
import re
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

import config


def morfix(word):
    url = "http://www.morfix.co.il/en/%s" % quote(word)

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
        req = requests.get(url)
        soup = BeautifulSoup(req.text, "lxml")
        divs = soup.find_all('div', class_='title_ph')

        pairs = []
        for div in divs:
            he = div.find('div', class_=re.compile('translation_he'))
            he = re.sub('\s+', ' ', he.get_text()).strip()

            en = div.find('div', class_=re.compile('translation_en'))
            en = re.sub('\s+', ' ', en.get_text()).strip()

            if config.lang_from == 'he':
                pairs.append([he, en])
            else:
                pairs.append([en, he])

        word_descr = ''
        # extra check against double-writing from rouge threads
        if not os.path.isfile(fname):
            print('\n\n'.join(e[0] + '\n' + e[1] for e in pairs), file=open(fname, 'a'))
            print('\n' + '=====/////-----' + '\n', file=open(fname, 'a'))
            print(word_descr, file=open(fname, 'a'))

    return pairs, ['', '']
