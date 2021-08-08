import os
import re

import requests
from bs4 import BeautifulSoup

import interSubs_config as config


# leo.org
def leo(word):
    language = config.lang_from if config.lang_from != 'de' else config.lang_to

    url = "https://dict.leo.org/dictQuery/m-vocab/%sde/query.xml?tolerMode=nof&rmWords=off&rmSearch=on&searchLoc=0&resultOrder=basic&multiwordShowSingle=on&lang=de&search=%s" % (
    language, word)

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
        req = requests.get(url.format(lang=language))

        content = BeautifulSoup(req.text, "xml")
        pairs = []
        for section in content.sectionlist.findAll('section'):
            if int(section['sctCount']):
                for entry in section.findAll('entry'):
                    res0 = entry.find('side', attrs={'hc': '0'})
                    res1 = entry.find('side', attrs={'hc': '1'})
                    if res0 and res1:
                        line0 = re.sub('\s+', ' ', res0.repr.getText())
                        line1 = re.sub('\s+', ' ', res1.repr.getText())
                        line0 = line0.rstrip('|').strip()
                        line1 = line1.rstrip('|').strip()

                        if res0.attrs['lang'] == config.lang_from:
                            pairs.append([line0, line1])
                        else:
                            pairs.append([line1, line0])

        word_descr = ''
        # extra check against double-writing from rouge threads
        if not os.path.isfile(fname):
            print('\n\n'.join(e[0] + '\n' + e[1] for e in pairs), file=open(fname, 'a'))
            print('\n' + '=====/////-----' + '\n', file=open(fname, 'a'))
            print(word_descr, file=open(fname, 'a'))

    return pairs, ['', '']
