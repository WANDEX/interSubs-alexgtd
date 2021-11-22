import os
import re
from typing import Tuple, List
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

import config

USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.167 Safari/537.36"
CACHE_DIR_PATH = "urls/"
URL = "https://%s-%s.dict.cc/?s=%s"


def translate(word: str) -> Tuple[List[List[str]], List[str]]:
    compiled_url = URL % (config.lang_from, config.lang_to, quote(word))
    file_path = CACHE_DIR_PATH + compiled_url.replace('/', "-")

    if os.path.isfile(file_path):
        pairs_list = get_from_local(file_path)
    else:
        pairs_list = get_from_remote(compiled_url)
        store_in_local(file_path, pairs_list)

    return pairs_list, ['', '']


def get_from_remote(url: str) -> List[List[str]]:
    response = requests.get(url, headers={'User-Agent': USER_AGENT})
    if response.status_code != requests.codes.ok:
        response.raise_for_status()

    return _find_all_original_translation_pairs(response.text)


def _find_all_original_translation_pairs(content: str) -> List[List[str]]:
    content = re.sub('<div style="float:right;color:#999">\d*</div>', '', content)
    content = re.sub('<span style="color:#666;font-size:10px;padding:0 2px;position:relative;top:-3px">\d*</span>', '',
                     content)
    soup = BeautifulSoup(content, "lxml")
    translations = soup.find_all('tr', id=re.compile('tr\d*'))

    pairs_list = []
    for tr in translations:
        pairs = tr.find_all('td', class_='td7nl')
        original = pairs[1].get_text()
        translation = pairs[0].get_text()
        pairs_list.append([original, translation])
        if config.number_of_translations_to_save and len(pairs_list) > config.number_of_translations_to_save:
            break

    return pairs_list


def store_in_local(file_path: str, pairs_list: List[List[str]]) -> None:
    print('\n\n'.join(e[0] + '\n' + e[1] for e in pairs_list), file=open(file_path, 'a'))
    print('\n' + '=====/////-----' + '\n', file=open(file_path, 'a'))


def get_from_local(file_path: str) -> List[List[str]]:
    pairs_list = []
    lines = open(file_path).read().split('=====/////-----')
    if len(lines[0].strip()):
        for pair in lines[0].strip().split('\n\n'):
            pair = pair.split('\n')
            pairs_list.append([pair[0], pair[1]])

    return pairs_list
