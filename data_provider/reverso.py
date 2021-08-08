import os
import re
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

import interSubs_config as config


def reverso(word):
    reverso_combos = {'ar': 'Arabic', 'de': 'German', 'en': 'English', 'es': 'Spanish', 'fr': 'French', 'he': 'Hebrew',
                      'it': 'Italian', 'nl': 'Dutch', 'pl': 'Polish', 'pt': 'Portuguese', 'ro': 'Romanian',
                      'ru': 'Russian'}

    if not config.lang_from in reverso_combos and not config.lang_to in reverso_combos:
        return [['Language code is not correct.', '']], ['', '']

    url = 'http://context.reverso.net/translation/%s-%s/%s' % (
    reverso_combos[config.lang_from].lower(), reverso_combos[config.lang_to].lower(), quote(word))

    pairs = []
    fname = 'urls/' + url.replace('/', "-")
    try:
        p = open(fname).read().split('=====/////-----')

        if len(p[0].strip()):
            for pi in p[0].strip().split('\n\n'):
                pi = pi.split('\n')
                pairs.append([pi[0], pi[1]])
    except:
        p = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36'}).text

        soup = BeautifulSoup(p, "lxml")
        trs = soup.find_all(class_=re.compile('translation.*ltr.*'))
        exmpls = soup.find_all(class_='example')

        tr_combined = []
        for tr in trs:
            tr_combined.append(tr.get_text().strip().replace('\n', ' '))

            if len(tr_combined) == 4:
                pairs.append(['-', ' :: '.join(tr_combined)])
                tr_combined = []

        for exmpl in exmpls:
            pairs.append([x.strip() for x in exmpl.get_text().split('\n') if len(x.strip())])

        # extra check against double-writing from rouge threads
        if not os.path.isfile(fname):
            print('\n\n'.join(e[0] + '\n' + e[1] for e in pairs), file=open(fname, 'a'))
            print('\n' + '=====/////-----' + '\n', file=open(fname, 'a'))

    return pairs, ['', '']
