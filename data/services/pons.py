import re
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from data.services import USER_AGENT
from models.translation import Translation

LANG_COMBINATIONS = [
    'enes', 'enfr', 'deen', 'enpl', 'ensl', 'defr', 'dees', 'deru', 'depl', 'desl', 'deit', 'dept', 'detr', 'deel',
    'dela', 'espl', 'frpl', 'itpl', 'plru', 'essl', 'frsl', 'itsl', 'enit', 'enpt', 'enru', 'espt', 'esfr', 'delb',
    'dezh', 'enzh', 'eszh', 'frzh', 'denl', 'arde', 'aren', 'dade', 'csde', 'dehu', 'deno', 'desv', 'dede', 'dedx'
]
SERVICE_NAME = "pons"
URL = "https://en.pons.com/translate"


class PonsNotValidLanguageCombinationError(Exception):
    pass


def translate(text: str, lang_from: str, lang_to: str) -> Translation:
    if lang_from + lang_to not in LANG_COMBINATIONS:
        raise PonsNotValidLanguageCombinationError

    content = _get_content_from_service(lang_from, lang_to, text)
    pairs_list, _ = _parse_content(content)

    return Translation(SERVICE_NAME, text, pairs_list)


def _get_content_from_service(text: str, lang_from: str, lang_to: str) -> str:
    # Parameter: "q" is search term
    # Parameter: "l" is a dictionary (i.e. deen, deru)
    # Parameter: "in" is the source language
    response = requests.get(
        URL,
        headers={'User-Agent': USER_AGENT},
        params={"q": quote(text), "l": lang_from + lang_to, "in": lang_from}
    )
    if response.status_code != requests.codes.ok:
        response.raise_for_status()

    return response.text


def _parse_content(content: str) -> tuple[list[tuple[str, str]], list[str]]:
    soup = BeautifulSoup(content, "lxml")
    pairs_list = _find_all_original_translation_pairs(soup)
    word_description = _find_word_description(soup)
    return pairs_list, word_description


def _find_all_original_translation_pairs(soup) -> list[tuple[str, str]]:
    pairs_list = []
    pairs = soup.find_all('dl')

    for pair in pairs:
        try:
            original, translation = _find_original_translation_pair(pair)
        except Exception as e:
            print("Couldn't parse (original, translation) pair.\n", e)
            continue

        pairs_list.append((original, translation))

    return pairs_list


def _find_original_translation_pair(pair) -> tuple[str, str]:
    original = pair.find('dt').find('div', class_="source").get_text()
    original = re.sub('\n|\r|\t', ' ', original)
    original = re.sub(' +', ' ', original).strip()
    if not len(original):
        original = '-'

    translation = pair.find('dd').find('div', class_="target").get_text()
    translation = re.sub('\n|\r|\t', ' ', translation)
    translation = re.sub(' +', ' ', translation).strip()
    if not len(translation):
        translation = '-'

    return original, translation


def _find_word_description(soup) -> list[str]:
    try:
        word_description = soup.find_all('h2', class_='')
        if '<i class="icon-bolt">' not in str(word_description[0]):
            word_description = re.sub('\n|\r|\t', ' ', word_description[0].get_text())
            word_description = re.sub(' +', ' ', word_description) \
                .replace('&lt;', '<') \
                .replace('&gt;', '>') \
                .replace(' · ', '·') \
                .replace(' , ', ', ') \
                .strip()
        else:
            word_description = ''
    except Exception as e:
        print("Couldn't parse word description.\n", e)
        word_description = ''

    return _build_word_description_list(word_description)


def _build_word_description_list(word_description: str) -> list[str]:
    if len(word_description):
        if word_description.split(' ')[-1] == 'm':
            resulted_list = [word_description[:-2], 'm']
        elif word_description.split(' ')[-1] == 'f':
            resulted_list = [word_description[:-2], 'f']
        elif word_description.split(' ')[-1] == 'nt':
            resulted_list = [word_description[:-3], 'nt']
        else:
            resulted_list = [word_description, '']
    else:
        resulted_list = ['', '']
    return resulted_list
