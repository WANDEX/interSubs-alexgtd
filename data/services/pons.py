import os
import re
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

import config

pons_combos = ['enes', 'enfr', 'deen', 'enpl', 'ensl', 'defr', 'dees', 'deru', 'depl', 'desl', 'deit', 'dept', 'detr',
               'deel', 'dela', 'espl', 'frpl', 'itpl', 'plru', 'essl', 'frsl', 'itsl', 'enit', 'enpt', 'enru', 'espt',
               'esfr', 'delb', 'dezh', 'enzh', 'eszh', 'frzh', 'denl', 'arde', 'aren', 'dade', 'csde', 'dehu', 'deno',
               'desv', 'dede', 'dedx']


# returns ([[word, translation]..], [morphology = '', gender = ''])
def pons(word):
    if config.lang_from + config.lang_to in pons_combos:
        url = 'http://en.pons.com/translate?q=%s&l=%s%s&in=%s' % (
            quote(word), config.lang_from, config.lang_to, config.lang_from)
    else:
        url = 'http://en.pons.com/translate?q=%s&l=%s%s&in=%s' % (
            quote(word), config.lang_to, config.lang_from, config.lang_from)

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

        soup = BeautifulSoup(p, "lxml")
        trs = soup.find_all('dl')

        for tr in trs:
            try:
                tr1 = tr.find('dt').find('div', class_="source").get_text()
                tr1 = re.sub('\n|\r|\t', ' ', tr1)
                tr1 = re.sub(' +', ' ', tr1).strip()
                if not len(tr1):
                    tr1 = '-'

                tr2 = tr.find('dd').find('div', class_="target").get_text()
                tr2 = re.sub('\n|\r|\t', ' ', tr2)
                tr2 = re.sub(' +', ' ', tr2).strip()
                if not len(tr2):
                    tr2 = '-'
            except:
                continue

            pairs.append([tr1, tr2])

            if config.number_of_translations_to_save and len(pairs) > config.number_of_translations_to_save:
                break

        try:
            word_descr = soup.find_all('h2', class_='')
            if '<i class="icon-bolt">' not in str(word_descr[0]):
                word_descr = re.sub('\n|\r|\t', ' ', word_descr[0].get_text())
                word_descr = re.sub(' +', ' ', word_descr).replace('&lt;', '<').replace('&gt;', '>').replace(' · ',
                                                                                                             '·').replace(
                    ' , ', ', ').strip()
            else:
                word_descr = ''
        except:
            word_descr = ''

        # extra check against double-writing from rouge threads
        if not os.path.isfile(fname):
            print('\n\n'.join(e[0] + '\n' + e[1] for e in pairs), file=open(fname, 'a'))
            print('\n' + '=====/////-----' + '\n', file=open(fname, 'a'))
            print(word_descr, file=open(fname, 'a'))

    if len(word_descr):
        if word_descr.split(' ')[-1] == 'm':
            word_descr_gen = [word_descr[:-2], 'm']
        elif word_descr.split(' ')[-1] == 'f':
            word_descr_gen = [word_descr[:-2], 'f']
        elif word_descr.split(' ')[-1] == 'nt':
            word_descr_gen = [word_descr[:-3], 'nt']
        else:
            word_descr_gen = [word_descr, '']
    else:
        word_descr_gen = ['', '']

    return pairs, word_descr_gen
