import re
from typing import Tuple, List
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from data.services import USER_AGENT
from models.translation import Translation

SERVICE_NAME = "dict.cc"
URL = "https://%s-%s.dict.cc/?s=%s"


def translate(text: str, lang_from: str, lang_to: str) -> Translation:
    content = _get_content_from_service(URL % (lang_from, lang_to, quote(text)))
    pairs_list = _find_all_original_translation_pairs(content)

    return Translation(SERVICE_NAME, text, pairs_list)


def _get_content_from_service(url: str) -> str:
    response = requests.get(url, headers={'User-Agent': USER_AGENT})
    if response.status_code != requests.codes.ok:
        response.raise_for_status()

    return response.text


def _find_all_original_translation_pairs(content: str) -> List[Tuple[str, str]]:
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
        pairs_list.append((original, translation))

    return pairs_list
